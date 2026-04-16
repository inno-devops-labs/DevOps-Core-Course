import os
import platform
import socket
import logging
import sys
import time
import json
from pathlib import Path
from datetime import datetime, timezone
from pythonjsonlogger import jsonlogger

from flask import Flask, jsonify, request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest

### Configuration

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

SERVICE_NAME = "devops-info-service"
SERVICE_VERSION = "1.0.0"
SERVICE_DESCRIPTION = "DevOps course info service"
FRAMEWORK = "Flask"

CONFIG_FILE_PATH = os.getenv("CONFIG_FILE_PATH", "/config/config.json")
DATA_DIR = os.getenv("DATA_DIR", "/data")
VISITS_FILE = Path(DATA_DIR) / "visits.txt"

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

### Prometeus metrics

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests in progress"
)

visits_total = Counter(
    "visits_total",
    "Total number of visits to the application"
)

def load_config_from_configmap():
    """Load configuration from ConfigMap mounted file"""
    default_config = {
        "app_name": "DevOps Info Service",
        "environment": "development",
        "features": {
            "visits_tracking": True,
            "metrics_enabled": True
        },
        "log_level": "INFO",
        "max_visits_display": 1000000,
        "welcome_message": "Welcome to DevOps Info Service!"
    }

    try:
        if os.path.exists(CONFIG_FILE_PATH):
            with open(CONFIG_FILE_PATH, "r") as f:
                config = json.load(f)
                default_config.update(config)
                logger.info("Configuration loaded from {CONFIG_FILE_PATH}")
        else:
            logger.warning(f"Config file {CONFIG_FILE_PATH} not found. Using default configuration.")
    except Exception as e:
        logger.error(f"Error loading config: {e}.")
    return default_config

APP_CONFIG = load_config_from_configmap()

log_level = getattr(logging, APP_CONFIG.get("log_level", "INFO"))
logger.setLevel(log_level)

def read_visits():
    """Read visit count from persistent file"""
    try:
        if VISITS_FILE.exists():
            with open(VISITS_FILE, "r") as f:
                content = f.read().strip()
                if content:
                    return int(content)
    except (ValueError, IOError, OSError) as e:
        logger.error(f"Error reading visits file: {e}")
    return 0

def write_visits(count):
    """Write visit count to persistent file"""
    try:
        VISITS_FILE.parent.mkdir(parents=True, exist_ok=True)

        temp_file = VISITS_FILE.with_suffix(".tmp")
        with open(VISITS_FILE, "w") as f:
            f.write(str(count))
        temp_file.rename(VISITS_FILE)

        logger.debug(f"Visits counter updated to {count}")

    except Exception as e:
        logger.error(f"Error writing visits file: {e}")

def increment_visits():
    """Increment visit counter and return new value"""
    if not APP_CONFIG.get("features", {}).get("visits_tracking", True):
        return 0
    
    current = read_visits()
    new_count = current + 1
    
    max_visits = APP_CONFIG.get("max_visits_display", 1000000)
    if new_count > max_visits:
        new_count = max_visits
    
    write_visits(new_count)
    
    visits_total.inc()
    
    return new_count

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

    visit_count = increment_visits()

    logger.info("Main endpoint accessed, visit #{visit_count}")

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
        "visits": {
            "total": visit_count,
            "message": APP_CONFIG.get("welcome_message", "")
        },
        "request": {
            "client_ip": request.remote_addr,
            "user_agent": request.headers.get("User-Agent"),
            "method": request.method,
            "path": request.path
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information with visit counter"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
            {"path": "/ready", "method": "GET", "description": "Readiness probe"},
            {"path": "/visits", "method": "GET", "description": "Get current visit count"},
            {"path": "/config", "method": "GET", "description": "Show current configuration"}
        ],
    }

    return jsonify(response)

@app.route("/visits", methods=["GET"])
def get_visits():
    """Endpoint to get current visit count without incrementing"""
    visit_count = read_visits()
    
    logger.info(f"Visits endpoint accessed, current count: {visit_count}")
    
    return jsonify({
        "total_visits": visit_count,
        "data_file": str(VISITS_FILE),
        "tracking_enabled": APP_CONFIG.get("features", {}).get("visits_tracking", True)
    })

@app.route("/config", methods=["GET"])
def show_config():
    """Endpoint to show current configuration"""
    safe_config = {
        "app_name": APP_CONFIG.get("app_name"),
        "environment": APP_CONFIG.get("environment"),
        "features": APP_CONFIG.get("features"),
        "log_level": APP_CONFIG.get("log_level"),
        "data_dir": DATA_DIR,
        "config_file": CONFIG_FILE_PATH
    }

    logger.info("Config endpoint accessed")
    return jsonify(safe_config)

@app.route("/health", methods=["GET"])
def health():
    uptime_seconds, _ = get_uptime()

    data_writable = False
    try:
        test_file = Path(DATA_DIR) / ".health_test"
        test_file.write_text("test")
        test_file.unlink()
        data_writable = True
    except Exception:
        pass

    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_seconds,
        "checks": {
            "config_loaded": CONFIG_FILE_PATH if os.path.exists(CONFIG_FILE_PATH) else "default",
            "data_writable": data_writable,
            "visits_file_exists": VISITS_FILE.exists()
        }
    })

@app.route("/metrics", methods=["GET"])
def metrics():
    return generate_latest(), 200, {"Content-Type": "text/plain"}

@app.route("/ready", methods=["GET"])
def readiness():
    is_ready = True
    ready_details = {
        "status": "ready" if is_ready else "not ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {
            "app": "running",
            "config": "loaded",
            "data_directory": "available" if os.path.exists(DATA_DIR) else "creating",
            "dependencies": {
                "database": "not_configured",
                "cache": "not_configured"
            }
        }
    }

    if not is_ready:
        return jsonify(ready_details), 503

    return jsonify(ready_details), 200


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
    request.start_time = time.time()

    http_requests_in_progress.inc()

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
    duration = time.time() - request.start_time

    http_requests_total.labels(
        method=request.method,
        endpoint=request.path,
        status=response.status_code
    ).inc()

    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.path
    ).observe(duration)

    http_requests_in_progress.dec()

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
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    
    logger.info(
        "Application started",
        extra={
            "method": "-",
            "path": "-",
            "status": "-",
            "client_ip": "-",
            "port": PORT,
            "config_file": CONFIG_FILE_PATH,
            "data_dir": DATA_DIR
        }
    )
    
    initial_visits = read_visits()
    logger.info(f"Initial visits count: {initial_visits}")
    
    app.run(host=HOST, port=PORT, debug=DEBUG)