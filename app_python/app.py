import os
import platform
import socket
import logging
from datetime import datetime, timezone
from flask import Flask, jsonify, request

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

app = Flask(__name__)
START_TIME = datetime.now(timezone.utc)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.info("DevOps Info Service starting...")

@app.route("/")
def index():
    logger.info(f"Request from {request.remote_addr}: {request.method} {request.path}")

    cur_time = datetime.now(timezone.utc)
    uptime = cur_time - START_TIME
    data = {
        "service": {
            "name": "devops-info-service",
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
            "python_version": platform.python_version(),
        },
        "runtime": {
            "uptime_seconds": uptime.total_seconds(),
            "uptime_human": f"{uptime.total_seconds() // 3600}h {uptime.total_seconds() % 3600 // 60}m",
            "current_time": cur_time.isoformat(),
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
    return jsonify(data)


@app.route("/health")
def health():
    logger.info(f"Request from {request.remote_addr}: {request.method} {request.path}")

    cur_time = datetime.now(timezone.utc)
    uptime = cur_time - START_TIME
    return jsonify({
        "status": "healthy",
        "timestamp": cur_time.isoformat(),
        "uptime_seconds": uptime.total_seconds()
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal Server Error", "message": "Unexpected error"}), 500

if __name__ == "__main__":
    logger.info(f"Running on http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG)
