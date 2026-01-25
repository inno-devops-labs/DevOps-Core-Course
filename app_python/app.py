"""
DevOps Info Service
LAB01: Python Web Application (Flask)
"""
import os
import socket
import logging
import platform
from datetime import datetime, timezone
from flask import Flask, jsonify, request

# Logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("devops-info-service")

# Configuration (env)
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

SERVICE_NAME = os.getenv("SERVICE_NAME", "devops-info-service")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
SERVICE_DESCRIPTION = os.getenv("SERVICE_DESCRIPTION", "DevOps course info service")
SERVICE_FRAMEWORK = "Flask"

# App init
app = Flask(__name__)

START_TIME = datetime.now(timezone.utc)


# Helpers
def iso_utc_now() -> str:
    """Current time in UTC as ISO8601 with milliseconds and Z suffix."""
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _plural(n: int, one: str, many: str) -> str:
    return one if n == 1 else many


def get_uptime() -> dict:
    """Return uptime in seconds and human-readable format."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    human = f"{hours} {_plural(hours, 'hour', 'hours')}, {minutes} {_plural(minutes, 'minute', 'minutes')}"
    return {"seconds": seconds, "human": human}


def get_platform_version() -> str:
    """
    Try to return a friendly OS version string (e.g., Ubuntu 24.04).
    Falls back to platform.platform().
    """
    try:
        if hasattr(platform, "freedesktop_os_release"):
            data = platform.freedesktop_os_release()
            pretty = data.get("PRETTY_NAME")
            if pretty:
                return pretty
    except Exception:
        pass
    return platform.platform()


def get_system_info() -> dict:
    """Collect system information."""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": get_platform_version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 0,
        "python_version": platform.python_version(),
    }


def get_request_info() -> dict:
    """Collect request information."""
    # request.remote_addr gives client address (may be proxy without X-Forwarded-For)
    forwarded_for = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    client_ip = forwarded_for or request.remote_addr

    user_agent = request.headers.get("User-Agent", "")

    return {
        "client_ip": client_ip,
        "user_agent": user_agent,
        "method": request.method,
        "path": request.path,
    }


def get_endpoints() -> list:
    return [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"},
    ]


# Hooks
@app.before_request
def log_request():
    logger.info("%s %s from %s", request.method, request.path, request.remote_addr)


# Routes
@app.route("/", methods=["GET"])
def index():
    uptime = get_uptime()
    payload = {
        "service": {
            "name": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "description": SERVICE_DESCRIPTION,
            "framework": SERVICE_FRAMEWORK,
        },
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": iso_utc_now(),
            "timezone": "UTC",
        },
        "request": get_request_info(),
        "endpoints": get_endpoints(),
    }
    return jsonify(payload), 200


@app.route("/health", methods=["GET"])
def health():
    uptime = get_uptime()
    return (
        jsonify(
            {
                "status": "healthy",
                "timestamp": iso_utc_now(),
                "uptime_seconds": uptime["seconds"],
            }
        ),
        200,
    )


# Error handlers
@app.errorhandler(404)
def not_found(_error):
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
def internal_error(_error):
    logger.exception("Internal error")
    return (
        jsonify(
            {
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
            }
        ),
        500,
    )


# Entry point
if __name__ == "__main__":
    logger.info("Starting %s on %s:%s (debug=%s)", SERVICE_NAME, HOST, PORT, DEBUG)
    app.run(host=HOST, port=PORT, debug=DEBUG)
