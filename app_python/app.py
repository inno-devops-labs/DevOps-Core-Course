import logging
import os
import platform
import socket
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

APP_NAME = "devops-info-service"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "DevOps course info service"
FRAMEWORK = "Flask"

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

START_TIME = datetime.now(timezone.utc)
VISITS_LOCK = threading.Lock()

# Metrics (RED method + app-specific)
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
)

devops_info_endpoint_calls = Counter(
    "devops_info_endpoint_calls",
    "DevOps info service endpoint calls",
    ["endpoint"],
)

devops_info_system_collection_seconds = Histogram(
    "devops_info_system_collection_seconds",
    "Time to collect system info in seconds",
)


def iso_utc_z(dt: datetime) -> str:
    utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def get_uptime() -> dict:
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    hour_label = "hour" if hours == 1 else "hours"
    minute_label = "minute" if minutes == 1 else "minutes"
    return {
        "seconds": seconds,
        "human": f"{hours} {hour_label}, {minutes} {minute_label}",
    }


def get_client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def get_system_info() -> dict:
    start = time.perf_counter()
    try:
        return {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.platform(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count() or 0,
            "python_version": platform.python_version(),
        }
    finally:
        devops_info_system_collection_seconds.observe(time.perf_counter() - start)


def get_runtime_info() -> dict:
    uptime = get_uptime()
    now_utc = datetime.now(timezone.utc)
    return {
        "uptime_seconds": uptime["seconds"],
        "uptime_human": uptime["human"],
        "current_time": iso_utc_z(now_utc),
        "timezone": "UTC",
    }


def get_request_info() -> dict:
    return {
        "client_ip": get_client_ip(),
        "user_agent": request.headers.get("User-Agent", ""),
        "method": request.method,
        "path": request.path,
    }


def get_visits_file() -> Path:
    return Path(os.getenv("VISITS_FILE", "/data/visits"))


def read_visits_count() -> int:
    visits_file = get_visits_file()
    try:
        return int(visits_file.read_text(encoding="utf-8").strip())
    except FileNotFoundError:
        return 0
    except ValueError:
        return 0


def write_visits_count(value: int) -> None:
    visits_file = get_visits_file()
    visits_file.parent.mkdir(parents=True, exist_ok=True)
    visits_file.write_text(f"{value}\n", encoding="utf-8")


def increment_visits_count() -> int:
    with VISITS_LOCK:
        current = read_visits_count()
        updated = current + 1
        write_visits_count(updated)
        return updated


def get_endpoints() -> list[dict]:
    return [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/visits", "method": "GET", "description": "Current visits count"},
        {"path": "/health", "method": "GET", "description": "Health check"},
    ]


def create_app() -> Flask:
    app = Flask(__name__)

    logging.basicConfig(
        level=logging.DEBUG if DEBUG else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    @app.before_request
    def log_request() -> None:
        logger.debug("Request: %s %s", request.method, request.path)
        request._prom_start_time = time.perf_counter()  # type: ignore[attr-defined]
        http_requests_in_progress.inc()

    @app.after_request
    def record_metrics(response):
        try:
            endpoint = (
                request.url_rule.rule  # type: ignore[union-attr]
                if request.url_rule is not None
                else request.path
            )
            method = request.method
            status_code = str(response.status_code)
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
            ).inc()

            start = getattr(request, "_prom_start_time", None)
            if isinstance(start, (int, float)):
                http_request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint,
                ).observe(time.perf_counter() - start)
        finally:
            http_requests_in_progress.dec()
        return response

    @app.get("/")
    def index():
        devops_info_endpoint_calls.labels(endpoint="/").inc()
        increment_visits_count()
        payload = {
            "service": {
                "name": APP_NAME,
                "version": APP_VERSION,
                "description": APP_DESCRIPTION,
                "framework": FRAMEWORK,
            },
            "system": get_system_info(),
            "runtime": get_runtime_info(),
            "request": get_request_info(),
            "endpoints": get_endpoints(),
        }
        return jsonify(payload)

    @app.get("/visits")
    def visits():
        devops_info_endpoint_calls.labels(endpoint="/visits").inc()
        return jsonify({"visits": read_visits_count()})

    @app.get("/health")
    def health():
        devops_info_endpoint_calls.labels(endpoint="/health").inc()
        uptime = get_uptime()
        return jsonify(
            {
                "status": "healthy",
                "timestamp": iso_utc_z(datetime.now(timezone.utc)),
                "uptime_seconds": uptime["seconds"],
            }
        )

    @app.get("/boom")
    def boom():
        devops_info_endpoint_calls.labels(endpoint="/boom").inc()
        raise RuntimeError("Intentional error for monitoring demo")

    @app.get("/metrics")
    def metrics():
        devops_info_endpoint_calls.labels(endpoint="/metrics").inc()
        return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

    @app.errorhandler(404)
    def not_found(_error):
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
    def internal_error(_error):
        return (
            jsonify(
                {
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                }
            ),
            500,
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host=HOST, port=PORT, debug=DEBUG)
