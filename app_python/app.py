"""
DevOps Info Service
Main application module with JSON structured logging
"""

import json
import logging
import os
import platform
import socket
import sys
from datetime import datetime, timezone

from flask import Flask, jsonify, request

app = Flask(__name__)

# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Application start time
START_TIME = datetime.now(timezone.utc)


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "status"):
            log_data["status"] = record.status
        if hasattr(record, "client_ip"):
            log_data["client_ip"] = record.client_ip
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        return json.dumps(log_data)


def setup_logging():
    """Configure all loggers to use JSON formatter."""
    # Remove existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Create and configure JSON handler
    json_handler = logging.StreamHandler(sys.stdout)
    json_handler.setFormatter(JSONFormatter())
    json_handler.setLevel(logging.INFO)

    # Configure root logger
    logging.root.setLevel(logging.INFO)
    logging.root.addHandler(json_handler)

    # Configure werkzeug logger
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.INFO)
    werkzeug_logger.handlers = [json_handler]

    # Configure our app logger
    return logging.getLogger(__name__)


# Setup logging
logger = setup_logging()


@app.before_request
def log_request():
    """Log incoming requests."""
    request.start_time = datetime.now(timezone.utc)


@app.after_request
def log_response(response):
    """Log response information."""
    duration_ms = (datetime.now(timezone.utc) - request.start_time).total_seconds() * 1000

    log_record = logger.makeRecord(
        logger.name,
        logging.INFO,
        "", 0,
        f"{request.method} {request.path}",
        (), None
    )
    log_record.method = request.method
    log_record.path = request.path
    log_record.status = response.status_code
    log_record.client_ip = request.remote_addr
    log_record.duration_ms = round(duration_ms, 2)
    json_handler = logging.root.handlers[0]
    json_handler.handle(log_record)

    return response


def get_uptime():
    """Calculate application uptime."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    human_parts = []
    if hours > 0:
        human_parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        human_parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds < 60:
        human_parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

    return {
        "seconds": seconds,
        "human": ", ".join(human_parts) if human_parts else "0 seconds",
    }


def get_system_info():
    """Collect system information."""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 1,
        "python_version": platform.python_version(),
    }


def get_request_info():
    """Collect request information."""
    return {
        "client_ip": request.remote_addr,
        "user_agent": request.headers.get("User-Agent", "Unknown"),
        "method": request.method,
        "path": request.path,
    }


@app.route("/")
def index():
    """Main endpoint - service and system information."""
    uptime = get_uptime()
    now = datetime.now(timezone.utc)

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
            "current_time": now.isoformat(),
            "timezone": "UTC",
        },
        "request": get_request_info(),
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
        ],
    }

    logger.info(f"Serving info request from {request.remote_addr}")
    return jsonify(response)


@app.route("/health")
def health():
    """Health check endpoint."""
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
    log_record = logger.makeRecord(
        logger.name,
        logging.WARNING,
        "", 0,
        f"Not Found: {request.path}",
        (), None
    )
    log_record.method = request.method
    log_record.path = request.path
    log_record.status = 404
    log_record.client_ip = request.remote_addr
    logging.root.handlers[0].handle(log_record)

    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify(
        {"error": "Internal Server Error", "message": "An unexpected error occurred"}
    ), 500


if __name__ == "__main__":
    logger.info(f"Starting DevOps Info Service on {HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG, use_reloader=False)
