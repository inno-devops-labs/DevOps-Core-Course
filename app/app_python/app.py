from __future__ import annotations

import json
import logging
import os
import platform
import socket
import tempfile
from pathlib import Path
from threading import Lock
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_swagger_ui import get_swaggerui_blueprint
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest

app = Flask(__name__)

# conf
load_dotenv()
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '5000'))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
DEFAULT_CONFIG_PATH = os.getenv('APP_CONFIG_PATH', os.path.join('config', 'config.json'))
DEFAULT_VISITS_FILE_PATH = os.getenv('VISITS_FILE_PATH', os.path.join('data', 'visits'))

# start time
START_TIME = datetime.now(timezone.utc)
VISITS_LOCK = Lock()
REQUEST_COUNT = Counter(
    'devops_info_http_requests_total',
    'Total HTTP requests handled by the DevOps Info Service.',
    ['method', 'endpoint', 'status'],
)
VISITS_GAUGE = Gauge(
    'devops_info_visits_total',
    'Current persisted visit counter value.',
)
UPTIME_GAUGE = Gauge(
    'devops_info_uptime_seconds',
    'Application uptime in seconds.',
)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info('Application starting...')

# swagger info
SWAGGER_URL = '/docs'
SWAGGER_API_URL = '/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    SWAGGER_API_URL,
    config={'app_name': 'DevOps Info Service'}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def get_uptime() -> dict:
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }


def get_platform_version() -> str:
    system = platform.system()
    if system == 'Linux':
        try:
            os_release = platform.freedesktop_os_release()
            return os_release.get('PRETTY_NAME') or os_release.get('NAME') or platform.release()
        except (OSError, AttributeError):
            return platform.release()
    if system == 'Windows':
        return platform.version()
    return platform.release()


def get_system_info() -> dict:
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': get_platform_version(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count() or 0,
        'python_version': platform.python_version()
    }


def get_request_info() -> dict:
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr or '')
    if ',' in client_ip:
        client_ip = client_ip.split(',')[0].strip()

    return {
        'client_ip': client_ip,
        'user_agent': request.headers.get('User-Agent', ''),
        'method': request.method,
        'path': request.path
    }


def get_config_path() -> Path:
    configured_path = app.config.get('APP_CONFIG_PATH') or os.getenv('APP_CONFIG_PATH') or DEFAULT_CONFIG_PATH
    return Path(configured_path)


def get_visits_file_path() -> Path:
    configured_path = app.config.get('VISITS_FILE_PATH') or os.getenv('VISITS_FILE_PATH') or DEFAULT_VISITS_FILE_PATH
    return Path(configured_path)


def _default_application_config() -> dict[str, Any]:
    return {
        'applicationName': 'devops-info-service',
        'environment': os.getenv('APP_ENV', 'dev'),
        'featureFlags': {
            'visitsCounter': True,
            'swaggerEnabled': True
        },
        'settings': {
            'logLevel': os.getenv('LOG_LEVEL', 'info'),
            'configPath': str(get_config_path()),
            'visitsFilePath': str(get_visits_file_path())
        }
    }


def _merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def load_application_config() -> dict[str, Any]:
    config = _default_application_config()
    config_path = get_config_path()

    if not config_path.exists():
        return config

    try:
        file_config = json.loads(config_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning('Failed to load config file %s: %s', config_path, exc)
        return config

    return _merge_dicts(config, file_config)


def _write_text_atomically(file_path: Path, value: str) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=file_path.parent, delete=False) as temp_file:
        temp_file.write(value)
        temp_name = temp_file.name
    os.replace(temp_name, file_path)


def _read_visit_count_unlocked(file_path: Path) -> int:
    try:
        return int(file_path.read_text(encoding='utf-8').strip())
    except FileNotFoundError:
        return 0
    except ValueError:
        logger.warning('Visits file %s contains invalid data. Resetting counter to 0.', file_path)
        return 0


