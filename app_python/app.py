import json
import logging
import os
import platform
import socket
import threading
from datetime import datetime, timezone
from flask import Flask, jsonify, request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)
http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed'
)

APP_NAME = "devops-info-service"
APP_VERSION = "1.1.0"
APP_DESCRIPTION = "DevOps course info service"
FRAMEWORK = "Flask"

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
DATA_DIR = os.getenv("DATA_DIR", "/data")
VISITS_FILE = os.path.join(DATA_DIR, "visits")

START_TIME = datetime.now(timezone.utc)

_visits_lock = threading.Lock()

def _read_visits() -> int:
    try:
        with open(VISITS_FILE, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def _write_visits(count: int) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(VISITS_FILE, "w") as f:
        f.write(str(count))

def increment_visits() -> int:
    with _visits_lock:
        count = _read_visits() + 1
        _write_visits(count)
        return count

# Custom JSON Log Formatter
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Include custom request context if passed via 'extra'
        if hasattr(record, "req_context"):
            log_record.update(record.req_context)

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)

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
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.platform(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 0,
        "python_version": platform.python_version(),
    }


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


def get_endpoints() -> list[dict]:
    return [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"},
        {"path": "/ready", "method": "GET", "description": "Readiness check"},
        {"path": "/visits", "method": "GET", "description": "Visit counter"},
    ]

def create_app() -> Flask:
    app = Flask(__name__)

    logger = logging.getLogger(APP_NAME)
    logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

    logging.getLogger("werkzeug").disabled = True

    logger.info("Application starting up", extra={"req_context": {"version": APP_VERSION, "host": HOST, "port": PORT}})

    @app.before_request
    def before_request():
        http_requests_in_progress.inc()
        request.start_time = time.time()
    @app.after_request
    def log_response(response):
        context = {
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "client_ip": get_client_ip()
        }

        duration = time.time() - getattr(request, "start_time", 0)
        http_request_duration_seconds.labels(method=request.method, endpoint=request.path).observe(duration)
        http_requests_total.labels(method=request.method, endpoint=request.path, status=str(response.status_code)).inc()

        duration = time.time() - getattr(request, "start_time", 0)
        http_request_duration_seconds.labels(method=request.method, endpoint=request.path).observe(duration)
        http_requests_total.labels(method=request.method, endpoint=request.path, status=str(response.status_code)).inc()

        if response.status_code >= 500:
            logger.error(f"HTTP Request Server Error", extra={"req_context": context})
        elif response.status_code >= 400:
            logger.warning(f"HTTP Request Client Error", extra={"req_context": context})
        else:
            logger.info(f"HTTP Request Processed", extra={"req_context": context})


        http_requests_in_progress.dec()
        return response

    @app.get("/")
    def index():
        count = increment_visits()
        payload = {
            "service": {
                "name": APP_NAME,
                "version": APP_VERSION,
                "description": APP_DESCRIPTION,
                "framework": FRAMEWORK,
            },
            "visits": count,
            "system": get_system_info(),
            "runtime": get_runtime_info(),
            "request": get_request_info(),
            "endpoints": get_endpoints(),
        }
        return jsonify(payload)

    @app.get("/visits")
    def visits():
        count = _read_visits()
        return jsonify({"visits": count})

    @app.get("/health")
    def health():
        uptime = get_uptime()
        return jsonify(
            {
                "status": "healthy",
                "timestamp": iso_utc_z(datetime.now(timezone.utc)),
                "uptime_seconds": uptime["seconds"],
            }
        )

    @app.get("/ready")
    def ready():
        return jsonify(
            {
                "status": "ready",
                "timestamp": iso_utc_z(datetime.now(timezone.utc)),
            }
        )

    @app.route("/metrics")
    def metrics():
        return Response(generate_latest(), mimetype="text/plain")

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404

    @app.errorhandler(500)
    def internal_error(_error):
        return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred"}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host=HOST, port=PORT, debug=DEBUG)
