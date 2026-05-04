import logging
import os
import platform
import socket
import time
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, Response, g, jsonify, request
from prometheus_client import Counter, Gauge, Histogram, generate_latest

DATA_DIR = Path(os.getenv("DATA_DIR", str(Path(__file__).resolve().parent / "data")))
DATA_FILE = DATA_DIR / "visits"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("devops-info-service")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

app = Flask(__name__)
START_TIME = datetime.now(timezone.utc)

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
    "Endpoint calls for devops info service",
    ["endpoint"],
)

devops_info_system_collection_seconds = Histogram(
    "devops_info_system_collection_seconds",
    "System info collection time in seconds",
)


def _uptime_seconds() -> int:
    return int((datetime.now(timezone.utc) - START_TIME).total_seconds())


def _uptime_human(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours} hour(s), {minutes} minute(s)"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def read_visits() -> int:
    _ensure_data_dir()
    if not DATA_FILE.exists():
        return 0
    content = DATA_FILE.read_text(encoding="utf-8").strip()
    if not content:
        return 0
    return int(content)


def write_visits(count: int) -> None:
    _ensure_data_dir()
    DATA_FILE.write_text(str(count), encoding="utf-8")


def increment_visits() -> int:
    visits = read_visits() + 1
    write_visits(visits)
    return visits


def get_system_info() -> dict:
    start = time.time()
    result = {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 0,
        "python_version": platform.python_version(),
    }
    devops_info_system_collection_seconds.observe(time.time() - start)
    return result


def get_request_info() -> dict:
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else request.remote_addr

    return {
        "client_ip": client_ip or "",
        "user_agent": request.headers.get("User-Agent", ""),
        "method": request.method,
        "path": request.path,
    }


def list_endpoints() -> list:
    return [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"},
        {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
        {"path": "/visits", "method": "GET", "description": "Visits counter"},
    ]


@app.before_request
def before_request_metrics():
    g.start_time = time.time()
    http_requests_in_progress.inc()


@app.after_request
def after_request_metrics(response):
    endpoint = request.path
    status_code = str(response.status_code)

    if endpoint != "/metrics":
        http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=status_code,
        ).inc()

        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(time.time() - g.start_time)

    http_requests_in_progress.dec()
    return response


@app.get("/")
def index():
    logger.info("Request: %s %s", request.method, request.path)
    devops_info_endpoint_calls.labels(endpoint="/").inc()

    visits = increment_visits()
    uptime_sec = _uptime_seconds()
    payload = {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "Flask",
        },
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": uptime_sec,
            "uptime_human": _uptime_human(uptime_sec),
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "request": get_request_info(),
        "endpoints": list_endpoints(),
        "visits": visits,
    }
    return jsonify(payload), 200


@app.get("/visits")
def visits():
    logger.info("Request: %s %s", request.method, request.path)
    devops_info_endpoint_calls.labels(endpoint="/visits").inc()
    return jsonify({"visits": read_visits()}), 200


@app.get("/health")
def health():
    logger.info("Request: %s %s", request.method, request.path)
    devops_info_endpoint_calls.labels(endpoint="/health").inc()

    return (
        jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime_seconds": _uptime_seconds(),
            }
        ),
        200,
    )


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), mimetype="text/plain; version=0.0.4; charset=utf-8")


@app.errorhandler(404)
def not_found(_err):
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(_err):
    return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred"}), 500


if __name__ == "__main__":
    logger.info("Starting app on %s:%s (debug=%s)", HOST, PORT, DEBUG)
    app.run(host=HOST, port=PORT, debug=DEBUG)
