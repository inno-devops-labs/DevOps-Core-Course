"""
DevOps Info Service
Main application module
"""

import os
import fcntl
import socket
import platform
import logging
from pathlib import Path
from time import perf_counter
from datetime import datetime, timezone
from flask import Flask, Response, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests processed by the application",
    ["method", "endpoint", "status_code"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status_code"],
)
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method", "endpoint"],
)
DEVOPS_INFO_ENDPOINT_CALLS_TOTAL = Counter(
    "devops_info_endpoint_calls_total",
    "Total application endpoint calls grouped by endpoint",
    ["endpoint"],
)
DEVOPS_INFO_SYSTEM_INFO_COLLECTION_SECONDS = Histogram(
    "devops_info_system_info_collection_seconds",
    "Time spent collecting system information",
)


# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))

# Application start time
START_TIME = datetime.now(timezone.utc)


def get_visits_file_path():
    return Path(os.getenv("VISITS_FILE", "/data/visits"))


def ensure_visits_parent_directory():
    get_visits_file_path().parent.mkdir(parents=True, exist_ok=True)


def parse_visits_count(raw_value):
    raw_value = raw_value.strip()
    if not raw_value:
        return 0

    try:
        return int(raw_value)
    except ValueError:
        logger.warning("invalid_visits_file_contents", extra={"raw_value": raw_value})
        return 0


def read_visits_count():
    visits_file_path = get_visits_file_path()
    ensure_visits_parent_directory()

    with visits_file_path.open("a+", encoding="utf-8") as visits_file:
        fcntl.flock(visits_file.fileno(), fcntl.LOCK_EX)
        try:
            visits_file.seek(0)
            return parse_visits_count(visits_file.read())
        finally:
            fcntl.flock(visits_file.fileno(), fcntl.LOCK_UN)


def increment_visits_count():
    visits_file_path = get_visits_file_path()
    ensure_visits_parent_directory()

    with visits_file_path.open("a+", encoding="utf-8") as visits_file:
        fcntl.flock(visits_file.fileno(), fcntl.LOCK_EX)
        try:
            visits_file.seek(0)
            current_count = parse_visits_count(visits_file.read())
            next_count = current_count + 1
            visits_file.seek(0)
            visits_file.truncate()
            visits_file.write(str(next_count))
            visits_file.flush()
            os.fsync(visits_file.fileno())
            return next_count
        finally:
            fcntl.flock(visits_file.fileno(), fcntl.LOCK_UN)


def normalize_endpoint():
    """Normalize endpoint labels to keep metric cardinality low."""
    if request.url_rule and request.url_rule.rule:
        return request.url_rule.rule
    if request.path == "/metrics":
        return "/metrics"
    return "unmatched"


@app.before_request
def before_request_metrics():
    endpoint = normalize_endpoint()
    g.metrics_endpoint = endpoint
    g.metrics_start_time = perf_counter()
    g.metrics_tracked = endpoint != "/metrics"
    g.metrics_gauge_decremented = False

    if g.metrics_tracked:
        HTTP_REQUESTS_IN_PROGRESS.labels(
            method=request.method, endpoint=endpoint
        ).inc()


@app.after_request
def after_request_metrics(response):
    if g.get("metrics_tracked", False):
        duration = perf_counter() - g.metrics_start_time
        status_code = str(response.status_code)
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            endpoint=g.metrics_endpoint,
            status_code=status_code,
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            endpoint=g.metrics_endpoint,
            status_code=status_code,
        ).observe(duration)
        HTTP_REQUESTS_IN_PROGRESS.labels(
            method=request.method, endpoint=g.metrics_endpoint
        ).dec()
        g.metrics_gauge_decremented = True

    return response


@app.teardown_request
def teardown_request_metrics(error):
    if g.get("metrics_tracked", False) and not g.get("metrics_gauge_decremented", False):
        HTTP_REQUESTS_IN_PROGRESS.labels(
            method=request.method, endpoint=g.metrics_endpoint
        ).dec()
        g.metrics_gauge_decremented = True


def get_system_info():
    """Collect system information."""
    start = perf_counter()
    try:
        return {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
        }
    finally:
        DEVOPS_INFO_SYSTEM_INFO_COLLECTION_SECONDS.observe(perf_counter() - start)


def get_request():
    return {
        "client_ip": request.remote_addr,  # Client IP
        "user_agent": request.headers.get("User-Agent"),  # User agent
        "method": request.method,  # HTTP method
        "path": request.path,  # Request path
    }


def get_service():
    service = {
        "name": "devops-info-service",
        "version": os.getenv("DEVOPS_SERVICE_VERSION", "1.0.0"),
        "description": "DevOps course info service",
        "framework": "Flask",
    }
    release_track = os.getenv("DEVOPS_RELEASE_TRACK")
    release_color = os.getenv("DEVOPS_RELEASE_COLOR")

    if release_track:
        service["release_track"] = release_track
    if release_color:
        service["release_color"] = release_color

    return service


@app.route("/")
def index():
    logger.debug(f"Request: {request.method} {request.path}")
    """Main endpoint - service and system information."""
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint="/").inc()
    visit_count = increment_visits_count()
    return {
        "service": get_service(),
        "system": get_system_info(),
        "request": get_request(),
        "runtime": get_uptime(),
        "visits": {
            "count": visit_count,
            "file": str(get_visits_file_path()),
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/visits", "method": "GET", "description": "Current visit count"},
            {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
        ],
    }


def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    now_utc = datetime.now(timezone.utc).isoformat()
    # Example output: '2026-01-28T19:10:00.123456+00:00'
    # Replace the +00:00 with Z
    iso_format_zulu = now_utc.replace("+00:00", ".000Z")
    return {
        "seconds": seconds,
        "human": f"{hours} hours, {minutes} minutes",
        "current_time": iso_format_zulu,
        "timezone": "UTC",
    }


@app.route("/health")
def health():
    logger.debug(f"Request: {request.method} {request.path}")
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint="/health").inc()
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": get_uptime()["seconds"],
        }
    )


@app.route("/visits")
def visits():
    logger.debug(f"Request: {request.method} {request.path}")
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint="/visits").inc()
    return jsonify(
        {
            "visits": read_visits_count(),
            "file": str(get_visits_file_path()),
        }
    )


@app.route("/metrics")
def metrics():
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint="/metrics").inc()
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(error):
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
    logger.info("application_starting", extra={"host": HOST, "port": PORT})
    app.run(host=HOST, port=PORT)
