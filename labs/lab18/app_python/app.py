#!/usr/bin/env python3

"""
DevOps Info Service
Lab 1. Veronika Levasheva
"""

from flask import Flask, jsonify
from flask import request
import platform
from datetime import datetime
import socket
import os
import logging
from pythonjsonlogger.json import JsonFormatter
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
from flask import g, Response
from threading import Lock

app = Flask(__name__)  # creating an instance of Flask


logger = logging.getLogger(__name__)


# Log important events: startup, HTTP requests, errors
# Include context: method, path, status code, client IP

logHandler = logging.StreamHandler()
formatter = JsonFormatter(
    "levelname, asctime, message",
    style=",",
    rename_fields=(
        {"levelname": "LEVEL", "asctime": "TIMESTAMP", "message": "MESSAGE"}
    ),
)

logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

logger.setLevel(logging.DEBUG)

# Prometheus metrics

http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration", ["method", "endpoint"]
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed"
)

endpoint_calls = Counter("devops_info_endpoint_calls",
                         "Endpoint calls", ["endpoint"])

system_info_duration = Histogram(
    "devops_info_system_collection_seconds",
    "System info collection time"
)

DATA_DIR = os.getenv("DATA_DIR", "/tmp/data")
VISITS_FILE = os.path.join(DATA_DIR, "visits")

visits_lock = Lock()
visits_count = 0


def load_visits():
    global visits_count

    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(VISITS_FILE):
        visits_count = 0
        return

    try:
        with open(VISITS_FILE, "r") as f:
            visits_count = int(f.read().strip())
    except Exception:
        visits_count = 0


def increment_visits():
    global visits_count

    with visits_lock:
        visits_count += 1
        with open(VISITS_FILE, "w") as f:
            f.write(str(visits_count))

    return visits_count


def get_visits():
    with visits_lock:
        return visits_count


@app.before_request
def before_request():
    g.start_time = time.time()
    http_requests_in_progress.inc()


@app.after_request
def after_request(response):
    duration = time.time() - g.start_time

    endpoint = request.path

    if endpoint == "/metrics":
        return response

    if endpoint.startswith("/user/"):
        endpoint = "/user/{id}"

    http_requests_total.labels(
        method=request.method, endpoint=endpoint,
        status_code=response.status_code
    ).inc()

    http_request_duration_seconds.labels(
        method=request.method, endpoint=endpoint
    ).observe(duration)

    http_requests_in_progress.dec()

    return response


# variable names
platform_name = platform.system()
architecture = platform.machine()
python_version = platform.python_version()
hostname = socket.gethostname()

# env variables
ADDRESS = os.getenv("ADDRESS", "0.0.0.0")
PORT = int(os.getenv("PORT", 1999))
DEBUG = os.getenv("DEBUG", "True").lower() == "true"


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype="text/plain")


# decorator for / path
@app.route("/", methods=["GET"])
def get_endpoint():
    start = time.time()
    endpoint_calls.labels(endpoint="/").inc()
    current_visits = increment_visits()
    logger.info(
        {
            "MESSAGE": f"Request: {request.method} {request.path}",
        },
        extra={
            "CLIENT_IP": request.remote_addr,
            "STATUS_CODE": 200,
            "METHOD": request.method,
            "PATH": request.path,
        },
    )
    response = jsonify({
        "message": message,
        "visits": current_visits
    })
    response.status_code = 200
    system_info_duration.observe(time.time() - start)
    return response


@app.route("/visits", methods=["GET"])
def visits():
    start = time.time()
    endpoint_calls.labels(endpoint="/visits").inc()

    count = get_visits()

    response = jsonify({"visits": count})
    response.status_code = 200

    system_info_duration.observe(time.time() - start)
    return response


@app.route("/ready")
def ready():
    start = time.time()
    endpoint_calls.labels(endpoint="/ready").inc()
    logger.info(
        {
            "MESSAGE": f"Request: {request.method} {request.path}",
        },
        extra={
            "CLIENT_IP": request.remote_addr,
            "STATUS_CODE": 200,
            "METHOD": request.method,
            "PATH": request.path,
        },
    )
    response = jsonify({
        "status": "ready",
        "timestamp": datetime.now().isoformat()
    })
    response.status_code = 200
    system_info_duration.observe(time.time() - start)
    return response


# decorator for /health path
@app.route("/health")
def health():
    start = time.time()
    endpoint_calls.labels(endpoint="/health").inc()
    # extra: status code, client ip
    logger.info(
        {
            "MESSAGE": f"Request: {request.method} {request.path}",
        },
        extra={
            "CLIENT_IP": request.remote_addr,
            "STATUS_CODE": 200,
            "METHOD": request.method,
            "PATH": request.path,
        },
    )
    response = jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": get_uptime()["seconds"],
        }
    )
    response.status_code = 200
    system_info_duration.observe(time.time() - start)
    return response


# error handling


@app.errorhandler(404)
def not_found(error):
    logger.error(
        {"MESSAGE": "Endpoint does not exist"},
        extra={
            "ERROR": "Not Found",
            "STATUS_CODE": 404,
            "CLIENT_IP": request.remote_addr,
            "METHOD": request.method,
            "PATH": request.path,
        },
    )
    return (
        jsonify(({"error": "Not Found",
                 "MESSAGE": "Endpoint does not exist"})),
        404,
    )


@app.errorhandler(500)
def internal_error(error):
    logger.error(
        {"MESSAGE": "Internal Server Error"},
        extra={
            "ERROR": "Not Found",
            "STATUS_CODE": 500,
            "CLIENT_IP": request.remote_addr,
            "METHOD": request.method,
            "PATH": request.path,
        },
    )
    return (
        jsonify(
            {
                "error": "Internal Server Error",
                "MESSAGE": "An unexpected error occurred",
            }
        ),
        500,
    )


start_time = datetime.now()


def get_uptime():
    delta = datetime.now() - start_time
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {"seconds": seconds, "human": f"{hours} hours, {minutes} minutes"}


# json message with system and environment info
message = {
    "service": {
        "name": "devops-info-service",
        "version": "1.0.0",
        "description": "DevOps course info service",
        "framework": "Flask",
        "debug status": DEBUG,
    },
    "system": {
        "hostname": hostname,
        "platform": platform_name,
        "platform_version": "Ubuntu 24.04",
        "architecture": architecture,
        "cpu_count": 8,
        "python_version": python_version,
    },
    "runtime": {
        "uptime_seconds": get_uptime(),
        "uptime_human": "1 hour, 0 minutes",
        "current_time": "2026-01-07T14:30:00.000Z",
        "timezone": "UTC",
    },
    "request": {
        "client_ip": "127.0.0.1",
        "port": PORT,
        "user_agent": "curl/7.81.0",
        "method": "GET",
        "path": "/",
    },
    "endpoints": [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"},
    ],
}

logger.info(
    {
        "MESSAGE": f"Application starting on port {PORT}...",
    }
)

load_visits()
if __name__ == "__main__":
    app.run(host=ADDRESS, port=PORT, debug=DEBUG)
