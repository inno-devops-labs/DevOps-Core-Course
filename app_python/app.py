import os
import socket
import platform
import logging
import json
import time
from datetime import datetime, timezone
from flask import Flask, g, jsonify, request

app = Flask(__name__)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

SERVICE_NAME = "devops-info-service"
SERVICE_VERSION = "1.0.0"
SERVICE_DESCRIPTION = "DevOps course info service"
SERVICE_FRAMEWORK = "Flask"

START_TIME = datetime.now(timezone.utc)


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in {
                "args",
                "asctime",
                "created",
                "exc_info",
                "exc_text",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "taskName",
                "thread",
                "threadName",
            }:
                continue
            payload[key] = value
        if record.exc_info is not None:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def configure_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    return logging.getLogger("devops-info-service")


logger = configure_logging()


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


def build_request_context(status_code=None):
    context = {
        "service": SERVICE_NAME,
        "client_ip": request.remote_addr,
        "method": request.method,
        "path": request.path,
        "user_agent": request.headers.get("User-Agent", "Unknown"),
    }
    if status_code is not None:
        context["status_code"] = status_code
    if hasattr(g, "request_started_at"):
        context["duration_ms"] = round((time.perf_counter() - g.request_started_at) * 1000, 2)
    return context


@app.before_request
def before_request():
    g.request_started_at = time.perf_counter()
    logger.info("request_started", extra=build_request_context())


@app.after_request
def after_request(response):
    context = build_request_context(response.status_code)
    if response.status_code >= 500:
        logger.error("request_finished", extra=context)
    elif response.status_code >= 400:
        logger.warning("request_finished", extra=context)
    else:
        logger.info("request_finished", extra=context)
    return response


@app.route("/")
def index():
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
    response = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": get_uptime()["seconds"],
    }
    return jsonify(response)


@app.errorhandler(404)
def not_found(error):
    logger.warning("endpoint_not_found", extra=build_request_context(404))
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.exception("internal_server_error", extra=build_request_context(500))
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
        "application_starting",
        extra={
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "host": HOST,
            "port": PORT,
            "debug": DEBUG,
        },
    )
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
