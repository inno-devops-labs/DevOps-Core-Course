import os
import platform
import socket
import logging
import sys
import json
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from json import JSONEncoder

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

app = Flask(__name__)
START_TIME = datetime.now(timezone.utc)


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'timestamp': datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
            'function': record.funcName,
            'line': record.lineno
        }

        if hasattr(record, "method"):
            log_record["method"] = record.method
        if hasattr(record, "path"):
            log_record["path"] = record.path
        if hasattr(record, "status_code"):
            log_record["status_code"] = record.status_code
        if hasattr(record, "client_addr"):
            log_record["client_addr"] = record.client_addr
        if hasattr(record, "error"):
            log_record["error"] = record.error

        return json.dumps(log_record)
    
logger = logging.getLogger("devops-info-service")

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.info("DevOps Info Service starting...", extra={"method": "STARTUP", "path": f"{HOST}:{PORT}"})


@app.before_request
def log_request_info():
    logger.info(f"Incoming request: {request.method} {request.path} from {request.remote_addr}", extra={
        "method": request.method,
        "path": request.path,
        "client_addr": request.remote_addr,
    })


@app.after_request
def log_request_info(response):
    logger.info(f"Request completed: {request.method} {request.path} from {request.remote_addr}", extra={
        "method": request.method,
        "path": request.path,
        "client_addr": request.remote_addr,
        "status_code": response.status_code
    })
    return response


@app.route("/")
def index():
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
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/raise-error", "method": "GET", "description": "Endpoint that raises an error for testing"}
        ]
    }
    return jsonify(data)


@app.route("/health")
def health():
    cur_time = datetime.now(timezone.utc)
    uptime = cur_time - START_TIME
    return jsonify({
        "status": "healthy",
        "timestamp": cur_time.isoformat(),
        "uptime_seconds": uptime.total_seconds()
    }), 200


@app.route("/raise-error")
def raise_error():
    raise ValueError("This is a test error")


@app.errorhandler(404)
def not_found(error):
    logger.warning('Not found', extra={'path': request.path, 'client_addr': request.remote_addr})
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error('Internal server error', extra={'path': request.path, 'client_addr': request.remote_addr, 'error': str(error)})
    return jsonify({"error": "Internal Server Error", "message": "Unexpected error"}), 500


if __name__ == "__main__":
    logger.info(f"Running on http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG)
