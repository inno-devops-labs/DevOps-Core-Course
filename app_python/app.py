"""
DevOps Info Service
Main application module
"""
import json
import os
import socket
import platform
import logging
import sys
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter
from datetime import datetime, timezone
from flask import Flask, Response, jsonify, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

try:
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None


def format_timestamp(timestamp: datetime | None = None) -> str:
    """Return a UTC timestamp in ISO-8601 format."""
    value = timestamp or datetime.now(timezone.utc)
    return value.isoformat(timespec='milliseconds').replace('+00:00', 'Z')


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for log aggregation systems."""

    default_attrs = {
        'args',
        'asctime',
        'created',
        'exc_info',
        'exc_text',
        'filename',
        'funcName',
        'levelname',
        'levelno',
        'lineno',
        'module',
        'msecs',
        'message',
        'msg',
        'name',
        'pathname',
        'process',
        'processName',
        'relativeCreated',
        'stack_info',
        'taskName',
        'thread',
        'threadName',
    }

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            'timestamp': format_timestamp(
                datetime.fromtimestamp(record.created, tz=timezone.utc),
            ),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if key in self.default_attrs:
                continue
            payload[key] = value

        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> logging.Logger:
    """Configure application-wide JSON logging to stdout."""
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(stream_handler)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

    return logging.getLogger('devops-info-service')


logger = configure_logging()

app = Flask(__name__)

# Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
VISITS_FILE = os.getenv('VISITS_FILE', 'data/visits')
VISITS_LOCK_FILE = f'{VISITS_FILE}.lock'
VISITS_MUTEX = threading.Lock()

# Application start time
START_TIME = datetime.now(timezone.utc)

# Known endpoints are exposed as-is; unknown paths are grouped to keep
# label values low-cardinality.
KNOWN_ENDPOINTS = {'/', '/health', '/metrics', '/boom', '/visits'}

# RED metrics for HTTP traffic.
HTTP_REQUESTS_TOTAL = Counter(
    'http_requests_total',
    'Total HTTP requests processed',
    ['method', 'endpoint', 'status_code'],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'status_code'],
)
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed',
    ['method', 'endpoint'],
)

# Application-specific business metrics.
ENDPOINT_CALLS_TOTAL = Counter(
    'devops_info_endpoint_calls_total',
    'Total calls to service endpoints',
    ['endpoint'],
)
SYSTEM_INFO_COLLECTION_SECONDS = Histogram(
    'devops_info_system_info_collection_seconds',
    'Time spent collecting system information',
)


def normalize_endpoint(path: str) -> str:
    """Normalize unknown paths so label values do not explode."""
    return path if path in KNOWN_ENDPOINTS else '/other'


def get_uptime():
    """Calculate application uptime."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    human = (
        f"{hours} hour{'s' if hours != 1 else ''}, "
        f"{minutes} minute{'s' if minutes != 1 else ''}"
    )
    return {'seconds': seconds, 'human': human}


def get_system_info():
    """Collect system information."""
    with SYSTEM_INFO_COLLECTION_SECONDS.time():
        return {
            'hostname': socket.gethostname(),
            'platform': platform.system(),
            'platform_version': platform.platform(),
            'architecture': platform.machine(),
            'cpu_count': os.cpu_count() or 0,
            'python_version': platform.python_version(),
        }


def get_service_info():
    """Get service metadata."""
    return {
        'name': 'devops-info-service',
        'version': '1.0.0',
        'description': 'DevOps course info service',
        'framework': 'Flask'
    }


def get_runtime_info():
    """Get runtime information."""
    uptime = get_uptime()
    current_time = (
        datetime.now(timezone.utc)
        .isoformat()
        .replace('+00:00', '.000Z')
    )
    return {
        'uptime_seconds': uptime['seconds'],
        'uptime_human': uptime['human'],
        'current_time': current_time,
        'timezone': 'UTC',
    }


def get_request_info():
    """Get current request information."""
    return {
        'client_ip': get_client_ip(),
        'user_agent': request.headers.get('User-Agent', 'unknown'),
        'method': request.method,
        'path': request.path,
    }


def ensure_visits_parent_dir() -> None:
    """Create parent directory for visits data files when needed."""
    Path(VISITS_FILE).parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def acquire_visits_lock():
    """Serialize read/write access to visits files."""
    ensure_visits_parent_dir()
    with VISITS_MUTEX:
        with open(VISITS_LOCK_FILE, 'a+', encoding='utf-8') as lock_file:
            if fcntl is not None:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                if fcntl is not None:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def read_visits_count() -> int:
    """Return current visits counter value or zero when file is absent."""
    try:
        with open(VISITS_FILE, 'r', encoding='utf-8') as data_file:
            raw_value = data_file.read().strip()
            return int(raw_value) if raw_value else 0
    except FileNotFoundError:
        return 0
    except ValueError:
        logger.warning(
            'visits_file_invalid_content',
            extra={'path': VISITS_FILE},
        )
        return 0


