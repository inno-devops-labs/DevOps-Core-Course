import os
import platform
import socket
import logging
from datetime import datetime, timezone

from flask import Flask, jsonify, request

### Configuration

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

SERVICE_NAME = "devops-info-service"
SERVICE_VERSION = "1.0.0"
SERVICE_DESCRIPTION = "DevOps course info service"
FRAMEWORK = "Flask"

### App and logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

START_TIME = datetime.now(timezone.utc)

### Helper functions

def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    minutes = (seconds % 3600) // 60
    hours = seconds // 3600
    return seconds, f"{hours} hours, {minutes} minutes"

def get_system_info():
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform-version": platform.version(),
        "architecture": platform.machine(),
        "cpu-count": os.cpu_count(),
        "python-version": platform.python_version(),
    }

### Routes

@app.route("/", methods=["GET"])
def index():
    uptime_seconds, uptime_human = get_uptime()

    logger.info("Main endpoint accessed")

    response = {
        "service": {
            "name": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "description": SERVICE_DESCRIPTION,
            "framework": FRAMEWORK
        },
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": uptime_seconds,
            "uptime_human": uptime_human,
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC"
        },
        "request": {
            "client_ip": request.remote_addr,
            "user_agent": request.headers.get("User-Agent"),
            "method": request.method,
            "path": request.path
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"}
        ],
    }

    return jsonify(response)

@app.route("/health", methods=["GET"])
def health():
    uptime_seconds, _ = get_uptime()

    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_seconds,
    })

### Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist."}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred."}), 500

### Entrypoint
if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)