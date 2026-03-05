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
from datetime import datetime, timezone
from typing import Any, Dict

from flask import Flask, jsonify, request

APP_NAME = "devops-info-service"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "DevOps course info service"
APP_FRAMEWORK = "Flask"

# Configuration (env)
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Application start time (UTC)
START_TIME = datetime.now(timezone.utc)

# Logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logging.getLogger("werkzeug").disabled = True
logger = logging.getLogger(APP_NAME)

app = Flask(__name__)


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
    logger.debug(
        "Request: %s %s UA=%s IP=%s",
        request.method,
        request.path,
        request.headers.get("User-Agent", ""),
        get_client_ip(),
    )


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
    return (
        jsonify({"error": "Not Found", "message": "Endpoint does not exist"}),
        404,
    )


@app.errorhandler(500)
def internal_error(_error):
    logger.exception("Unhandled exception")
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
        "Starting %s v%s on %s:%s (DEBUG=%s)",
        APP_NAME,
        APP_VERSION,
        HOST,
        PORT,
        DEBUG,
    )
    app.run(host=HOST, port=PORT, debug=DEBUG)


if __name__ == "__main__":
    main()
