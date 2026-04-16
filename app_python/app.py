"""
DevOps Info Service
Main application module providing system information, persistence, and health status.
Structured JSON logging for Loki/observability (Lab 7).
"""

import json
import logging
import os
import platform
import socket
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, Response, g, jsonify, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from pythonjsonlogger import jsonlogger


def setup_logging():
    """Configure JSON logging for Loki/observability (timestamp, level, message + extra)."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level, logging.INFO))
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        timestamp=True,
        rename_fields={"levelname": "level", "asctime": "timestamp"},
    )
    handler.setFormatter(formatter)
    root.handlers = [handler]
    return logging.getLogger(__name__)


logger = setup_logging()

app = Flask(__name__)


def normalize_endpoint(path: str) -> str:
    """Normalize request paths to keep Prometheus label cardinality low."""
    if path in {"/", "/health", "/metrics", "/visits"}:
        return path
    return "other"


# HTTP RED metrics (skip /metrics itself to avoid self-scraping noise).
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
)
http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
)

# Task 1.4: application-specific metrics.
devops_info_endpoint_calls_total = Counter(
    "devops_info_endpoint_calls_total",
    "DevOps Info Service endpoint calls",
    ["endpoint"],
)
devops_info_system_collection_seconds = Histogram(
    "devops_info_system_collection_seconds",
    "System info collection time",
)

# Configuration from environment variables
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
VISITS_FILE_PATH = Path(os.getenv("VISITS_FILE_PATH", "/data/visits"))
APP_CONFIG_FILE = Path(os.getenv("APP_CONFIG_FILE", "/config/config.json"))

# Application start time for uptime calculation
START_TIME = datetime.now(timezone.utc)

visit_counter_lock = threading.Lock()


def get_uptime():
    """Calculate application uptime."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    hour_str = "hour" if hours == 1 else "hours"
    minute_str = "minute" if minutes == 1 else "minutes"
    return {
        "seconds": seconds,
        "human": f"{hours} {hour_str}, {minutes} {minute_str}",
    }


def get_system_info():
    """Collect system information."""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.platform(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }


def get_service_info():
    """Return service metadata."""
    return {
        "name": os.getenv("SERVICE_NAME", "devops-info-service"),
        "version": os.getenv("SERVICE_VERSION", "1.0.0"),
        "description": os.getenv("SERVICE_DESCRIPTION", "DevOps course info service"),
        "framework": os.getenv("SERVICE_FRAMEWORK", "Flask"),
    }


def get_request_info():
    """Extract request information."""
    return {
        "client_ip": request.remote_addr,
        "user_agent": request.headers.get("User-Agent", "Unknown"),
        "method": request.method,
        "path": request.path,
    }


def get_endpoints():
    """Return list of available endpoints."""
    return [
        {"path": "/", "method": "GET", "description": "Service information and visit increment"},
        {"path": "/health", "method": "GET", "description": "Health check"},
        {"path": "/visits", "method": "GET", "description": "Current persisted visit counter"},
        {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
    ]


def ensure_parent_directory(file_path: Path):
    """Ensure that the target directory for persistent files exists."""
    file_path.parent.mkdir(parents=True, exist_ok=True)


def read_visit_count_from_file() -> int:
    """Read the visit counter from the persistent file."""
    try:
        content = VISITS_FILE_PATH.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return 0
    except OSError as error:
        logger.warning(
            "Failed to read visits file",
            extra={"path": str(VISITS_FILE_PATH), "error": str(error)},
        )
        return 0

    if not content:
        return 0

    try:
        return int(content)
    except ValueError:
        logger.warning(
            "Visits file contained invalid counter value",
            extra={"path": str(VISITS_FILE_PATH), "content": content},
        )
        return 0


def write_visit_count_to_file(count: int):
    """Persist the visit counter using an atomic file replacement."""
    ensure_parent_directory(VISITS_FILE_PATH)
    temp_file_path = VISITS_FILE_PATH.with_name(f"{VISITS_FILE_PATH.name}.tmp")
    temp_file_path.write_text(f"{count}\n", encoding="utf-8")
    os.replace(temp_file_path, VISITS_FILE_PATH)


def get_visit_count() -> int:
    """Return the current persisted visit count."""
    global VISIT_COUNTER
    with visit_counter_lock:
        VISIT_COUNTER = read_visit_count_from_file()
        return VISIT_COUNTER


def increment_visit_count() -> int:
    """Increment and persist the visit counter."""
    global VISIT_COUNTER
    with visit_counter_lock:
        VISIT_COUNTER = read_visit_count_from_file() + 1
        write_visit_count_to_file(VISIT_COUNTER)
        return VISIT_COUNTER


def load_app_config():
    """Load optional JSON configuration from a mounted file."""
    config_path = str(APP_CONFIG_FILE)
    try:
        raw_config = APP_CONFIG_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"loaded": False, "path": config_path, "data": {}}
    except OSError as error:
        logger.warning(
            "Failed to read application config file",
            extra={"path": config_path, "error": str(error)},
        )
        return {
            "loaded": False,
            "path": config_path,
            "data": {},
            "error": str(error),
        }

    try:
        return {
            "loaded": True,
            "path": config_path,
            "data": json.loads(raw_config),
        }
    except json.JSONDecodeError as error:
        logger.warning(
            "Application config file contained invalid JSON",
            extra={"path": config_path, "error": str(error)},
        )
        return {
            "loaded": False,
            "path": config_path,
            "data": {},
            "error": "Invalid JSON configuration",
        }


