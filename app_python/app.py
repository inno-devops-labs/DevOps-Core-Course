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
from flask import Flask, Response, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from pythonjsonlogger import jsonlogger

# Flask app initialization
app = Flask(__name__)

# Configuration via environment variables
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Application startup time
START_TIME = datetime.now(timezone.utc)

# Prometheus metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests handled by the application",
    ["method", "endpoint", "status_code"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "Duration of HTTP requests in seconds",
    ["method", "endpoint", "status_code"],
)
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method", "endpoint"],
)
ENDPOINT_CALLS_TOTAL = Counter(
    "devops_info_endpoint_calls_total",
    "Total calls to application endpoints",
    ["endpoint"],
)
SYSTEM_INFO_COLLECTION_SECONDS = Histogram(
    "devops_info_system_info_collection_seconds",
    "Time spent collecting system information",
)

# Setting up logging
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    fmt='%(asctime)s %(levelname)s %(name)s %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S%z'
)
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)


def get_request_endpoint():
    """Return a normalized endpoint label with low cardinality."""
    if request.url_rule and request.url_rule.rule:
        return request.url_rule.rule
    if request.path == "/metrics":
        return "/metrics"
    return "unmatched"


@app.before_request
def log_request():
    endpoint = get_request_endpoint()
    g.request_start_time = time.perf_counter()
    g.metrics_endpoint = endpoint
    HTTP_REQUESTS_IN_PROGRESS.labels(
        method=request.method,
        endpoint=endpoint,
    ).inc()
    logger.info("Request received", extra={
        'method': request.method,
        'path': request.path,
        'ip': request.remote_addr
    })

@app.after_request
def log_response(response):
    endpoint = getattr(g, "metrics_endpoint", get_request_endpoint())
    HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=str(response.status_code),
    ).inc()
    duration = time.perf_counter() - getattr(g, "request_start_time", time.perf_counter())
    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=str(response.status_code),
    ).observe(duration)
    HTTP_REQUESTS_IN_PROGRESS.labels(
        method=request.method,
        endpoint=endpoint,
    ).dec()
    logger.info("Response sent", extra={
        'status': response.status_code,
        'method': request.method,
        'path': request.path
    })
    return response


def get_system_info():
    """Collecting information about the system.

    Returns:
        dict: System configuration
    """
    with SYSTEM_INFO_COLLECTION_SECONDS.time():
        return {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.release(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count() or 0,
            "python_version": platform.python_version(),
        }


def get_uptime():
    """Calculating the running time of the application.

    Returns:
        dict: Uptime in seconds and human-readable format
    """
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {"seconds": seconds, "human": f"{hours} hours, {minutes} minutes"}


@app.route("/")
def index():
    """The main endpoint - Information about the service and the system."""
    client_ip = request.remote_addr
    user_agent = request.headers.get("User-Agent", "Unknown")
    endpoint = get_request_endpoint()
    ENDPOINT_CALLS_TOTAL.labels(endpoint=endpoint).inc()
    uptime = get_uptime()
    system_info = get_system_info()

    # Forming a response
    response = {
        "service": {
            "name": "devops-info-service",
            "version": "2.0.0",
            "description": "DevOps course info service",
            "framework": "Flask",
        },
        "system": system_info,
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "request": {
            "client_ip": client_ip,
            "user_agent": user_agent,
            "method": request.method,
            "path": request.path,
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
        ],
    }
    return jsonify(response)


@app.route("/health")
def health():
    """Endpoint for health check."""
    ENDPOINT_CALLS_TOTAL.labels(endpoint=get_request_endpoint()).inc()
    response = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": get_uptime()["seconds"],
    }
    logger.debug(f"Health check: {response}")
    return jsonify(response), 200


@app.route("/metrics")
def metrics():
    """Expose Prometheus metrics for scraping."""
    ENDPOINT_CALLS_TOTAL.labels(endpoint=get_request_endpoint()).inc()
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.errorhandler(404)
def not_found(error):
    """Error handler 404."""
    logger.warning(f"404 Not Found: {request.path}")
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Error handler 500."""
    logger.error(f"500 Internal Server Error: {str(error)}")
    return (
        jsonify(
            {
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
            }
        ),
        500,
    )


if __name__ == "__main__":
    logger.info(f"Starting DevOps Info Service on {HOST}:{PORT} (debug={DEBUG})")
    app.run(host=HOST, port=PORT, debug=DEBUG)
