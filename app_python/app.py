import logging
import os
import platform
import socket
from datetime import datetime, timezone

from flask import Flask, Response, jsonify, request, g
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from pythonjsonlogger import jsonlogger

VISITS_FILE = os.getenv("VISITS_FILE", "/data/visits")


def read_visits() -> int:
    try:
        with open(VISITS_FILE, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def write_visits(count: int) -> None:
    os.makedirs(os.path.dirname(VISITS_FILE), exist_ok=True)
    tmp = VISITS_FILE + ".tmp"
    with open(tmp, "w") as f:
        f.write(str(count))
    os.replace(tmp, VISITS_FILE)


def create_app() -> Flask:
    app = Flask(__name__)

    configure_logging()
    logger = logging.getLogger("devops-info-service")
    logger.info("application_startup", extra={"event": "startup"})

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    start_time = datetime.now(timezone.utc)

    http_requests_total = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status"],
    )

    http_request_duration_seconds = Histogram(
        "http_request_duration_seconds",
        "HTTP request duration seconds",
        ["method", "endpoint"],
    )

    http_requests_in_progress = Gauge(
        "http_requests_in_progress",
        "HTTP requests currently being processed",
    )

    endpoint_calls = Counter(
        "devops_info_endpoint_calls",
        "Endpoint calls",
        ["endpoint"],
    )

    system_info_duration = Histogram(
        "devops_info_system_collection_seconds",
        "System info collection time",
    )

    def uptime_seconds() -> int:
        delta = datetime.now(timezone.utc) - start_time
        return int(delta.total_seconds())

    @app.before_request
    def before_request_metrics() -> None:
        g.request_start_time = datetime.now(timezone.utc)
        http_requests_in_progress.inc()

    @app.after_request
    def after_request_metrics(response):
        try:
            start_time_local = getattr(g, "request_start_time", None)
            if start_time_local is not None:
                duration = (
                    datetime.now(timezone.utc) - start_time_local
                ).total_seconds()
                http_request_duration_seconds.labels(
                    method=request.method,
                    endpoint=request.path,
                ).observe(duration)

            http_requests_total.labels(
                method=request.method,
                endpoint=request.path,
                status=str(response.status_code),
            ).inc()

            logger.info(
                "request",
                extra={
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code,
                    "client_ip": request.remote_addr,
                    "user_agent": request.headers.get("User-Agent", ""),
                },
            )
        finally:
            http_requests_in_progress.dec()

        return response

    @app.errorhandler(Exception)
    def handle_exception(exc):
        http_requests_total.labels(
            method=request.method,
            endpoint=request.path,
            status="500",
        ).inc()
        http_requests_in_progress.dec()

        logger.error(
            "unhandled_exception",
            extra={
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
                "method": request.method,
                "path": request.path,
                "client_ip": request.remote_addr,
            },
        )
        return jsonify({"error": "Internal Server Error"}), 500

    @app.route("/", methods=["GET"])
    def index():
        endpoint_calls.labels(endpoint="/").inc()

        count = read_visits() + 1
        write_visits(count)

        system_start = datetime.now(timezone.utc)
        system_info = {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
            "python_version": platform.python_version(),
        }
        system_duration = (
            datetime.now(timezone.utc) - system_start
        ).total_seconds()
        system_info_duration.observe(system_duration)

        now = datetime.now(timezone.utc)
        uptime = uptime_seconds()
        uptime_hours = uptime // 3600
        uptime_minutes = (uptime % 3600) // 60

        runtime_info = {
            "uptime_seconds": uptime,
            "uptime_human": f"{uptime_hours} hours, {uptime_minutes} minutes",
            "current_time": now.isoformat(),
            "timezone": "UTC",
        }

        request_info = {
            "client_ip": request.remote_addr,
            "user_agent": request.headers.get("User-Agent", ""),
            "method": request.method,
            "path": request.path,
        }

        response = {
            "service": {
                "name": "devops-info-service",
                "version": "1.0.0",
                "description": "DevOps course info service",
                "framework": "Flask",
            },
            "system": system_info,
            "runtime": runtime_info,
            "request": request_info,
            "visits": count,
            "endpoints": [
                {
                    "path": "/",
                    "method": "GET",
                    "description": "Service information",
                },
                {
                    "path": "/visits",
                    "method": "GET",
                    "description": "Visit counter",
                },
                {
                    "path": "/health",
                    "method": "GET",
                    "description": "Health check",
                },
                {
                    "path": "/metrics",
                    "method": "GET",
                    "description": "Prometheus metrics",
                },
            ],
        }

        return jsonify(response)

    @app.route("/visits", methods=["GET"])
    def visits():
        endpoint_calls.labels(endpoint="/visits").inc()
        count = read_visits()
        return jsonify({"visits": count})

    @app.route("/health", methods=["GET"])
    def health():
        endpoint_calls.labels(endpoint="/health").inc()

        return jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime_seconds": uptime_seconds(),
            }
        )

    @app.route("/metrics", methods=["GET"])
    def metrics() -> Response:
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    def run() -> None:
        app.run(host=host, port=port)

    app.run_app = run  # type: ignore[attr-defined]
    return app


def configure_logging() -> None:
    logger = logging.getLogger("devops-info-service")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return

    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s "
        "%(method)s %(path)s %(status_code)s %(client_ip)s %(user_agent)s %(event)s"
    )
    formatter.converter = lambda *args: datetime.now(timezone.utc).timetuple()
    handler.setFormatter(formatter)
    logger.addHandler(handler)


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run_app()  # type: ignore[attr-defined]
