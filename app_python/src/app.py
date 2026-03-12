"""
DevOps Info Service
Main application module
"""

import os
import socket
import platform
import logging
import json
from datetime import datetime, timezone
from flask import Flask, jsonify, request


class JSONFormatter(logging.Formatter):
    """Format logs as structured JSON for log aggregation systems."""

    _default_fields = set(logging.makeLogRecord({}).__dict__.keys())

    @staticmethod
    def _to_json_value(value):
        try:
            json.dumps(value)
            return value
        except TypeError:
            return str(value)

    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if key not in self._default_fields and not key.startswith("_"):
                log_entry[key] = self._to_json_value(value)

        return json.dumps(log_entry, ensure_ascii=True)


def configure_logging():
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(stream_handler)


configure_logging()
logger = logging.getLogger("devops-info-service")

app = Flask(__name__)


# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))

# Application start time
START_TIME = datetime.now(timezone.utc)


def get_system_info():
    """Collect system information."""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
    }


def get_request():
    return {
        "client_ip": request.remote_addr,  # Client IP
        "user_agent": request.headers.get("User-Agent"),  # User agent
        "method": request.method,  # HTTP method
        "path": request.path,  # Request path
    }


def get_service():
    return {
        "name": "devops-info-service",
        "version": "1.0.0",
        "description": "DevOps course info service",
        "framework": "Flask",
    }


@app.before_request
def log_request_started():
    logger.info(
        "request_started",
        extra={
            "method": request.method,
            "path": request.path,
            "client_ip": request.remote_addr,
            "user_agent": request.headers.get("User-Agent"),
        },
    )


@app.after_request
def log_request_completed(response):
    logger.info(
        "request_completed",
        extra={
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "client_ip": request.remote_addr,
        },
    )
    return response


@app.route("/")
def index():
    """Main endpoint - service and system information."""
    return {
        "service": get_service(),
        "system": get_system_info(),
        "request": get_request(),
        "runtime": get_uptime(),
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
        ],
    }


def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    now_utc = datetime.now(timezone.utc).isoformat()
    # Example output: '2026-01-28T19:10:00.123456+00:00'
    # Replace the +00:00 with Z
    iso_format_zulu = now_utc.replace("+00:00", ".000Z")
    return {
        "seconds": seconds,
        "human": f"{hours} hours, {minutes} minutes",
        "current_time": iso_format_zulu,
        "timezone": "UTC",
    }


@app.route("/health")
def health():
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": get_uptime()["seconds"],
        }
    )


@app.errorhandler(404)
def not_found(error):
    logger.warning(
        "not_found",
        extra={
            "method": request.method,
            "path": request.path,
            "status_code": 404,
            "client_ip": request.remote_addr,
        },
    )
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(
        "internal_error",
        extra={
            "method": request.method,
            "path": request.path,
            "status_code": 500,
            "client_ip": request.remote_addr,
            "error": str(error),
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
    logger.info("application_starting", extra={"host": HOST, "port": PORT})
    app.run(host=HOST, port=PORT)
