from __future__ import annotations

import logging
import os
import platform
import socket
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)

# conf
load_dotenv()
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '5000'))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# start time
START_TIME = datetime.now(timezone.utc)

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


def get_service_info() -> dict:
    """return metadata"""
    return {
        'name': 'devops-info-service',
        'version': '1.0.0',
        'description': 'DevOps course info service',
        'framework': 'Flask'
    }


def get_endpoints() -> list[dict]:
    """return a list of available endpoints"""
    return [
        {'path': '/', 'method': 'GET', 'description': 'Service information'},
        {'path': '/health', 'method': 'GET', 'description': 'Health check'}
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
        }
    }
}


@app.before_request
def log_request() -> None:
    logger.debug('Request: %s %s', request.method, request.path)


@app.route('/')
def index():
    """main endpoint"""
    uptime = get_uptime()
    payload = {
        'service': get_service_info(),
        'system': get_system_info(),
        'runtime': {
            'uptime_seconds': uptime['seconds'],
            'uptime_human': uptime['human'],
            'current_time': _iso_utc_now(),
            'timezone': 'UTC'
        },
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
