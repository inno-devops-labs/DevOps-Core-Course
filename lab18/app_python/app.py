"""
DevOps Info Service - Flask implementation
Provides system and runtime information with health checks.
"""
from __future__ import annotations

import json
import logging
import os
import platform
import socket
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock
from time import perf_counter
from datetime import datetime, timezone
from typing import Dict, List, Any

from flask import Flask, Response, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

APP_NAME = "devops-info-service"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "DevOps course info service"
FRAMEWORK = "Flask"

# Configuration via environment variables
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8080))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
VISITS_FILE = Path(os.getenv("VISITS_FILE", "data/visits"))

# Track application start time for uptime calculations
START_TIME = datetime.now(timezone.utc)
VISITS_LOCK = Lock()

app = Flask(__name__)

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
    "devops_info_endpoint_calls_total",
    "Application endpoint calls",
    ["endpoint"],
)
devops_info_system_collection_seconds = Histogram(
    "devops_info_system_collection_seconds",
    "System info collection duration in seconds",
)


class JSONFormatter(logging.Formatter):
    """Render log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        for field in (
            "method",
            "path",
            "status_code",
            "client_ip",
            "host",
            "port",
            "debug",
            "app",
            "version",
            "event",
            "visits",
        ):
            if hasattr(record, field):
                payload[field] = getattr(record, field)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True)


def setup_logging() -> None:
    """Configure JSON structured logging."""
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root.addHandler(handler)

    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.info(
        "application_startup",
        extra={
            "event": "startup",
            "app": APP_NAME,
            "version": APP_VERSION,
            "host": HOST,
            "port": PORT,
            "debug": DEBUG,
        },
    )


def get_system_info() -> Dict[str, Any]:
    """Collect host system information."""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 0,
        "python_version": platform.python_version(),
    }


def get_uptime() -> Dict[str, Any]:
    """Calculate service uptime in seconds and human format."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return {
        "seconds": seconds,
        "human": f"{hours} hours, {minutes} minutes",
    }


def get_runtime_info() -> Dict[str, Any]:
    """Return runtime timing details."""
    now = datetime.now(timezone.utc)
    local_now = now.astimezone()
    uptime = get_uptime()
    return {
        "uptime_seconds": uptime["seconds"],
        "uptime_human": uptime["human"],
        "current_time": now.isoformat(),
        "timezone": local_now.tzname() or "UTC",
    }


def get_request_info() -> Dict[str, Any]:
    """Extract request metadata for observability."""
    forwarded_for = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    client_ip = forwarded_for or request.remote_addr or ""
    return {
        "client_ip": client_ip,
        "user_agent": request.headers.get("User-Agent", ""),
        "method": request.method,
        "path": request.path,
    }


