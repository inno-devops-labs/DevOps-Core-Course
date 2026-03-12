import logging
import os
import platform
import socket
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, request, g
from pythonjsonlogger import jsonlogger

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

app = Flask(__name__)

START_TIME = datetime.now(timezone.utc)


def configure_logging():
    logger = logging.getLogger()
    logger.handlers.clear()
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


configure_logging()
logger = logging.getLogger("devops-info-service")


def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    human_parts = []
    if hours == 1:
        human_parts.append("1 hour")
    elif hours > 1:
        human_parts.append(f"{hours} hours")

    if minutes == 1:
        human_parts.append("1 minute")
    else:
        human_parts.append(f"{minutes} minutes")

    human = ", ".join(human_parts) if human_parts else "0 minutes"

    return {"seconds": seconds, "human": human}


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
        "name": "devops-info-service",
        "version": "1.0.0",
        "description": "DevOps course info service",
        "framework": "Flask",
    }


def get_request_info():
    return {
        "client_ip": request.headers.get("X-Forwarded-For", request.remote_addr),
        "user_agent": request.headers.get("User-Agent", "unknown"),
        "method": request.method,
        "path": request.path,
    }


def get_runtime_info():
    uptime = get_uptime()
    return {
        "uptime_seconds": uptime["seconds"],
        "uptime_human": uptime["human"],
        "current_time": datetime.now(timezone.utc).isoformat(),
        "timezone": "UTC",
    }


@app.before_request
def before_request_logging():
    g.start_time = time.time()


@app.after_request
def after_request_logging(response):
    duration_ms = round((time.time() - g.start_time) * 1000, 2)

    logger.info(
        "http_request",
        extra={
            "event": "http_request",
            "service": "devops-info-service",
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "client_ip": request.headers.get("X-Forwarded-For", request.remote_addr),
            "user_agent": request.headers.get("User-Agent", "unknown"),
            "duration_ms": duration_ms,
        },
    )
    return response


@app.route("/", methods=["GET"])
def index():
    response = {
        "service": get_service_info(),
        "system": get_system_info(),
        "runtime": get_runtime_info(),
        "request": get_request_info(),
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
        ],
    }
    return jsonify(response), 200


@app.route("/health", methods=["GET"])
def health():
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
def not_found(error):
    logger.warning(
        "not_found",
        extra={
            "event": "not_found",
            "path": request.path,
            "method": request.method,
            "client_ip": request.headers.get("X-Forwarded-For", request.remote_addr),
        },
    )
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
def internal_error(error):
    logger.exception(
        "internal_server_error",
        extra={
            "event": "internal_server_error",
            "path": request.path,
            "method": request.method,
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
        "service_start",
        extra={
            "event": "service_start",
            "host": HOST,
            "port": PORT,
            "debug": DEBUG,
            "service": "devops-info-service",
        },
    )
    app.run(host=HOST, port=PORT, debug=DEBUG)