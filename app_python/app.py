import json
import logging
import os
import platform
import socket
import threading
import time
from datetime import datetime, timezone

from flask import Flask, Response, jsonify, request, g
from prometheus_client import Counter, Histogram, Gauge, generate_latest


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
            ):
                log_obj[key] = value
        return json.dumps(log_obj)


handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.setLevel(logging.INFO)
logging.root.handlers = [handler]

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Prometheus metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
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

endpoint_calls = Counter(
    "devops_info_endpoint_calls",
    "Endpoint calls by endpoint name",
    ["endpoint"],
)

system_info_duration = Histogram(
    "devops_info_system_collection_seconds",
    "Time spent collecting system info",
)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

VISITS_FILE = os.getenv("VISITS_FILE", "/data/visits")
_visits_lock = threading.Lock()

START_TIME = datetime.now()


def read_visits():
    try:
        with open(VISITS_FILE, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def increment_visits():
    with _visits_lock:
        count = read_visits() + 1
        os.makedirs(os.path.dirname(VISITS_FILE), exist_ok=True)
        with open(VISITS_FILE, "w") as f:
            f.write(str(count))
        return count


def get_uptime():
    delta = datetime.now() - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {"seconds": seconds, "human": f"{hours} hours, {minutes} minutes"}


def get_platform_version():
    system = platform.system()
    if system == "Linux":
        return platform.freedesktop_os_release()["PRETTY_NAME"]
    elif system == "Darwin":
        return str(platform.mac_ver()[0])
    elif system == "Windows":
        return platform.version()
    return platform.release()


def get_system_info():
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": get_platform_version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }


def get_service_info():
    return {
        "name": "devops-info-service",
        "version": "1.0.0",
        "description": "DevOps course info service",
        "framework": "Flask",
    }


def get_runtime_info():
    uptime = get_uptime()
    return {
        "uptime_seconds": uptime["seconds"],
        "uptime_human": uptime["human"],
        "current_time": datetime.now(timezone.utc).isoformat(),
        "timezone": "UTC",
    }


def get_request_info():
    return {
        "client_ip": request.remote_addr,
        "user_agent": request.headers.get("User-Agent", "unknown"),
        "method": request.method,
        "path": request.path,
    }


def get_endpoints():
    return [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"},
        {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
        {"path": "/visits", "method": "GET", "description": "Visit counter"},
    ]


@app.before_request
def before_request():
    g.start_time = time.time()
    if request.path != "/metrics":
        http_requests_in_progress.inc()


@app.after_request
def after_request(response):
    duration = time.time() - g.start_time
    duration_ms = round(duration * 1000, 2)

    if request.path != "/metrics":
        http_requests_total.labels(
            method=request.method,
            endpoint=request.path,
            status=response.status_code,
        ).inc()
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.path,
        ).observe(duration)
        http_requests_in_progress.dec()

    logger.info(
        "http_request",
        extra={
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
            "remote_addr": request.remote_addr,
            "user_agent": request.headers.get("User-Agent", "unknown"),
        },
    )
    return response


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype="text/plain")


@app.route("/visits")
def visits():
    endpoint_calls.labels(endpoint="/visits").inc()
    return jsonify({"visits": read_visits()})


@app.route("/")
def index():
    endpoint_calls.labels(endpoint="/").inc()
    increment_visits()
    with system_info_duration.time():
        sys_info = get_system_info()
    return jsonify(
        {
            "service": get_service_info(),
            "system": sys_info,
            "runtime": get_runtime_info(),
            "request": get_request_info(),
            "endpoints": get_endpoints(),
        }
    )


@app.route("/health")
def health():
    endpoint_calls.labels(endpoint="/health").inc()
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": get_uptime()["seconds"],
        }
    )


@app.errorhandler(404)
def not_found(error):
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
    logger.error(f"Internal server error: {error}")
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
        "app_startup",
        extra={"host": HOST, "port": PORT, "debug": DEBUG},
    )
    app.run(host=HOST, port=PORT, debug=DEBUG)
