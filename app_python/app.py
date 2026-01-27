"""
DevOps Info Service
Main Flask application module.
"""

import logging
import os
import platform
import socket
from datetime import datetime, timezone

from flask import Flask, jsonify, request


app = Flask(__name__)


# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
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


def get_system_info() -> dict:
    """Collect basic system information."""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }


def get_uptime() -> dict:
    """Calculate uptime in seconds and human-readable form."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        "uptime_seconds": seconds,
        "uptime_human": f"{hours} hours, {minutes} minutes",
    }


def get_request_info() -> dict:
    """Extract request-related information."""
    user_agent = request.headers.get("User-Agent") or request.headers.get(
        "user-agent"
    )
    return {
        "client_ip": request.remote_addr,
        "user_agent": user_agent,
        "method": request.method,
        "path": request.path,
    }


@app.route("/", methods=["GET"])
def index():
    """Main endpoint — service, system, runtime, and request information."""
    logger.info("Handling / request")

    uptime_info = get_uptime()

    response = {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "Flask",
        },
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": uptime_info["uptime_seconds"],
            "uptime_human": uptime_info["uptime_human"],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "request": get_request_info(),
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

    logger.debug("Response payload for / endpoint generated")
    return jsonify(response)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    logger.info("Handling /health request")
    uptime_info = get_uptime()
    response = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_info["uptime_seconds"],
    }
    return jsonify(response), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors."""
    logger.warning("404 Not Found: %s %s", request.method, request.path)
    return (
        jsonify(
            {
                "error": "Not Found",
                "message": "Endpoint does not exist",
                "path": request.path,
            }
        ),
        404,
    )


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server Error."""
    logger.exception("500 Internal Server Error: %s", error)
    return (
        jsonify(
            {
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
            }
        ),
        500,
    )


def main():
    """Application entrypoint."""
    logger.info("Starting DevOps Info Service on %s:%s (debug=%s)", HOST, PORT, DEBUG)
    app.run(host=HOST, port=PORT, debug=DEBUG)


if __name__ == "__main__":
    main()

