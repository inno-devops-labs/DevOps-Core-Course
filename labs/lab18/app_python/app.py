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
from flask import Flask, jsonify, request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured logging."""

    EXTRA_FIELDS = ("method", "path", "status_code", "client_ip")

    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in self.EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                log_data[field] = value
        if record.exc_info and record.exc_info[0]:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.handlers = [handler]
logging.root.setLevel(logging.INFO)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configuration from environment variables
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Application start time for uptime calculation
START_TIME = datetime.now(timezone.utc)

# ── Visits counter ──────────────────────────────────────────────────
VISITS_FILE = os.getenv('VISITS_FILE', '/tmp/data/visits')
_visits_lock = threading.Lock()


def _read_visits():
    try:
        with open(VISITS_FILE, 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError, PermissionError):
        return 0


def _write_visits(count):
    try:
        os.makedirs(os.path.dirname(VISITS_FILE), exist_ok=True)
        tmp = VISITS_FILE + '.tmp'
        with open(tmp, 'w') as f:
            f.write(str(count))
        os.replace(tmp, VISITS_FILE)
    except PermissionError:
        logger.warning("Cannot write visits file: permission denied")

# ── Prometheus metrics ──────────────────────────────────────────────
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

endpoint_calls = Counter(
    'devops_info_endpoint_calls',
    'Endpoint call count',
    ['endpoint']
)

system_info_duration = Histogram(
    'devops_info_system_collection_seconds',
    'Time spent collecting system information'
)


def get_system_info():
    """Collect system information."""
    with system_info_duration.time():
        try:
            return {
                'hostname': socket.gethostname(),
                'platform': platform.system(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'cpu_count': os.cpu_count(),
                'python_version': platform.python_version()
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {}


def get_uptime():
    """Calculate application uptime since start."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    # Format human-readable uptime
    if hours > 0:
        human = f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
    elif minutes > 0:
        human = f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        human = f"{seconds} second{'s' if seconds != 1 else ''}"

    return {
        'seconds': seconds,
        'human': human
    }


def get_request_info():
    """Extract current request information."""
    return {
        'client_ip': request.remote_addr or 'unknown',
        'user_agent': request.headers.get('User-Agent', 'unknown'),
        'method': request.method,
        'path': request.path
    }


@app.before_request
def before_request_hook():
    if request.path == '/metrics':
        return
    request._start_time = time.monotonic()
    http_requests_in_progress.inc()
    logger.info("Incoming request", extra={
        "method": request.method,
        "path": request.path,
        "client_ip": request.remote_addr,
    })


@app.after_request
def after_request_hook(response):
    if request.path == '/metrics':
        return response
    duration = time.monotonic() - getattr(request, '_start_time', time.monotonic())
    endpoint = request.path
    http_requests_total.labels(
        method=request.method,
        endpoint=endpoint,
        status=str(response.status_code)
    ).inc()
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=endpoint
    ).observe(duration)
    http_requests_in_progress.dec()
    logger.info("Response sent", extra={
        "method": request.method,
        "path": request.path,
        "status_code": response.status_code,
        "client_ip": request.remote_addr,
    })
    return response


@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route('/')
def index():
    """Main endpoint providing comprehensive service and system information."""
    endpoint_calls.labels(endpoint='/').inc()
    uptime = get_uptime()

    with _visits_lock:
        visits = _read_visits() + 1
        _write_visits(visits)

    response_data = {
        'service': {
            'name': 'devops-info-service',
            'version': '1.0.0',
            'description': 'DevOps course info service',
            'framework': 'Flask'
        },
        'system': get_system_info(),
        'runtime': {
            'uptime_seconds': uptime['seconds'],
            'uptime_human': uptime['human'],
            'current_time': datetime.now(timezone.utc).isoformat(),
            'timezone': 'UTC'
        },
        'request': get_request_info(),
        'visits': visits,
        'endpoints': [
            {
                'path': '/',
                'method': 'GET',
                'description': 'Service information'
            },
            {
                'path': '/visits',
                'method': 'GET',
                'description': 'Visit counter'
            },
            {
                'path': '/health',
                'method': 'GET',
                'description': 'Health check'
            },
            {
                'path': '/metrics',
                'method': 'GET',
                'description': 'Prometheus metrics'
            }
        ]
    }

    return jsonify(response_data)


@app.route('/visits')
def visits():
    """Return the current visit count."""
    endpoint_calls.labels(endpoint='/visits').inc()
    count = _read_visits()
    return jsonify({'visits': count})


@app.route('/health')
def health():
    """Health check endpoint for monitoring and orchestration tools."""
    endpoint_calls.labels(endpoint='/health').inc()
    uptime = get_uptime()

    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': uptime['seconds']
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors with JSON response."""
    logger.warning(f'404 error: {request.path}')
    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist',
        'path': request.path
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors with JSON response."""
    logger.error(f'500 error: {error}')
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500


if __name__ == '__main__':
    logger.info(f'Starting DevOps Info Service...')
    logger.info(f'Host: {HOST}, Port: {PORT}, Debug: {DEBUG}')
    logger.info(f'Visit: http://{HOST}:{PORT}/')

    app.run(host=HOST, port=PORT, debug=DEBUG)
