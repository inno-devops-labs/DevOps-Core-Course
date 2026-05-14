import logging
import os
import platform
import socket
import tempfile
import threading
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, Gauge, generate_latest

app = Flask(__name__)

# Prometheus metrics
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds", "HTTP request duration", ["method", "endpoint"]
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress", "HTTP requests currently being processed"
)

# App-specific metrics
endpoint_calls = Counter("devops_info_endpoint_calls", "Endpoint calls", ["endpoint"])
system_info_duration = Histogram(
    "devops_info_system_collection_seconds", "System info collection time"
)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
START_TIME = datetime.now(timezone.utc)
SERVICE_NAME = "devops-info-service"
SERVICE_VERSION = "1.0.0"
SERVICE_DESCRIPTION = "DevOps course info service"
SERVICE_FRAMEWORK = "Flask"
VISITS_FILE_DEFAULT = "/data/visits"
_visits_lock = threading.Lock()


logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("devops-info-service")


def utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def get_uptime_seconds() -> int:
    return int((datetime.now(timezone.utc) - START_TIME).total_seconds())


def get_uptime_human(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    h = "hour" if hours == 1 else "hours"
    m = "minute" if minutes == 1 else "minutes"
    return f"{hours} {h}, {minutes} {m}"


def get_platform_version() -> str:
    if hasattr(platform, "freedesktop_os_release") and platform.system() == "Linux":
        try:
            info = platform.freedesktop_os_release()
            if info.get("PRETTY_NAME"):
                return info["PRETTY_NAME"]
        except OSError:
            pass
    return platform.release() or platform.version() or "unknown"


def get_client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    return forwarded or (request.remote_addr or "unknown")


def get_endpoints():
    return [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"},
        {"path": "/visits", "method": "GET", "description": "Current visits count"},
    ]


def get_visits_file_path() -> str:
    return os.getenv("VISITS_FILE", VISITS_FILE_DEFAULT)


def read_visits_count() -> int:
    visits_file = get_visits_file_path()
    try:
        with open(visits_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return int(content) if content else 0
    except FileNotFoundError:
        return 0
    except (ValueError, OSError):
        logger.warning("Could not read visits file: %s", visits_file)
        return 0


def write_visits_count(value: int) -> None:
    visits_file = get_visits_file_path()
    visits_dir = os.path.dirname(visits_file)
    if visits_dir:
        os.makedirs(visits_dir, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(prefix="visits-", dir=visits_dir or None)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            tmp.write(str(value))
        os.replace(temp_path, visits_file)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def increment_visits_count() -> int:
    with _visits_lock:
        new_value = read_visits_count() + 1
        write_visits_count(new_value)
        return new_value


def get_current_visits_count() -> int:
    with _visits_lock:
        return read_visits_count()


def initialize_visits_storage() -> None:
    visits_file = get_visits_file_path()
    visits_dir = os.path.dirname(visits_file)
    if visits_dir:
        os.makedirs(visits_dir, exist_ok=True)

    if not os.path.exists(visits_file):
        write_visits_count(0)


initialize_visits_storage()


@app.before_request
def log_request():
    logger.debug("Request: %s %s", request.method, request.path)
    # Track in-progress requests and timing for Prometheus
    http_requests_in_progress.inc()
    request.start_time = time.time()
    request._metrics_reported = False


@app.after_request
def instrument_request(response):
    # Record metrics for successful request paths
    _record_metrics(response.status_code)
    return response


@app.teardown_request
def teardown_request(exc):
    # Ensure metrics are recorded even if an exception occurs
    if not getattr(request, "_metrics_reported", False):
        status_code = 500 if exc else 200
        _record_metrics(status_code)


def _record_metrics(status_code: int):
    if getattr(request, "_metrics_reported", False):
        return

    http_requests_in_progress.dec()

    duration = time.time() - getattr(request, "start_time", time.time())
    http_request_duration_seconds.labels(
        method=request.method, endpoint=request.path
    ).observe(duration)
    http_requests_total.labels(
        method=request.method, endpoint=request.path, status=str(status_code)
    ).inc()
    request._metrics_reported = True


# routes
@app.get("/")
def index():
    endpoint_calls.labels(endpoint="/").inc()
    visits_count = increment_visits_count()
    start_time = time.time()
    uptime_seconds = get_uptime_seconds()
    payload = {
        "service": {
            "name": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "description": SERVICE_DESCRIPTION,
            "framework": SERVICE_FRAMEWORK,
        },
        "system": {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": get_platform_version(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count() or 0,
            "python_version": platform.python_version(),
        },
        "runtime": {
            "uptime_seconds": uptime_seconds,
            "uptime_human": get_uptime_human(uptime_seconds),
            "current_time": utc_now_iso(),
            "timezone": "UTC",
        },
        "request": {
            "client_ip": get_client_ip(),
            "user_agent": request.headers.get("User-Agent", ""),
            "method": request.method,
            "path": request.path,
        },
        "visits": visits_count,
        "endpoints": get_endpoints(),
    }
    system_info_duration.observe(time.time() - start_time)
    return jsonify(payload), 200


@app.get("/health")
def health():
    endpoint_calls.labels(endpoint="/health").inc()
    return (
        jsonify(
            {
                "status": "healthy",
                "timestamp": utc_now_iso(),
                "uptime_seconds": get_uptime_seconds(),
            }
        ),
        200,
    )


@app.get("/visits")
def visits():
    endpoint_calls.labels(endpoint="/visits").inc()
    return (
        jsonify(
            {
                "visits": get_current_visits_count(),
                "file": get_visits_file_path(),
                "timestamp": utc_now_iso(),
            }
        ),
        200,
    )


@app.get("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": "text/plain; charset=utf-8"}


# error handling
@app.errorhandler(404)
def not_found(_):
    return (
        jsonify({"error": "Not Found", "message": "Endpoint does not exist"}),
        404,
    )


@app.errorhandler(500)
def internal_error(_):
    logger.exception("Unhandled server error")
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
    logger.info("Starting %s on %s:%s (debug=%s)", SERVICE_NAME, HOST, PORT, DEBUG)
    app.run(host=HOST, port=PORT, debug=DEBUG)
