"""DevOps Info Service - A Flask web application for Lab 01."""

import json
import logging
import os
import platform
import socket
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

app = Flask(__name__)

START_TIME = time.time()

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 5000))
DEBUG = os.environ.get("DEBUG", "false").lower() in ("true", "1", "yes")

# --- Prometheus Metrics ---

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
)

endpoint_calls = Counter(
    "devops_info_endpoint_calls",
    "Endpoint calls by name",
    ["endpoint"],
)

system_info_duration = Histogram(
    "devops_info_system_collection_seconds",
    "Time spent collecting system information",
)

# --- Logging ---


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured logging."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.handlers = [handler]
logging.root.setLevel(logging.DEBUG if DEBUG else logging.INFO)
logger = logging.getLogger(__name__)


# --- Middleware ---


@app.before_request
def before_request_hook():
    """Track request start time and increment in-progress gauge."""
    request._start_time = time.time()
    if request.path != "/metrics":
        http_requests_in_progress.inc()
    logger.info("Incoming request: %s %s from %s",
                request.method, request.path, request.remote_addr)


@app.after_request
def after_request_hook(response):
    """Record request metrics and log response."""
    if request.path != "/metrics":
        duration = time.time() - getattr(request, "_start_time", time.time())
        endpoint = request.path
        http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status=str(response.status_code),
        ).inc()
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(duration)
        http_requests_in_progress.dec()
    logger.info("Response: %s %s -> %d",
                request.method, request.path, response.status_code)
    return response


# --- Routes ---


@app.route("/")
def index():
    """Return comprehensive service metadata and system information."""
    endpoint_calls.labels(endpoint="/").inc()

    with system_info_duration.time():
        uptime_seconds = time.time() - START_TIME
        current_time = datetime.now(timezone.utc).isoformat()

        response = {
            "service": {
                "name": "DevOps Info Service",
                "version": "1.0.0",
                "description": "A web service providing system and runtime information",
            },
            "system": {
                "hostname": socket.gethostname(),
                "platform": platform.system(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "cpu_count": os.cpu_count(),
            },
            "runtime": {
                "python_version": platform.python_version(),
                "uptime_seconds": round(uptime_seconds, 2),
                "current_time": current_time,
                "timezone": "UTC",
            },
            "request": {
                "client_ip": request.remote_addr,
                "user_agent": request.headers.get("User-Agent", ""),
                "method": request.method,
                "path": request.path,
            },
            "endpoints": [
                {"path": "/", "method": "GET", "description": "Service info and metadata"},
                {"path": "/health", "method": "GET", "description": "Health check"},
                {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
            ],
        }

    return jsonify(response)


@app.route("/health")
def health():
    """Return health status of the service."""
    endpoint_calls.labels(endpoint="/health").inc()

    uptime_seconds = time.time() - START_TIME
    current_time = datetime.now(timezone.utc).isoformat()

    return jsonify({
        "status": "healthy",
        "timestamp": current_time,
        "uptime_seconds": round(uptime_seconds, 2),
    }), 200


@app.route("/metrics")
def metrics():
    """Expose Prometheus metrics."""
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    logger.warning("404 Not Found: %s %s", request.method, request.path)
    return jsonify({"error": "Not Found", "path": request.path}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error("500 Internal Server Error: %s", error)
    return jsonify({"error": "Internal Server Error"}), 500


if __name__ == "__main__":
    logger.info("Starting DevOps Info Service on %s:%d (debug=%s)", HOST, PORT, DEBUG)
    app.run(host=HOST, port=PORT, debug=DEBUG)
