"""
DevOps Info Service
Main Flask application module.
"""

import json
import logging
import os
import platform
import socket
import tempfile
import threading
import time
from datetime import datetime, timezone

from flask import Flask, g, jsonify, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

USE_JSON_LOGGING = os.getenv("LOG_FORMAT", "").lower() == "json"

app = Flask(__name__)

# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Application start time (for uptime calculation)
START_TIME = datetime.now(timezone.utc)

# Logging configuration
if USE_JSON_LOGGING:
    from pythonjsonlogger import jsonlogger

    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter()
    handler.setFormatter(formatter)
    logging.root.handlers = [handler]
    logging.root.setLevel(logging.INFO)
    logger = logging.getLogger(__name__)
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

# Prometheus metrics (RED method: Rate, Errors, Duration)
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
)
endpoint_calls = Counter(
    "devops_info_endpoint_calls",
    "Endpoint calls by endpoint",
    ["endpoint"],
)
system_info_duration = Histogram(
    "devops_info_system_collection_seconds",
    "System info collection duration in seconds",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
)


def _normalize_endpoint(path: str) -> str:
    """Normalize path for low-cardinality metrics."""
    if path in ("/", "/health", "/metrics", "/visits"):
        return path
    return "other"


_visits_lock = threading.Lock()


def _visits_path() -> str:
    return os.environ.get("VISITS_DATA_PATH", "/data/visits")


def _read_visits_unlocked() -> int:
    path = _visits_path()
    try:
        with open(path, encoding="utf-8") as f:
            return int((f.read() or "0").strip() or "0")
    except (FileNotFoundError, ValueError, OSError):
        return 0


def _write_visits_atomic(n: int) -> None:
    path = _visits_path()
    parent = os.path.dirname(path) or "."
    os.makedirs(parent, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        dir=parent, prefix=".visits_", suffix=".tmp", text=True
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(str(n))
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def increment_visits() -> int:
    """Increment persisted visit counter; returns new total."""
    with _visits_lock:
        n = _read_visits_unlocked() + 1
        _write_visits_atomic(n)
        return n


def get_visits() -> int:
    """Return current persisted visit total."""
    with _visits_lock:
        return _read_visits_unlocked()


def load_config_file() -> dict | None:
    """Return parsed /config/config.json if present (Kubernetes ConfigMap mount)."""
    path = "/config/config.json"
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        logger.warning("Could not read or parse %s", path)
        return None


# Startup log
logger.info(
    "Application starting",
    extra={"host": HOST, "port": PORT, "debug": DEBUG} if USE_JSON_LOGGING else {},
)
logger.info(
    "Visit counter path %s (initial count=%s)",
    _visits_path(),
    get_visits(),
)


@app.before_request
def log_request():
    """Log incoming request and record metrics start time."""
    g._request_start = time.perf_counter()
    http_requests_in_progress.inc()
    if USE_JSON_LOGGING:
        logger.info(
            "Request received",
            extra={
                "method": request.method,
                "path": request.path,
                "client_ip": request.remote_addr or "unknown",
            },
        )
    else:
        logger.info("Request: %s %s from %s", request.method, request.path, request.remote_addr)


@app.after_request
def log_response(response):
    """Log response status and record Prometheus metrics."""
    try:
        if hasattr(g, "_request_start"):
            duration = time.perf_counter() - g._request_start
            endpoint = _normalize_endpoint(request.path)
            http_requests_total.labels(
                method=request.method,
                endpoint=endpoint,
                status=str(response.status_code),
            ).inc()
            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=endpoint,
            ).observe(duration)
            endpoint_calls.labels(endpoint=endpoint).inc()
    finally:
        http_requests_in_progress.dec()

    if USE_JSON_LOGGING:
        logger.info(
            "Response sent",
            extra={
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "client_ip": request.remote_addr or "unknown",
            },
        )
    return response


def get_system_info() -> dict:
    """Collect basic system information."""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }


def get_uptime() -> dict:
    """Calculate uptime in seconds and human-readable form."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        "uptime_seconds": seconds,
        "uptime_human": f"{hours} hours, {minutes} minutes",
    }


def get_request_info() -> dict:
    """Extract request-related information."""
    user_agent = request.headers.get("User-Agent") or request.headers.get(
        "user-agent"
    )
    return {
        "client_ip": request.remote_addr,
        "user_agent": user_agent,
        "method": request.method,
        "path": request.path,
    }


@app.route("/", methods=["GET"])
def index():
    """Main endpoint — service, system, runtime, and request information."""
    logger.info("Handling / request")

    visits_total = increment_visits()
    uptime_info = get_uptime()

    # Track system info collection duration
    with system_info_duration.time():
        system_info = get_system_info()

    response = {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "Flask",
        },
        "system": system_info,
        "runtime": {
            "uptime_seconds": uptime_info["uptime_seconds"],
            "uptime_human": uptime_info["uptime_human"],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "visits_total": visits_total,
        "config": {
            "environment": os.environ.get("APP_CONFIG_ENV", "local"),
            "log_level": os.environ.get("LOG_LEVEL", "INFO"),
            "feature_debug": os.environ.get("FEATURE_DEBUG", "false"),
            "file": load_config_file(),
        },
        "request": get_request_info(),
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/visits", "method": "GET", "description": "Persisted visit counter"},
            {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
        ],
    }

    logger.debug("Response payload for / endpoint generated")
    return jsonify(response)


@app.route("/metrics", methods=["GET"])
def metrics():
    """Prometheus metrics endpoint."""
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@app.route("/visits", methods=["GET"])
def visits():
    """Return current persisted root-path visit total (without incrementing)."""
    total = get_visits()
    return (
        jsonify(
            {
                "visits_total": total,
                "data_path": _visits_path(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ),
        200,
    )


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    logger.info("Handling /health request")
    uptime_info = get_uptime()
    response = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_info["uptime_seconds"],
    }
    return jsonify(response), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors."""
    if USE_JSON_LOGGING:
        logger.warning(
            "404 Not Found",
            extra={"method": request.method, "path": request.path},
        )
    else:
        logger.warning("404 Not Found: %s %s", request.method, request.path)
    return (
        jsonify(
            {
                "error": "Not Found",
                "message": "Endpoint does not exist",
                "path": request.path,
            }
        ),
        404,
    )


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server Error."""
    logger.exception(
        "500 Internal Server Error",
        extra={"error": str(error)} if USE_JSON_LOGGING else {},
    )
    return (
        jsonify(
            {
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
            }
        ),
        500,
    )


def main():
    """Application entrypoint."""
    logger.info("Starting DevOps Info Service on %s:%s (debug=%s)", HOST, PORT, DEBUG)
    app.run(host=HOST, port=PORT, debug=DEBUG)


if __name__ == "__main__":
    main()
