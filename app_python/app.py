import logging
import os
import platform
import socket
from datetime import datetime, timezone

from flask import Flask, jsonify, request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("devops-info-service")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

app = Flask(__name__)
START_TIME = datetime.now(timezone.utc)


def _uptime_seconds() -> int:
    return int((datetime.now(timezone.utc) - START_TIME).total_seconds())


def _uptime_human(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours} hour(s), {minutes} minute(s)"


def get_system_info() -> dict:
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 0,
        "python_version": platform.python_version(),
    }


def get_request_info() -> dict:
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else request.remote_addr

    return {
        "client_ip": client_ip or "",
        "user_agent": request.headers.get("User-Agent", ""),
        "method": request.method,
        "path": request.path,
    }


def list_endpoints() -> list:
    return [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"},
    ]


@app.get("/")
def index():
    logger.info("Request: %s %s", request.method, request.path)

    uptime_sec = _uptime_seconds()
    payload = {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "Flask",
        },
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": uptime_sec,
            "uptime_human": _uptime_human(uptime_sec),
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "request": get_request_info(),
        "endpoints": list_endpoints(),
    }
    return jsonify(payload), 200


@app.get("/health")
def health():
    logger.info("Request: %s %s", request.method, request.path)

    return (
        jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime_seconds": _uptime_seconds(),
            }
        ),
        200,
    )

@app.errorhandler(404)
def not_found(_err):
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(_err):
    return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred"}), 500


if __name__ == "__main__":
    logger.info("Starting app on %s:%s (debug=%s)", HOST, PORT, DEBUG)
    app.run(host=HOST, port=PORT, debug=DEBUG)
