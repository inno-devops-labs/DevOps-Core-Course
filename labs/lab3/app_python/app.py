"""
DevOps Info Service
Lab 03 — DevOps Core Course
"""

import json
import logging
import os
import platform
import socket
import sys
from datetime import UTC, datetime
from typing import Any

from flask import Flask, g, jsonify, request
from werkzeug.exceptions import HTTPException

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8005"))  # Lab 7 expects port 8000, but vs code use this too :(
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

START_TIME = datetime.now(UTC)

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

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())

logger.handlers = [handler]
logger.propagate = False

# -----------------------------------------------------------------------------
# App
# -----------------------------------------------------------------------------
app = Flask(__name__)


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


@app.route("/", methods=["GET"])
def index():
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
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
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


# -----------------------------------------------------------------------------
# Error Handlers (JSON + logging)
# -----------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(error):
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


if __name__ == "__main__":
    logger.info("startup")
    app.run(host=HOST, port=PORT, debug=DEBUG)