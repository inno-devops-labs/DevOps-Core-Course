"""DevOps Info Service - Flask application for system information."""
import logging
import os
import platform
import socket
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from pythonjsonlogger import jsonlogger


def setup_json_logging():
    """Configure JSON logging for Loki/Grafana (Lab 7)."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level, logging.INFO))
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s",
        rename_fields={"levelname": "level", "asctime": "timestamp"},
    )
    handler.setFormatter(formatter)
    root.handlers = [handler]


setup_json_logging()
logger = logging.getLogger(__name__)
# Werkzeug has its own log format; routing it through JsonFormatter raises an
# exception inside send_response, which drops the connection before the client
# receives the response body.
logging.getLogger("werkzeug").propagate = False

try:
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5001))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
except ValueError as e:
    logger.error(f"Invalid environment variable: {e}")
    HOST = '0.0.0.0'
    PORT = 5001
    DEBUG = False

app = Flask(__name__)
start_time = time.time()

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


@app.before_request
def log_request_start():
    """Log incoming request (context for JSON logs)."""
    request.start_time = time.time()
    http_requests_in_progress.inc()
    logger.info(
        "Request started",
        extra={
            "method": request.method,
            "path": request.path,
            "client_ip": request.remote_addr or "unknown",
        },
    )


@app.after_request
def log_request_end(response):
    """Log response status and duration."""
    endpoint = (
        request.url_rule.rule
        if getattr(request, "url_rule", None) is not None
        else request.path
    )
    duration_seconds = time.time() - getattr(request, "start_time", time.time())
    duration_ms = duration_seconds * 1000

    http_requests_total.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=str(response.status_code),
    ).inc()
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=endpoint,
    ).observe(duration_seconds)
    http_requests_in_progress.dec()

    logger.info(
        "Request completed",
        extra={
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "client_ip": request.remote_addr or "unknown",
            "duration_ms": round(duration_ms, 2),
        },
    )
    return response


@app.route("/metrics", methods=["GET"])
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


def format_uptime(seconds):
    """Format uptime in seconds to human-readable string."""
    try:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        hour_str = f"{hours} hour{'s' if hours != 1 else ''}"
        minute_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
        sec_str = f"{secs} second{'s' if secs != 1 else ''}"

        return f"{hour_str}, {minute_str}, {sec_str}"
    except (ValueError, TypeError) as e:
        logger.error(f"Error formatting uptime: {e}")
        return "Unknown"


def get_system_info():
    """Get system information with error handling."""
    system_info = {}

    try:
        system_info['hostname'] = socket.gethostname()
    except (socket.error, OSError) as e:
        logger.warning(f"Failed to get hostname: {e}")
        system_info['hostname'] = 'Unknown'

    try:
        system_info['platform'] = platform.system()
    except Exception as e:
        logger.warning(f"Failed to get platform: {e}")
        system_info['platform'] = 'Unknown'

    try:
        system_info['platform_version'] = platform.release()
    except Exception as e:
        logger.warning(f"Failed to get platform version: {e}")
        system_info['platform_version'] = 'Unknown'

    try:
        system_info['architecture'] = platform.machine()
    except Exception as e:
        logger.warning(f"Failed to get architecture: {e}")
        system_info['architecture'] = 'Unknown'

    try:
        cpu_count = os.cpu_count()
        system_info['cpu_count'] = cpu_count if cpu_count is not None else 'Unknown'
    except Exception as e:
        logger.warning(f"Failed to get CPU count: {e}")
        system_info['cpu_count'] = 'Unknown'

    try:
        system_info['python_version'] = platform.python_version()
    except Exception as e:
        logger.warning(f"Failed to get Python version: {e}")
        system_info['python_version'] = 'Unknown'

    return system_info


@app.route('/', methods=['GET'])
def main():
    """Main endpoint returning service and system information."""
    try:
        logger.info("Main endpoint accessed", extra={"path": "/", "method": "GET"})
        uptime_seconds = time.time() - start_time

        system_info = get_system_info()

        response_data = {
            "service": {
                "name": "devops-info-service",
                "version": "1.0.0",
                "description": "DevOps course info service",
                "framework": "Flask"
            },
            "system": system_info,
            "runtime": {
                "uptime_seconds": round(uptime_seconds, 2),
                "uptime_human": format_uptime(uptime_seconds),
                "current_time": datetime.now(timezone.utc).isoformat(),
                "timezone": "UTC"
            },
            "request": {
                "client_ip": request.remote_addr or 'Unknown',
                "user_agent": request.headers.get('User-Agent', 'Unknown'),
                "method": request.method,
                "path": request.path
            },
            "endpoints": [
                {
                    "path": "/",
                    "method": "GET",
                    "description": "Service information"
                },
                {
                    "path": "/health",
                    "method": "GET",
                    "description": "Health check"
                }
            ]
        }

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error in main endpoint: {e}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring."""
    try:
        uptime_seconds = time.time() - start_time
        timestamp = datetime.now(timezone.utc).isoformat().replace(
            '+00:00', '.000Z'
        )

        response_data = {
            "status": "healthy",
            "timestamp": timestamp,
            "uptime_seconds": round(uptime_seconds, 2)
        }

        logger.debug("Health check", extra={"status": "healthy"})
        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Error in health check: {e}", exc_info=True)
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    logger.warning(f"404 error: {request.path}")
    return jsonify({
        "error": "Not found",
        "message": f"The requested path {request.path} was not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"500 error: {error}", exc_info=True)
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500


if __name__ == "__main__":
    logger.info(
        "Starting application",
        extra={"host": HOST, "port": PORT, "debug": DEBUG},
    )
    try:
        app.run(host=HOST, port=PORT, debug=DEBUG)
    except Exception as e:
        logger.critical(f"Failed to start application: {e}", exc_info=True)
        raise
