import os
import socket
import platform
import logging
import json
from datetime import datetime, timezone
from flask import Flask, jsonify, request


# JSON Formatter for structured logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "client_ip"):
            log_data["client_ip"] = record.client_ip
        if hasattr(record, "user_agent"):
            log_data["user_agent"] = record.user_agent
            
        return json.dumps(log_data)


# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

SERVICE_NAME = "devops-info-service"
SERVICE_VERSION = "1.1.0"
SERVICE_DESCRIPTION = "DevOps course info service"
FRAMEWORK = "Flask"
VISITS_FILE = os.getenv("VISITS_FILE", "/data/visits")


# App setup
app = Flask(__name__)
START_TIME = datetime.now(timezone.utc)


# Configure JSON logging
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)


# Also configure root logger for Flask
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers = []
root_logger.addHandler(handler)


logger.info("Application starting", extra={
    "service": SERVICE_NAME,
    "version": SERVICE_VERSION,
    "port": PORT
})


# Helper functions
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


# Request/Response logging middleware
@app.before_request
def log_request():
    logger.info("Incoming request", extra={
        "method": request.method,
        "path": request.path,
        "client_ip": request.remote_addr,
        "user_agent": request.headers.get("User-Agent", "Unknown")
    })


@app.after_request
def log_response(response):
    logger.info("Outgoing response", extra={
        "method": request.method,
        "path": request.path,
        "status_code": response.status_code,
        "client_ip": request.remote_addr
    })
    return response


# Routes
@app.route("/", methods=["GET"])
def index():
    uptime = get_uptime()

    response = {
        "service": {
            "name": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "description": SERVICE_DESCRIPTION,
            "framework": FRAMEWORK,
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
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/visits", "method": "GET", "description": "Visit counter (persistent)"},
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
    count = 0
    try:
        with open(VISITS_FILE, "r") as f:
            count = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        count = 0

    count += 1

    os.makedirs(os.path.dirname(VISITS_FILE), exist_ok=True)
    with open(VISITS_FILE, "w") as f:
        f.write(str(count))

    logger.info("Visit counted", extra={
        "visits": count,
        "pod": socket.gethostname(),
        "visits_file": VISITS_FILE,
    })

    return jsonify({
        "visits": count,
        "pod": socket.gethostname(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# Error Handlers
@app.errorhandler(404)
def not_found(error):
    logger.warning("404 Not Found", extra={
        "method": request.method,
        "path": request.path,
        "client_ip": request.remote_addr,
        "status_code": 404
    })

    return jsonify(
        {
            "error": "Not Found",
            "message": "Endpoint does not exist",
        }
    ), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error("500 Internal Server Error", extra={
        "method": request.method,
        "path": request.path,
        "client_ip": request.remote_addr,
        "status_code": 500,
        "error": str(error)
    })

    return jsonify(
        {
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        }
    ), 500


# Entry point
if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)
