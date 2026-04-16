"""
DevOps Info Service
Main application module providing system information and health check.
"""

import fcntl
import json
import logging
import os
import platform
import socket
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from flask import Flask, Response, g, jsonify, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

app = Flask(__name__)

# Configuration
DEFAULT_SERVICE_NAME = 'devops-info-service'
SERVICE_NAME = os.getenv('APP_NAME', DEFAULT_SERVICE_NAME)
APP_ENV = os.getenv('APP_ENV', 'local')
SERVICE_VERSION = '1.1.0'
DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 5000
DEFAULT_VISITS_FILE_PATH = os.path.join('data', 'visits')
DEFAULT_CONFIG_FILE_PATH = os.path.join('config', 'config.json')
HOST = os.getenv('HOST', DEFAULT_HOST)
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()


def get_int_env(name, default):
    """Read an integer environment variable with a safe fallback."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        return int(raw_value)
    except ValueError:
        return default


PORT = get_int_env('PORT', DEFAULT_PORT)

# Application start time for uptime calculation
START_TIME = datetime.now(UTC)

REQUEST_DURATION_BUCKETS = (
    0.001,
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    10.0,
)

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests processed by the Flask application.',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds.',
    ['method', 'endpoint'],
    buckets=REQUEST_DURATION_BUCKETS
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed.',
    ['method', 'endpoint']
)

devops_info_endpoint_calls_total = Counter(
    'devops_info_endpoint_calls_total',
    'Application endpoint calls grouped by logical endpoint.',
    ['endpoint']
)

devops_info_system_collection_seconds = Histogram(
    'devops_info_system_collection_seconds',
    'Time spent collecting system information for the root endpoint.',
    buckets=REQUEST_DURATION_BUCKETS
)


class JSONFormatter(logging.Formatter):
    """Serialize log records to JSON for log aggregation systems."""

    def format(self, record):
        payload = {
            'timestamp': datetime.fromtimestamp(record.created, UTC).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage()
        }

        structured_data = getattr(record, 'structured_data', None)
        if isinstance(structured_data, dict):
            payload.update(
                {
                    key: value for key, value in structured_data.items()
                    if value is not None
                }
            )

        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True)


def configure_logging():
    """Configure the root logger to emit JSON logs to stdout."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(LOG_LEVEL)

    app.logger.handlers.clear()
    app.logger.propagate = True

    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.handlers.clear()
    werkzeug_logger.propagate = True


def log_event(level, message, **fields):
    """Emit a structured application log entry."""
    logging.getLogger(SERVICE_NAME).log(
        level,
        message,
        extra={'structured_data': fields}
    )


configure_logging()


def get_system_info():
    """Collect comprehensive system information."""
    started_at = time.perf_counter()
    system_info = {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count(),
        'python_version': platform.python_version()
    }
    devops_info_system_collection_seconds.observe(time.perf_counter() - started_at)
    return system_info


def get_uptime():
    """Calculate application uptime."""
    delta = datetime.now(UTC) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    hour_text = "hour" if hours == 1 else "hours"
    minute_text = "minute" if minutes == 1 else "minutes"

    return {
        'seconds': seconds,
        'human': f"{hours} {hour_text}, {minutes} {minute_text}"
    }


def get_runtime_info():
    """Get current runtime information."""
    uptime = get_uptime()
    return {
        'uptime_seconds': uptime['seconds'],
        'uptime_human': uptime['human'],
        'current_time': datetime.now(UTC).isoformat(),
        'timezone': 'UTC'
    }


