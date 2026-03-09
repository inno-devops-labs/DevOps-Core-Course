from __future__ import annotations
import os
import socket
import platform
import logging
import time
from datetime import datetime, timezone
from typing import Dict

from flask import Flask, request, jsonify, g
from pythonjsonlogger import jsonlogger

app = Flask(__name__)


# take parameters from environment variables with defaults
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"


# ── JSON logger configuration ──────────────────────────────────────────────
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Extend the default JsonFormatter with fixed extra fields."""

    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = datetime.now(timezone.utc).isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        # drop duplicate/verbose keys added by the base class
        log_record.pop("color_message", None)


handler = logging.StreamHandler()
handler.setFormatter(
    CustomJsonFormatter(
        fmt="%(timestamp)s %(level)s %(logger)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
)

logging.root.setLevel(logging.INFO)
logging.root.handlers = [handler]

logger = logging.getLogger("devops-info-service")

# ── Request / response lifecycle hooks ─────────────────────────────────────
@app.before_request
def _before() -> None:
    g.start_ts = time.monotonic()


@app.after_request
def _after(response):  # type: ignore[return]
    duration_ms = round((time.monotonic() - g.start_ts) * 1000, 2)
    xff = request.headers.get("X-Forwarded-For")
    client_ip = xff.split(",")[0].strip() if xff else request.remote_addr
    logger.info(
        "HTTP request",
        extra={
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "client_ip": client_ip,
            "user_agent": request.headers.get("User-Agent", ""),
            "duration_ms": duration_ms,
        },
    )
    return response


logger.info("Starting devops-info-service", extra={"host": HOST, "port": PORT, "debug": DEBUG})

# additional startup info for diagnostics
logger.debug("Environment variables", extra={"HOST": HOST, "PORT": PORT, "DEBUG": DEBUG, "PATH": os.getenv("PATH")})

# save service start time
START_TIME = datetime.now(timezone.utc)

# utility functions
def get_system_info() -> Dict[str, object]:
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 1,
        "python_version": platform.python_version(),
    }

def get_uptime() -> Dict[str, object]:
    delta = datetime.now(timezone.utc) - START_TIME
    sec = int(delta.total_seconds())
    hours = sec // 3600
    minutes = (sec % 3600) // 60
    return {
        "seconds": sec,
        "human": f"{hours} hours, {minutes} minutes",
    }

def get_request_info() -> Dict[str, object]:
    xff = request.headers.get("X-Forwarded-For")
    client_ip = xff.split(",")[0].strip() if xff else request.remote_addr
    return {
        "client_ip": client_ip,
        "user_agent": request.headers.get("User-Agent"),
        "method": request.method,
        "path": request.path,
    }

# main endpoints for getting service info
@app.route("/", methods=["GET"])
def index():
    logger.info("Handling index request", extra={"path": request.path, "method": request.method})
    payload = {
        "service": {
            "name" : "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service"
        },
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": get_uptime()["seconds"],
            "uptime_human": get_uptime()["human"],
            "current-time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "request": get_request_info(),
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
        ],
    }
    return jsonify(payload)

# health check endpoint
@app.route("/health", methods=["GET"])
def health():
    logger.info("Health check requested")
    response = jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": get_uptime()["seconds"],
        }
    )
    logger.debug("Health response", extra={"uptime": get_uptime()})
    return response, 200

# error handlers
@app.errorhandler(404)
def not_found(_error):
    logger.warning("Not found", extra={"path": request.path, "method": request.method})
    logger.debug("Request headers", extra={"headers": dict(request.headers)})
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(_error):
    logger.exception("Internal server error", extra={"path": request.path, "method": request.method})
    logger.debug("Exception detail", extra={"error": str(_error)})   
    return (
        jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred"}),
        500,
    )

if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)