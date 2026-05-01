"""
DevOps Info Service
Main application module
"""

import os
import socket
import platform
import logging
import time
import json
import tempfile
from threading import Lock
from datetime import datetime, timezone
from flask import Flask, Response, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from pythonjsonlogger import jsonlogger

# Flask app initialization
app = Flask(__name__)

# Configuration via environment variables
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.getenv("DATA_DIR", os.path.join(BASE_DIR, "data"))
VISITS_FILE = os.getenv("VISITS_FILE", os.path.join(DATA_DIR, "visits"))
CONFIG_FILE = os.getenv("CONFIG_FILE", os.path.join(BASE_DIR, "config", "config.json"))
VISITS_LOCK = Lock()

# Application startup time
START_TIME = datetime.now(timezone.utc)

# Prometheus metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests handled by the application",
    ["method", "endpoint", "status_code"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "Duration of HTTP requests in seconds",
    ["method", "endpoint", "status_code"],
)
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method", "endpoint"],
)
ENDPOINT_CALLS_TOTAL = Counter(
    "devops_info_endpoint_calls_total",
    "Total calls to application endpoints",
    ["endpoint"],
)
SYSTEM_INFO_COLLECTION_SECONDS = Histogram(
    "devops_info_system_info_collection_seconds",
    "Time spent collecting system information",
)

# Setting up logging
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    fmt='%(asctime)s %(levelname)s %(name)s %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S%z'
)
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)


def ensure_parent_directory(file_path):
    """Ensure the parent directory for a file exists."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)


def read_visits_count():
    """Read the visits counter from disk, defaulting to zero."""
    try:
        with open(VISITS_FILE, "r", encoding="utf-8") as visits_file:
            raw_value = visits_file.read().strip()
    except FileNotFoundError:
        return 0

    if not raw_value:
        return 0

    try:
        return int(raw_value)
    except ValueError:
        logger.warning("Invalid visits counter value, resetting to zero", extra={"file": VISITS_FILE})
        return 0


def write_visits_count(count):
    """Persist the visits counter using an atomic file replacement."""
    ensure_parent_directory(VISITS_FILE)

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=os.path.dirname(VISITS_FILE),
        delete=False,
    ) as temp_file:
        temp_file.write(str(count))
        temp_file.flush()
        os.fsync(temp_file.fileno())
        temp_path = temp_file.name

    os.replace(temp_path, VISITS_FILE)


def increment_visits_count():
    """Increment the visits counter in a thread-safe way."""
    with VISITS_LOCK:
        count = read_visits_count() + 1
        write_visits_count(count)
        return count


def load_app_config():
    """Load JSON configuration from disk if available."""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        logger.warning("Invalid JSON configuration file", extra={"file": CONFIG_FILE})
        return {}


def get_request_endpoint():
    """Return a normalized endpoint label with low cardinality."""
    if request.url_rule and request.url_rule.rule:
        return request.url_rule.rule
    if request.path == "/metrics":
        return "/metrics"
    return "unmatched"


@app.before_request
def log_request():
    endpoint = get_request_endpoint()
    g.request_start_time = time.perf_counter()
    g.metrics_endpoint = endpoint
    HTTP_REQUESTS_IN_PROGRESS.labels(
        method=request.method,
        endpoint=endpoint,
    ).inc()
    logger.info("Request received", extra={
        'method': request.method,
        'path': request.path,
        'ip': request.remote_addr
    })

@app.after_request
def log_response(response):
    endpoint = getattr(g, "metrics_endpoint", get_request_endpoint())
    HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=str(response.status_code),
    ).inc()
    duration = time.perf_counter() - getattr(g, "request_start_time", time.perf_counter())
    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=str(response.status_code),
    ).observe(duration)
    HTTP_REQUESTS_IN_PROGRESS.labels(
        method=request.method,
        endpoint=endpoint,
    ).dec()
    logger.info("Response sent", extra={
        'status': response.status_code,
        'method': request.method,
        'path': request.path
    })
    return response


def get_system_info():
    """Collecting information about the system.

    Returns:
        dict: System configuration
    """
    with SYSTEM_INFO_COLLECTION_SECONDS.time():
        return {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.release(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count() or 0,
            "python_version": platform.python_version(),
        }


def get_uptime():
    """Calculating the running time of the application.

    Returns:
        dict: Uptime in seconds and human-readable format
    """
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {"seconds": seconds, "human": f"{hours} hours, {minutes} minutes"}


@app.route("/")
def index():
    """The main endpoint - Information about the service and the system."""
    client_ip = request.remote_addr
    user_agent = request.headers.get("User-Agent", "Unknown")
    endpoint = get_request_endpoint()
    ENDPOINT_CALLS_TOTAL.labels(endpoint=endpoint).inc()
    uptime = get_uptime()
    system_info = get_system_info()
    visits_count = increment_visits_count()
    file_config = load_app_config()

    # Forming a response
    response = {
        "service": {
            "name": "devops-info-service",
            "version": "2.0.0",
            "description": "DevOps course info service",
            "framework": "Flask",
        },
        "system": system_info,
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
            "visits_count": visits_count,
        },
        "request": {
            "client_ip": client_ip,
            "user_agent": user_agent,
            "method": request.method,
            "path": request.path,
        },
        "configuration": {
            "file": file_config,
            "environment": {
                "APP_ENV": os.getenv("APP_ENV", "undefined"),
                "LOG_LEVEL": os.getenv("LOG_LEVEL", "undefined"),
                "FEATURE_GREETINGS": os.getenv("FEATURE_GREETINGS", "undefined"),
                "CONFIG_FILE": CONFIG_FILE,
                "DATA_DIR": DATA_DIR,
            },
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/visits", "method": "GET", "description": "Visit counter"},
            {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
        ],
    }
    return jsonify(response)


@app.route("/health")
def health():
    """Endpoint for health check."""
    ENDPOINT_CALLS_TOTAL.labels(endpoint=get_request_endpoint()).inc()
    response = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": get_uptime()["seconds"],
    }
    logger.debug(f"Health check: {response}")
    return jsonify(response), 200


@app.route("/visits")
def visits():
    """Return the current visits counter without incrementing it."""
    ENDPOINT_CALLS_TOTAL.labels(endpoint=get_request_endpoint()).inc()
    response = {
        "visits": read_visits_count(),
        "file": VISITS_FILE,
    }
    return jsonify(response), 200


@app.route("/metrics")
def metrics():
    """Expose Prometheus metrics for scraping."""
    ENDPOINT_CALLS_TOTAL.labels(endpoint=get_request_endpoint()).inc()
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.errorhandler(404)
def not_found(error):
    """Error handler 404."""
    logger.warning(f"404 Not Found: {request.path}")
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Error handler 500."""
    logger.error(f"500 Internal Server Error: {str(error)}")
    return (
        jsonify(
            {
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
            }
        ),
        500,
    )


if __name__ == "__main__":
    logger.info(f"Starting DevOps Info Service on {HOST}:{PORT} (debug={DEBUG})")
    app.run(host=HOST, port=PORT, debug=DEBUG)
