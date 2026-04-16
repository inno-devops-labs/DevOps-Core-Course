"""
DevOps Info Service
Main application module
"""

import json
import logging
import os
import platform
import socket
import time
from threading import Lock
from datetime import datetime, timezone

from flask import Flask, jsonify, g, request

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

START_TIME = datetime.now(timezone.utc)


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key.startswith("_"):
                continue
            if key in {
                "name",
                "msg",
                "args",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "levelno",
                "levelname",
                "pathname",
                "filename",
                "module",
                "thread",
                "threadName",
                "processName",
                "process",
            }:
                continue
            if key not in log_record:
                log_record[key] = value

        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(log_record, default=str)


logger = logging.getLogger("devops-python")
logger.setLevel(logging.INFO)

_handler = logging.StreamHandler()
_handler.setFormatter(JSONFormatter())
logger.handlers.clear()
logger.addHandler(_handler)
logger.propagate = False

app = Flask(__name__)
VISITS_FILE = os.getenv("VISITS_FILE", "/data/visits")
_visits_lock = Lock()


def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        "seconds": seconds,
        "human": f"{hours} hours, {minutes} minutes",
    }


def get_system_info():
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }


def _ensure_visits_dir_exists() -> None:
    directory = os.path.dirname(VISITS_FILE)
    if directory:
        os.makedirs(directory, exist_ok=True)


def _read_visits_count() -> int:
    try:
        with open(VISITS_FILE, "r", encoding="utf-8") as visits_file:
            return int(visits_file.read().strip() or "0")
    except FileNotFoundError:
        return 0
    except ValueError:
        logger.warning(
            "invalid_visits_file_contents",
            extra={"event": "invalid_visits_file_contents", "path": VISITS_FILE},
        )
        return 0


def _write_visits_count(count: int) -> None:
    _ensure_visits_dir_exists()
    temp_path = f"{VISITS_FILE}.tmp"
    with open(temp_path, "w", encoding="utf-8") as visits_file:
        visits_file.write(str(count))
    os.replace(temp_path, VISITS_FILE)


def increment_visits_count() -> int:
    with _visits_lock:
        current_count = _read_visits_count()
        new_count = current_count + 1
        _write_visits_count(new_count)
        return new_count


def get_visits_count() -> int:
    with _visits_lock:
        return _read_visits_count()


@app.before_request
def log_request():
    g.request_start_time = time.perf_counter()
    logger.info(
        "request_started",
        extra={
            "event": "request_started",
            "method": request.method,
            "path": request.path,
            "remote_addr": request.remote_addr,
            "user_agent": request.headers.get("User-Agent"),
        },
    )


@app.after_request
def log_response(response):
    start_time = getattr(g, "request_start_time", None)
    duration_ms = None
    if start_time is not None:
        duration_ms = (time.perf_counter() - start_time) * 1000

    logger.info(
        "request_completed",
        extra={
            "event": "request_completed",
            "method": request.method,
            "path": request.path,
            "remote_addr": request.remote_addr,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )

    return response


@app.route("/", methods=["GET"])
def index():
    uptime = get_uptime()
    visits = increment_visits_count()

    response = {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "Flask",
        },
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "request": {
            "client_ip": request.remote_addr,
            "user_agent": request.headers.get("User-Agent"),
            "method": request.method,
            "path": request.path,
        },
        "visits": {"count": visits},
        "endpoints": [
            {
                "path": "/",
                "method": "GET",
                "description": "Service information"
            },
            {
                "path": "/health",
                "method": "GET",
                "description": "Health check"
            },
            {
                "path": "/visits",
                "method": "GET",
                "description": "Visit counter"
            },
        ],
    }

    return jsonify(response)


@app.route("/health", methods=["GET"])
def health():
    uptime = get_uptime()

    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": uptime["seconds"],
        }
    )


@app.route("/visits", methods=["GET"])
def visits():
    return jsonify({"visits": get_visits_count()})


@app.errorhandler(404)
def not_found(error):
    logger.warning(
        "not_found",
        extra={
            "event": "error_404",
            "method": request.method,
            "path": request.path,
        },
    )
    return jsonify(
        {
            "error": "Not Found",
            "message": "Endpoint does not exist",
        }
    ), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(
        "internal_server_error",
        extra={
            "event": "error_500",
            "method": request.method,
            "path": request.path,
        },
        exc_info=error,
    )
    return jsonify(
        {
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        }
    ), 500


if __name__ == "__main__":
    _ensure_visits_dir_exists()
    if not os.path.exists(VISITS_FILE):
        _write_visits_count(0)
    logger.info(
        "Starting DevOps Info Service",
        extra={
            "event": "startup",
            "host": HOST,
            "port": PORT,
            "debug": DEBUG,
            "visits_file": VISITS_FILE,
        },
    )
    app.run(host=HOST, port=PORT, debug=DEBUG)
