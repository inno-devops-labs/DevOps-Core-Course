"""
DevOps Info Service - Flask implementation
Provides system and runtime information with health checks.
"""
from __future__ import annotations

import logging
import os
import platform
import socket
from datetime import datetime, timezone
from typing import Dict, List, Any

from flask import Flask, jsonify, request

APP_NAME = "devops-info-service"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "DevOps course info service"
FRAMEWORK = "Flask"

# Configuration via environment variables
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8080))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Track application start time for uptime calculations
START_TIME = datetime.now(timezone.utc)

app = Flask(__name__)


def setup_logging() -> None:
    """Configure basic application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.info("Application starting...")


def get_system_info() -> Dict[str, Any]:
    """Collect host system information."""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 0,
        "python_version": platform.python_version(),
    }


def get_uptime() -> Dict[str, Any]:
    """Calculate service uptime in seconds and human format."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return {
        "seconds": seconds,
        "human": f"{hours} hours, {minutes} minutes",
    }


def get_runtime_info() -> Dict[str, Any]:
    """Return runtime timing details."""
    now = datetime.now(timezone.utc)
    local_now = now.astimezone()
    uptime = get_uptime()
    return {
        "uptime_seconds": uptime["seconds"],
        "uptime_human": uptime["human"],
        "current_time": now.isoformat(),
        "timezone": local_now.tzname() or "UTC",
    }


def get_request_info() -> Dict[str, Any]:
    """Extract request metadata for observability."""
    forwarded_for = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    client_ip = forwarded_for or request.remote_addr or ""
    return {
        "client_ip": client_ip,
        "user_agent": request.headers.get("User-Agent", ""),
        "method": request.method,
        "path": request.path,
    }


def get_endpoints() -> List[Dict[str, str]]:
    """List known HTTP endpoints."""
    return [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"},
    ]


@app.before_request
def log_request() -> None:
    """Log incoming requests at INFO level."""
    logging.info("%s %s from %s", request.method, request.path, request.remote_addr)


@app.route("/", methods=["GET"])
def index() -> Any:
    """Main endpoint returning service, system, runtime, and request info."""
    response = {
        "service": {
            "name": APP_NAME,
            "version": APP_VERSION,
            "description": APP_DESCRIPTION,
            "framework": FRAMEWORK,
        },
        "system": get_system_info(),
        "runtime": get_runtime_info(),
        "request": get_request_info(),
        "endpoints": get_endpoints(),
    }
    return jsonify(response), 200


@app.route("/health", methods=["GET"])
def health() -> Any:
    """Lightweight health probe endpoint."""
    uptime = get_uptime()
    return (
        jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime_seconds": uptime["seconds"],
            }
        ),
        200,
    )


@app.errorhandler(404)
def not_found(error):  # type: ignore[override]
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(error):  # type: ignore[override]
    logging.exception("Unhandled exception: %s", error)
    return (
        jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred"}),
        500,
    )


def main() -> None:
    setup_logging()
    app.run(host=HOST, port=PORT, debug=DEBUG)


if __name__ == "__main__":
    main()
