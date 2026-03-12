"""
DevOps Info Service
Main application module

Provides system, runtime, and request information,
as well as a health check endpoint.
"""

import os
import socket
import platform
import logging
import json
from datetime import datetime, timezone

from flask import Flask, jsonify, request

# ------------------------------------------------------------------------------
# Application setup
# ------------------------------------------------------------------------------

app = Flask(__name__)

# Configuration via environment variables
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Application start time (used for uptime calculation)
START_TIME = datetime.now(timezone.utc)

# ------------------------------------------------------------------------------
# Logging configuration
# ------------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger(__name__)

logger.info(json.dumps({
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "level": "INFO",
    "event": "startup",
    "message": "DevOps Info Service starting..."
}))

# ------------------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------------------

def get_uptime():
    """
    Calculate application uptime.

    Returns:
        tuple: uptime in seconds (int), human-readable uptime (str)
    """
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return seconds, f"{hours} hours, {minutes} minutes"


def get_system_info():
    """
    Collect system information.

    Returns:
        dict: system information
    """
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.release(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }

# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def index():
    """
    Main endpoint returning service, system, runtime, and request information.
    """
    logger.info(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "INFO",
        "event": "request",
        "endpoint": "index",
        "method": request.method,
        "path": request.path,
        "client_ip": request.remote_addr,
        "status_code": 200,
        "user_agent": request.headers.get("User-Agent"),
    }))

    uptime_seconds, uptime_human = get_uptime()

    response = {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "Flask",
        },
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": uptime_seconds,
            "uptime_human": uptime_human,
            "current_time": datetime.now(timezone.utc).isoformat(),
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
    """
    Health check endpoint.
    """
    uptime_seconds, _ = get_uptime()

    logger.info(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "INFO",
        "event": "request",
        "endpoint": "health",
        "method": request.method,
        "path": request.path,
        "client_ip": request.remote_addr,
        "status_code": 200,
        "user_agent": request.headers.get("User-Agent"),
    }))

    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_seconds,
    })

# ------------------------------------------------------------------------------
# Error handlers
# ------------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(error):
    """
    Handle 404 errors.
    """
    logger.warning(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "WARNING",
        "event": "http_error",
        "error_type": "NotFound",
        "path": request.path,
        "method": request.method,
        "status_code": 404,
        "client_ip": request.remote_addr,
    }))
    return jsonify({
        "error": "Not Found",
        "message": "Endpoint does not exist",
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """
    Handle 500 errors.
    """
    logger.error(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "ERROR",
        "event": "http_error",
        "error_type": "InternalServerError",
        "path": request.path,
        "method": request.method,
        "status_code": 500,
        "client_ip": request.remote_addr,
        "error": str(error),
    }))
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
    }), 500

# ------------------------------------------------------------------------------
# Application entry point
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)
