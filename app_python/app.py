"""
DevOps Info Service
Flask application that exposes system/runtime information
and a health endpoint.
"""

from __future__ import annotations

import logging
import os
import platform
import socket
import json
import sys
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from flask import Flask, Response, jsonify, request, g
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

APP_NAME = "devops-info-service"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "DevOps course info service"
APP_FRAMEWORK = "Flask"

# Configuration (env)
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
DEFAULT_CONFIG_PATH = Path(os.getenv("APP_CONFIG_PATH", "/config/config.json"))
DEFAULT_VISITS_FILE = Path(os.getenv("VISITS_FILE", "data/visits"))

# Application start time (UTC)
START_TIME = datetime.now(timezone.utc)


class VisitCounter:
    """Thread-safe file-backed visit counter."""

    def __init__(self, file_path: Path) -> None:
        self._lock = threading.Lock()
        self._count = 0
        self.file_path = Path(file_path)
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self._count = int(self.file_path.read_text().strip())
        except FileNotFoundError:
            self._count = 0
        except (OSError, ValueError):
            self._count = 0

    def _write_to_disk(self, count: int) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        temp_file = self.file_path.with_suffix(f"{self.file_path.suffix}.tmp")
        temp_file.write_text(f"{count}\n")
        os.replace(temp_file, self.file_path)

    def increment(self) -> int:
        with self._lock:
            self._count += 1
            self._write_to_disk(self._count)
            return self._count

    def get_count(self) -> int:
        with self._lock:
            return self._count

    def reset(self, file_path: Path | None = None) -> None:
        with self._lock:
            if file_path is not None:
                self.file_path = Path(file_path)
            self._count = 0
            if self.file_path.exists():
                self.file_path.unlink()
            self.file_path.parent.mkdir(parents=True, exist_ok=True)


visit_counter = VisitCounter(DEFAULT_VISITS_FILE)


class JSONFormatter(logging.Formatter):
    """Format log records as JSON with UTC timestamps."""

    RESERVED_ATTRS = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
    }

    # type: ignore[override]
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key in self.RESERVED_ATTRS or key.startswith("_"):
                continue
            log_record[key] = value

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record, default=str)


def configure_logging() -> logging.Logger:
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.setLevel(logging.WARNING)

    app_logger = logging.getLogger(APP_NAME)
    app_logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    return app_logger


app = Flask(__name__)
logger = configure_logging()

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests handled by the Flask app",
    ["method", "endpoint", "status_code"],
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status_code"],
)
http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method", "endpoint"],
)
devops_info_endpoint_calls_total = Counter(
    "devops_info_endpoint_calls_total",
    "Number of calls to application endpoints",
    ["endpoint"],
)
devops_info_system_collection_seconds = Histogram(
    "devops_info_system_collection_seconds",
    "Time spent collecting system information",
)


def normalize_endpoint() -> str:
    """Return a low-cardinality endpoint label for metrics."""
    if request.url_rule and request.url_rule.rule:
        return request.url_rule.rule
    return request.path or "unknown"


