"""
DevOps Info Service

Small Flask web app for DevOps labs.
Provides basic system/runtime/request information and a health check endpoint.
Configured via environment variables (HOST, PORT, DEBUG).
"""

import json
import logging
import os
import platform
import socket
import sys
import threading
import time
from datetime import datetime, timezone

from flask import Flask, Response, g, jsonify, request
from prometheus_client import (CONTENT_TYPE_LATEST, Counter, Gauge,
                               Histogram, generate_latest)

# Flask application instance
app = Flask(__name__)

# Runtime configuration (can be overridden via environment variables)
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
DATA_DIR = os.getenv("DATA_DIR", "/data")
VISITS_FILE = os.getenv("VISITS_FILE", os.path.join(DATA_DIR, "visits"))

# Lock for safe counter updates within one application process
VISITS_LOCK = threading.Lock()

# Timestamp captured at startup (used to calculate uptime)
START_TIME = datetime.now(timezone.utc)

# Static service metadata returned by the root endpoint
SERVICE = {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask",
}

# Prometheus metrics
# Counter: total HTTP requests by method / endpoint / status code
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

# Histogram: request duration distribution
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status_code"],
)

# Gauge: current number of requests being processed
http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
)


# JSON log formatter
# Produces structured logs suitable for Loki / Promtail / Grafana
class JSONFormatter(logging.Formatter):
    """Serialize log records as JSON for centralized logging systems."""

    def format(self, record):
        payload = {
            "timestamp":
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add selected custom fields from `extra={...}` if they are present
        for field in (
            "method",
            "path",
            "status_code",
            "client_ip",
            "user_agent",
            "latency_ms",
        ):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        # Include traceback for exception logs
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


# Logging configuration (stdout; suitable for Docker/Kubernetes)
# We explicitly log to stdout because container
# log collectors read stdout/stderr
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())

# Configure root logger so library/application logs also go
# through JSON formatter
root_logger = logging.getLogger()
root_logger.handlers.clear()
root_logger.addHandler(handler)
root_logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

# Configure Flask app logger separately and prevent duplicate log propagation
app.logger.handlers.clear()
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
app.logger.propagate = False

# Configure Werkzeug logger too, so startup/request logs are also JSON
werkzeug_logger = logging.getLogger("werkzeug")
werkzeug_logger.handlers.clear()
werkzeug_logger.addHandler(handler)
werkzeug_logger.setLevel(logging.INFO)
werkzeug_logger.propagate = False


# General functions of application
def ensure_visits_file():
    """Create visits counter file with default value if it does not exist."""

    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(VISITS_FILE):
        with open(VISITS_FILE, "w", encoding="utf-8") as file:
            file.write("0")


def read_visits():
    """Read current visits counter from file."""

    ensure_visits_file()
    with open(VISITS_FILE, "r", encoding="utf-8") as file:
        raw_value = file.read().strip()

    return int(raw_value) if raw_value else 0


def write_visits(value):
    """Write visits counter to file atomically."""

    ensure_visits_file()
    temp_file = f"{VISITS_FILE}.{os.getpid()}.{threading.get_ident()}.tmp"

    with open(temp_file, "w", encoding="utf-8") as file:
        file.write(str(value))

    os.replace(temp_file, VISITS_FILE)


def increment_visits():
    """Increment visits counter and persist the new value."""

    with VISITS_LOCK:
        current_value = read_visits()
        new_value = current_value + 1
        write_visits(new_value)
        return new_value


def system_info():
    """Return basic host and Python runtime information."""

    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.release(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }


def runtime_info():
    """Return uptime and current UTC timestamp for the running application."""

    current_time = datetime.now(timezone.utc)
    delta = current_time - START_TIME
    timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        "uptime_seconds": seconds,
        "uptime_human": f"{hours} hour, {minutes} minutes",
        "current_time": timestamp,
        "timezone": "UTC",
    }


def request_info():
    """
    Extract request metadata.

    If the app is behind a reverse proxy, the client IP may be passed via
    X-Forwarded-For header (first IP in the list). Fallback to remote_addr.
    """

    xff = request.headers.get("X-Forwarded-For", "")
    client_ip = xff.split(",")[0].strip() if xff else request.remote_addr

    return {
        "client_ip": client_ip,
        "user_agent": request.headers.get("User-Agent"),
        "method": request.method,
        "path": request.path,
    }


