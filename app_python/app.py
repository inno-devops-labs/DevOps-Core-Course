"""
DevOps Info Service
Main application module for Lab 1.
"""

import json
import logging
import os
import platform
import socket
import time
from datetime import datetime, timezone
from typing import Any, Dict

from flask import Flask, Response, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest


app = Flask(__name__)


# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5002))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"


# Application start time (for uptime calculation)
START_TIME = datetime.now(timezone.utc)


class JsonFormatter(logging.Formatter):
    """Render application logs as one-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        context = getattr(record, "context", None)
        if isinstance(context, dict):
            payload.update(context)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload)


def configure_logging() -> logging.Logger:
    """Configure JSON logging for structured log aggregation."""
    app_logger = logging.getLogger("devops-info-service")
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False

    if not app_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        app_logger.addHandler(handler)

    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    return app_logger


logger = configure_logging()
logger.info(
    "Application starting",
    extra={
        "context": {
            "event": "startup",
            "host": HOST,
            "port": PORT,
        }
    },
)

# Prometheus metrics (RED method + app-specific signals)
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status_code"],
)
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method", "endpoint"],
)
DEVOPS_INFO_ENDPOINT_CALLS = Counter(
    "devops_info_endpoint_calls",
    "Total endpoint calls in DevOps info service",
    ["endpoint"],
)
DEVOPS_INFO_SYSTEM_COLLECTION_SECONDS = Histogram(
    "devops_info_system_collection_seconds",
    "System information collection duration in seconds",
)


def get_uptime() -> Dict[str, Any]:
    """Return uptime in seconds and human-readable form."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        "seconds": seconds,
        "human": f"{hours} hours, {minutes} minutes",
    }


def get_system_info() -> Dict[str, Any]:
    """Collect system information."""
    started_at = time.perf_counter()
    try:
        return {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.platform(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count() or 1,
            "python_version": platform.python_version(),
        }
    finally:
        DEVOPS_INFO_SYSTEM_COLLECTION_SECONDS.observe(time.perf_counter() - started_at)


def get_request_info() -> Dict[str, Any]:
    """Collect request information from the current Flask request."""
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    user_agent = request.headers.get("User-Agent", "")

    return {
        "client_ip": client_ip,
        "user_agent": user_agent,
        "method": request.method,
        "path": request.path,
    }


def get_normalized_endpoint() -> str:
    """Map routes to low-cardinality labels for Prometheus metrics."""
    if request.url_rule is not None and request.url_rule.rule:
        return request.url_rule.rule
    if request.path in {"/", "/health", "/metrics"}:
        return request.path
    return "/unknown"


@app.before_request
def before_request_logging() -> None:
    """Track request start for logging and metrics."""
    g.request_started_at = time.perf_counter()
    g.request_endpoint = get_normalized_endpoint()
    HTTP_REQUESTS_IN_PROGRESS.labels(
        method=request.method, endpoint=g.request_endpoint
    ).inc()


@app.after_request
def after_request_logging(response):
    """Emit logs and collect request metrics."""
    request_info = get_request_info()
    request_info["status_code"] = response.status_code

    endpoint = getattr(g, "request_endpoint", get_normalized_endpoint())
    method = request.method
    status_code = str(response.status_code)

    started_at = getattr(g, "request_started_at", None)
    duration_seconds = 0.0
    if started_at is not None:
        duration_seconds = time.perf_counter() - started_at
        request_info["duration_ms"] = round(duration_seconds * 1000, 2)

    HTTP_REQUESTS_TOTAL.labels(
        method=method, endpoint=endpoint, status_code=status_code
    ).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=method, endpoint=endpoint, status_code=status_code
    ).observe(duration_seconds)
    HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()

    logger.info("HTTP request handled", extra={"context": request_info})
    return response


@app.route("/", methods=["GET"])
def index():
    """Main endpoint - service and system information."""
    DEVOPS_INFO_ENDPOINT_CALLS.labels(endpoint="/").inc()
    uptime = get_uptime()
    system_info = get_system_info()
    request_info = get_request_info()

    response = {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
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
        "request": request_info,
        "endpoints": [
            {
                "path": "/",
                "method": "GET",
                "description": "Service information",
            },
            {
                "path": "/health",
                "method": "GET",
                "description": "Health check",
            },
            {
                "path": "/metrics",
                "method": "GET",
                "description": "Prometheus metrics",
            },
        ],
    }

    return jsonify(response)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    DEVOPS_INFO_ENDPOINT_CALLS.labels(endpoint="/health").inc()
    uptime = get_uptime()
    payload = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime["seconds"],
    }
    return jsonify(payload), 200


@app.route("/metrics", methods=["GET"])
def metrics():
    """Expose Prometheus scrape endpoint."""
    DEVOPS_INFO_ENDPOINT_CALLS.labels(endpoint="/metrics").inc()
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.errorhandler(404)
def not_found(error):
    """Return JSON for 404 errors."""
    request_info = get_request_info()
    request_info["status_code"] = 404
    logger.warning("Not found", extra={"context": request_info})
    return (
        jsonify(
            {
                "error": "Not Found",
                "message": "Endpoint does not exist",
            }
        ),
        404,
    )


@app.errorhandler(500)
def internal_error(error):
    """Return JSON for 500 errors."""
    request_info = get_request_info()
    request_info["status_code"] = 500
    logger.error("Internal server error", extra={"context": request_info})
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
    logger.info(
        "Starting Flask development server",
        extra={"context": {"event": "flask_start", "host": HOST, "port": PORT}},
    )
    app.run(host=HOST, port=PORT, debug=DEBUG)
