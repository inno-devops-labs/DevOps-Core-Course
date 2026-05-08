"""
DevOps Info Service
LAB01: Python Web Application (Flask)
"""

import json
import os
import socket
import logging
import platform
import sys
import time
from threading import Lock
from datetime import datetime, timezone

from flask import Flask, jsonify, request, g
from werkzeug.exceptions import HTTPException
from prometheus_client import (
    Counter, Histogram, Gauge,
    generate_latest, CONTENT_TYPE_LATEST
)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
VISITS_FILE = os.getenv("VISITS_FILE", "/data/visits")

SERVICE_NAME = os.getenv("SERVICE_NAME", "devops-info-service")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
SERVICE_DESCRIPTION = os.getenv("SERVICE_DESCRIPTION", "DevOps course info service")
SERVICE_FRAMEWORK = "Flask"

# ── Prometheus Metrics ────────────────────────────────────────────────────────

# RED Method: Rate
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

# RED Method: Duration
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0],
)

# Active connections (Gauge)
http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method", "endpoint"],
)

# App-specific: endpoint usage counter
devops_info_endpoint_calls_total = Counter(
    "devops_info_endpoint_calls_total",
    "Total calls per application endpoint",
    ["endpoint"],
)

# App-specific: system info collection time
devops_info_system_collection_seconds = Histogram(
    "devops_info_system_collection_seconds",
    "Time spent collecting system information",
)

# ── Logging ───────────────────────────────────────────────────────────────────

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
        }

        for key, value in record.__dict__.items():
            if key in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
                "asctime",
            }:
                continue
            if key.startswith("_"):
                continue
            payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def setup_logging() -> logging.Logger:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(LOG_LEVEL)
    app_logger = logging.getLogger("devops-info-service")
    app_logger.setLevel(LOG_LEVEL)
    return app_logger


logger = setup_logging()
app = Flask(__name__)
START_TIME = datetime.now(timezone.utc)
VISITS_LOCK = Lock()

# ── Helpers ───────────────────────────────────────────────────────────────────

def iso_utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _plural(n: int, one: str, many: str) -> str:
    return one if n == 1 else many


def get_uptime() -> dict:
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    human = (
        f"{hours} {_plural(hours, 'hour', 'hours')}, "
        f"{minutes} {_plural(minutes, 'minute', 'minutes')}"
    )
    return {"seconds": seconds, "human": human}


def get_platform_version() -> str:
    try:
        if hasattr(platform, "freedesktop_os_release"):
            data = platform.freedesktop_os_release()
            pretty = data.get("PRETTY_NAME")
            if pretty:
                return pretty
    except Exception:
        pass
    return platform.platform()


def get_system_info() -> dict:
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": get_platform_version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 0,
        "python_version": platform.python_version(),
    }


def get_request_info() -> dict:
    forwarded_for = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    client_ip = forwarded_for or request.remote_addr
    return {
        "client_ip": client_ip,
        "user_agent": request.headers.get("User-Agent", ""),
        "method": request.method,
        "path": request.path,
    }


def get_endpoints() -> list:
    return [
        {"path": "/",        "method": "GET", "description": "Service information"},
        {"path": "/visits",  "method": "GET", "description": "Current visits counter"},
        {"path": "/health",  "method": "GET", "description": "Health check"},
        {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
    ]


def read_visits_count() -> int:
    try:
        with open(VISITS_FILE, "r", encoding="utf-8") as visits_file:
            content = visits_file.read().strip()
            return int(content) if content else 0
    except FileNotFoundError:
        return 0
    except ValueError:
        return 0


def write_visits_count(count: int) -> None:
    os.makedirs(os.path.dirname(VISITS_FILE), exist_ok=True)
    temp_file = f"{VISITS_FILE}.tmp"
    with open(temp_file, "w", encoding="utf-8") as visits_file:
        visits_file.write(str(count))
    os.replace(temp_file, VISITS_FILE)


def increment_visits_count() -> int:
    with VISITS_LOCK:
        current = read_visits_count()
        updated = current + 1
        write_visits_count(updated)
        return updated

# ── Middleware ────────────────────────────────────────────────────────────────

@app.before_request
def before_request_logging():
    g.request_started_at = datetime.now(timezone.utc)
    g.start_time = time.perf_counter()
    http_requests_in_progress.labels(
        method=request.method, endpoint=request.path
    ).inc()
    logger.info("HTTP request started", extra=get_request_info())


@app.after_request
def after_request_logging(response):
    duration = time.perf_counter() - g.get("start_time", time.perf_counter())
    endpoint = request.path
    method = request.method
    status_code = str(response.status_code)

    http_requests_total.labels(
        method=method, endpoint=endpoint, status_code=status_code
    ).inc()
    http_request_duration_seconds.labels(
        method=method, endpoint=endpoint
    ).observe(duration)
    http_requests_in_progress.labels(
        method=method, endpoint=endpoint
    ).dec()

    extra = get_request_info()
    extra["status_code"] = response.status_code
    logger.info("HTTP request completed", extra=extra)
    return response

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    devops_info_endpoint_calls_total.labels(endpoint="/").inc()
    visits_count = increment_visits_count()
    with devops_info_system_collection_seconds.time():
        system_info = get_system_info()
    uptime = get_uptime()
    payload = {
        "service": {
            "name": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "description": SERVICE_DESCRIPTION,
            "framework": SERVICE_FRAMEWORK,
        },
        "system": system_info,
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": iso_utc_now(),
            "timezone": "UTC",
        },
        "request": get_request_info(),
        "visits": {"count": visits_count, "storage_file": VISITS_FILE},
        "endpoints": get_endpoints(),
    }
    return jsonify(payload), 200


@app.route("/visits", methods=["GET"])
def visits():
    devops_info_endpoint_calls_total.labels(endpoint="/visits").inc()
    return jsonify({"visits": read_visits_count(), "storage_file": VISITS_FILE}), 200


@app.route("/health", methods=["GET"])
def health():
    devops_info_endpoint_calls_total.labels(endpoint="/health").inc()
    uptime = get_uptime()
    return jsonify(
        {
            "status": "healthy",
            "timestamp": iso_utc_now(),
            "uptime_seconds": uptime["seconds"],
        }
    ), 200


@app.route("/metrics", methods=["GET"])
def metrics():
    """Prometheus metrics endpoint."""
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@app.errorhandler(404)
def not_found(_error):
    extra = get_request_info()
    extra["status_code"] = 404
    logger.warning("Endpoint does not exist", extra=extra)
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(Exception)
def handle_exception(error):
    if isinstance(error, HTTPException):
        return error
    extra = {}
    try:
        extra = get_request_info()
    except Exception:
        pass
    extra["status_code"] = 500
    logger.exception("Unhandled exception", extra=extra)
    return jsonify(
        {"error": "Internal Server Error", "message": "An unexpected error occurred"}
    ), 500


if __name__ == "__main__":
    logger.info(
        "Application startup",
        extra={
            "host": HOST,
            "port": PORT,
            "debug": DEBUG,
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
        },
    )
    app.run(host=HOST, port=PORT, debug=DEBUG)