def normalized_endpoint():
    """
    Return a normalized endpoint for metrics labels.

    Uses Flask route rule when available, fallback to raw request path.
    """
    if request.url_rule is not None:
        return request.url_rule.rule
    return request.path


def endpoints_info():
    """
    Build an API endpoints list dynamically from Flask URL map.
    Description is taken from the first line of each handler's docstring.
    """

    endpoints = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue

        view_func = app.view_functions.get(rule.endpoint)
        doc = getattr(view_func, "__doc__", None) if view_func else None
        desc = (doc or "").strip().splitlines()[0] if doc else "No description"

        methods = sorted((rule.methods or set()) - {"HEAD", "OPTIONS"})
        for m in methods:
            endpoints.append({
                "method": m,
                "path": rule.rule,
                "description": desc,
            })

    endpoints.sort(key=lambda e: (e["path"], e["method"]))
    return endpoints


# General endpoints
@app.get("/")
def index():
    """Root endpoint: returns service metadata and diagnostic information."""

    increment_visits()

    payload = {
        "service": SERVICE,
        "system": system_info(),
        "runtime": runtime_info(),
        "request": request_info(),
        "endpoints": endpoints_info(),
    }
    return jsonify(payload)


@app.get("/visits")
def visits():
    """Visits endpoint: returns the current persistent visits counter."""

    payload = {
        "visits": read_visits(),
    }
    return jsonify(payload)


@app.get("/health")
def health():
    """Health check endpoint for monitoring and Kubernetes probes."""
    rt = runtime_info()
    payload = {
        "status": "healthy",
        "timestamp": rt["current_time"],
        "uptime_seconds": rt["uptime_seconds"],
    }
    return jsonify(payload)


@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), content_type=CONTENT_TYPE_LATEST)


# Test-only endpoint to trigger HTTP 500 (uncomment to verify error handler)
@app.get("/crash")
def crash():
    """Intentional error to test 500 handler."""
    1 / 0


# Error Handlers
@app.errorhandler(404)
def not_found(error):
    """Return JSON error for unknown endpoints."""

    info = request_info()
    app.logger.warning(
        "not_found",
        extra={
            "method": info["method"],
            "path": info["path"],
            "status_code": 404,
            "client_ip": info["client_ip"],
            "user_agent": info["user_agent"],
        },
    )
    return jsonify({
        "error": "Not Found",
        "message": "Endpoint does not exist",
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Return JSON error for unhandled server exceptions."""

    info = request_info()
    app.logger.exception(
        "internal_error",
        extra={
            "method": info["method"],
            "path": info["path"],
            "status_code": 500,
            "client_ip": info["client_ip"],
            "user_agent": info["user_agent"],
        },
    )
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
    }), 500


# Logging endpoints
@app.before_request
def log_requests():
    """Log basic request metadata before handling."""

    # Skip Prometheus self-scrape from app HTTP metrics
    g.track_metrics = request.path != "/metrics"

    # Save request start time and increment in-progress gauge
    if g.track_metrics:
        g.request_start_time = time.perf_counter()
        http_requests_in_progress.inc()

    info = request_info()
    app.logger.info(
        "request_started",
        extra={
            "method": info["method"],
            "path": info["path"],
            "client_ip": info["client_ip"],
            "user_agent": info["user_agent"],
        },
    )


@app.after_request
def log_response(response):
    """Log response status code after handling."""

    info = request_info()

    # Record Prometheus metrics after request is processed
    if getattr(g, "track_metrics", False):
        duration = time.perf_counter() - g.request_start_time
        endpoint = normalized_endpoint()
        status_code = str(response.status_code)

        http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=status_code,
        ).inc()

        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=status_code,
        ).observe(duration)

        http_requests_in_progress.dec()

        latency_ms = round(duration * 1000, 2)
    else:
        latency_ms = None

    extra_payload = {
        "method": info["method"],
        "path": info["path"],
        "status_code": response.status_code,
        "client_ip": info["client_ip"],
        "user_agent": info["user_agent"],
    }

    # Add measured latency for normal app requests
    if latency_ms is not None:
        extra_payload["latency_ms"] = latency_ms

    app.logger.info("request_finished", extra=extra_payload)

    return response


if __name__ == "__main__":
    # Startup log to confirm the app has launched and which port it uses
    app.logger.info(
        "application_started",
        extra={
            "status_code": 200,
        },
    )
    app.run(host=HOST, port=PORT, debug=DEBUG, use_reloader=False)
