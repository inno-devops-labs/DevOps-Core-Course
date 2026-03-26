from __future__ import annotations

import json
import logging
import os
import platform
import socket
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, Response, g, jsonify, request
from flask_swagger_ui import get_swaggerui_blueprint
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

app = Flask(__name__)

TRACKED_ENDPOINTS = {'/', '/health', '/ready', '/metrics', '/swagger.json'}

HTTP_REQUESTS_TOTAL = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed',
    ['method', 'endpoint', 'status_code']
)

DEVOPS_INFO_ENDPOINT_CALLS_TOTAL = Counter(
    'devops_info_endpoint_calls_total',
    'Total endpoint calls for DevOps info service',
    ['endpoint']
)

DEVOPS_INFO_SYSTEM_COLLECTION_SECONDS = Histogram(
    'devops_info_system_collection_seconds',
    'System info collection duration in seconds'
)


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            'timestamp': datetime.fromtimestamp(
                record.created,
                timezone.utc
            ).isoformat(timespec='milliseconds').replace('+00:00', 'Z'),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        extra_fields = (
            'event',
            'method',
            'path',
            'status_code',
            'client_ip',
            'user_agent',
            'duration_ms',
            'host',
            'port',
            'debug',
        )

        for field in extra_fields:
            if hasattr(record, field):
                payload[field] = getattr(record, field)

        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True)


def configure_logging() -> logging.Logger:
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    # Route Flask internals through the same root logger.
    app.logger.handlers.clear()
    app.logger.propagate = True

    return logging.getLogger('devops-info-service')


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def get_client_ip() -> str:
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr or '')
    if ',' in client_ip:
        return client_ip.split(',')[0].strip()
    return client_ip


def normalize_endpoint() -> str:
    url_rule = getattr(request, 'url_rule', None)
    endpoint = url_rule.rule if url_rule and url_rule.rule else request.path

    if endpoint.startswith('/docs'):
        return '/docs'
    if endpoint in TRACKED_ENDPOINTS:
        return endpoint
    return '/other'


# conf
load_dotenv()
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '5000'))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# start time
START_TIME = datetime.now(timezone.utc)

# logging
logger = configure_logging()
logger.info(
    'Application starting',
    extra={
        'event': 'startup',
        'host': HOST,
        'port': PORT,
        'debug': DEBUG,
    }
)

# swagger info
SWAGGER_URL = '/docs'
SWAGGER_API_URL = '/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    SWAGGER_API_URL,
    config={'app_name': 'DevOps Info Service'}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


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
    return {
        'client_ip': get_client_ip(),
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
        {'path': '/health', 'method': 'GET', 'description': 'Health check'},
        {'path': '/ready', 'method': 'GET', 'description': 'Readiness check'},
        {'path': '/metrics', 'method': 'GET', 'description': 'Prometheus metrics'},
    ]


# API
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
        '/ready': {
            'get': {
                'summary': 'Readiness check',
                'responses': {
                    '200': {
                        'description': 'Readiness status'
                    }
                }
            }
        },
        '/metrics': {
            'get': {
                'summary': 'Prometheus metrics',
                'responses': {
                    '200': {
                        'description': 'Prometheus text exposition format'
                    }
                }
            }
        }
    }
}


@app.before_request
def log_request() -> None:
    g.request_started_at = time.perf_counter()
    g.normalized_endpoint = normalize_endpoint()

    HTTP_REQUESTS_IN_PROGRESS.labels(
        method=request.method,
        endpoint=g.normalized_endpoint,
        status_code='in_progress',
    ).inc()

    logger.info(
        'Incoming request',
        extra={
            'event': 'request_start',
            'method': request.method,
            'path': request.path,
            'client_ip': get_client_ip(),
            'user_agent': request.headers.get('User-Agent', ''),
        }
    )


@app.after_request
def log_response(response):
    started_at = getattr(g, 'request_started_at', None)
    duration_seconds = None
    duration_ms = None
    if started_at is not None:
        duration_seconds = time.perf_counter() - started_at
        duration_ms = round(duration_seconds * 1000, 2)

    endpoint = getattr(g, 'normalized_endpoint', normalize_endpoint())
    status_code = str(response.status_code)

    HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=status_code,
    ).inc()

    if duration_seconds is not None:
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(duration_seconds)

    HTTP_REQUESTS_IN_PROGRESS.labels(
        method=request.method,
        endpoint=endpoint,
        status_code='in_progress',
    ).dec()

    log_extra: dict[str, object] = {
        'event': 'request_end',
        'method': request.method,
        'path': request.path,
        'status_code': response.status_code,
        'client_ip': get_client_ip(),
    }
    if duration_ms is not None:
        log_extra['duration_ms'] = duration_ms

    logger.log(
        logging.ERROR if response.status_code >= 500 else logging.INFO,
        'Request completed',
        extra=log_extra
    )
    return response


@app.route('/')
def index():
    """main endpoint"""
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint='/').inc()

    uptime = get_uptime()
    with DEVOPS_INFO_SYSTEM_COLLECTION_SECONDS.time():
        system_info = get_system_info()

    payload = {
        'service': get_service_info(),
        'system': system_info,
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
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint='/health').inc()
    uptime = get_uptime()
    return jsonify({
        'status': 'healthy',
        'timestamp': _iso_utc_now(),
        'uptime_seconds': uptime['seconds']
    })


@app.route('/ready')
def ready():
    """readiness check endpoint"""
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint='/ready').inc()
    return jsonify({
        'status': 'ready',
        'timestamp': _iso_utc_now(),
    })


@app.route('/metrics')
def metrics():
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint='/metrics').inc()
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route('/swagger.json')
def swagger_json():
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint='/swagger.json').inc()
    return jsonify(OPENAPI_SPEC)


@app.errorhandler(404)
def not_found(error):
    logger.warning(
        'Endpoint not found',
        extra={
            'event': 'http_404',
            'method': request.method,
            'path': request.path,
            'client_ip': get_client_ip(),
            'status_code': 404,
        }
    )
    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    original_error = getattr(error, 'original_exception', None)
    extra = {
        'event': 'http_500',
        'method': request.method,
        'path': request.path,
        'client_ip': get_client_ip(),
        'status_code': 500,
    }

    if original_error is not None:
        logger.exception(
            'Unhandled application exception',
            exc_info=(type(original_error), original_error, original_error.__traceback__),
            extra=extra
        )
    else:
        logger.error(
            'Internal server error',
            extra=extra
        )

    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500


if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=DEBUG)
