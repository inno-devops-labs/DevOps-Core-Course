"""
DevOps Info Service
Labs 3/7/8 — DevOps Core Course

Features:
- Flask API endpoints: /, /health, /metrics
- JSON structured logging to stdout (for Loki/Promtail)
- Prometheus metrics (RED):
  - Counter: http_requests_total{method,endpoint,status_code}
  - Histogram: http_request_duration_seconds{method,endpoint}
  - Gauge: http_requests_in_progress
- Low-cardinality endpoint label via normalize_endpoint()
"""

from __future__ import annotations

import json
import logging
import os
import platform
import socket
import sys
import time
from datetime import UTC, datetime
from typing import Any
from pathlib import Path

from flask import Flask, g, jsonify, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from werkzeug.exceptions import HTTPException

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8005"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

START_TIME = datetime.now(UTC)
VISITS_FILE = Path(os.getenv("VISITS_FILE", "/app/visits"))
# -----------------------------------------------------------------------------
# Logging (JSON to stdout)
# -----------------------------------------------------------------------------
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        # Optional structured fields
        for k in ("method", "path", "status_code", "client_ip", "user_agent"):
            if hasattr(record, k):
                payload[k] = getattr(record, k)

        return json.dumps(payload, ensure_ascii=False)


logger = logging.getLogger("devops-info-service")
logger.setLevel(logging.INFO)

_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(JSONFormatter())

logger.handlers = [_handler]
logger.propagate = False

# -----------------------------------------------------------------------------
# Prometheus metrics (RED)
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# App
# -----------------------------------------------------------------------------
app = Flask(__name__)


def read_visits() -> int:
    try:
        if VISITS_FILE.exists():
            return int(VISITS_FILE.read_text().strip() or "0")
    except Exception:
        return 0
    return 0

def write_visits(value: int) -> None:
    VISITS_FILE.parent.mkdir(parents=True, exist_ok=True)
    VISITS_FILE.write_text(str(value))


def get_uptime() -> dict[str, Any]:
    delta = datetime.now(UTC) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {"seconds": seconds, "human": f"{hours} hours, {minutes} minutes"}


def get_system_info() -> dict[str, Any]:
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }


def get_client_ip() -> str:
    # Prefer X-Forwarded-For if present (first IP)
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.remote_addr or "unknown"


def normalize_endpoint(path: str) -> str:
    """
    Keep endpoint label low-cardinality:
    - known endpoints: '/', '/health', '/metrics'
    - everything else -> '/other'
    """
    if path in ("/", "/health", "/metrics", "/visits"):
        return path
    return "/other"


# -----------------------------------------------------------------------------
# Request logging hooks (JSON logs)
# -----------------------------------------------------------------------------
@app.before_request
def log_request_start() -> None:
    g.client_ip = get_client_ip()
    logger.info(
        "request_started",
        extra={
            "method": request.method,
            "path": request.path,
            "client_ip": g.client_ip,
            "user_agent": request.headers.get("User-Agent", ""),
        },
    )


@app.after_request
def log_request_finish(response):
    logger.info(
        "request_finished",
        extra={
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "client_ip": getattr(g, "client_ip", "unknown"),
        },
    )
    return response


# -----------------------------------------------------------------------------
# Prometheus metrics hooks
# -----------------------------------------------------------------------------
@app.before_request
def metrics_before() -> None:
    g._start_time = time.perf_counter()
    http_requests_in_progress.inc()


@app.after_request
def metrics_after(resp):
    try:
        duration = time.perf_counter() - getattr(g, "_start_time", time.perf_counter())
        endpoint = normalize_endpoint(request.path)

        http_requests_total.labels(
            request.method, endpoint, str(resp.status_code)
        ).inc()

        http_request_duration_seconds.labels(
            request.method, endpoint
        ).observe(duration)
    finally:
        http_requests_in_progress.dec()

    return resp


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    visits = read_visits() + 1
    write_visits(visits)

    uptime = get_uptime()

    response = {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "Flask",
        },
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": datetime.now(UTC).isoformat(),
            "timezone": "UTC",
        },
        "request": {
            "client_ip": request.remote_addr,
            "user_agent": request.headers.get("User-Agent"),
            "method": request.method,
            "path": request.path,
        },
        "visits": visits,
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
            {"path": "/visits", "method": "GET", "description": "Visits counter"},
        ],
    }

    return jsonify(response)


@app.route("/health", methods=["GET"])
def health():
    uptime = get_uptime()
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now(UTC).isoformat(),
            "uptime_seconds": uptime["seconds"],
        }
    )


@app.route("/metrics", methods=["GET"])
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@app.route("/visits")
def visits():
    return jsonify(visits=read_visits())

# -----------------------------------------------------------------------------
# Error Handlers (JSON + logging)
# -----------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(_error):
    logger.warning(
        "http_error",
        extra={
            "method": request.method,
            "path": request.path,
            "status_code": 404,
            "client_ip": getattr(g, "client_ip", "unknown"),
        },
    )
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(Exception)
def handle_exception(error):
    # Convert HTTP errors to JSON
    if isinstance(error, HTTPException):
        code = error.code or 500
        logger.warning(
            "http_error",
            extra={
                "method": request.method,
                "path": request.path,
                "status_code": code,
                "client_ip": getattr(g, "client_ip", "unknown"),
            },
        )
        return jsonify({"error": error.name, "message": error.description}), code

    # Unhandled exception -> 500 JSON
    logger.error(
        "unhandled_exception",
        extra={
            "method": request.method,
            "path": request.path,
            "status_code": 500,
            "client_ip": getattr(g, "client_ip", "unknown"),
        },
    )
    return jsonify({"error": "Internal Server Error", "message": "Unexpected error"}), 500


# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("startup")
    app.run(host=HOST, port=PORT, debug=DEBUG)