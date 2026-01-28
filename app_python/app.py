import logging
import os
import platform
import socket
from datetime import datetime, timezone

from flask import Flask, jsonify, request

app = Flask(__name__)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
START_TIME = datetime.now(timezone.utc)
SERVICE_NAME = "devops-info-service"
SERVICE_VERSION = "1.0.0"
SERVICE_DESCRIPTION = "DevOps course info service"
SERVICE_FRAMEWORK = "Flask"


logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("devops-info-service")



def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def get_uptime_seconds() -> int:
    return int((datetime.now(timezone.utc) - START_TIME).total_seconds())


def get_uptime_human(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    h = "hour" if hours == 1 else "hours"
    m = "minute" if minutes == 1 else "minutes"
    return f"{hours} {h}, {minutes} {m}"


def get_platform_version() -> str:
    if hasattr(platform, "freedesktop_os_release") and platform.system() == "Linux":
        try:
            info = platform.freedesktop_os_release()
            if info.get("PRETTY_NAME"):
                return info["PRETTY_NAME"]
        except OSError:
            pass
    return platform.release() or platform.version() or "unknown"


def get_client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    return forwarded or (request.remote_addr or "unknown")


def get_endpoints():
    return [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"},
    ]


@app.before_request
def log_request():
    logger.debug("Request: %s %s", request.method, request.path)


# routes
@app.get("/")
def index():
    uptime_seconds = get_uptime_seconds()
    payload = {
        "service": {
            "name": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "description": SERVICE_DESCRIPTION,
            "framework": SERVICE_FRAMEWORK,
        },
        "system": {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": get_platform_version(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count() or 0,
            "python_version": platform.python_version(),
        },
        "runtime": {
            "uptime_seconds": uptime_seconds,
            "uptime_human": get_uptime_human(uptime_seconds),
            "current_time": utc_now_iso(),
            "timezone": "UTC",
        },
        "request": {
            "client_ip": get_client_ip(),
            "user_agent": request.headers.get("User-Agent", ""),
            "method": request.method,
            "path": request.path,
        },
        "endpoints": get_endpoints(),
    }
    return jsonify(payload), 200


@app.get("/health")
def health():
    return (
        jsonify(
            {
                "status": "healthy",
                "timestamp": utc_now_iso(),
                "uptime_seconds": get_uptime_seconds(),
            }
        ),
        200,
    )


# error handling
@app.errorhandler(404)
def not_found(_):
    return (
        jsonify({"error": "Not Found", "message": "Endpoint does not exist"}),
        404,
    )


@app.errorhandler(500)
def internal_error(_):
    logger.exception("Unhandled server error")
    return (
        jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred"}),
        500,
    )


if __name__ == "__main__":
    logger.info("Starting %s on %s:%s (debug=%s)", SERVICE_NAME, HOST, PORT, DEBUG)
    app.run(host=HOST, port=PORT, debug=DEBUG)