def get_bool_env(name, default):
    """Read a boolean environment variable with a safe fallback."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    return raw_value.strip().lower() in {'1', 'true', 'yes', 'on'}


def get_visits_file_path():
    """Return the configured visits counter file path."""
    return Path(os.getenv('VISITS_FILE_PATH', DEFAULT_VISITS_FILE_PATH))


def get_config_file_path():
    """Return the configured application config file path."""
    return Path(os.getenv('APP_CONFIG_PATH', DEFAULT_CONFIG_FILE_PATH))


def _read_counter_value(raw_value):
    """Parse the persisted visits counter and fall back safely."""
    try:
        return int(raw_value.strip()) if raw_value.strip() else 0
    except ValueError:
        return 0


def _with_locked_visits_file(update_counter):
    """Read and optionally update the visits file while holding an exclusive lock."""
    visits_file_path = get_visits_file_path()
    visits_file_path.parent.mkdir(parents=True, exist_ok=True)

    with visits_file_path.open('a+', encoding='utf-8') as visits_file:
        fcntl.flock(visits_file.fileno(), fcntl.LOCK_EX)
        try:
            visits_file.seek(0)
            raw_value = visits_file.read()
            current_value = _read_counter_value(raw_value)
            next_value = update_counter(current_value)

            # Normalize empty or invalid file contents so the persisted state is explicit.
            if raw_value.strip() != str(next_value):
                visits_file.seek(0)
                visits_file.truncate()
                visits_file.write(f'{next_value}\n')
                visits_file.flush()
                os.fsync(visits_file.fileno())

            return next_value
        finally:
            fcntl.flock(visits_file.fileno(), fcntl.LOCK_UN)


def get_visits_count():
    """Read the current visits counter from disk."""
    return _with_locked_visits_file(lambda count: count)


def increment_visits_count():
    """Increment the visits counter and persist the new value."""
    return _with_locked_visits_file(lambda count: count + 1)


def initialize_visits_storage():
    """Load the persisted counter during application startup and ensure the file exists."""
    return get_visits_count()


def load_application_config():
    """Load the mounted application config file on demand."""
    config_file_path = get_config_file_path()
    config_info = {
        'path': str(config_file_path),
        'loaded': False,
    }

    try:
        config_info['data'] = json.loads(config_file_path.read_text(encoding='utf-8'))
        config_info['loaded'] = True
        config_info['last_modified'] = datetime.fromtimestamp(
            config_file_path.stat().st_mtime,
            UTC,
        ).isoformat()
    except FileNotFoundError:
        config_info['error'] = 'config file not found'
    except json.JSONDecodeError as exc:
        config_info['error'] = f'invalid JSON: {exc.msg}'

    return config_info


def get_configuration_info():
    """Return runtime configuration sourced from env vars and mounted files."""
    return {
        'environment': APP_ENV,
        'env': {
            'host': HOST,
            'port': PORT,
            'log_level': LOG_LEVEL,
            'app_name': SERVICE_NAME,
            'app_env': APP_ENV,
            'feature_flags': {
                'visits_endpoint_enabled': get_bool_env(
                    'FEATURE_VISITS_ENDPOINT_ENABLED',
                    True,
                ),
                'config_reload_enabled': get_bool_env(
                    'FEATURE_CONFIG_RELOAD_ENABLED',
                    True,
                ),
                'metrics_endpoint_enabled': get_bool_env(
                    'FEATURE_METRICS_ENDPOINT_ENABLED',
                    True,
                ),
            },
            'message': os.getenv('APP_MESSAGE', 'Hello from DevOps Info Service'),
            'visits_file_path': str(get_visits_file_path()),
            'config_file_path': str(get_config_file_path()),
        },
        'file': load_application_config(),
    }


def get_request_info(req):
    """Extract information from the current request."""
    return {
        'client_ip': req.remote_addr,
        'user_agent': req.headers.get('User-Agent', 'Unknown'),
        'method': req.method,
        'path': req.path
    }


def get_endpoints_list():
    """Return list of available endpoints."""
    return [
        {
            'path': '/',
            'method': 'GET',
            'description': 'Service and system information'
        },
        {
            'path': '/health',
            'method': 'GET',
            'description': 'Health check endpoint'
        },
        {
            'path': '/visits',
            'method': 'GET',
            'description': 'Persistent visits counter'
        },
        {
            'path': '/metrics',
            'method': 'GET',
            'description': 'Prometheus metrics endpoint'
        }
    ]


def get_request_endpoint_label(req):
    """Return a normalized endpoint label for Prometheus metrics."""
    if req.url_rule and req.url_rule.rule:
        return req.url_rule.rule
    return 'unmatched'


def should_track_request_metrics(req):
    """Skip self-observation for the metrics endpoint to avoid scrape noise."""
    return get_request_endpoint_label(req) != '/metrics'


@app.before_request
def before_request_logging():
    """Store request timing and request state for logging and metrics."""
    g.request_started_at = time.perf_counter()
    g.metrics_tracked = False

    if not should_track_request_metrics(request):
        return

    g.metrics_method = request.method
    g.metrics_endpoint = get_request_endpoint_label(request)
    http_requests_in_progress.labels(
        method=g.metrics_method,
        endpoint=g.metrics_endpoint
    ).inc()
    g.metrics_tracked = True


@app.after_request
def after_request_logging(response):
    """Emit metrics and a structured access log for every request."""
    started_at = getattr(g, 'request_started_at', time.perf_counter())
    duration_seconds = time.perf_counter() - started_at
    duration_ms = round(duration_seconds * 1000, 2)

    if getattr(g, 'metrics_tracked', False):
        method = getattr(g, 'metrics_method', request.method)
        endpoint = getattr(g, 'metrics_endpoint', get_request_endpoint_label(request))
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(response.status_code)
        ).inc()
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration_seconds)

    level = logging.INFO
    if response.status_code >= 500:
        level = logging.ERROR
    elif response.status_code >= 400:
        level = logging.WARNING

    log_event(
        level,
        'request.completed',
        service=SERVICE_NAME,
        method=request.method,
        path=request.path,
        status_code=response.status_code,
        client_ip=request.remote_addr,
        user_agent=request.headers.get('User-Agent', 'Unknown'),
        duration_ms=duration_ms
    )
    return response


@app.teardown_request
def teardown_request_metrics(exception):
    """Ensure in-progress request gauges are decremented after every request."""
    if not getattr(g, 'metrics_tracked', False):
        return

    http_requests_in_progress.labels(
        method=g.metrics_method,
        endpoint=g.metrics_endpoint
    ).dec()
    g.metrics_tracked = False


@app.route('/')
def index():
    """
    Main endpoint - returns comprehensive service and system information.

    Returns:
        JSON response with service, system, runtime, and request information.
    """
    devops_info_endpoint_calls_total.labels(endpoint='/').inc()
    visits_count = increment_visits_count()
    response = {
        'service': {
            'name': SERVICE_NAME,
            'version': SERVICE_VERSION,
            'description': 'DevOps course info service',
            'framework': 'Flask',
            'environment': APP_ENV,
        },
        'system': get_system_info(),
        'runtime': get_runtime_info(),
        'request': get_request_info(request),
        'configuration': get_configuration_info(),
        'visits': {
            'count': visits_count,
            'path': str(get_visits_file_path()),
        },
        'endpoints': get_endpoints_list()
    }

    return jsonify(response), 200


@app.route('/health')
def health():
    """
    Health check endpoint for monitoring and Kubernetes probes.

    Returns:
        JSON response with health status and uptime.
    """
    devops_info_endpoint_calls_total.labels(endpoint='/health').inc()
    response = {
        'status': 'healthy',
        'timestamp': datetime.now(UTC).isoformat(),
        'uptime_seconds': get_uptime()['seconds']
    }

    return jsonify(response), 200


@app.route('/visits')
def visits():
    """Return the current persistent visits counter."""
    devops_info_endpoint_calls_total.labels(endpoint='/visits').inc()
    response = {
        'count': get_visits_count(),
        'path': str(get_visits_file_path()),
        'timestamp': datetime.now(UTC).isoformat(),
    }

    return jsonify(response), 200


@app.route('/metrics')
def metrics():
    """Expose Prometheus metrics for scraping."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested endpoint does not exist',
        'status_code': 404
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle unsupported HTTP methods with a JSON response."""
    response = {
        'error': 'Method Not Allowed',
        'message': 'The requested method is not allowed for this endpoint',
        'status_code': 405
    }

    valid_methods = getattr(error, 'valid_methods', None)
    if valid_methods:
        response['allowed_methods'] = sorted(valid_methods)

    return jsonify(response), 405


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    log_event(
        logging.ERROR,
        'request.failed',
        service=SERVICE_NAME,
        method=request.method,
        path=request.path,
        client_ip=request.remote_addr,
        error=str(error)
    )
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
        'status_code': 500
    }), 500


if __name__ == '__main__':
    initial_visits_count = initialize_visits_storage()
    log_event(
        logging.INFO,
        'app.startup',
        service=SERVICE_NAME,
        host=HOST,
        port=PORT,
        debug=DEBUG,
        environment=APP_ENV,
        initial_visits_count=initial_visits_count,
        visits_file_path=str(get_visits_file_path()),
        config_file_path=str(get_config_file_path()),
        started_at=START_TIME.isoformat(),
        endpoints=['/', '/health', '/visits', '/metrics']
    )

    app.run(host=HOST, port=PORT, debug=DEBUG)
