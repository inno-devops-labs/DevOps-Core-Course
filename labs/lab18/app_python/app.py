"""
DevOps Info Service
Main application module with Persistence and Vault support
"""
import os
import socket
import platform
import logging
import time
import threading
from datetime import datetime, timezone

from flask import Flask, jsonify, request, g
from pythonjsonlogger import jsonlogger
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8080)) # Изменено на 8080 для соответствия k8s
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

SERVICE_NAME = "devops-info-service"
SERVICE_VERSION = "1.0.0"
SERVICE_DESCRIPTION = "DevOps course info service"
FRAMEWORK = "Flask"

# App
app = Flask(__name__)

# Persistence settings
DATA_FILE = os.getenv("VISITS_FILE", "/data/visits")
VISITS_LOCK = threading.Lock()

# =====================
# PERSISTENCE HELPERS
# =====================
def read_visits():
    with VISITS_LOCK:
        if not os.path.exists(DATA_FILE):
            return 0
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return int(content) if content else 0
        except Exception as e:
            logger.error(f"Error reading visits: {e}")
            return 0

def write_visits(count):
    with VISITS_LOCK:
        try:
            os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
            tmp_file = f"{DATA_FILE}.tmp"
            with open(tmp_file, "w", encoding="utf-8") as f:
                f.write(str(count))
            os.replace(tmp_file, DATA_FILE)
        except Exception as e:
            logger.error(f"Error writing visits: {e}")

def increment_visits():
    with VISITS_LOCK:
        current = 0
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    current = int(content) if content else 0
        except Exception as e:
            logger.error(f"Error reading visits for increment: {e}")

        updated = current + 1
        try:
            os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
            tmp_file = f"{DATA_FILE}.tmp"
            with open(tmp_file, "w", encoding="utf-8") as f:
                f.write(str(updated))
            os.replace(tmp_file, DATA_FILE)
        except Exception as e:
            logger.error(f"Error writing visits for increment: {e}")
        return updated

# =====================
# PROMETHEUS METRICS
# =====================
http_requests_total = Counter(
    'http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status']
)
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint']
)
http_requests_in_progress = Gauge(
    'http_requests_in_progress', 'HTTP requests currently being processed'
)
endpoint_calls = Counter(
    'devops_info_endpoint_calls', 'Endpoint calls', ['endpoint']
)

# =====================
# LOGGING
# =====================
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(message)s %(method)s %(path)s %(status)s %(ip)s"
)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

START_TIME = datetime.now(timezone.utc)
write_visits(read_visits())

# =====================
# SYSTEM HELPERS
# =====================
def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    return {
        "seconds": seconds,
        "human": f"{seconds // 3600} hours, {(seconds % 3600) // 60} minutes",
    }

def get_system_info():
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }

# =====================
# MIDDLEWARE
# =====================
@app.before_request
def before_request():
    g.start_time = time.time()
    http_requests_in_progress.inc()

@app.after_request
def after_request(response):
    duration = time.time() - g.start_time
    http_requests_total.labels(
        method=request.method, endpoint=request.path, status=str(response.status_code)
    ).inc()
    http_request_duration_seconds.labels(
        method=request.method, endpoint=request.path
    ).observe(duration)
    http_requests_in_progress.dec()
    return response

# =====================
# ROUTES
# =====================

@app.route("/", methods=["GET"])
def index():
    endpoint_calls.labels(endpoint="/").inc()
    count = increment_visits()
    
    uptime = get_uptime()
    app_name = os.getenv("APP_NAME", "DevOps App")
    env = os.getenv("APP_ENV", "development")

    response = {
        "service": {
            "name": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "display_name": app_name,
            "env": env
        },
        "stats": {
            "total_visits": count,
            "storage_path": DATA_FILE
        },
        "system": get_system_info(),
        "runtime": uptime
    }
    return jsonify(response)

@app.route("/visits", methods=["GET"])
def visits():
    endpoint_calls.labels(endpoint="/visits").inc()
    return jsonify({"count": read_visits()})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "uptime": get_uptime()["seconds"]})

@app.route("/metrics", methods=["GET"])
def metrics():
    return generate_latest(), 200, {'Content-Type': 'text/plain'}

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404

if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)