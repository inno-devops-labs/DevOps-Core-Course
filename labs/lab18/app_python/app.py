import os
import logging
import platform
import socket
from datetime import datetime, timezone

import time
from functools import wraps

from flask import Flask, request, jsonify, Response
from pythonjsonlogger import jsonlogger
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST


logger = logging.getLogger()

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    fmt="%(asctime)s %(name)s %(levelname)s %(message)s"
)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)


app = Flask(__name__)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
VISITS_FILE = os.getenv("VISITS_FILE", "/data/visits")

START_TIME = datetime.now(timezone.utc)

# Define metrics
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


def track_metrics(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        http_requests_in_progress.inc()
        start_time = time.time()

        try:
            response = func(*args, **kwargs)
            status = getattr(response, "status_code", 200)
        except Exception:
            status = 500
            raise
        finally:
            duration = time.time() - start_time
            endpoint = request.path
            method = request.method

            http_requests_total.labels(method=method, endpoint=endpoint, status=str(status)).inc()
            http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)

            http_requests_in_progress.dec()

        return response

    return wrapper


def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {"seconds": seconds, "human": f"{hours} hours, {minutes} minutes"}


def get_system_info():
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }

def read_visits():
    try:
        with open(VISITS_FILE, 'r') as f:
            return int(f.read().strip())
    except FileNotFoundError:
        return 0
    except Exception:
        return 0

def write_visits(count):
    temp_file = VISITS_FILE + ".tmp"
    with open(temp_file, 'w') as f:
        f.write(str(count))
    os.replace(temp_file, VISITS_FILE)


@app.route("/visits", methods=["GET"])
@track_metrics
def get_visits():
    count = read_visits()
    return jsonify({
        "visits": count,
        "endpoint": "/",
        "description": "Number of requests to root endpoint"
    })


@app.route("/health", methods=["GET"])
@track_metrics
def health():
    uptime = get_uptime()
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": uptime["seconds"],
        }
    )

# k8s
@app.route('/ready')
def ready():
    return 'OK', 200


@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)



@app.route("/", methods=["GET"])
@track_metrics
def default_route():
    logger.info(f"Request: {request.method} {request.path}")
    
    current = read_visits()
    current += 1
    write_visits(current)
    
    
    uptime = get_uptime()
    
    response = {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "Flask",
        },
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "request": {
            "client_ip": request.remote_addr,
            "user_agent": request.headers.get("User-Agent"),
            "method": request.method,
            "path": request.path,
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/visits", "method": "GET", "description": "Visit counter"}, 
        ],
    }

    return jsonify(response)


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(error):
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
    logger.info("[+] Starting...")
    try:
        app.run(host=HOST, port=PORT, debug=DEBUG)
    finally:
        logger.info("[i] Shutting down")