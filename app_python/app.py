"""
DevOps Info Service
Main application module
"""
import os
import socket
import platform
import logging
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, request, g
from pythonjsonlogger import jsonlogger
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

SERVICE_NAME = "devops-info-service"
SERVICE_VERSION = "1.0.0"
SERVICE_DESCRIPTION = "DevOps course info service"
FRAMEWORK = "Flask"

# App
app = Flask(__name__)

# =====================
# PROMETHEUS METRICS
# =====================
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

# Example business metrics
endpoint_calls = Counter(
    'devops_info_endpoint_calls',
    'Endpoint calls',
    ['endpoint']
)

system_info_duration = Histogram(
    'devops_info_system_collection_seconds',
    'System info collection time'
)

# =====================
# LOGGING
# =====================
logger = logging.getLogger()
logger.setLevel(logging.INFO)

logHandler = logging.StreamHandler()

formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(message)s %(method)s %(path)s %(status)s %(ip)s"
)

logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

START_TIME = datetime.now(timezone.utc)

logger.info(
    "Application starting",
    extra={
        "method": None,
        "path": None,
        "status": None,
        "ip": None,
    },
)

# =====================
# HELPERS
# =====================
def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    return {
        "seconds": seconds,
        "human": f"{hours} hours, {minutes} minutes",
    }


def get_system_info():
    with system_info_duration.time():
        return {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
            "python_version": platform.python_version(),
        }

# =====================
# REQUEST LOGGING + METRICS
# =====================
@app.before_request
def before_request():
    g.start_time = time.time()
    http_requests_in_progress.inc()

    logger.info(
        "Request received",
        extra={
            "method": request.method,
            "path": request.path,
            "status": None,
            "ip": request.remote_addr,
        },
    )


@app.after_request
def after_request(response):
    duration = time.time() - g.start_time

    http_requests_total.labels(
        method=request.method,
        endpoint=request.path,
        status=str(response.status_code)
    ).inc()

    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.path
    ).observe(duration)

    http_requests_in_progress.dec()

    logger.info(
        "Response sent",
        extra={
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "ip": request.remote_addr,
        },
    )

    return response

# =====================
# ROUTES
# =====================
@app.route("/", methods=["GET"])
def index():
    endpoint_calls.labels(endpoint="/").inc()

    uptime = get_uptime()

    response = {
        "service": {
            "name": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "description": SERVICE_DESCRIPTION,
            "framework": FRAMEWORK,
        },
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "request": {
            "client_ip": request.remote_addr,
            "user_agent": request.headers.get("User-Agent"),
            "method": request.method,
            "path": request.path,
        },
    }

    return jsonify(response)


@app.route("/health", methods=["GET"])
def health():
    endpoint_calls.labels(endpoint="/health").inc()

    uptime = get_uptime()

    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": uptime["seconds"],
        }
    )


@app.route("/metrics", methods=["GET"])
def metrics():
    return generate_latest(), 200, {'Content-Type': 'text/plain'}

# =====================
# ERROR HANDLERS
# =====================
@app.errorhandler(404)
def not_found(error):
    logger.error(
        "404 error",
        extra={
            "method": request.method,
            "path": request.path,
            "status": 404,
            "ip": request.remote_addr,
        },
    )
    return jsonify(
        {
            "error": "Not Found",
            "message": "Endpoint does not exist",
        }
    ), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(
        "500 error",
        extra={
            "method": request.method,
            "path": request.path,
            "status": 500,
            "ip": request.remote_addr,
        },
    )
    return jsonify(
        {
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        }
    ), 500


# =====================
# ENTRY POINT
# =====================
if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)
