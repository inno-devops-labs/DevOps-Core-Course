"""DevOps Info Service - A Flask web application for Lab 01."""

import fcntl
import json
import logging
import os
import platform
import socket
import tempfile
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, request

app = Flask(__name__)

START_TIME = time.time()

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 5000))
DEBUG = os.environ.get("DEBUG", "false").lower() in ("true", "1", "yes")

VISITS_FILE = os.environ.get(
    "VISITS_FILE",
    os.path.join(tempfile.gettempdir(), "devops_visits"),
)


def _read_visits() -> int:
    try:
        with open(VISITS_FILE) as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def _increment_visits() -> int:
    os.makedirs(os.path.dirname(VISITS_FILE), exist_ok=True)
    with open(VISITS_FILE, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        try:
            count = int(f.read().strip())
        except ValueError:
            count = 0
        count += 1
        f.seek(0)
        f.truncate()
        f.write(str(count))
        fcntl.flock(f, fcntl.LOCK_UN)
    return count


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured logging."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.handlers = [handler]
logging.root.setLevel(logging.DEBUG if DEBUG else logging.INFO)
logger = logging.getLogger(__name__)


@app.before_request
def log_request():
    """Log incoming HTTP request."""
    logger.info("Incoming request: %s %s from %s",
                request.method, request.path, request.remote_addr)


@app.after_request
def log_response(response):
    """Log HTTP response."""
    logger.info("Response: %s %s -> %d",
                request.method, request.path, response.status_code)
    return response


@app.route("/")
def index():
    """Return comprehensive service metadata and system information."""
    logger.info("GET / requested from %s", request.remote_addr)

    uptime_seconds = time.time() - START_TIME
    current_time = datetime.now(timezone.utc).isoformat()

    response = {
        "service": {
            "name": "DevOps Info Service",
            "version": "1.0.0",
            "description": "A web service providing system and runtime information",
        },
        "system": {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
        },
        "runtime": {
            "python_version": platform.python_version(),
            "uptime_seconds": round(uptime_seconds, 2),
            "current_time": current_time,
            "timezone": "UTC",
        },
        "request": {
            "client_ip": request.remote_addr,
            "user_agent": request.headers.get("User-Agent", ""),
            "method": request.method,
            "path": request.path,
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service info and metadata"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/visits", "method": "GET", "description": "Visit counter"},
        ],
        "visits": _increment_visits(),
    }

    return jsonify(response)


@app.route("/visits")
def visits():
    """Return the current visit count."""
    return jsonify({"visits": _read_visits()}), 200


@app.route("/health")
def health():
    """Return health status of the service."""
    logger.info("GET /health requested from %s", request.remote_addr)

    uptime_seconds = time.time() - START_TIME
    current_time = datetime.now(timezone.utc).isoformat()

    return jsonify({
        "status": "healthy",
        "timestamp": current_time,
        "uptime_seconds": round(uptime_seconds, 2),
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    logger.warning("404 Not Found: %s %s", request.method, request.path)
    return jsonify({"error": "Not Found", "path": request.path}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error("500 Internal Server Error: %s", error)
    return jsonify({"error": "Internal Server Error"}), 500


if __name__ == "__main__":
    logger.info("Starting DevOps Info Service on %s:%d (debug=%s)", HOST, PORT, DEBUG)
    app.run(host=HOST, port=PORT, debug=DEBUG)