def write_visits_count(value: int) -> None:
    """Persist visits counter with an atomic file replace."""
    ensure_visits_parent_dir()
    temp_fd, temp_path = tempfile.mkstemp(
        prefix='visits-',
        dir=str(Path(VISITS_FILE).parent),
    )
    try:
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as temp_file:
            temp_file.write(f'{value}\n')
        os.replace(temp_path, VISITS_FILE)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def increment_visits_count() -> int:
    """Increase visits counter by one and return updated value."""
    with acquire_visits_lock():
        current = read_visits_count()
        updated = current + 1
        write_visits_count(updated)
        return updated


def get_visits_count() -> int:
    """Read current visits counter value."""
    with acquire_visits_lock():
        return read_visits_count()


def get_client_ip() -> str:
    """Extract client IP address with proxy awareness."""
    forwarded_for = request.headers.get('X-Forwarded-For', '')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()

    return request.remote_addr or 'unknown'


@app.before_request
def log_request_started():
    """Log incoming HTTP requests before handlers execute."""
    request.start_time = perf_counter()
    request.metric_endpoint = normalize_endpoint(request.path)
    if request.path != '/metrics':
        HTTP_REQUESTS_IN_PROGRESS.labels(
            method=request.method,
            endpoint=request.metric_endpoint,
        ).inc()
    logger.info(
        'request_started',
        extra={
            'method': request.method,
            'path': request.path,
            'client_ip': get_client_ip(),
            'user_agent': request.headers.get('User-Agent', 'unknown'),
        },
    )


@app.after_request
def log_request_completed(response):
    """Log request completion status and execution time."""
    start_time = getattr(request, 'start_time', perf_counter())
    endpoint = getattr(
        request,
        'metric_endpoint',
        normalize_endpoint(request.path),
    )
    duration_seconds = perf_counter() - start_time
    duration_ms = int(duration_seconds * 1000)

    level = logging.INFO
    if response.status_code >= 500:
        level = logging.ERROR
    elif response.status_code >= 400:
        level = logging.WARNING

    logger.log(
        level,
        'request_completed',
        extra={
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'client_ip': get_client_ip(),
            'duration_ms': duration_ms,
        },
    )

    if request.path != '/metrics':
        status_code = str(response.status_code)
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=status_code,
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=status_code,
        ).observe(duration_seconds)
        HTTP_REQUESTS_IN_PROGRESS.labels(
            method=request.method,
            endpoint=endpoint,
        ).dec()
    return response


@app.route('/')
def index():
    """Main endpoint - service and system information."""
    ENDPOINT_CALLS_TOTAL.labels(endpoint='/').inc()
    visits_count = increment_visits_count()
    response = {
        'service': get_service_info(),
        'system': get_system_info(),
        'runtime': get_runtime_info(),
        'request': get_request_info(),
        'visits': {
            'count': visits_count,
            'file': VISITS_FILE,
        },
        'endpoints': [
            {
                'path': '/',
                'method': 'GET',
                'description': 'Service information',
            },
            {
                'path': '/health',
                'method': 'GET',
                'description': 'Health check',
            },
            {
                'path': '/metrics',
                'method': 'GET',
                'description': 'Prometheus metrics endpoint',
            },
            {
                'path': '/visits',
                'method': 'GET',
                'description': 'Current visits counter value',
            },
        ],
    }

    return jsonify(response)


@app.route('/health')
def health():
    """Health check endpoint for monitoring."""
    ENDPOINT_CALLS_TOTAL.labels(endpoint='/health').inc()
    uptime = get_uptime()
    timestamp = format_timestamp()
    return jsonify(
        {
            'status': 'healthy',
            'timestamp': timestamp,
            'uptime_seconds': uptime['seconds'],
        },
    )


@app.route('/visits')
def visits():
    """Return current visits counter value."""
    ENDPOINT_CALLS_TOTAL.labels(endpoint='/visits').inc()
    return jsonify({'visits': get_visits_count()})


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    logger.warning(
        'not_found',
        extra={
            'method': request.method,
            'path': request.path,
            'status_code': 404,
            'client_ip': get_client_ip(),
        },
    )
    return jsonify(
        {'error': 'Not Found', 'message': 'Endpoint does not exist'},
    ), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.exception(
        'internal_server_error',
        extra={
            'method': request.method,
            'path': request.path,
            'status_code': 500,
            'client_ip': get_client_ip(),
        },
    )
    return jsonify(
        {
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
        },
    ), 500


@app.route('/boom')
def boom():
    ENDPOINT_CALLS_TOTAL.labels(endpoint='/boom').inc()
    raise RuntimeError("synthetic lab error")


@app.route('/metrics')
def metrics() -> Response:
    """Expose Prometheus metrics for scraping."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == '__main__':
    logger.info(
        'application_starting',
        extra={
            'host': HOST,
            'port': PORT,
            'debug': DEBUG,
            'visits_file': VISITS_FILE,
            'started_at': format_timestamp(START_TIME),
        },
    )
    app.run(host=HOST, port=PORT, debug=DEBUG)
