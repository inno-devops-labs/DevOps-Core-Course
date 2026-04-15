import logging
import os
import platform
import socket
import time
from pathlib import Path
from threading import Lock
from datetime import datetime, timezone

from flask import Flask, Response, jsonify, request, g
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from pythonjsonlogger import jsonlogger

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
VISITS_FILE = Path(os.getenv("VISITS_FILE", "/data/visits"))

app = Flask(__name__)

START_TIME = datetime.now(timezone.utc)

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests processed",
    ["method", "endpoint", "status_code"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
)
DEVOPS_INFO_ENDPOINT_CALLS = Counter(
    "devops_info_endpoint_calls_total",
    "Number of endpoint calls in the DevOps info service",
    ["endpoint"],
)
DEVOPS_INFO_SYSTEM_COLLECTION_SECONDS = Histogram(
    "devops_info_system_collection_seconds",
    "Time spent collecting system information",
    buckets=(0.0005, 0.001, 0.0025, 0.005, 0.01, 0.025, 0.05),
)
APP_INFO = Gauge(
    "devops_info_app_info",
    "Static metadata about the application",
    ["name", "version", "framework"],
)
APP_INFO.labels(name="devops-info-service", version="1.0.0", framework="Flask").set(1)


def configure_logging():
    logger = logging.getLogger()
    logger.handlers.clear()
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


configure_logging()
logger = logging.getLogger("devops-info-service")


class VisitCounter:
    def __init__(self, path: Path):
        self.path = path
        self._lock = Lock()
        self._count = self._load_count()

    def _load_count(self) -> int:
        try:
            return int(self.path.read_text(encoding="utf-8").strip() or "0")
        except FileNotFoundError:
            return 0
        except ValueError:
            logger.warning(
                "invalid_visits_counter",
                extra={
                    "event": "invalid_visits_counter",
                    "path": str(self.path),
                },
            )
            return 0

    def _write_count(self, count: int) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(".tmp")
        temp_path.write_text(f"{count}\n", encoding="utf-8")
        os.replace(temp_path, self.path)

    def increment(self) -> int:
        with self._lock:
            self._count += 1
            self._write_count(self._count)
            return self._count

    def get(self) -> int:
        with self._lock:
            return self._count


visit_counter = VisitCounter(VISITS_FILE)


def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    human_parts = []
    if hours == 1:
        human_parts.append("1 hour")
    elif hours > 1:
        human_parts.append(f"{hours} hours")

    if minutes == 1:
        human_parts.append("1 minute")
    else:
        human_parts.append(f"{minutes} minutes")

    human = ", ".join(human_parts) if human_parts else "0 minutes"

    return {"seconds": seconds, "human": human}


def get_system_info():
    start = time.perf_counter()
    try:
        return {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
            "python_version": platform.python_version(),
        }
    finally:
        DEVOPS_INFO_SYSTEM_COLLECTION_SECONDS.observe(time.perf_counter() - start)


def get_service_info():
    return {
        "name": "devops-info-service",
        "version": "1.0.0",
        "description": "DevOps course info service",
        "framework": "Flask",
        "visits_file": str(VISITS_FILE),
    }


def get_request_info():
    return {
        "client_ip": request.headers.get("X-Forwarded-For", request.remote_addr),
        "user_agent": request.headers.get("User-Agent", "unknown"),
        "method": request.method,
        "path": request.path,
    }


def get_runtime_info():
    uptime = get_uptime()
    return {
        "uptime_seconds": uptime["seconds"],
        "uptime_human": uptime["human"],
        "current_time": datetime.now(timezone.utc).isoformat(),
        "timezone": "UTC",
    }


def normalize_endpoint() -> str:
    if request.path == "/metrics":
        return "/metrics"
    if request.url_rule and request.url_rule.rule:
        return request.url_rule.rule
    if request.path.startswith("/health"):
        return "/health"
    return request.path or "unknown"


@app.before_request
def before_request_logging():
    g.start_time = time.perf_counter()
    HTTP_REQUESTS_IN_PROGRESS.inc()


@app.after_request
def after_request_logging(response):
    duration_seconds = max(time.perf_counter() - getattr(g, "start_time", time.perf_counter()), 0)
    duration_ms = round(duration_seconds * 1000, 2)
    endpoint = normalize_endpoint()

    HTTP_REQUEST_DURATION_SECONDS.labels(request.method, endpoint).observe(duration_seconds)
    HTTP_REQUESTS_TOTAL.labels(request.method, endpoint, str(response.status_code)).inc()
    HTTP_REQUESTS_IN_PROGRESS.dec()

    logger.info(
        "http_request",
        extra={
            "event": "http_request",
            "service": "devops-info-service",
            "method": request.method,
            "path": request.path,
            "endpoint": endpoint,
            "status_code": response.status_code,
            "client_ip": request.headers.get("X-Forwarded-For", request.remote_addr),
            "user_agent": request.headers.get("User-Agent", "unknown"),
            "duration_ms": duration_ms,
        },
    )
    return response


@app.teardown_request
def teardown_request_metrics(exception):
    if exception is not None:
        try:
            HTTP_REQUESTS_IN_PROGRESS.dec()
        except ValueError:
            pass


@app.route("/", methods=["GET"])
def index():
    DEVOPS_INFO_ENDPOINT_CALLS.labels(endpoint="/").inc()
    current_visits = visit_counter.increment()
    response = {
        "service": get_service_info(),
        "system": get_system_info(),
        "runtime": get_runtime_info(),
        "request": get_request_info(),
        "visits": current_visits,
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/visits", "method": "GET", "description": "Current visit count"},
            {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
        ],
    }
    return jsonify(response), 200


@app.route("/health", methods=["GET"])
def health():
    DEVOPS_INFO_ENDPOINT_CALLS.labels(endpoint="/health").inc()
    uptime = get_uptime()
    return (
        jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime_seconds": uptime["seconds"],
            }
        ),
        200,
    )


@app.route("/visits", methods=["GET"])
def visits():
    DEVOPS_INFO_ENDPOINT_CALLS.labels(endpoint="/visits").inc()
    return jsonify({"visits": visit_counter.get(), "visits_file": str(VISITS_FILE)}), 200


@app.route("/metrics", methods=["GET"])
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.errorhandler(404)
def not_found(error):
    logger.warning(
        "not_found",
        extra={
            "event": "not_found",
            "path": request.path,
            "method": request.method,
            "client_ip": request.headers.get("X-Forwarded-For", request.remote_addr),
        },
    )
    return (
        jsonify(
            {
                "error": "Not Found",
                "message": "Endpoint does not exist",
            }
        ),
        404,
    )


@app.errorhandler(500)
def internal_error(error):
    logger.exception(
        "internal_server_error",
        extra={
            "event": "internal_server_error",
            "path": request.path,
            "method": request.method,
        },
    )
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
    logger.info(
        "service_start",
        extra={
            "event": "service_start",
            "host": HOST,
            "port": PORT,
            "debug": DEBUG,
            "service": "devops-info-service",
        },
    )
    app.run(host=HOST, port=PORT, debug=DEBUG)
