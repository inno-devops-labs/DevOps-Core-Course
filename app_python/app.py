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
from datetime import datetime, timezone

from flask import Flask, jsonify, request, g
from werkzeug.exceptions import HTTPException

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

SERVICE_NAME = os.getenv("SERVICE_NAME", "devops-info-service")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
SERVICE_DESCRIPTION = os.getenv("SERVICE_DESCRIPTION", "DevOps course info service")
SERVICE_FRAMEWORK = "Flask"


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
                "asctime"
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
    human = f"{hours} {_plural(hours, 'hour', 'hours')}, {minutes} {_plural(minutes, 'minute', 'minutes')}"
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
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"},
    ]


@app.before_request
def before_request_logging():
    g.request_started_at = datetime.now(timezone.utc)
    logger.info("HTTP request started", extra=get_request_info())


@app.after_request
def after_request_logging(response):
    extra = get_request_info()
    extra["status_code"] = response.status_code
    logger.info("HTTP request completed", extra=extra)
    return response

# Routes
@app.route("/", methods=["GET"])
def index():
    uptime = get_uptime()
    payload = {
        "service": {
            "name": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "description": SERVICE_DESCRIPTION,
            "framework": SERVICE_FRAMEWORK,
        },
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": iso_utc_now(),
            "timezone": "UTC",
        },
        "request": get_request_info(),
        "endpoints": get_endpoints(),
    }
    return jsonify(payload), 200


@app.route("/health", methods=["GET"])
def health():
    uptime = get_uptime()
    return jsonify(
        {
            "status": "healthy",
            "timestamp": iso_utc_now(),
            "uptime_seconds": uptime["seconds"],
        }
    ), 200


@app.errorhandler(404)
def not_found(_error):
    extra = get_request_info()
    extra["status_code"] = 404
    logger.warning("Endpoint does not exist", extra=extra)
    return jsonify(
        {
            "error": "Not Found",
            "message": "Endpoint does not exist",
        }
    ), 404


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
        {
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        }
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
