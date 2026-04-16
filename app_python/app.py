"""
DevOps Info Service - Flask implementation for Lab 1 Task 1
"""
import os
import json
import socket
import platform
import logging
import time
import threading
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from flask import Flask, jsonify, request, g, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# Prometheus metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'status_code']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently in progress',
    ['method', 'endpoint']
)

# Application-specific metrics
endpoint_calls = Counter(
    'devops_info_endpoint_calls_total',
    'Total endpoint calls in devops info service',
    ['endpoint']
)

system_info_duration = Histogram(
    'devops_info_system_collection_seconds',
    'Time spent collecting system information'
)

# Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
VISITS_FILE = Path(os.getenv('VISITS_FILE', '/data/visits'))
VISITS_LOCK = threading.Lock()

# Application start time (UTC)
START_TIME = datetime.now(timezone.utc)


class JSONFormatter(logging.Formatter):
    """Custom JSON log formatter for structured logging."""

    def format(self, record):
        log_record = {
            'timestamp': datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat().replace('+00:00', 'Z'),
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
        }
        for field in ('method', 'path', 'status_code', 'client_ip'):
            if hasattr(record, field):
                log_record[field] = getattr(record, field)
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_record)


# Configure JSON logging
_handler = logging.StreamHandler()
_handler.setFormatter(JSONFormatter())
logging.basicConfig(level=logging.INFO, handlers=[_handler], force=True)
logger = logging.getLogger(__name__)
logger.info('DevOps Info Service starting', extra={'version': '1.0.0'})


def ensure_visits_storage():
    VISITS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not VISITS_FILE.exists():
        VISITS_FILE.write_text('0\n', encoding='utf-8')


def load_visits():
    try:
        content = VISITS_FILE.read_text(encoding='utf-8').strip()
        return int(content) if content else 0
    except FileNotFoundError:
        return 0
    except (ValueError, OSError):
        logger.warning('Visits file is invalid, resetting counter', extra={'path': str(VISITS_FILE)})
        return 0


def save_visits(count):
    VISITS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', delete=False, dir=str(VISITS_FILE.parent), encoding='utf-8') as tmp:
        tmp.write(f'{count}\n')
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, VISITS_FILE)


def increment_visits():
    with VISITS_LOCK:
        count = load_visits() + 1
        save_visits(count)
        return count


def get_visits():
    with VISITS_LOCK:
        return load_visits()


ensure_visits_storage()


def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }


def get_system_info():
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count() or 1,
        'python_version': platform.python_version(),
    }


def get_endpoint_label():
    if request.url_rule and request.url_rule.rule:
        return request.url_rule.rule
    return request.path or 'unknown'


@app.before_request
def log_request_start():
    g.request_start_time = time.perf_counter()
    g.endpoint_label = get_endpoint_label()
    http_requests_in_progress.labels(method=request.method, endpoint=g.endpoint_label).inc()

    logger.info('Request received', extra={
        'method': request.method,
        'path': request.path,
        'client_ip': request.remote_addr,
    })


@app.after_request
def log_request_end(response):
    endpoint_label = getattr(g, 'endpoint_label', get_endpoint_label())
    request_start_time = getattr(g, 'request_start_time', time.perf_counter())
    duration = max(0.0, time.perf_counter() - request_start_time)
    status_code = str(response.status_code)

    http_requests_total.labels(
        method=request.method,
        endpoint=endpoint_label,
        status_code=status_code
    ).inc()
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=endpoint_label,
        status_code=status_code
    ).observe(duration)
    http_requests_in_progress.labels(method=request.method, endpoint=endpoint_label).dec()

    logger.info('Request completed', extra={
        'method': request.method,
        'path': request.path,
        'status_code': response.status_code,
        'client_ip': request.remote_addr,
    })
    return response


@app.route('/')
def index():
    endpoint_calls.labels(endpoint='/').inc()
    visits = increment_visits()
    uptime = get_uptime()
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    with system_info_duration.time():
        system = get_system_info()

    info = {
        'service': {
            'name': 'devops-info-service',
            'version': '1.0.0',
            'description': 'DevOps course info service',
            'framework': 'Flask'
        },
        'system': system,
        'runtime': {
            'uptime_seconds': uptime['seconds'],
            'uptime_human': uptime['human'],
            'current_time': now,
            'timezone': 'UTC',
            'visits': visits
        },
        'request': {
            'client_ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'method': request.method,
            'path': request.path
        },
        'endpoints': [
            {'path': '/', 'method': 'GET', 'description': 'Service information'},
            {'path': '/health', 'method': 'GET', 'description': 'Health check'},
            {'path': '/metrics', 'method': 'GET', 'description': 'Prometheus metrics'}
        ]
    }

    return jsonify(info)


@app.route('/health')
def health():
    endpoint_calls.labels(endpoint='/health').inc()
    uptime = get_uptime()
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    return jsonify({
        'status': 'healthy',
        'timestamp': now,
        'uptime_seconds': uptime['seconds']
    }), 200


@app.route('/visits')
def visits():
    endpoint_calls.labels(endpoint='/visits').inc()
    return jsonify({
        'visits': get_visits(),
        'file': str(VISITS_FILE)
    }), 200


@app.route('/metrics')
def metrics():
    endpoint_calls.labels(endpoint='/metrics').inc()
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.errorhandler(404)
def not_found(error):
    logger.warning('Not found', extra={'path': request.path, 'client_ip': request.remote_addr})
    return jsonify({'error': 'Not Found', 'message': 'Endpoint does not exist'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error('Internal server error', exc_info=True)
    return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}), 500


if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=DEBUG)
