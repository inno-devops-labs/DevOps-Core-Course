import os
import sys
import socket
from flask import Flask, jsonify, request, Response
import platform

import logging
from pythonjsonlogger import jsonlogger

from datetime import datetime, timezone

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')

VISITS_FILE = os.getenv('VISITS_FILE', '/data/visits')

app = Flask(__name__)

def get_visits():
    try:
        with open(VISITS_FILE, 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def increment_visits():
    count = get_visits() + 1
    os.makedirs(os.path.dirname(VISITS_FILE), exist_ok=True)
    with open(VISITS_FILE, 'w') as f:
        f.write(str(count))
    return count

logger = logging.getLogger()
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
logHandler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(message)s %(method)s %(path)s %(client_ip)s %(status_code)s"
)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logging.getLogger("werkzeug").disabled = True

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
    'HTTP requests in progress'
)


@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.before_request
def before_request():
    request.start_time = time.time()
    http_requests_in_progress.inc()


@app.after_request
def after_request(response):
    if request.path == "/metrics":
         return response
         
    duration = time.time() - request.start_time

    http_requests_total.labels(
        method=request.method,
        endpoint=request.path,
        status=response.status_code
    ).inc()

    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.path
    ).observe(duration)

    http_requests_in_progress.dec()

    logger.info(
        "request_finished",
        extra={
            "method": request.method,
            "path": request.path,
            "client_ip": request.remote_addr,
            "status_code": response.status_code,
        }
    )

    return response

def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }

def get_response():
    uptime = get_uptime()

    response = {
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
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC"
        },
        "request": {
            "client_ip": request.remote_addr,
            "user_agent": request.headers.get("User-Agent"),
            "method": request.method,
            "path": request.path
        },
        "visits": get_visits(),
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/visits", "method": "GET", "description": "Visit counter"}
        ]
    }
    return response

@app.before_request
def log_request():
    request.log_start_time = datetime.now(timezone.utc)
    logger.info(
        "request_started",
        extra={
            "method": request.method,
            "path": request.path,
            "client_ip": request.remote_addr,
        }
    )


@app.route('/health')
def health():
    logger.info(f"Health check from {request.remote_addr}")
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': get_uptime()['seconds']
    })

@app.route("/", methods=["GET"])
def index():
    logger.info(f"{request.method} {request.path} from {request.remote_addr}")
    increment_visits()
    return jsonify(get_response())

@app.route("/visits", methods=["GET"])
def visits():
    logger.info(f"{request.method} {request.path} from {request.remote_addr}")
    return jsonify({'visits': get_visits()})

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Not Found",
        "message": "Endpoint does not exist"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal Server Error",
        "message": "Unexpected server error"
    }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.exception(
        "Unexpected error",
        extra={
            "method": request.method,
            "path": request.path,
            "client_ip": request.remote_addr
        }
    )
    return jsonify({
        "error": "Internal Server Error",
        "message": str(e)
    }), 500

if __name__ == "__main__":
    logger.info("Starting application")
    app.run(host=HOST, port=PORT, debug=DEBUG)


    
