import os
import platform
import socket
import logging
import sys
from datetime import datetime, timezone
from pythonjsonlogger import jsonlogger

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
logger = logging.getLogger()
logger.setLevel(logging.INFO)

logHandler = logging.StreamHandler(sys.stdout)

formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(message)s %(method)s %(path)s %(status)s %(client_ip)s"
)

logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

app = Flask(__name__)

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

@app.errorhandler(Exception)
def handle_error(e):
    logger.error(
        "Unhandled exception",
        extra={
            "method": request.method if request else "-",
            "path": request.path if request else "-",
            "status": 500,
            "client_ip": request.remote_addr if request else "-",
        },
        exc_info=True
    )
    return {"error": "internal server error"}, 500

### Logging middleware

@app.before_request
def log_request():
    logger.info(
        "Request received",
        extra={
            "method": request.method,
            "path": request.path,
            "client_ip": request.remote_addr,
        },
    )

@app.after_request
def log_response(response):
    logger.info(
        "Response sent",
        extra={
            "status": response.status_code,
            "path": request.path,
            "method": request.method,
            "client_ip": request.remote_addr,
        },
    )
    return response

### Entrypoint
if __name__ == "__main__":
    logger.info(
        "Application started",
        extra={
            "method": "-",
            "path": "-",
            "status": "-",
            "client_ip": "-",
            "port": PORT
        }
    )
    app.run(host=HOST, port=PORT, debug=DEBUG)