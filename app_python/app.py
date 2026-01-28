"""
DevOps Info Service
Main application module for Lab 1.
"""

import logging
import os
import platform
import socket
from datetime import datetime, timezone
from typing import Any, Dict

from flask import Flask, jsonify, request


app = Flask(__name__)


# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5002))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"


# Application start time (for uptime calculation)
START_TIME = datetime.now(timezone.utc)


# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
logger.info("Application starting...")


def get_uptime() -> Dict[str, Any]:
    """Return uptime in seconds and human-readable form."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        "seconds": seconds,
        "human": f"{hours} hours, {minutes} minutes",
    }


def get_system_info() -> Dict[str, Any]:
    """Collect system information."""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.platform(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 1,
        "python_version": platform.python_version(),
    }


def get_request_info() -> Dict[str, Any]:
    """Collect request information from the current Flask request."""
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    user_agent = request.headers.get("User-Agent", "")

    return {
        "client_ip": client_ip,
        "user_agent": user_agent,
        "method": request.method,
        "path": request.path,
    }


@app.route("/", methods=["GET"])
def index():
    """Main endpoint - service and system information."""
    uptime = get_uptime()
    system_info = get_system_info()
    request_info = get_request_info()

    response = {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "Flask",
        },
        "system": system_info,
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "request": request_info,
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

    logger.info("Handled main / request")
    return jsonify(response)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    uptime = get_uptime()
    payload = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime["seconds"],
    }
    logger.info("Health check OK")
    return jsonify(payload), 200


@app.errorhandler(404)
def not_found(error):
    """Return JSON for 404 errors."""
    logger.warning("404 Not Found: %s %s", request.method, request.path)
    return (
        jsonify(
            {
                "error": "Not Found",
                "message": "Endpoint does not exist",
            }
        ),
        404,
    )


@app.errorhandler(500)
def internal_error(error):
    """Return JSON for 500 errors."""
    logger.exception("500 Internal Server Error")
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
    logger.info("Starting Flask development server on %s:%s", HOST, PORT)
    app.run(host=HOST, port=PORT, debug=DEBUG)