def get_endpoints() -> List[Dict[str, str]]:
    """List known HTTP endpoints."""
    return [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/visits", "method": "GET", "description": "Current visits counter"},
        {"path": "/health", "method": "GET", "description": "Health check"},
        {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
    ]


def get_metrics_endpoint_label() -> str:
    """Normalize endpoint labels to keep cardinality low."""
    if request.path in {"/", "/visits", "/health", "/metrics"}:
        return request.path
    if request.url_rule and request.url_rule.rule:
        return request.url_rule.rule
    return "unknown"


def _parse_visits(raw_value: str) -> int:
    """Parse a persisted visit counter value."""
    try:
        return max(0, int(raw_value.strip()))
    except (TypeError, ValueError):
        return 0


def read_visits_count() -> int:
    """Read visit counter from file, defaulting to 0 when missing/invalid."""
    if not VISITS_FILE.exists():
        return 0
    try:
        return _parse_visits(VISITS_FILE.read_text(encoding="utf-8"))
    except OSError:
        return 0


def write_visits_count(value: int) -> None:
    """Persist visit counter using atomic replace."""
    VISITS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", delete=False, dir=str(VISITS_FILE.parent), encoding="utf-8") as tmp:
        tmp.write(str(max(0, value)))
        temp_name = tmp.name
    os.replace(temp_name, VISITS_FILE)


def initialize_visits_storage() -> int:
    """Ensure visits file is initialized and return startup value."""
    with VISITS_LOCK:
        visits = read_visits_count()
        if not VISITS_FILE.exists():
            write_visits_count(visits)
        return visits


def increment_visits_count() -> int:
    """Increment and persist visits counter."""
    with VISITS_LOCK:
        current = read_visits_count()
        updated = current + 1
        write_visits_count(updated)
        return updated


@app.before_request
def log_request() -> None:
    """Log incoming requests with context for observability."""
    g.request_start_time = perf_counter()
    g.metrics_endpoint = get_metrics_endpoint_label()
    http_requests_in_progress.inc()
    devops_info_endpoint_calls.labels(endpoint=g.metrics_endpoint).inc()

    request_info = get_request_info()
    logging.info(
        "http_request_started",
        extra={
            "event": "request_started",
            "method": request_info["method"],
            "path": request_info["path"],
            "client_ip": request_info["client_ip"],
            "app": APP_NAME,
            "version": APP_VERSION,
        },
    )


@app.after_request
def log_response(response):  # type: ignore[no-untyped-def]
    """Log response metadata, including status code."""
    endpoint = getattr(g, "metrics_endpoint", get_metrics_endpoint_label())
    request_start_time = getattr(g, "request_start_time", None)

    if request_start_time is not None:
        http_request_duration_seconds.labels(method=request.method, endpoint=endpoint).observe(
            max(0.0, perf_counter() - request_start_time)
        )
    http_requests_total.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=str(response.status_code),
    ).inc()
    http_requests_in_progress.dec()

    request_info = get_request_info()
    logging.info(
        "http_request_completed",
        extra={
            "event": "request_completed",
            "method": request_info["method"],
            "path": request_info["path"],
            "status_code": response.status_code,
            "client_ip": request_info["client_ip"],
            "app": APP_NAME,
            "version": APP_VERSION,
        },
    )
    return response


@app.route("/", methods=["GET"])
def index() -> Any:
    """Main endpoint returning service, system, runtime, and request info."""
    visits = increment_visits_count()
    response = {
        "service": {
            "name": APP_NAME,
            "version": APP_VERSION,
            "description": APP_DESCRIPTION,
            "framework": FRAMEWORK,
        },
        "visits": visits,
        "system": get_system_info(),
        "runtime": get_runtime_info(),
        "request": get_request_info(),
        "endpoints": get_endpoints(),
    }
    return jsonify(response), 200


@app.route("/visits", methods=["GET"])
def visits() -> Any:
    """Return the current visits counter."""
    return jsonify({"visits": read_visits_count()}), 200


@app.route("/health", methods=["GET"])
def health() -> Any:
    """Lightweight health probe endpoint."""
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


@app.route("/metrics", methods=["GET"])
def metrics() -> Response:
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.errorhandler(404)
def not_found(error):  # type: ignore[override]
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(error):  # type: ignore[override]
    request_info = get_request_info()
    logging.exception(
        "unhandled_exception",
        extra={
            "event": "error",
            "method": request_info["method"],
            "path": request_info["path"],
            "client_ip": request_info["client_ip"],
            "app": APP_NAME,
            "version": APP_VERSION,
        },
    )
    return (
        jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred"}),
        500,
    )


def main() -> None:
    startup_visits = initialize_visits_storage()
    setup_logging()
    logging.info(
        "visits_counter_initialized",
        extra={
            "event": "visits_counter_initialized",
            "visits": startup_visits,
            "app": APP_NAME,
            "version": APP_VERSION,
        },
    )
    app.run(host=HOST, port=PORT, debug=DEBUG, use_reloader=False)


if __name__ == "__main__":
    main()
