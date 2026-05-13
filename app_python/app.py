"""
DevOps Info Service
Main application module with JSON structured logging
"""

import json
import logging
import os
import platform
import socket
import sys
import threading
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

app = Flask(__name__)

# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
VISITS_FILE = os.getenv("VISITS_FILE", "/data/visits")
CONFIG_FILE = os.getenv("CONFIG_FILE", "/config/config.json")
SECRET_NAMES = ("LAB17_API_KEY", "LAB17_DEPLOYMENT_TOKEN")

# Application start time
START_TIME = datetime.now(timezone.utc)

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests processed by the Flask application",
    ["method", "endpoint", "status_code"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method", "endpoint"],
)
DEVOPS_INFO_ENDPOINT_CALLS_TOTAL = Counter(
    "devops_info_endpoint_calls_total",
    "Number of application endpoint calls",
    ["endpoint"],
)
DEVOPS_INFO_SYSTEM_COLLECTION_SECONDS = Histogram(
    "devops_info_system_collection_seconds",
    "Time spent collecting system information",
    buckets=(0.0005, 0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1),
)

visits_lock = threading.Lock()
config_lock = threading.Lock()
config_cache = {}
config_mtime = None


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "status"):
            log_data["status"] = record.status
        if hasattr(record, "client_ip"):
            log_data["client_ip"] = record.client_ip
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        return json.dumps(log_data)


def setup_logging():
    """Configure all loggers to use JSON formatter."""
    # Remove existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Create and configure JSON handler
    json_handler = logging.StreamHandler(sys.stdout)
    json_handler.setFormatter(JSONFormatter())
    json_handler.setLevel(logging.INFO)

    # Configure root logger
    logging.root.setLevel(logging.INFO)
    logging.root.addHandler(json_handler)

    # Configure werkzeug logger
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.setLevel(logging.INFO)
    werkzeug_logger.handlers = [json_handler]

    # Configure our app logger
    return logging.getLogger(__name__)


# Setup logging
logger = setup_logging()


def get_endpoint_label():
    """Return a normalized endpoint label for metrics."""
    if request.url_rule and request.url_rule.rule:
        return request.url_rule.rule
    return request.path or "unknown"


def should_track_metrics():
    """Exclude Prometheus scrapes from RED metrics to avoid self-observation noise."""
    return request.path != "/metrics"


def read_visits():
    """Read the persisted visits counter from disk."""
    try:
        with open(VISITS_FILE, encoding="utf-8") as counter_file:
            return int(counter_file.read().strip() or "0")
    except FileNotFoundError:
        return 0
    except ValueError:
        logger.warning("Visits file contains invalid data; resetting counter to 0")
        return 0


def write_visits(value):
    """Persist the visits counter using an atomic replace."""
    visits_dir = os.path.dirname(VISITS_FILE)
    if visits_dir:
        os.makedirs(visits_dir, exist_ok=True)

    temp_path = f"{VISITS_FILE}.tmp"
    with open(temp_path, "w", encoding="utf-8") as counter_file:
        counter_file.write(f"{value}\n")
    os.replace(temp_path, VISITS_FILE)


def increment_visits():
    """Increment and persist the visits counter."""
    with visits_lock:
        visits = read_visits() + 1
        write_visits(visits)
        return visits


def load_app_config():
    """Load ConfigMap-backed JSON config and refresh when the file changes."""
    global config_cache, config_mtime

    with config_lock:
        try:
            current_mtime = os.path.getmtime(CONFIG_FILE)
        except FileNotFoundError:
            config_cache = {
                "applicationName": "devops-info-service",
                "environment": os.getenv("APP_ENV", "local"),
                "features": {"visitsCounter": True, "configHotReload": True},
                "settings": {"source": "defaults"},
            }
            config_mtime = None
            return config_cache

        if config_mtime == current_mtime:
            return config_cache

        with open(CONFIG_FILE, encoding="utf-8") as config_file:
            config_cache = json.load(config_file)
        config_mtime = current_mtime
        logger.info("Reloaded application config from %s", CONFIG_FILE)
        return config_cache