VISIT_COUNTER = read_visit_count_from_file()


@app.before_request
def before_request():
    """Log incoming request."""
    g.start_time = datetime.now(timezone.utc)

    g.metrics_enabled = True
    if g.metrics_enabled:
        http_requests_in_progress.inc()
        g.normalized_endpoint = normalize_endpoint(request.path)
        devops_info_endpoint_calls_total.labels(
            endpoint=g.normalized_endpoint
        ).inc()
    logger.info(
        "Request started",
        extra={
            "method": request.method,
            "path": request.path,
            "client_ip": request.remote_addr,
        },
    )


@app.after_request
def after_request(response):
    """Log response status."""
    duration_ms = 0
    if hasattr(g, "start_time"):
        duration_ms = int((datetime.now(timezone.utc) - g.start_time).total_seconds() * 1000)

    if getattr(g, "metrics_enabled", False):
        duration_s = max(duration_ms / 1000.0, 0.0)
        endpoint = getattr(g, "normalized_endpoint", normalize_endpoint(request.path))
        status_code = str(response.status_code)

        http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=status_code,
        ).inc()
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(duration_s)

        http_requests_in_progress.dec()
    logger.info(
        "Request completed",
        extra={
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "client_ip": request.remote_addr,
            "duration_ms": duration_ms,
        },
    )
    return response


@app.route("/")
def index():
    """Main endpoint - service, system information, configuration, and visits."""
    uptime = get_uptime()
    t0 = time.perf_counter()
    system = get_system_info()
    devops_info_system_collection_seconds.observe(time.perf_counter() - t0)
    current_visits = increment_visit_count()
    response = {
        "service": get_service_info(),
        "system": system,
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "request": get_request_info(),
        "configuration": load_app_config(),
        "visits": {
            "count": current_visits,
            "file_path": str(VISITS_FILE_PATH),
        },
        "endpoints": get_endpoints(),
    }
    return jsonify(response)


@app.route("/health")
def health():
    """Health check endpoint for monitoring and Kubernetes probes."""
    uptime = get_uptime()
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": uptime["seconds"],
        }
    )


@app.route("/visits")
def visits():
    """Return the current persisted visit count without incrementing it."""
    return jsonify(
        {
            "count": get_visit_count(),
            "file_path": str(VISITS_FILE_PATH),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.route("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    logger.warning(
        "Not found",
        extra={"path": request.path, "client_ip": request.remote_addr},
    )
    return (
        jsonify({"error": "Not Found", "message": "Endpoint does not exist"}),
        404,
    )


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(
        "Internal server error",
        extra={
            "error": str(error),
            "path": request.path,
            "client_ip": request.remote_addr,
        },
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


if __name__ == "__main__":
    logger.info(
        "Starting DevOps Info Service",
        extra={
            "host": HOST,
            "port": PORT,
            "debug": DEBUG,
            "visits_file_path": str(VISITS_FILE_PATH),
            "app_config_file": str(APP_CONFIG_FILE),
            "visit_counter": VISIT_COUNTER,
        },
    )
    app.run(host=HOST, port=PORT, debug=DEBUG)
