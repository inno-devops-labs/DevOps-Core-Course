from __future__ import annotations
import os
import socket
import platform
import logging
from datetime import datetime, timezone
from typing import Dict

from flask import Flask, request, jsonify

app = Flask(__name__)


# take parameters from environment variables with defaults
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"


# logger configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  
)

logger = logging.getLogger("devops-info-service")
logger.info("Starting devops-info-service")

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
    logger.info(f"Received request from {request.remote_addr}. Method: {request.method}, Path: {request.path}")
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
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": get_uptime()["seconds"],
        }
    ), 200

# error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.exception("Internal server error")
    return (
        jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred"}),
        500,
    )

if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)