"""
DevOps Info Service
Main application module providing system information and health status.
Structured JSON logging for Loki/observability (Lab 7).
"""

import os
import socket
import platform
import logging
from datetime import datetime, timezone
from flask import Flask, jsonify, request, g

from pythonjsonlogger import jsonlogger

def setup_logging():
    """Configure JSON logging for Loki/observability (timestamp, level, message + extra)."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level, logging.INFO))
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        timestamp=True,
        rename_fields={"levelname": "level", "asctime": "timestamp"},
    )
    handler.setFormatter(formatter)
    root.handlers = [handler]
    return logging.getLogger(__name__)

logger = setup_logging()

app = Flask(__name__)

# Configuration from environment variables
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Application start time for uptime calculation
START_TIME = datetime.now(timezone.utc)


def get_uptime():
    """Calculate application uptime."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    hour_str = "hour" if hours == 1 else "hours"
    minute_str = "minute" if minutes == 1 else "minutes"
    return {
        "seconds": seconds,
        "human": f"{hours} {hour_str}, {minutes} {minute_str}",
    }


def get_system_info():
    """Collect system information."""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.platform(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }


def get_service_info():
    """Return service metadata."""
    return {
        "name": "devops-info-service",
        "version": "1.0.0",
        "description": "DevOps course info service",
        "framework": "Flask",
    }


def get_request_info():
    """Extract request information."""
    return {
        "client_ip": request.remote_addr,
        "user_agent": request.headers.get("User-Agent", "Unknown"),
        "method": request.method,
        "path": request.path,
    }


def get_endpoints():
    """Return list of available endpoints."""
    return [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"},
    ]


@app.before_request
def before_request():
    """Log incoming request."""
    g.start_time = datetime.now(timezone.utc)
    logger.info(
        "Request started",
        extra={
            "method": request.method,
            "path": request.path,
            "client_ip": request.remote_addr,
        },
    )


@app.after_request
def after_request(response):
    """Log response status."""
    duration_ms = 0
    if hasattr(g, "start_time"):
        duration_ms = int((datetime.now(timezone.utc) - g.start_time).total_seconds() * 1000)
    logger.info(
        "Request completed",
        extra={
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "client_ip": request.remote_addr,
            "duration_ms": duration_ms,
        },
    )
    return response


@app.route("/")
def index():
    """Main endpoint - service and system information."""
    uptime = get_uptime()
    response = {
        "service": get_service_info(),
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "request": get_request_info(),
        "endpoints": get_endpoints(),
    }
    return jsonify(response)


@app.route("/health")
def health():
    """Health check endpoint for monitoring and Kubernetes probes."""
    uptime = get_uptime()
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": uptime["seconds"],
        }
    )


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    logger.warning(
        "Not found",
        extra={"path": request.path, "client_ip": request.remote_addr},
    )
    return (
        jsonify({"error": "Not Found", "message": "Endpoint does not exist"}),
        404,
    )


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(
        "Internal server error",
        extra={
            "error": str(error),
            "path": request.path,
            "client_ip": request.remote_addr,
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
    logger.info(
        "Starting DevOps Info Service",
        extra={"host": HOST, "port": PORT, "debug": DEBUG},
    )
    app.run(host=HOST, port=PORT, debug=DEBUG)
