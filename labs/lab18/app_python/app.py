import os
import socket
import platform
import logging
import json
import sys
import time
from datetime import datetime, timezone
from flask import Flask, jsonify, request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# JSON Formatter for structured logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        if hasattr(record, 'method'):
            log_data['method'] = record.method
        if hasattr(record, 'path'):
            log_data['path'] = record.path
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
        if hasattr(record, 'client_ip'):
            log_data['client_ip'] = record.client_ip
        if hasattr(record, 'user_agent'):
            log_data['user_agent'] = record.user_agent
        return json.dumps(log_data)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers = []
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

app = Flask(__name__)

# Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Application start time
START_TIME = datetime.now(timezone.utc)

# Visits counter file path
VISITS_FILE = os.getenv('VISITS_FILE', '/data/visits')


def read_visits():
    try:
        with open(VISITS_FILE, 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def write_visits(count):
    os.makedirs(os.path.dirname(VISITS_FILE), exist_ok=True)
    with open(VISITS_FILE, 'w') as f:
        f.write(str(count))

# ── Prometheus Metrics ──────────────────────────────────────────────────────
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

endpoint_calls_total = Counter(
    'devops_info_endpoint_calls_total',
    'Total calls per endpoint',
    ['endpoint']
)

system_info_collection_seconds = Histogram(
    'devops_info_system_collection_seconds',
    'Time spent collecting system info'
)
# ────────────────────────────────────────────────────────────────────────────

logger.info('Application starting', extra={
    'host': HOST, 'port': PORT, 'debug': DEBUG,
    'python_version': platform.python_version(),
    'platform': platform.system()
})


def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60
    if hours > 0:
        human = f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
    elif minutes > 0:
        human = f"{minutes} minute{'s' if minutes != 1 else ''}, {remaining_seconds} second{'s' if remaining_seconds != 1 else ''}"
    else:
        human = f"{remaining_seconds} second{'s' if remaining_seconds != 1 else ''}"
    return {'seconds': seconds, 'human': human}


def get_system_info():
    t0 = time.time()
    try:
        platform_info = platform.uname()
        info = {
            'hostname': socket.gethostname(),
            'platform': platform_info.system,
            'platform_version': platform_info.version,
            'architecture': platform_info.machine,
            'cpu_count': os.cpu_count(),
            'python_version': platform.python_version()
        }
    except Exception as e:
        logger.error('Error getting system info', extra={'error': str(e)})
        info = {
            'hostname': 'unknown', 'platform': 'unknown',
            'platform_version': 'unknown', 'architecture': 'unknown',
            'cpu_count': 0, 'python_version': platform.python_version()
        }
    system_info_collection_seconds.observe(time.time() - t0)
    return info


def get_request_info():
    return {
        'client_ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown'),
        'method': request.method,
        'path': request.path
    }


@app.before_request
def before_request():
    request._start_time = time.time()
    http_requests_in_progress.inc()
    logger.info('Incoming request', extra={
        'method': request.method,
        'path': request.path,
        'client_ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown')
    })


@app.after_request
def after_request(response):
    duration = time.time() - getattr(request, '_start_time', time.time())
    endpoint = request.path
    http_requests_in_progress.dec()
    http_requests_total.labels(
        method=request.method,
        endpoint=endpoint,
        status=str(response.status_code)
    ).inc()
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=endpoint
    ).observe(duration)
    logger.info('Outgoing response', extra={
        'method': request.method,
        'path': request.path,
        'status_code': response.status_code,
        'client_ip': request.remote_addr
    })
    return response


@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route('/visits')
def visits():
    endpoint_calls_total.labels(endpoint='/visits').inc()
    count = read_visits()
    return jsonify({'visits': count})


@app.route('/')
def index():
    endpoint_calls_total.labels(endpoint='/').inc()
    # Increment visits counter
    count = read_visits() + 1
    write_visits(count)
    uptime = get_uptime()
    system_info = get_system_info()
    request_info = get_request_info()
    response = {
        'service': {
            'name': 'devops-info-service',
            'version': '1.0.0',
            'description': 'DevOps course info service',
            'framework': 'Flask'
        },
        'system': system_info,
        'runtime': {
            'uptime_seconds': uptime['seconds'],
            'uptime_human': uptime['human'],
            'current_time': datetime.now(timezone.utc).isoformat(),
            'timezone': 'UTC'
        },
        'request': request_info,
        'endpoints': [
            {'path': '/', 'method': 'GET', 'description': 'Service information'},
            {'path': '/health', 'method': 'GET', 'description': 'Health check'},
            {'path': '/visits', 'method': 'GET', 'description': 'Visit counter'},
            {'path': '/metrics', 'method': 'GET', 'description': 'Prometheus metrics'}
        ]
    }
    pretty = request.args.get('pretty', 'false').lower() == 'true'
    if pretty:
        return Response(json.dumps(response, indent=4), status=200, mimetype='application/json')
    return jsonify(response)


@app.route('/health')
def health():
    endpoint_calls_total.labels(endpoint='/health').inc()
    uptime = get_uptime()
    response = {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': uptime['seconds']
    }
    pretty = request.args.get('pretty', 'false').lower() == 'true'
    if pretty:
        return Response(json.dumps(response, indent=4), status=200, mimetype='application/json')
    return jsonify(response)


@app.errorhandler(404)
def not_found(error):
    logger.warning('Page not found', extra={'path': request.path, 'client_ip': request.remote_addr})
    return jsonify({'error': 'Not Found', 'message': 'Endpoint does not exist'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error('Internal server error', extra={'path': request.path, 'error': str(error)})
    return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}), 500


if __name__ == '__main__':
    logger.info('Starting DevOps Info Service', extra={'host': HOST, 'port': PORT, 'debug': DEBUG})
    app.run(host=HOST, port=PORT, debug=DEBUG)