def get_uptime() -> Dict[str, Any]:
    """Return uptime in seconds and a human-friendly format."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {"seconds": seconds, "human": f"{hours} hours, {minutes} minutes"}


def get_system_info() -> Dict[str, Any]:
    """Collect basic system information."""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.platform(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 0,
        "python_version": platform.python_version(),
    }


def load_app_config() -> Dict[str, Any]:
    """Load application configuration from file with env overrides."""
    config_path = Path(app.config.get("APP_CONFIG_PATH", DEFAULT_CONFIG_PATH))
    file_config: Dict[str, Any] = {}
    config_loaded = False

    try:
        file_config = json.loads(config_path.read_text())
        config_loaded = True
    except FileNotFoundError:
        file_config = {}
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning(
            "config_load_failed",
            extra={
                "event": "config_load_failed",
                "config_path": str(config_path),
                "error": str(exc),
            },
        )

    return {
        "name": os.getenv(
            "APP_DISPLAY_NAME",
            file_config.get("applicationName", APP_NAME),
        ),
        "environment": os.getenv(
            "APP_ENV",
            file_config.get("environment", "dev"),
        ),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "feature_flags": file_config.get("featureFlags", {}),
        "settings": file_config.get("settings", {}),
        "config_path": str(config_path),
        "config_loaded": config_loaded,
    }


def get_client_ip() -> str:
    """
    Best-effort client IP extraction.
    If behind reverse proxy, X-Forwarded-For may exist.
    """
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        # XFF can be: "client, proxy1, proxy2"
        return xff.split(",")[0].strip()
    return request.remote_addr or "unknown"


@app.before_request
def log_request() -> None:
    g.request_start = datetime.now(timezone.utc)
    g.request_start_perf = time.perf_counter()
    g.metrics_endpoint = normalize_endpoint()
    g.request_gauge = http_requests_in_progress.labels(
        method=request.method,
        endpoint=g.metrics_endpoint,
    )
    g.request_gauge.inc()
    logger.info(
        "request_received",
        extra={
            "event": "request_received",
            "method": request.method,
            "path": request.path,
            "client_ip": get_client_ip(),
            "user_agent": request.headers.get("User-Agent", ""),
        },
    )


@app.after_request
def log_response(response):
    start_time = getattr(g, "request_start", datetime.now(timezone.utc))
    temp = datetime.now(timezone.utc) - start_time
    duration_ms = int(temp.total_seconds() * 1000)
    endpoint = getattr(g, "metrics_endpoint", normalize_endpoint())
    start_perf = getattr(g, "request_start_perf", time.perf_counter())
    duration_seconds = max(time.perf_counter() - start_perf, 0.0)
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
    ).observe(duration_seconds)

    logger.info(
        "response_sent",
        extra={
            "event": "response_sent",
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "client_ip": get_client_ip(),
            "duration_ms": duration_ms,
            "content_length": response.content_length or 0,
        },
    )
    return response


@app.teardown_request
def track_request_teardown(_error) -> None:
    request_gauge = getattr(g, "request_gauge", None)
    if request_gauge is not None:
        request_gauge.dec()
        g.request_gauge = None


@app.route("/", methods=["GET"])
def index():
    """Main endpoint - service and system information."""
    devops_info_endpoint_calls_total.labels(endpoint="/").inc()
    current_visits = visit_counter.increment()
    uptime = get_uptime()
    app_config = load_app_config()
    with devops_info_system_collection_seconds.time():
        system_info = get_system_info()

    payload = {
        "service": {
            "name": app_config["name"],
            "version": APP_VERSION,
            "description": APP_DESCRIPTION,
            "framework": APP_FRAMEWORK,
        },
        "system": system_info,
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "configuration": {
            "environment": app_config["environment"],
            "log_level": app_config["log_level"],
            "feature_flags": app_config["feature_flags"],
            "settings": app_config["settings"],
            "config_path": app_config["config_path"],
            "config_loaded": app_config["config_loaded"],
        },
        "visits": {
            "count": current_visits,
            "storage_path": str(visit_counter.file_path),
        },
        "request": {
            "client_ip": get_client_ip(),
            "user_agent": request.headers.get("User-Agent", ""),
            "method": request.method,
            "path": request.path,
        },
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
            {
                "path": "/visits",
                "method": "GET",
                "description": "Persistent visits counter",
            },
        ],
    }

    return jsonify(payload), 200


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint - used for probes and monitoring."""
    devops_info_endpoint_calls_total.labels(endpoint="/health").inc()
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
    devops_info_endpoint_calls_total.labels(endpoint="/metrics").inc()
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route("/visits", methods=["GET"])
def visits():
    """Return the current visit count."""
    devops_info_endpoint_calls_total.labels(endpoint="/visits").inc()
    return jsonify({"visits": visit_counter.get_count()}), 200


@app.errorhandler(404)
def not_found(_error):
    logger.warning(
        "not_found",
        extra={
            "event": "not_found",
            "method": request.method,
            "path": request.path,
            "client_ip": get_client_ip(),
        },
    )
    return (
        jsonify({"error": "Not Found", "message": "Endpoint does not exist"}),
        404,
    )


@app.errorhandler(500)
def internal_error(_error):
    logger.exception(
        "Unhandled exception",
        extra={
            "event": "internal_error",
            "method": request.method,
            "path": request.path,
            "client_ip": get_client_ip(),
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


def main() -> None:
    logger.info(
        "service_startup",
        extra={
            "event": "startup",
            "service": APP_NAME,
            "version": APP_VERSION,
            "host": HOST,
            "port": PORT,
            "debug": DEBUG,
        },
    )
    app.run(host=HOST, port=PORT, debug=DEBUG)


if __name__ == "__main__":
    main()
