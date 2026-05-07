#!/usr/bin/env python3
"""
DevOps Info Service
Main application module
"""
import os
import socket
import platform
import time
import logging
import json
import threading
from datetime import datetime, timezone
from flask import Flask, jsonify, request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


app = Flask(__name__)

# Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Application start time
start_time = datetime.now()

# Logging
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)
http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed'
)
system_info_collection_seconds = Histogram(
    'system_info_collection_seconds',
    'Time spent collecting system information'
)

# Path to the counter file
DATA_DIR = "/tmp/data"
VISITS_FILE = os.path.join(DATA_DIR, "visits.json")

# Ensure the data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Lock for thread-safe file access
counter_lock = threading.Lock()


def read_counter():
    """Read the current counter value from the file."""
    if not os.path.exists(VISITS_FILE):
        return 0
    try:
        with open(VISITS_FILE, 'r') as f:
            data = json.load(f)
            return data.get("visits", 0)
    except (json.JSONDecodeError, IOError):
        return 0


def write_counter(value):
    """Write the counter value to the file."""
    with open(VISITS_FILE, 'w') as f:
        json.dump({"visits": value}, f)


def increment_counter():
    """Increment the counter and return the new value."""
    with counter_lock:
        current = read_counter()
        current += 1
        write_counter(current)
        return current


@app.before_request
def before_request():
    request._start_time = time.time()
    http_requests_in_progress.inc()
    logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")


@app.after_request
def after_request(response):
    duration = time.time() - request._start_time

    # Observe histogram with labels
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.path
    ).observe(duration)

    # Increment counter with labels (status as string)
    http_requests_total.labels(
        method=request.method,
        endpoint=request.path,
        status=str(response.status_code)
    ).inc()

    # Decrement in-progress gauge
    http_requests_in_progress.dec()

    logger.info(f"Request status: {response.status_code}")
    return response


@app.teardown_request
def teardown_request(exception=None):
    """Ensure gauge is decremented even if an exception occurs."""
    if exception is not None:
        http_requests_in_progress.dec()
        logger.error(f"Request failed: {exception}")


# Function that collects system info
def get_system_info():
    """Collect system information."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count(),
        'python_version': platform.python_version()
    }


# Function that gets total uptime of a service
def get_uptime():
    delta = datetime.now() - start_time
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    hum = f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
    return {
        'seconds': seconds,
        'human': hum
    }


# API Endpoints
# Main - service and system information
@app.route('/')
def index():
    """Main endpoint - service and system information."""
    # Collect all required information
    system_info = get_system_info()
    uptime_info = get_uptime()

    response = {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "Flask"
        },
        "system": {
            "hostname": system_info['hostname'],
            "platform": system_info['platform'],
            "platform_version": system_info['platform_version'],
            "architecture": system_info['architecture'],
            "cpu_count": system_info['cpu_count'],
            "python_version": system_info['python_version']
        },
        "runtime": {
            "uptime_seconds": uptime_info['seconds'],
            "uptime_human": uptime_info['human'],
            "current_time": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "timezone": "UTC"
        },
        "request": {
            "client_ip": request.remote_addr,
            "user_agent": request.headers.get('User-Agent', 'Unknown'),
            "method": request.method,
            "path": request.path
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/metrics", "method": "GET", "description": "Metrics gathering"}
        ]
    }

    increment_counter()

    return jsonify(response)


# Health check
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'uptime_seconds': get_uptime()['seconds']
    })


@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain')


@app.route('/ready')
def ready():
    return jsonify({'status': 'ready'})


@app.route('/visits')
def visits():
    count = read_counter()
    return jsonify({"visits": count})


# Error Handling
@app.errorhandler(404)
def not_found(error):
    logger.error("Not found error occured: {error}")
    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error("Internal error occured: {error}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500


# Start of the service
if __name__ == '__main__':
    logger.info('Application starting...')
    logger.info(f'Running on http://{HOST}:{PORT}')
    logger.info(f'Debug mode: {DEBUG}')
    app.run(host=HOST, port=PORT, debug=DEBUG)
