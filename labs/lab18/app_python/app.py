"""
DevOps Info Service
Main application module
"""
import os
import json
import time
import socket
import platform
import logging
import threading
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured log aggregation."""

    def format(self, record):
        log_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        if hasattr(record, 'method'):
            log_data['method'] = record.method
        if hasattr(record, 'path'):
            log_data['path'] = record.path
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
        if hasattr(record, 'client_ip'):
            log_data['client_ip'] = record.client_ip
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_data)


app = Flask(__name__)

# --- Prometheus metrics (RED method) ---
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed'
)

devops_info_endpoint_calls = Counter(
    'devops_info_endpoint_calls_total',
    'Business-level endpoint call counter',
    ['endpoint']
)

devops_info_system_collection_seconds = Histogram(
    'devops_info_system_collection_seconds',
    'Time spent collecting system information'
)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.handlers = [handler]
logging.root.setLevel(logging.INFO)

werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.handlers = [handler]
werkzeug_logger.setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8080))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
VISITS_FILE = os.getenv('VISITS_FILE', '/data/visits')

# Application start time
START_TIME = datetime.now(timezone.utc)

# Thread-safe visits counter backed by file
_visits_lock = threading.Lock()


def _read_visits():
    try:
        with open(VISITS_FILE, 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def _write_visits(count):
    os.makedirs(os.path.dirname(VISITS_FILE), exist_ok=True)
    tmp = VISITS_FILE + '.tmp'
    with open(tmp, 'w') as f:
        f.write(str(count))
    os.replace(tmp, VISITS_FILE)


def increment_visits():
    with _visits_lock:
        count = _read_visits() + 1
        _write_visits(count)
        return count


def get_system_info():
    """Collect system information."""
    with devops_info_system_collection_seconds.time():
        return {
            'hostname': socket.gethostname(),
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'cpu_count': os.cpu_count(),
            'python_version': platform.python_version()
        }


def get_uptime():
    """Calculate application uptime."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    # Format human-readable uptime
    if hours > 0:
        human = f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
    else:
        human = f"{minutes} minute{'s' if minutes != 1 else ''}"

    return {
        'seconds': seconds,
        'human': human
    }


@app.before_request
def before_request_hook():
    """Track request start time and in-progress gauge."""
    if request.path == '/metrics':
        return
    request._start_time = time.monotonic()
    http_requests_in_progress.inc()
    logger.info(
        'Incoming request',
        extra={
            'method': request.method,
            'path': request.path,
            'client_ip': request.remote_addr,
        }
    )


@app.after_request
def after_request_hook(response):
    """Record metrics and log response."""
    if request.path == '/metrics':
        return response

    endpoint = request.path
    method = request.method
    status = str(response.status_code)

    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()

    duration = time.monotonic() - getattr(request, '_start_time', time.monotonic())
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)

    http_requests_in_progress.dec()

    logger.info(
        'Request completed',
        extra={
            'method': method,
            'path': endpoint,
            'status_code': response.status_code,
            'client_ip': request.remote_addr,
        }
    )
    return response


@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint."""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}


@app.route('/')
def index():
    """Main endpoint - service and system information."""
    devops_info_endpoint_calls.labels(endpoint='/').inc()
    visits = increment_visits()
    uptime = get_uptime()
    system = get_system_info()

    response = {
        'service': {
            'name': 'devops-info-service',
            'version': '1.0.0',
            'description': 'DevOps course info service',
            'framework': 'Flask'
        },
        'visits': visits,
        'system': system,
        'runtime': {
            'uptime_seconds': uptime['seconds'],
            'uptime_human': uptime['human'],
            'current_time': datetime.now(timezone.utc).isoformat(),
            'timezone': 'UTC'
        },
        'request': {
            'client_ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'method': request.method,
            'path': request.path
        },
        'endpoints': [
            {
                'path': '/',
                'method': 'GET',
                'description': 'Service information'
            },
            {
                'path': '/health',
                'method': 'GET',
                'description': 'Health check'
            },
            {
                'path': '/visits',
                'method': 'GET',
                'description': 'Visit counter'
            },
            {
                'path': '/metrics',
                'method': 'GET',
                'description': 'Prometheus metrics'
            }
        ]
    }

    return jsonify(response)


@app.route('/visits')
def visits():
    """Return current visit count."""
    devops_info_endpoint_calls.labels(endpoint='/visits').inc()
    return jsonify({'visits': _read_visits()})


@app.route('/health')
def health():
    """Health check endpoint for monitoring."""
    devops_info_endpoint_calls.labels(endpoint='/health').inc()
    uptime = get_uptime()

    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': uptime['seconds']
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    logger.warning(
        'Not found',
        extra={
            'method': request.method,
            'path': request.path,
            'status_code': 404,
            'client_ip': request.remote_addr,
        }
    )
    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(
        f'Internal server error: {error}',
        extra={
            'method': request.method,
            'path': request.path,
            'status_code': 500,
            'client_ip': request.remote_addr,
        }
    )
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500


if __name__ == '__main__':
    logger.info(
        f'Starting DevOps Info Service on {HOST}:{PORT}',
        extra={'method': 'STARTUP', 'path': '/'}
    )
    logger.info(f'Debug mode: {DEBUG}')
    app.run(host=HOST, port=PORT, debug=DEBUG)
