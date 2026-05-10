import logging
import os
import platform
import socket
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, request

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback for local tests
    fcntl = None


app = Flask(__name__)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
VISITS_FILE = os.getenv("VISITS_FILE", "/data/visits")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

start_time = time.time()


def get_uptime():
    uptime_seconds = int(time.time() - start_time)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    return {
        "uptime_seconds": uptime_seconds,
        "uptime_human": f"{hours} hour, {minutes} minutes",
    }


def _ensure_visits_directory():
    directory = os.path.dirname(VISITS_FILE)
    if directory:
        os.makedirs(directory, exist_ok=True)


def _lock_file(file_handle):
    if fcntl is not None:
        fcntl.flock(file_handle, fcntl.LOCK_EX)


def _unlock_file(file_handle):
    if fcntl is not None:
        fcntl.flock(file_handle, fcntl.LOCK_UN)


def read_visits():
    """Read visit count from file. Returns 0 if file doesn't exist."""
    try:
        with open(VISITS_FILE, "r", encoding="utf-8") as visits_file:
            raw_value = visits_file.read().strip()
            return int(raw_value) if raw_value else 0
    except (FileNotFoundError, ValueError):
        return 0


def write_visits(count):
    """Write visit count atomically to the visits file."""
    _ensure_visits_directory()
    tmp_path = f"{VISITS_FILE}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as visits_file:
        visits_file.write(str(count))
        visits_file.flush()
        os.fsync(visits_file.fileno())
    os.replace(tmp_path, VISITS_FILE)


def increment_visits():
    """Increment visit counter and return the new value."""
    _ensure_visits_directory()
    lock_path = f"{VISITS_FILE}.lock"

    with open(lock_path, "a+", encoding="utf-8") as lock_file:
        _lock_file(lock_file)
        try:
            count = read_visits() + 1
            write_visits(count)
            return count
        finally:
            _unlock_file(lock_file)


@app.route("/")
def index():
    """Main endpoint returning system info and incrementing visit counter."""
    visits = increment_visits()
    uptime = get_uptime()

    return jsonify(
        {
            "service": {
                "name": "devops-info-service",
                "version": "1.0.0",
                "description": "DevOps course info service",
                "framework": "Flask",
            },
            "system": {
                "hostname": socket.gethostname(),
                "platform": platform.system(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "cpu_count": os.cpu_count(),
                "python_version": platform.python_version(),
            },
            "runtime": {
                "uptime_seconds": uptime["uptime_seconds"],
                "uptime_human": uptime["uptime_human"],
                "current_time": datetime.now(timezone.utc).isoformat(),
                "timezone": "UTC",
            },
            "request": {
                "client_ip": request.remote_addr,
                "user_agent": request.headers.get("User-Agent"),
                "method": request.method,
                "path": request.path,
            },
            "visits": visits,
            "endpoints": [
                {"path": "/", "method": "GET", "description": "Service information"},
                {"path": "/health", "method": "GET", "description": "Health check"},
                {"path": "/visits", "method": "GET", "description": "Visit counter"},
            ],
        }
    )


@app.route("/health")
def health():
    """Health check endpoint for K8s probes."""
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": int(time.time() - start_time),
        }
    )


@app.route("/visits")
def visits():
    """Return the current visit count without incrementing it."""
    count = read_visits()
    return jsonify(
        {
            "visits": count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


if __name__ == "__main__":
    logger.info("Starting application on %s:%s", HOST, PORT)
    logger.info("Visits file: %s", VISITS_FILE)
    app.run(host=HOST, port=PORT)
