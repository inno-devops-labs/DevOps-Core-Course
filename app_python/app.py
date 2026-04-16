"""
DevOps Info Service
Main application module

Provides system, runtime, and request information,
as well as a health check endpoint.
"""

import os
import socket
import platform
import logging
import json
import time
import threading
from pathlib import Path
from datetime import datetime, timezone

from flask import Flask, jsonify, request, g

from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

# ------------------------------------------------------------------------------
# Application setup
# ------------------------------------------------------------------------------

app = Flask(__name__)

# Configuration via environment variables
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
VISITS_FILE = Path(os.getenv("VISITS_FILE", "/data/visits"))

_visits_lock = threading.Lock()

# Application start time (used for uptime calculation)
START_TIME = datetime.now(timezone.utc)

# ------------------------------------------------------------------------------
# Logging configuration
# ------------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger(__name__)

logger.info(json.dumps({
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "level": "INFO",
    "event": "startup",
    "message": "DevOps Info Service starting..."
}))

# ------------------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------------------

def get_uptime():
    """
    Calculate application uptime.

    Returns:
        tuple: uptime in seconds (int), human-readable uptime (str)
    """
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return seconds, f"{hours} hours, {minutes} minutes"


def _normalize_endpoint_label():
    rule = getattr(request, "url_rule", None)
    if rule and getattr(rule, "rule", None):
        return rule.rule
    return request.path


def _read_visits_counter():
    try:
        raw = VISITS_FILE.read_text(encoding="utf-8").strip()
        return int(raw) if raw else 0
    except FileNotFoundError:
        return 0
    except ValueError:
        logger.warning(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "WARNING",
            "event": "visits_counter_invalid",
            "message": f"Invalid integer in {VISITS_FILE}; treating as 0",
        }))
        return 0


def _write_visits_counter(value: int) -> None:
    VISITS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = VISITS_FILE.with_suffix(".tmp")
    tmp.write_text(str(value), encoding="utf-8")
    tmp.replace(VISITS_FILE)


def _increment_visits_counter() -> int:
    with _visits_lock:
        n = _read_visits_counter() + 1
        _write_visits_counter(n)
        return n


# ------------------------------------------------------------------------------
# Prometheus metrics
# ------------------------------------------------------------------------------

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
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

devops_info_endpoint_calls = Counter(
    "devops_info_endpoint_calls",
    "DevOps Info Service endpoint calls",
    ["endpoint"],
)

devops_info_system_collection_seconds = Histogram(
    "devops_info_system_collection_seconds",
    "Time spent collecting system info in seconds",
)


def get_system_info():
    """
    Collect system information.

    Returns:
        dict: system information
    """
    start = time.perf_counter()
    try:
        return {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.release(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
            "python_version": platform.python_version(),
        }
    finally:
        devops_info_system_collection_seconds.observe(time.perf_counter() - start)


# ------------------------------------------------------------------------------
# Request instrumentation
# ------------------------------------------------------------------------------

@app.before_request
def _metrics_before_request():
    g._metrics_start = time.perf_counter()
    g._metrics_endpoint = _normalize_endpoint_label()

    if request.path != "/metrics":
        http_requests_in_progress.inc()


@app.after_request
def _metrics_after_request(response):
    endpoint = getattr(g, "_metrics_endpoint", _normalize_endpoint_label())

    if request.path != "/metrics":
        duration = time.perf_counter() - getattr(g, "_metrics_start", time.perf_counter())
        http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=str(response.status_code),
        ).inc()
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(duration)
        http_requests_in_progress.dec()

    return response


@app.teardown_request
def _metrics_teardown_request(error):
    if request.path == "/metrics":
        return

    if error is not None:
        try:
            http_requests_in_progress.dec()
        except ValueError:
            pass

# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def index():
    """
    Main endpoint returning service, system, runtime, and request information.
    """
    logger.info(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "INFO",
        "event": "request",
        "endpoint": "index",
        "method": request.method,
        "path": request.path,
        "client_ip": request.remote_addr,
        "status_code": 200,
        "user_agent": request.headers.get("User-Agent"),
    }))

    uptime_seconds, uptime_human = get_uptime()
    visits_count = _increment_visits_counter()
    devops_info_endpoint_calls.labels(endpoint="/").inc()

    response = {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "Flask",
        },
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": uptime_seconds,
            "uptime_human": uptime_human,
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "request": {
            "client_ip": request.remote_addr,
            "user_agent": request.headers.get("User-Agent"),
            "method": request.method,
            "path": request.path,
        },
        "visits": {
            "count": visits_count,
            "file": str(VISITS_FILE),
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/visits", "method": "GET", "description": "Visits counter"},
        ],
    }

    return jsonify(response)


@app.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint.
    """
    uptime_seconds, _ = get_uptime()
    devops_info_endpoint_calls.labels(endpoint="/health").inc()

    logger.info(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "INFO",
        "event": "request",
        "endpoint": "health",
        "method": request.method,
        "path": request.path,
        "client_ip": request.remote_addr,
        "status_code": 200,
        "user_agent": request.headers.get("User-Agent"),
    }))

    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_seconds,
    })


@app.route("/visits", methods=["GET"])
def visits():
    devops_info_endpoint_calls.labels(endpoint="/visits").inc()

    with _visits_lock:
        count = _read_visits_counter()

    return jsonify({
        "visits": count,
        "file": str(VISITS_FILE),
    })


@app.route("/metrics", methods=["GET"])
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

# ------------------------------------------------------------------------------
# Error handlers
# ------------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(error):
    """
    Handle 404 errors.
    """
    logger.warning(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "WARNING",
        "event": "http_error",
        "error_type": "NotFound",
        "path": request.path,
        "method": request.method,
        "status_code": 404,
        "client_ip": request.remote_addr,
    }))
    return jsonify({
        "error": "Not Found",
        "message": "Endpoint does not exist",
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """
    Handle 500 errors.
    """
    logger.error(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "ERROR",
        "event": "http_error",
        "error_type": "InternalServerError",
        "path": request.path,
        "method": request.method,
        "status_code": 500,
        "client_ip": request.remote_addr,
        "error": str(error),
    }))
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
    }), 500

# ------------------------------------------------------------------------------
# Application entry point
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)
