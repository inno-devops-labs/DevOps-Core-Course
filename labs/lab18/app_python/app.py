#!/usr/bin/env python3
import os
import platform
import socket
import logging
import sys
import json
import tempfile
import time
import portalocker
from datetime import datetime, timezone
from flask import Flask, jsonify, request, Response
from json import JSONEncoder
from prometheus_client import Counter, Histogram, Gauge, generate_latest


HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

DATA_DIR = os.getenv('DATA_DIR', 'data')
VISITS_FILE = os.path.join(DATA_DIR, 'visits')
VISITS_LOCK_FILE = os.path.join(DATA_DIR, "visits.lock")

os.makedirs(DATA_DIR, exist_ok=True)

def get_visits():
    if not os.path.exists(VISITS_FILE):
        return 0
    
    with open(VISITS_FILE, 'r') as f:
        try:
            return int(f.read())
        except ValueError:
            return 0

def increment_visits():
    os.makedirs(DATA_DIR, exist_ok=True)

    with open(VISITS_LOCK_FILE, "a+") as lock_fp:
        portalocker.lock(lock_fp, portalocker.LOCK_EX)

        new_value = get_visits() + 1

        fd, tmp_path = tempfile.mkstemp(dir=DATA_DIR, prefix="visits.", text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tf:
                tf.write(str(new_value))
                tf.flush()
                os.fsync(tf.fileno())
            os.replace(tmp_path, VISITS_FILE)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    return new_value

app = Flask(__name__)
START_TIME = datetime.now(timezone.utc)


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


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'timestamp': datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
            'function': record.funcName,
            'line': record.lineno
        }

        if hasattr(record, "method"):
            log_record["method"] = record.method
        if hasattr(record, "path"):
            log_record["path"] = record.path
        if hasattr(record, "status_code"):
            log_record["status_code"] = record.status_code
        if hasattr(record, "client_addr"):
            log_record["client_addr"] = record.client_addr
        if hasattr(record, "error"):
            log_record["error"] = record.error

        return json.dumps(log_record)
    
logger = logging.getLogger("devops-info-service")

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.info("DevOps Info Service starting...", extra={"method": "STARTUP", "path": f"{HOST}:{PORT}"})


@app.before_request
def log_request_info():
    request._start_time = time.time()
    http_requests_in_progress.inc()

    logger.info(f"Incoming request: {request.method} {request.path} from {request.remote_addr}", extra={
        "method": request.method,
        "path": request.path,
        "client_addr": request.remote_addr,
    })


@app.after_request
def log_request_info(response):
    duration = time.time() - request._start_time
    http_request_duration_seconds.labels(method=request.method, endpoint=request.path).observe(duration)

    http_requests_total.labels(method=request.method, endpoint=request.path, status=response.status_code).inc()
    http_requests_in_progress.dec()

    logger.info(f"Request completed: {request.method} {request.path} from {request.remote_addr}", extra={
        "method": request.method,
        "path": request.path,
        "client_addr": request.remote_addr,
        "status_code": response.status_code
    })
    return response


@app.route("/")
def index():
    increment_visits()
    cur_time = datetime.now(timezone.utc)
    uptime = cur_time - START_TIME
    data = {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "Flask"
        },
        "system": {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
            "python_version": platform.python_version(),
        },
        "runtime": {
            "uptime_seconds": uptime.total_seconds(),
            "uptime_human": f"{uptime.total_seconds() // 3600}h {uptime.total_seconds() % 3600 // 60}m",
            "current_time": cur_time.isoformat(),
            "timezone": "UTC"
        },
        "request": {
            "client_ip": request.remote_addr,
            "user_agent": request.headers.get("User-Agent"),
            "method": request.method,
            "path": request.path
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/raise-error", "method": "GET", "description": "Endpoint that raises an error for testing"},
            {"path": "/metrics", "method": "GET", "description": "Metrics endpoint"},
            {"path": "/visits", "method": "GET", "description": "Visits endpoint"}
        ]
    }
    return jsonify(data)


@app.route("/health")
def health():
    cur_time = datetime.now(timezone.utc)
    uptime = cur_time - START_TIME
    return jsonify({
        "status": "healthy",
        "timestamp": cur_time.isoformat(),
        "uptime_seconds": uptime.total_seconds()
    }), 200


@app.route("/raise-error")
def raise_error():
    raise ValueError("This is a test error")


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype='text/plain')


@app.errorhandler(404)
def not_found(error):
    logger.warning('Not found', extra={'path': request.path, 'client_addr': request.remote_addr})
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error('Internal server error', extra={'path': request.path, 'client_addr': request.remote_addr, 'error': str(error)})
    return jsonify({"error": "Internal Server Error", "message": "Unexpected error"}), 500


@app.route('/visits')
def visits():
    return jsonify({"visits": get_visits()})


if __name__ == "__main__":
    logger.info(f"Running on http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG)
