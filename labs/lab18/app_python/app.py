#!/usr/bin/env python3
import os
import socket
import json
from datetime import datetime, timezone
from flask import Flask, jsonify, request

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

app = Flask(__name__)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

START_TIME = datetime.now(timezone.utc)

DATA_DIR = os.getenv("DATA_DIR", "/data")
CONFIG_PATH = "/config/config.json"

try:
    os.makedirs(DATA_DIR, exist_ok=True)
except Exception:
    DATA_DIR = "/tmp"
    os.makedirs(DATA_DIR, exist_ok=True)

# ----------------------------
# DOCKER INFO
# ----------------------------
IS_DOCKER = os.path.exists("/.dockerenv")
CONTAINER_ID = socket.gethostname() if IS_DOCKER else None

# ----------------------------
# VISITS
# ----------------------------
VISITS_FILE = os.path.join(DATA_DIR, "visits.json")


def load_visits():
    try:
        with open(VISITS_FILE, "r") as f:
            return json.load(f).get("visits", 0)
    except Exception:
        return 0


def save_visits(count):
    try:
        with open(VISITS_FILE, "w") as f:
            json.dump({"visits": count}, f)
    except Exception:
        pass


def load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


# ----------------------------
# METRICS
# ----------------------------
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "Request duration",
    ["method", "endpoint"],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "In progress requests",
)


@app.before_request
def before_request():
    request.start_time = datetime.now(timezone.utc)
    http_requests_in_progress.inc()


@app.after_request
def after_request(response):
    dur = (datetime.now(timezone.utc) - request.start_time).total_seconds()

    http_requests_total.labels(
        method=request.method,
        endpoint=request.path,
        status=str(response.status_code),
    ).inc()

    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.path,
    ).observe(dur)

    http_requests_in_progress.dec()
    return response


# ----------------------------
# ROUTES
# ----------------------------
@app.route("/")
def main():
    visits = load_visits() + 1
    save_visits(visits)

    config = load_config()

    return jsonify({
        "service": {
            "name": "devops-info-service",
            "framework": "Flask",   # <-- ВОТ ЭТОГО НЕ ХВАТАЛО
            "version": "2.0.0",
            "environment": config.get("environment", "unknown"),
        },
        "system": {
            "environment": config.get("environment", "unknown"),
            "name": socket.gethostname(),
            "version": "2.0.0",
        },
        "runtime": {
            "environment": config.get("environment", "unknown"),
            "host": socket.gethostname(),
            "uptime_seconds": int(
                (datetime.now(timezone.utc) - START_TIME).total_seconds()
            ),
        },
        "request": {
            "method": request.method,
            "path": request.path,
        },
        "config": config,
        "endpoints": [
            "/",
            "/health",
            "/visits",
            "/docker",
            "/metrics",
        ],
    })


@app.route("/visits")
def visits():
    return jsonify({"visits": load_visits()})


@app.route("/health")
def health():
    delta = datetime.now(timezone.utc) - START_TIME

    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": int(delta.total_seconds()),
        "environment": os.getenv("APP_ENV", "unknown"),
    })


@app.route("/docker")
def docker():
    return jsonify({
        "is_docker": IS_DOCKER,
        "container_id": CONTAINER_ID,
        "message": (
            "docker environment detected"
            if IS_DOCKER
            else "not running in docker"
        ),
    })


@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "error": "Not Found",
        "path": request.path,
        "available_endpoints": [
            "/",
            "/health",
            "/visits",
            "/docker",
            "/metrics",
        ],
    }), 404


@app.route("/metrics")
def metrics():
    return (
        generate_latest(),
        200,
        {"Content-Type": CONTENT_TYPE_LATEST},
    )


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)
