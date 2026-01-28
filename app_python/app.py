import os
import socket
import platform
import logging
from datetime import datetime, timezone
from flask import Flask, jsonify, request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

SERVICE_NAME = "devops-info-service"
SERVICE_VERSION = "1.0.0"
SERVICE_DESCRIPTION = "DevOps course info service"
SERVICE_FRAMEWORK = "Flask"

START_TIME = datetime.now(timezone.utc)


def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {"seconds": seconds, "human": f"{hours} hours, {minutes} minutes"}


def get_system_info():
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }


def get_service_info():
    return {
        "name": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "description": SERVICE_DESCRIPTION,
        "framework": SERVICE_FRAMEWORK,
    }


def get_runtime_info():
    uptime = get_uptime()
    return {
        "uptime_seconds": uptime["seconds"],
        "uptime_human": uptime["human"],
        "current_time": datetime.now(timezone.utc).isoformat(),
        "timezone": "UTC",
    }


def get_request_info(req):
    return {
        "client_ip": req.remote_addr,
        "user_agent": req.headers.get("User-Agent", "Unknown"),
        "method": req.method,
        "path": req.path,
    }


def get_endpoints():
    return [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"},
    ]


@app.route("/")
def index():
    logger.debug(f"Request: {request.method} {request.path}")
    response = {
        "service": get_service_info(),
        "system": get_system_info(),
        "runtime": get_runtime_info(),
        "request": get_request_info(request),
        "endpoints": get_endpoints(),
    }
    return jsonify(response)


@app.route("/health")
def health():
    logger.debug(f"Health check: {request.method} {request.path}")
    response = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": get_uptime()["seconds"],
    }
    return jsonify(response)


@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error: {request.path}")
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {str(error)}")
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
    logger.info("Application starting...")
    logger.info(f"Service: {SERVICE_NAME} v{SERVICE_VERSION}")
    logger.info(f"Listening on {HOST}:{PORT}")
    logger.info(f"Debug mode: {DEBUG}")
    app.run(host=HOST, port=PORT, debug=DEBUG)


#   ██████████████    ██████████      ██  ██    ██      ██████████████
#   ██          ██        ██████  ██  ████  ██████  ██  ██          ██
#   ██  ██████  ██  ██  ██  ██    ██        ██████      ██  ██████  ██
#   ██  ██████  ██  ████████      ██████    ██  ██      ██  ██████  ██
#   ██  ██████  ██  ████  ██  ██    ████  ██  ██        ██  ██████  ██
#   ██          ██  ████  ██    ██████  ██              ██          ██
#   ██████████████  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██████████████
#                   ██    ████  ██  ██    ██  ██  ████
#   ██  ██████████        ████  ██    ████████  ██      ██████████
#       ██  ██      ████    ████    ██  ██  ██    ████████    ██  ██
#       ██████  ██  ████  ██████████    ██    ██    ██    ██    ████
#     ██              ██      ██        ██  ██████          ██████
#     ██        ██    ██████    ████  ████████  ████████    ██████  ██
#       ██████    ████  ██            ██████    ████  ██  ██        ██
#     ██  ████  ██    ██        ████    ██  ██      ██    ████
#   ██  ██    ██    ██  ████    ██████        ████              ██████
#           ██████  ██        ██  ██████        ████  ██  ████      ██
#     ██████████      ██  ██        ████████████  ██████████  ██
#       ██  ██  ██        ██████████████    ██        ████        ██
#         ██  ██  ██████████████  ██    ████████    ██  ████  ████████
#   ██    ████  ██    ██    ████████      ██          ██    ██  ██
#   ██  ████████        ██████  ██████    ██  ██  ████    ██  ██    ██
#   ██  ████    ████  ██  ████    ██████      ██    ██        ████
#   ██  ████          ██    ████████    ██    ██████      ██  ██████
#   ██  ██  ██  ██  ██              ██████  ██      ██████████    ████
#                   ██  ████  ████  ██  ████  ████  ██      ██  ██  ██
#   ██████████████      ████████  ██  ████        ████  ██  ████
#   ██          ██  ██    ██        ██  ██  ██████  ██      ██  ██████
#   ██  ██████  ██  ████      ██  ██  ██████  ████  ██████████      ██
#   ██  ██████  ██  ██  ████    ██        ████    ██████  ██    ██████
#   ██  ██████  ██  ██████  ████████████    ██████      ██      ██
#   ██          ██                      ██  ██████    ████      ██
#   ██████████████  ████  ██████  ██  ██████  ████  ██    ██████  ██
