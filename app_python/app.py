"""
DevOps Info Service
Main application module providing system information and health status.
"""
import os
import socket
import platform
import logging
from datetime import datetime, timezone
from flask import Flask, jsonify, request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

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


@app.route("/")
def index():
    """Main endpoint - service and system information."""
    client_ip = request.remote_addr
    logger.info(
        f"Request: {request.method} {request.path} from {client_ip}"
    )

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
    client_ip = request.remote_addr
    logger.debug(f"Health check from {client_ip}")

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
    logger.warning(f"404 Not Found: {request.path}")
    return (
        jsonify({"error": "Not Found", "message": "Endpoint does not exist"}),
        404,
    )


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    error_msg = str(error)
    logger.error(f"500 Internal Server Error: {error_msg}")
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
    logger.info(f"Starting DevOps Info Service on {HOST}:{PORT}")
    logger.info(f"Debug mode: {DEBUG}")
    app.run(host=HOST, port=PORT, debug=DEBUG)
