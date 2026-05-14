import json
import logging
import os
import platform
import socket
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from pythonjsonlogger import jsonlogger

# -----------------------------
# Environment
# -----------------------------
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

APP_NAME = os.getenv("APP_NAME", "devops-info-service")
APP_ENV = os.getenv("APP_ENV", "dev")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
VISITS_FILE = Path(os.getenv("VISITS_FILE", str(DATA_DIR / "visits")))
APP_CONFIG_FILE = Path(os.getenv("APP_CONFIG_FILE", "/config/config.json"))

# -----------------------------
# Prometheus metrics
# -----------------------------
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Active HTTP requests",
)

# ---------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------
logger = logging.getLogger("devops-info-service")
logger.setLevel(logging.DEBUG if DEBUG else LOG_LEVEL)
logger.propagate = False

for handler in logger.handlers[:]:
    logger.removeHandler(handler)

stream_handler = logging.StreamHandler(sys.stdout)
if os.getenv("LOG_FORMAT", "json").lower() == "json":
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(message)s %(pathname)s %(lineno)d %(name)s"
    )
else:
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

logger.info("Starting DevOps Info Service...")

# ---------------------------------------------------------
# FastAPI app initialization
# ---------------------------------------------------------
app = FastAPI()
START_TIME = datetime.now(timezone.utc)

VISITS_LOCK = threading.Lock()
VISITS_COUNT = 0


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------
def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    return {
        "seconds": seconds,
        "human": f"{hours} hours, {minutes} minutes",
    }


def get_system_info():
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": psutil.cpu_count(),
        "python_version": platform.python_version(),
    }


def ensure_storage():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not VISITS_FILE.exists():
        VISITS_FILE.write_text("0\n", encoding="utf-8")


def read_visits_from_file() -> int:
    try:
        raw = VISITS_FILE.read_text(encoding="utf-8").strip()
        return int(raw) if raw else 0
    except FileNotFoundError:
        return 0
    except (ValueError, OSError) as exc:
        logger.warning("Could not read visits file %s: %s", VISITS_FILE, exc)
        return 0


def write_visits_to_file(value: int) -> None:
    VISITS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = VISITS_FILE.with_name(f"{VISITS_FILE.name}.tmp")
    tmp_file.write_text(f"{value}\n", encoding="utf-8")
    os.replace(tmp_file, VISITS_FILE)


def load_json_config() -> dict | None:
    try:
        if not APP_CONFIG_FILE.exists():
            return None
        return json.loads(APP_CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Could not load app config %s: %s", APP_CONFIG_FILE, exc)
        return {"error": "invalid_config", "path": str(APP_CONFIG_FILE)}


def get_current_visits() -> int:
    with VISITS_LOCK:
        return VISITS_COUNT


def increment_visits() -> int:
    global VISITS_COUNT
    with VISITS_LOCK:
        VISITS_COUNT += 1
        write_visits_to_file(VISITS_COUNT)
        return VISITS_COUNT


# ---------------------------------------------------------
# Startup
# ---------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    global VISITS_COUNT
    ensure_storage()
    with VISITS_LOCK:
        VISITS_COUNT = read_visits_from_file()
    logger.info("Visits counter loaded: %s", VISITS_COUNT)


# ---------------------------------------------------------
# Error handlers
# ---------------------------------------------------------
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    logger.warning("404 Not Found: %s", request.url)
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "Endpoint does not exist",
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error("500 Internal Server Error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        },
    )


# ---------------------------------------------------------
# Middleware
# ---------------------------------------------------------
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    http_requests_in_progress.inc()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration = time.time() - start_time
        http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=str(status_code),
        ).inc()

        http_request_duration.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(duration)

        http_requests_in_progress.dec()


# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------
@app.get("/")
async def main(request: Request):
    logger.info("Received request: %s %s", request.method, request.url.path)

    visits = increment_visits()
    uptime = get_uptime()
    config_file = load_json_config()

    return {
        "service": {
            "name": APP_NAME,
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "FastAPI",
        },
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "persistence": {
            "visits": visits,
            "visits_file": str(VISITS_FILE),
            "data_dir": str(DATA_DIR),
        },
        "configuration": {
            "env": {
                "APP_NAME": APP_NAME,
                "APP_ENV": APP_ENV,
                "LOG_LEVEL": LOG_LEVEL,
                "DATA_DIR": str(DATA_DIR),
                "VISITS_FILE": str(VISITS_FILE),
                "APP_CONFIG_FILE": str(APP_CONFIG_FILE),
            },
            "file": config_file,
        },
        "request": {
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "method": request.method,
            "path": request.url.path,
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information and visit counter"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/visits", "method": "GET", "description": "Current visit count"},
            {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
        ],
    }


@app.get("/health")
async def health():
    uptime = get_uptime()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime["seconds"],
    }


@app.get("/visits")
async def visits():
    return {
        "visits": get_current_visits(),
        "visits_file": str(VISITS_FILE),
    }


@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# ---------------------------------------------------------
# Application entrypoint
# ---------------------------------------------------------
if __name__ == "__main__":
    logger.info("Running on %s:%s (debug=%s)", HOST, PORT, DEBUG)
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        reload=DEBUG,
    )