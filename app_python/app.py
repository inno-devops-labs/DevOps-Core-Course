"""
DevOps Info Service
Main application module
"""
import os
import platform
import socket
import time
import logging
from datetime import datetime, timezone
from flask import Flask, jsonify, request

# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Application start time
app = Flask(__name__)
start_time = time.time()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Helpers
def get_uptime():
    uptime_seconds = int(time.time() - start_time)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    return uptime_seconds, f"{hours} hour(s), {minutes} minute(s)"

# Routes
@app.route("/", methods=["GET"])
def main_info():
    """Main endpoint - service and system information."""
    # Implementation
    uptime_seconds, uptime_human = get_uptime()

    response = {
        "service": {
            "name": "info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "Flask"
        },
        "system": {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
            "python_version": platform.python_version()
        },
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
        ]
    }

    logging.info("Main endpoint accessed")
    return jsonify(response)


@app.route("/health", methods=["GET"])
def health_check():
    """Health endpoint - available server information."""
    # Implementation
    uptime_seconds, _ = get_uptime()

    response = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_seconds
    }

    logging.info("Health check accessed")
    return jsonify(response), 200

# Run
if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)
