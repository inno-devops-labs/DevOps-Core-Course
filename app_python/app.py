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
from datetime import datetime, timezone
from typing import Any, Dict

from flask import Flask, jsonify, request, g

APP_NAME = "devops-info-service"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "DevOps course info service"
APP_FRAMEWORK = "Flask"

# Configuration (env)2
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Application start time (UTC)
START_TIME = datetime.now(timezone.utc)


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
    handler = logging.StreamHandler()
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


@app.route("/", methods=["GET"])
def index():
    """Main endpoint - service and system information."""
    uptime = get_uptime()

    payload = {
        "service": {
            "name": APP_NAME,
            "version": APP_VERSION,
            "description": APP_DESCRIPTION,
            "framework": APP_FRAMEWORK,
        },
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
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
        ],
    }

    return jsonify(payload), 200


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint - used for probes and monitoring."""
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
