"""
DevOps Info Service
A simple web service that exposes runtime and system information.
"""

import logging
import os
import platform
import socket
import time
from datetime import datetime, timezone

from flask import Flask, Response, jsonify, g, request
from prometheus_client import Counter, Gauge, Histogram, generate_latest

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("devops-info-service")

# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").strip().lower() == "true"

SERVICE_NAME = os.getenv("SERVICE_NAME", "devops-info-service")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
SERVICE_DESCRIPTION = os.getenv("SERVICE_DESCRIPTION", "DevOps course info service")
FRAMEWORK = "Flask"

START_TIME_UTC = datetime.now(timezone.utc)

app = Flask(__name__)

# Prometheus metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently being processed",
)


def get_uptime() -> dict:
    delta = datetime.now(timezone.utc) - START_TIME_UTC
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        "seconds": seconds,
        "human": f"{hours} hours, {minutes} minutes",
    }


def get_system_info() -> dict:
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.platform(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 0,
        "python_version": platform.python_version(),
    }


def get_request_info() -> dict:
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else request.remote_addr

    return {
        "client_ip": client_ip,
        "user_agent": request.headers.get("User-Agent", ""),
        "method": request.method,
        "path": request.path,
    }


@app.before_request
def before_request():
    if request.path != "/metrics":
        g.start_time = time.time()
        HTTP_REQUESTS_IN_PROGRESS.inc()


@app.after_request
def after_request(response):
    if request.path != "/metrics":
        endpoint = request.path
        method = request.method
        status = str(response.status_code)

        HTTP_REQUESTS_TOTAL.labels(
            method=method,
            endpoint=endpoint,
            status=status,
        ).inc()

        if hasattr(g, "start_time"):
            duration = time.time() - g.start_time
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method,
                endpoint=endpoint,
            ).observe(duration)

        HTTP_REQUESTS_IN_PROGRESS.dec()

    return response


@app.get("/")
def index():
    logger.info("Request: %s %s", request.method, request.path)

    uptime = get_uptime()
    payload = {
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
        "request": get_request_info(),
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
        ],
    }
    return jsonify(payload), 200


@app.get("/health")
def health():
    logger.info("Health check: %s %s", request.method, request.path)
    uptime = get_uptime()
    return (
        jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime_seconds": uptime["seconds"],
            }
        ),
        200,
    )


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), mimetype="text/plain")


@app.errorhandler(404)
def not_found(_error):
    return (
        jsonify({"error": "Not Found", "message": "Endpoint does not exist"}),
        404,
    )


@app.errorhandler(500)
def internal_error(_error):
    return (
        jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred"}),
        500,
    )


if __name__ == "__main__":
    logger.info("Starting %s on %s:%s (debug=%s)", SERVICE_NAME, HOST, PORT, DEBUG)
    app.run(host=HOST, port=PORT, debug=DEBUG)