def initialize_visit_counter() -> None:
    file_path = get_visits_file_path()
    with VISITS_LOCK:
        if file_path.exists():
            current_value = _read_visit_count_unlocked(file_path)
            _write_text_atomically(file_path, str(current_value))
            return
        _write_text_atomically(file_path, '0')


def increment_visit_counter() -> int:
    file_path = get_visits_file_path()
    with VISITS_LOCK:
        current_value = _read_visit_count_unlocked(file_path) + 1
        _write_text_atomically(file_path, str(current_value))
        return current_value


def get_visit_count() -> int:
    file_path = get_visits_file_path()
    with VISITS_LOCK:
        return _read_visit_count_unlocked(file_path)


def get_service_info() -> dict:
    """return metadata"""
    app_config = load_application_config()
    return {
        'name': app_config.get('applicationName', 'devops-info-service'),
        'version': '1.0.0',
        'description': 'DevOps course info service',
        'framework': 'Flask',
        'environment': app_config.get('environment', os.getenv('APP_ENV', 'dev'))
    }


def get_endpoints() -> list[dict]:
    """return a list of available endpoints"""
    return [
        {'path': '/', 'method': 'GET', 'description': 'Service information'},
        {'path': '/health', 'method': 'GET', 'description': 'Health check'},
        {'path': '/visits', 'method': 'GET', 'description': 'Current visits count'},
        {'path': '/metrics', 'method': 'GET', 'description': 'Prometheus metrics'}
    ]

#API
OPENAPI_SPEC = {
    'openapi': '3.0.3',
    'info': {
        'title': 'DevOps Info Service',
        'version': '1.0.0',
        'description': 'Service and system information API'
    },
    'paths': {
        '/': {
            'get': {
                'summary': 'Service information',
                'responses': {
                    '200': {
                        'description': 'Service and system information'
                    }
                }
            }
        },
        '/health': {
            'get': {
                'summary': 'Health check',
                'responses': {
                    '200': {
                        'description': 'Health status'
                    }
                }
            }
        },
        '/visits': {
            'get': {
                'summary': 'Visits counter',
                'responses': {
                    '200': {
                        'description': 'Current visits count'
                    }
                }
            }
        },
        '/metrics': {
            'get': {
                'summary': 'Prometheus metrics',
                'responses': {
                    '200': {
                        'description': 'Prometheus exposition format metrics'
                    }
                }
            }
        }
    }
}

@app.before_request
def log_request() -> None:
    logger.debug('Request: %s %s', request.method, request.path)


@app.after_request
def record_request_metrics(response):
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.endpoint or 'unknown',
        status=str(response.status_code),
    ).inc()
    return response


@app.route('/')
def index():
    """main endpoint"""
    uptime = get_uptime()
    visits = increment_visit_counter()
    payload = {
        'service': get_service_info(),
        'system': get_system_info(),
        'runtime': {
            'uptime_seconds': uptime['seconds'],
            'uptime_human': uptime['human'],
            'current_time': _iso_utc_now(),
            'timezone': 'UTC'
        },
        'visits': {
            'count': visits,
            'storage_path': str(get_visits_file_path())
        },
        'configuration': load_application_config(),
        'request': get_request_info(),
        'endpoints': get_endpoints()
    }
    return jsonify(payload)


@app.route('/health')
def health():
    """health check endpoint"""
    uptime = get_uptime()
    return jsonify({
        'status': 'healthy',
        'timestamp': _iso_utc_now(),
        'uptime_seconds': uptime['seconds']
    })


@app.route('/visits')
def visits():
    return jsonify({
        'count': get_visit_count(),
        'storage_path': str(get_visits_file_path())
    })


@app.route('/metrics')
def metrics():
    UPTIME_GAUGE.set(get_uptime()['seconds'])
    VISITS_GAUGE.set(get_visit_count())
    return app.response_class(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route('/swagger.json')
def swagger_json():
    return jsonify(OPENAPI_SPEC)


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500


if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=DEBUG)