@app.before_request
def log_request():
    """Log incoming requests."""
    request.start_time = datetime.now(timezone.utc)
    request.metrics_enabled = should_track_metrics()
    request.endpoint_label = get_endpoint_label()
    if request.metrics_enabled:
        HTTP_REQUESTS_IN_PROGRESS.labels(
            method=request.method,
            endpoint=request.endpoint_label,
        ).inc()


@app.after_request
def log_response(response):
    """Log response information."""
    duration_ms = (
        datetime.now(timezone.utc) - request.start_time
    ).total_seconds() * 1000
    endpoint_label = getattr(request, "endpoint_label", get_endpoint_label())

    if getattr(request, "metrics_enabled", False):
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            endpoint=endpoint_label,
            status_code=str(response.status_code),
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            endpoint=endpoint_label,
        ).observe(duration_ms / 1000)
        HTTP_REQUESTS_IN_PROGRESS.labels(
            method=request.method,
            endpoint=endpoint_label,
        ).dec()

    log_record = logger.makeRecord(
        logger.name, logging.INFO, "", 0, f"{request.method} {request.path}", (), None
    )
    log_record.method = request.method
    log_record.path = request.path
    log_record.status = response.status_code
    log_record.client_ip = request.remote_addr
    log_record.duration_ms = round(duration_ms, 2)
    json_handler = logging.root.handlers[0]
    json_handler.handle(log_record)

    return response


def get_uptime():
    """Calculate application uptime."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    human_parts = []
    if hours > 0:
        human_parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        human_parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds < 60:
        human_parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

    return {
        "seconds": seconds,
        "human": ", ".join(human_parts) if human_parts else "0 seconds",
    }


def get_system_info():
    """Collect system information."""
    with DEVOPS_INFO_SYSTEM_COLLECTION_SECONDS.time():
        return {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count() or 1,
            "python_version": platform.python_version(),
        }


def get_request_info():
    """Collect request information."""
    return {
        "client_ip": request.remote_addr,
        "user_agent": request.headers.get("User-Agent", "Unknown"),
        "method": request.method,
        "path": request.path,
    }


def get_secret_status():
    """Return presence metadata for configured secrets without exposing values."""
    return {
        secret_name: {
            "configured": bool(os.getenv(secret_name)),
            "value": "set" if os.getenv(secret_name) else "missing",
        }
        for secret_name in SECRET_NAMES
    }


@app.route("/")
def index():
    """Main endpoint - service and system information."""
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint="/").inc()
    visits = increment_visits()
    app_config = load_app_config()
    uptime = get_uptime()
    now = datetime.now(timezone.utc)

    response = {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "Flask",
        },
        "configuration": app_config,
        "visits": visits,
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": now.isoformat(),
            "timezone": "UTC",
        },
        "request": get_request_info(),
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/visits", "method": "GET", "description": "Current visit count"},
            {
                "path": "/config",
                "method": "GET",
                "description": "Current application config",
            },
            {
                "path": "/secrets",
                "method": "GET",
                "description": "Secret presence check",
            },
            {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
        ],
    }

    logger.info(f"Serving info request from {request.remote_addr}")
    return jsonify(response)


@app.route("/health")
def health():
    """Health check endpoint."""
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint="/health").inc()
    uptime = get_uptime()
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": uptime["seconds"],
        }
    )


@app.route("/visits")
def visits():
    """Return the current persisted visit count."""
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint="/visits").inc()
    with visits_lock:
        current_visits = read_visits()
    return jsonify({"visits": current_visits, "file": VISITS_FILE})


@app.route("/config")
def config():
    """Return the current application configuration."""
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint="/config").inc()
    return jsonify({"config": load_app_config(), "file": CONFIG_FILE})


@app.route("/secrets")
def secrets():
    """Return whether required Fly secrets are present without returning values."""
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint="/secrets").inc()
    return jsonify({"secrets": get_secret_status()})


@app.route("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    log_record = logger.makeRecord(
        logger.name, logging.WARNING, "", 0, f"Not Found: {request.path}", (), None
    )
    log_record.method = request.method
    log_record.path = request.path
    log_record.status = 404
    log_record.client_ip = request.remote_addr
    logging.root.handlers[0].handle(log_record)

    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify(
        {"error": "Internal Server Error", "message": "An unexpected error occurred"}
    ), 500


if __name__ == "__main__":
    logger.info(f"Starting DevOps Info Service on {HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG, use_reloader=False)
