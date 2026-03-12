import logging
import os
import platform
import socket
from datetime import datetime, timezone

from flask import Flask, jsonify, request, g
from pythonjsonlogger import jsonlogger


def create_app() -> Flask:
    app = Flask(__name__)

    configure_logging()
    logger = logging.getLogger("devops-info-service")
    logger.info("application_startup", extra={"event": "startup"})

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    start_time = datetime.now(timezone.utc)

    def uptime_seconds() -> int:
        delta = datetime.now(timezone.utc) - start_time
        return int(delta.total_seconds())

    @app.before_request
    def before_request_logging() -> None:
        g.request_start_time = datetime.now(timezone.utc)

    @app.after_request
    def after_request_logging(response):
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
        return response

    @app.errorhandler(Exception)
    def handle_exception(exc):
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
        system_info = {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
            "python_version": platform.python_version(),
        }

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
            "endpoints": [
                {
                    "path": "/",
                    "method": "GET",
                    "description": "Service information",
                },
                {
                    "path": "/health",
                    "method": "GET",
                    "description": "Health check",
                },
            ],
        }

        return jsonify(response)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime_seconds": uptime_seconds(),
            }
        )

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

