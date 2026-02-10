"""
DevOps Info Service
Lab 03 — DevOps Core Course
"""

import logging
import os
import platform
import socket
from datetime import UTC, datetime

from flask import Flask, jsonify, request

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

START_TIME = datetime.now(UTC)

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# App
# -----------------------------------------------------------------------------
app = Flask(__name__)


def get_uptime():
    delta = datetime.now(UTC) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        "seconds": seconds,
        "human": f"{hours} hours, {minutes} minutes",
    }


def get_system_info():
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }


@app.route("/", methods=["GET"])
def index():
    logger.info("Handling main endpoint request")

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
# Error Handlers (Best Practices from course)
# -----------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(error):
    return jsonify(
        {"error": "Not Found", "message": "Endpoint does not exist"}
    ), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify(
        {"error": "Internal Server Error", "message": "Unexpected error"}
    ), 500


if __name__ == "__main__":
    logger.info("Starting application...")
    app.run(host=HOST, port=PORT, debug=DEBUG)
