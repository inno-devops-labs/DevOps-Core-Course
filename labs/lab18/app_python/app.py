import logging
import os
import platform
import socket
from datetime import datetime, timezone
from flask import Flask, jsonify, request

APP_NAME = "devops-info-service"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "DevOps course info service"
FRAMEWORK = "Flask"

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

START_TIME = datetime.now(timezone.utc)


def iso_utc_z(dt: datetime) -> str:
    utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def get_uptime() -> dict:
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    hour_label = "hour" if hours == 1 else "hours"
    minute_label = "minute" if minutes == 1 else "minutes"
    return {
        "seconds": seconds,
        "human": f"{hours} {hour_label}, {minutes} {minute_label}",
    }


def get_client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def get_system_info() -> dict:
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.platform(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 0,
        "python_version": platform.python_version(),
    }


def get_runtime_info() -> dict:
    uptime = get_uptime()
    now_utc = datetime.now(timezone.utc)
    return {
        "uptime_seconds": uptime["seconds"],
        "uptime_human": uptime["human"],
        "current_time": iso_utc_z(now_utc),
        "timezone": "UTC",
    }


def get_request_info() -> dict:
    return {
        "client_ip": get_client_ip(),
        "user_agent": request.headers.get("User-Agent", ""),
        "method": request.method,
        "path": request.path,
    }


def get_endpoints() -> list[dict]:
    return [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"},
    ]


def create_app() -> Flask:
    app = Flask(__name__)

    logging.basicConfig(
        level=logging.DEBUG if DEBUG else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    @app.before_request
    def log_request() -> None:
        logger.debug("Request: %s %s", request.method, request.path)

    @app.get("/")
    def index():
        payload = {
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
        return jsonify(payload)

    @app.get("/health")
    def health():
        uptime = get_uptime()
        return jsonify(
            {
                "status": "healthy",
                "timestamp": iso_utc_z(datetime.now(timezone.utc)),
                "uptime_seconds": uptime["seconds"],
            }
        )

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
        return (
            jsonify(
                {
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                }
            ),
            500,
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host=HOST, port=PORT, debug=DEBUG)
