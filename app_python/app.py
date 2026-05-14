"""
DevOps Info Service
Main application module providing system information and health status.
"""

import os
import socket
import platform
import logging
from threading import Lock
from datetime import datetime, timezone
from flask import Flask, jsonify, request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration from environment variables
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Application start time for uptime calculation
START_TIME = datetime.now(timezone.utc)
VISITS_LOCK = Lock()


def get_visits_file_path():
    """Return path to persisted visits counter."""
    default_data_dir = os.path.join(app.root_path, "data")
    data_dir = os.getenv("DATA_DIR", default_data_dir)
    return os.getenv("VISITS_FILE", os.path.join(data_dir, "visits"))


def read_visits_count():
    """Read persisted visits count."""
    visits_file = get_visits_file_path()
    try:
        with open(visits_file, "r", encoding="utf-8") as file:
            return int(file.read().strip() or "0")
    except FileNotFoundError:
        return 0
    except ValueError:
        logger.warning("Invalid visits counter in %s, resetting to 0", visits_file)
        return 0


def write_visits_count(count):
    """Persist visits count using atomic replace."""
    visits_file = get_visits_file_path()
    directory = os.path.dirname(visits_file)
    if directory:
        os.makedirs(directory, exist_ok=True)

    temp_file = f"{visits_file}.tmp"
    with open(temp_file, "w", encoding="utf-8") as file:
        file.write(str(count))
    os.replace(temp_file, visits_file)


def increment_visits_count():
    """Increment and persist visits count."""
    with VISITS_LOCK:
        count = read_visits_count() + 1
        write_visits_count(count)
        return count


def get_deployment_info():
    """Return deployment metadata safe for public exposure."""
    secrets = ("API_KEY", "DATABASE_URL")
    fly_app_name = os.getenv("FLY_APP_NAME")

    return {
        "platform": ("fly.io" if fly_app_name or os.getenv("FLY_REGION") else "local"),
        "app_name": fly_app_name,
        "region": os.getenv("FLY_REGION"),
        "primary_region": os.getenv("PRIMARY_REGION"),
        "machine_id": os.getenv("FLY_MACHINE_ID"),
        "image_ref": os.getenv("FLY_IMAGE_REF"),
        "secrets": {secret: bool(os.getenv(secret)) for secret in secrets},
    }


def get_persistence_info(visits=None):
    """Return persistence state for current request."""
    current_visits = read_visits_count() if visits is None else visits
    return {
        "path": get_visits_file_path(),
        "visits": current_visits,
    }


def get_uptime():
    """Calculate application uptime."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    hour_str = "hour" if hours == 1 else "hours"
    minute_str = "minute" if minutes == 1 else "minutes"
    return {
        "seconds": seconds,
        "human": f"{hours} {hour_str}, {minutes} {minute_str}",
    }


def get_system_info():
    """Collect system information."""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.platform(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }


def get_service_info():
    """Return service metadata."""
    return {
        "name": "devops-info-service",
        "version": "1.0.0",
        "description": "DevOps course info service",
        "framework": "Flask",
    }


def get_request_info():
    """Extract request information."""
    return {
        "client_ip": request.remote_addr,
        "user_agent": request.headers.get("User-Agent", "Unknown"),
        "method": request.method,
        "path": request.path,
    }


def get_endpoints():
    """Return list of available endpoints."""
    return [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"},
        {
            "path": "/visits",
            "method": "GET",
            "description": "Persistent visit count",
        },
    ]


@app.route("/")
def index():
    """Main endpoint - service and system information."""
    client_ip = request.remote_addr
    logger.info(f"Request: {request.method} {request.path} from {client_ip}")

    uptime = get_uptime()
    visits = increment_visits_count()

    response = {
        "service": get_service_info(),
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "request": get_request_info(),
        "deployment": get_deployment_info(),
        "persistence": get_persistence_info(visits),
        "endpoints": get_endpoints(),
    }

    return jsonify(response)


@app.route("/health")
def health():
    """Health check endpoint for monitoring and Kubernetes probes."""
    client_ip = request.remote_addr
    logger.debug(f"Health check from {client_ip}")

    uptime = get_uptime()

    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": uptime["seconds"],
        }
    )


@app.route("/visits")
def visits():
    """Return current persisted visit counter without incrementing it."""
    current_visits = read_visits_count()
    return jsonify(
        {
            "visits": current_visits,
            "storage": {"path": get_visits_file_path()},
        }
    )


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    logger.warning(f"404 Not Found: {request.path}")
    return (
        jsonify({"error": "Not Found", "message": "Endpoint does not exist"}),
        404,
    )


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    error_msg = str(error)
    logger.error(f"500 Internal Server Error: {error_msg}")
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
    logger.info(f"Starting DevOps Info Service on {HOST}:{PORT}")
    logger.info(f"Debug mode: {DEBUG}")
    app.run(host=HOST, port=PORT, debug=DEBUG)
