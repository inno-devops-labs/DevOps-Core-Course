import json
import logging
import os
import platform
import socket
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)
START_TIME = time.time()

VISITS_FILE = os.environ.get("VISITS_FILE", "/data/visits")

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed'
)

endpoint_calls = Counter(
    'devops_info_endpoint_calls_total',
    'Total calls per endpoint',
    ['endpoint']
)

system_info_collection_seconds = Histogram(
    'devops_info_system_collection_seconds',
    'Time spent collecting system info'
)


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "client_ip"):
            log_data["client_ip"] = record.client_ip
        return json.dumps(log_data)


logger = logging.getLogger("devops-info-service")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)


@app.before_request
def before_request():
    request.start_time = time.time()
    http_requests_in_progress.inc()
    logger.info(
        "Incoming request",
        extra={
            "method": request.method,
            "path": request.path,
            "client_ip": request.remote_addr,
        },
    )


@app.after_request
def after_request(response):
    if request.path != '/metrics':
        duration = time.time() - request.start_time
        endpoint = request.path
        http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status=str(response.status_code)
        ).inc()
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)
    http_requests_in_progress.dec()
    logger.info(
        "Request completed",
        extra={
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "client_ip": request.remote_addr,
        },
    )
    return response


@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route("/")
def index():
    endpoint_calls.labels(endpoint="/").inc()
    visits = _read_visits() + 1
    _write_visits(visits)
    start = time.time()
    uptime_seconds = time.time() - START_TIME
    minutes, seconds = divmod(int(uptime_seconds), 60)
    hours, minutes = divmod(minutes, 60)

    if hours > 0:
        uptime_human = f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
    elif minutes > 0:
        uptime_human = f"{minutes} minute{'s' if minutes != 1 else ''}, {seconds} second{'s' if seconds != 1 else ''}"
    else:
        uptime_human = f"{seconds} second{'s' if seconds != 1 else ''}"

    with system_info_collection_seconds.time():
        system_data = {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
            "python_version": platform.python_version(),
        }

    return jsonify({
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "Flask",
        },
        "system": system_data,
        "runtime": {
            "uptime_seconds": round(uptime_seconds, 2),
            "uptime_human": uptime_human,
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "request": {
            "client_ip": request.remote_addr,
            "user_agent": request.headers.get("User-Agent", ""),
            "method": request.method,
            "path": request.path,
        },
        "visits": visits,
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/visits", "method": "GET", "description": "Visit counter"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
        ],
    })


def _read_visits():
    try:
        with open(VISITS_FILE, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def _write_visits(count):
    os.makedirs(os.path.dirname(VISITS_FILE), exist_ok=True)
    with open(VISITS_FILE, "w") as f:
        f.write(str(count))


@app.route("/visits")
def visits():
    endpoint_calls.labels(endpoint="/visits").inc()
    count = _read_visits()
    return jsonify({"visits": count})


@app.route("/health")
def health():
    endpoint_calls.labels(endpoint="/health").inc()
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(time.time() - START_TIME, 2),
    })


if __name__ == "__main__":
    logger.info("Starting devops-info-service", extra={"method": "STARTUP", "path": "/", "client_ip": "localhost"})
    app.run(host="0.0.0.0", port=8000, debug=False)
