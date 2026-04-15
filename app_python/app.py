#!/usr/bin/env python3
"""
DevOps Info Service
Main application module
"""
import os
import time
import socket
import platform
import logging
import json
import tempfile
import threading
from datetime import datetime, timezone
from flask import Flask, jsonify, request, Response
from prometheus_client import (
    Counter, Histogram, Gauge,
    generate_latest, CONTENT_TYPE_LATEST
)


# Custom JSON formatter for structured logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        # Add extra fields from log record
        if hasattr(record, 'event'):
            log_data["event"] = record.event
        if hasattr(record, 'method'):
            log_data["method"] = record.method
        if hasattr(record, 'path'):
            log_data["path"] = record.path
        if hasattr(record, 'status_code'):
            log_data["status_code"] = record.status_code
        if hasattr(record, 'duration_ms'):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, 'remote_addr'):
            log_data["remote_addr"] = record.remote_addr
        if hasattr(record, 'user_agent'):
            log_data["user_agent"] = record.user_agent
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


# Configure JSON logging
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Configuration from environment variables
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5001))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
VISITS_FILE = os.getenv('VISITS_FILE', '/data/visits')

# Application start time for uptime calculation
START_TIME = datetime.now(timezone.utc)

app = Flask(__name__)
VISITS_LOCK = threading.Lock()

# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------

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

# App-specific: count calls per logical endpoint
devops_endpoint_calls = Counter(
    'devops_info_endpoint_calls_total',
    'Total calls per application endpoint',
    ['endpoint']
)

# App-specific: track system info collection duration
system_info_duration = Histogram(
    'devops_info_system_collection_seconds',
    'Time spent collecting system information'
)


def _normalize_endpoint(path: str) -> str:
    """Collapse dynamic path segments to keep cardinality low."""
    if path == '/':
        return '/'
    if path.startswith('/health'):
        return '/health'
    if path.startswith('/ready'):
        return '/ready'
    if path.startswith('/metrics'):
        return '/metrics'
    if path.startswith('/visits'):
        return '/visits'
    return '/other'


def _read_visits_count() -> int:
    """Read visits count from file; return 0 if file does not exist."""
    try:
        with open(VISITS_FILE, 'r', encoding='utf-8') as visits_file:
            value = visits_file.read().strip()
            return int(value) if value else 0
    except FileNotFoundError:
        return 0
    except ValueError:
        logger.warning(
            "Invalid visits counter value; resetting to 0",
            extra={"event": "visits_counter_invalid", "path": VISITS_FILE}
        )
        return 0


def _write_visits_count(count: int) -> None:
    """Persist visits count using atomic replace."""
    visits_dir = os.path.dirname(VISITS_FILE) or '.'
    os.makedirs(visits_dir, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(dir=visits_dir, prefix='visits-', text=True)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as tmp:
            tmp.write(str(count))
        os.replace(temp_path, VISITS_FILE)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def initialize_visits_storage() -> None:
    """Ensure visits counter file exists and is valid."""
    with VISITS_LOCK:
        count = _read_visits_count()
        _write_visits_count(count)


def get_visits_count() -> int:
    """Return current visits counter value."""
    with VISITS_LOCK:
        return _read_visits_count()


def increment_visits_count() -> int:
    """Increment and persist visits counter value."""
    with VISITS_LOCK:
        count = _read_visits_count() + 1
        _write_visits_count(count)
        return count


# ---------------------------------------------------------------------------
# Request lifecycle hooks
# ---------------------------------------------------------------------------

@app.before_request
def before_request():
    """Record request start time and increment in-progress gauge."""
    request.start_time = time.monotonic()
    http_requests_in_progress.inc()
    logger.info(
        "Request started",
        extra={
            "event": "request_started",
            "method": request.method,
            "path": request.path,
            "remote_addr": request.remote_addr,
            "user_agent": request.headers.get('User-Agent', 'unknown')
        }
    )


@app.after_request
def after_request(response):
    """Record metrics and log response after each request."""
    duration = time.monotonic() - request.start_time
    endpoint = _normalize_endpoint(request.path)

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

    logger.info(
        "Request completed",
        extra={
            "event": "request_completed",
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "duration_ms": duration * 1000,
            "remote_addr": request.remote_addr
        }
    )
    return response


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_system_info():
    """Collect system information."""
    with system_info_duration.time():
        return {
            'hostname': socket.gethostname(),
            'platform': platform.system(),
            'platform_version': platform.release(),
            'architecture': platform.machine(),
            'cpu_count': os.cpu_count() or 0,
            'python_version': platform.python_version()
        }


def get_uptime():
    """Calculate uptime since application start."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route('/')
def index():
    """Main endpoint - service and system information."""
    try:
        visits_count = increment_visits_count()
    except OSError:
        logger.exception(
            "Failed to update visits counter",
            extra={"event": "visits_counter_write_failed", "path": VISITS_FILE}
        )
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to update visits counter"
        }), 500

    devops_endpoint_calls.labels(endpoint='/').inc()
    return jsonify({
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "Flask"
        },
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": get_uptime()['seconds'],
            "uptime_human": get_uptime()['human'],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC"
        },
        "request": {
            "client_ip": request.remote_addr,
            "user_agent": request.headers.get('User-Agent'),
            "method": request.method,
            "path": request.path
        },
        "visits": {
            "count": visits_count,
            "storage_file": VISITS_FILE
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/visits", "method": "GET", "description": "Current visits count"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/ready", "method": "GET", "description": "Readiness probe"},
            {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"}
        ]
    })


@app.route('/visits')
def visits():
    """Return current visits counter."""
    devops_endpoint_calls.labels(endpoint='/visits').inc()
    try:
        return jsonify({
            "visits": get_visits_count(),
            "storage_file": VISITS_FILE
        })
    except OSError:
        logger.exception(
            "Failed to read visits counter",
            extra={"event": "visits_counter_read_failed", "path": VISITS_FILE}
        )
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to read visits counter"
        }), 500


@app.route('/health')
def health():
    """Health check endpoint for monitoring."""
    devops_endpoint_calls.labels(endpoint='/health').inc()
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': get_uptime()['seconds']
    })


@app.route('/ready')
def ready():
    """Readiness probe endpoint for Kubernetes."""
    devops_endpoint_calls.labels(endpoint='/ready').inc()
    return jsonify({
        'status': 'ready',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors with JSON response."""
    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors with JSON response."""
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500


if __name__ == '__main__':
    initialize_visits_storage()
    logger.info(f'Starting DevOps Service on {HOST}:{PORT} (debug={DEBUG})')
    app.run(host=HOST, port=PORT, debug=DEBUG)
