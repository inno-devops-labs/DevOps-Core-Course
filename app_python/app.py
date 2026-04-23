"""
DevOps Info Service (Lab 1)
FastAPI implementation.
"""

import json
import logging
import os
import platform
import socket
import time
from pathlib import Path
from threading import Lock
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.exceptions import HTTPException as StarletteHTTPException

# -------------------------
# Configuration (env vars)
# -------------------------
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_FORMAT = os.getenv("LOG_FORMAT", "text")  # "json" for structured logging
VISITS_FILE = os.getenv("VISITS_FILE", "./data/visits")


# -------------------------
# JSON Log Formatter
# -------------------------
class JSONFormatter(logging.Formatter):
    """Outputs log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


# -------------------------
# Logging
# -------------------------
_log_level = logging.DEBUG if DEBUG else logging.INFO
_handler = logging.StreamHandler()

if LOG_FORMAT == "json":
    _handler.setFormatter(JSONFormatter())
else:
    _handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

logging.basicConfig(level=_log_level, handlers=[_handler])
logger = logging.getLogger("devops-info-service")

# -------------------------
# App + runtime state
# -------------------------
app = FastAPI(title="DevOps Info Service", version="1.0.0")
START_TIME = datetime.now(timezone.utc)

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method", "endpoint"],
)

ENDPOINT_CALLS = Counter(
    "devops_info_endpoint_calls_total",
    "Total endpoint calls in devops info service",
    ["endpoint"],
)

SYSTEM_INFO_DURATION_SECONDS = Histogram(
    "devops_info_system_collection_seconds",
    "System info collection duration in seconds",
)

VISITS_LOCK = Lock()


def read_visits() -> int:
    visits_path = Path(VISITS_FILE)
    try:
        raw_value = visits_path.read_text(encoding="utf-8").strip()
        return int(raw_value) if raw_value else 0
    except FileNotFoundError:
        return 0
    except ValueError:
        logger.warning("Invalid visits counter content in %s, resetting to 0", visits_path)
        return 0


def write_visits(value: int) -> int:
    visits_path = Path(VISITS_FILE)
    visits_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = visits_path.with_name(f"{visits_path.name}.tmp")
    tmp_path.write_text(str(value), encoding="utf-8")
    tmp_path.replace(visits_path)
    return value


def increment_visits() -> int:
    with VISITS_LOCK:
        visits = read_visits() + 1
        return write_visits(visits)


def iso_utc_now() -> str:
    # Example desired format: 2026-01-07T14:30:00.000Z
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def get_uptime() -> dict:
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {"seconds": seconds, "human": f"{hours} hours, {minutes} minutes"}


def get_platform_version() -> str:
    # Try to get something user-friendly on Linux (e.g., "Ubuntu 24.04").
    if hasattr(platform, "freedesktop_os_release"):
        try:
            data = platform.freedesktop_os_release()
            pretty = data.get("PRETTY_NAME")
            if pretty:
                return pretty
        except Exception:
            pass
    # Fallback for other OSes.
    return platform.platform()


def get_system_info() -> dict:
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": get_platform_version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 1,
        "python_version": platform.python_version(),
    }


@app.on_event("startup")
async def initialize_visits_counter() -> None:
    with VISITS_LOCK:
        current_visits = read_visits()
        write_visits(current_visits)
    logger.info("Visits counter initialized at %d in %s", current_visits, VISITS_FILE)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={"error": "Not Found", "message": "Endpoint does not exist"},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP Error", "message": exc.detail},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": "An unexpected error occurred"},
    )


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    method = request.method
    endpoint = request.url.path
    start = time.perf_counter()
    status_code = 500

    HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration_seconds = time.perf_counter() - start
        HTTP_REQUESTS_TOTAL.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code),
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code),
        ).observe(duration_seconds)
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    response = await call_next(request)
    logger.info(
        "method=%s path=%s status=%d client=%s",
        request.method,
        request.url.path,
        response.status_code,
        client_ip,
    )
    return response


@app.get("/")
async def index(request: Request) -> dict:
    ENDPOINT_CALLS.labels(endpoint="/").inc()
    visits = increment_visits()
    uptime = get_uptime()
    with SYSTEM_INFO_DURATION_SECONDS.time():
        system_info = get_system_info()

    return {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "FastAPI",
        },
        "system": system_info,
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": iso_utc_now(),
            "timezone": "UTC",
        },
        "request": {
            "client_ip": (request.client.host if request.client else None),
            "user_agent": request.headers.get("user-agent"),
            "method": request.method,
            "path": request.url.path,
        },
        "stats": {
            "visits": visits,
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/visits", "method": "GET", "description": "Current visits count"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
        ],
    }


@app.get("/visits")
async def visits() -> dict:
    ENDPOINT_CALLS.labels(endpoint="/visits").inc()
    with VISITS_LOCK:
        return {"visits": read_visits()}


@app.get("/health")
async def health() -> dict:
    ENDPOINT_CALLS.labels(endpoint="/health").inc()
    uptime = get_uptime()
    return {
        "status": "healthy",
        "timestamp": iso_utc_now(),
        "uptime_seconds": uptime["seconds"],
    }


@app.get("/metrics")
async def metrics() -> Response:
    ENDPOINT_CALLS.labels(endpoint="/metrics").inc()
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    logger.info("Starting app on %s:%s (debug=%s)", HOST, PORT, DEBUG)
    uvicorn.run(app, host=HOST, port=PORT, reload=DEBUG)