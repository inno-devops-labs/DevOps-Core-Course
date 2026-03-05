"""
DevOps Info Service
Main application module
"""

import os
import socket
import platform
import logging
from datetime import datetime, timezone
from flask import Flask, jsonify, request

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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


@app.route("/")
def index():
    logger.debug(f"Request: {request.method} {request.path}")
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
    logger.debug(f"Request: {request.method} {request.path}")
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": get_uptime()["seconds"],
        }
    )


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(error):
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
    app.run(host=HOST, port=PORT)
    logger.info("Application starting...")
