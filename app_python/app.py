"""
DevOps Info Service

Small Flask web app for DevOps labs.
Provides basic system/runtime/request information and a health check endpoint.
Configured via environment variables (HOST, PORT, DEBUG).
"""

import logging
import os
import platform
import socket
from datetime import datetime, timezone

from flask import Flask, jsonify, request

# Flask application instance
app = Flask(__name__)

# Runtime configuration (can be overridden via environment variables)
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Timestamp captured at startup (used to calculate uptime)
START_TIME = datetime.now(timezone.utc)

SERVICE = {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask",
    }

# Logging configuration (stdout; suitable for Docker/Kubernetes)
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)


# General functions of application
def system_info():
    """Return basic host and Python runtime information."""

    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.release(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }


def runtime_info():
    """Return uptime and current UTC timestamp for the running application."""

    current_time = datetime.now(timezone.utc)
    delta = current_time - START_TIME
    timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        "uptime_seconds": seconds,
        "uptime_human": f"{hours} hour, {minutes} minutes",
        "current_time": timestamp,
        "timezone": "UTC",
    }


def request_info():
    """
    Extract request metadata.

    If the app is behind a reverse proxy, the client IP may be passed via
    X-Forwarded-For header (first IP in the list). Fallback to remote_addr.
    """

    xff = request.headers.get("X-Forwarded-For", "")
    client_ip = xff.split(",")[0].strip() if xff else request.remote_addr

    return {
        "client_ip": client_ip,
        "user_agent": request.headers.get("User-Agent"),
        "method": request.method,
        "path": request.path,
    }


def endpoints_info():
    """
    Build an API endpoints list dynamically from Flask URL map.
    Description is taken from the first line of each handler's docstring.
    """

    endpoints = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue

        view_func = app.view_functions.get(rule.endpoint)
        doc = getattr(view_func, "__doc__", None) if view_func else None
        desc = (doc or "").strip().splitlines()[0] if doc else "No description"

        methods = sorted((rule.methods or set()) - {"HEAD", "OPTIONS"})
        for m in methods:
            endpoints.append({
                "method": m,
                "path": rule.rule,
                "description": desc,
            })

    endpoints.sort(key=lambda e: (e["path"], e["method"]))
    return endpoints


# General endpoints
@app.get("/")
def index():
    """Root endpoint: returns service metadata and diagnostic information."""

    payload = {
        "service": SERVICE,
        "system": system_info(),
        "runtime": runtime_info(),
        "request": request_info(),
        "endpoints": endpoints_info(),
    }
    return jsonify(payload)


@app.get("/health")
def health():
    """Health check endpoint for monitoring and Kubernetes probes."""
    rt = runtime_info()
    payload = {
        "status": "healthy",
        "timestamp": rt["current_time"],
        "uptime_seconds": rt["uptime_seconds"],
    }
    return jsonify(payload)


# Test-only endpoint to trigger HTTP 500 (uncomment to verify error handler)
# @app.get("/crash")
# def crash():
#     """Intentional error to test 500 handler."""
#     1 / 0


# Error Handlers
@app.errorhandler(404)
def not_found(error):
    """Return JSON error for unknown endpoints."""

    app.logger.warning("404 Not Found: %s %s", request.method, request.path)
    return jsonify({
        "error": "Not Found",
        "message": "Endpoint does not exist",
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Return JSON error for unhandled server exceptions."""

    app.logger.exception("500 Internal Server Error")
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
    }), 500


# Logging endpoints
@app.before_request
def log_requests():
    """Log basic request metadata before handling."""

    app.logger.info(
        "Request %s %s from %s UA=%s",
        request.method,
        request.path,
        request.headers.get("X-Forwarded-For", request.remote_addr),
        request.headers.get("User-Agent"),
    )


@app.after_request
def log_response(response):
    """Log response status code after handling."""

    app.logger.info(
        "Response %s %s -> %s",
        request.method,
        request.path,
        response.status_code,
    )

    return response


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)
