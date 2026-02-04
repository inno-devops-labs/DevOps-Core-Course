"""
DevOps Info Service (Lab 01)
Flask web application that reports system/runtime/request info.
"""

import logging
import os
import platform
import socket
from datetime import datetime, timezone
from typing import Dict, Any

from flask import Flask, jsonify, request

app = Flask(__name__)

# Configuration via environment variables
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# App start time (UTC)
START_TIME = datetime.now(timezone.utc)

# Logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("devops-info-service")


def get_uptime() -> Dict[str, Any]:
    """Return uptime in seconds and human-readable form."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        "uptime_seconds": seconds,
        "uptime_human": f"{hours} hours, {minutes} minutes",
    }


def get_system_info() -> Dict[str, Any]:
    """Collect system information."""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.platform(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 0,
        "python_version": platform.python_version(),
    }


def get_request_info() -> Dict[str, Any]:
    """Collect request information."""
    return {
        "client_ip": request.headers.get("X-Forwarded-For", request.remote_addr),
        "user_agent": request.headers.get("User-Agent", ""),
        "method": request.method,
        "path": request.path,
    }


@app.before_request
def log_request() -> None:
    logger.debug("Request: %s %s", request.method, request.path)


@app.route("/", methods=["GET"])
def index():
    uptime = get_uptime()

    payload = {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "Flask",
        },
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": uptime["uptime_seconds"],
            "uptime_human": uptime["uptime_human"],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "request": get_request_info(),
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
        ],
    }
    return jsonify(payload), 200


@app.route("/health", methods=["GET"])
def health():
    uptime = get_uptime()
    return (
        jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime_seconds": uptime["uptime_seconds"],
            }
        ),
        200,
    )


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(_error):
    return (
        jsonify(
            {"error": "Internal Server Error", "message": "An unexpected error occurred"}
        ),
        500,
    )


if __name__ == "__main__":
    logger.info("Starting app on %s:%s (debug=%s)", HOST, PORT, DEBUG)
    app.run(host=HOST, port=PORT, debug=DEBUG)
