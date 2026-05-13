import json
import os
import platform
import socket
import time
import logging
from pathlib import Path
from threading import Lock
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)


class JSONFormatter(logging.Formatter):
    """Outputs each log record as a single-line JSON object for log aggregation."""

    def format(self, record):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for attr in ("method", "path", "status_code", "client_ip", "duration_ms"):
            value = getattr(record, attr, None)
            if value is not None:
                entry[attr] = value
        if record.exc_info and record.exc_info[0] is not None:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry)


_json_handler = logging.StreamHandler()
_json_handler.setFormatter(JSONFormatter())
logging.root.handlers = [_json_handler]
logging.root.setLevel(logging.INFO)

for _name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
    _uv = logging.getLogger(_name)
    _uv.handlers = [_json_handler]
    _uv.propagate = False

logger = logging.getLogger(__name__)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
VISITS_FILE = os.getenv("VISITS_FILE", "data/visits")
CONFIG_FILE = os.getenv("CONFIG_FILE", "/config/config.json")

START_TIME = datetime.now(timezone.utc)

# ---------------------------------------------------------------------------
# Prometheus metrics (RED method: Rate, Errors, Duration)
# ---------------------------------------------------------------------------
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
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

devops_info_endpoint_calls = Counter(
    "devops_info_endpoint_calls",
    "Endpoint calls by endpoint name",
    ["endpoint"],
)

devops_info_system_collection_seconds = Histogram(
    "devops_info_system_collection_seconds",
    "Time spent collecting system information",
)

_KNOWN_ENDPOINTS = frozenset({"/", "/health", "/metrics", "/visits"})


class VisitCounter:
    """Simple file-backed counter with process-level locking."""

    def __init__(self, file_path: str):
        self.path = Path(file_path)
        self.lock = Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read_unlocked(self) -> int:
        if not self.path.exists():
            return 0
        content = self.path.read_text(encoding="utf-8").strip()
        if not content:
            return 0
        try:
            return int(content)
        except ValueError:
            logger.warning("Invalid visits counter content, resetting to 0")
            return 0

    def _write_unlocked(self, value: int) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(str(value), encoding="utf-8")
        os.replace(tmp, self.path)

    def get(self) -> int:
        with self.lock:
            return self._read_unlocked()

    def increment(self) -> int:
        with self.lock:
            current = self._read_unlocked()
            current += 1
            self._write_unlocked(current)
            return current


visit_counter = VisitCounter(VISITS_FILE)


def load_runtime_config() -> dict:
    config_path = Path(CONFIG_FILE)
    if not config_path.exists():
        return {"status": "missing", "path": str(config_path)}

    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.exception("Invalid JSON config at %s", config_path)
        return {"status": "invalid-json", "path": str(config_path)}


def _normalize_endpoint(path: str) -> str:
    """Keep cardinality low by grouping unknown paths."""
    return path if path in _KNOWN_ENDPOINTS else "other"


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


@asynccontextmanager
async def lifespan(_app):
    initial_visits = visit_counter.get()
    logger.info("Application started on %s:%d (debug=%s)", HOST, PORT, DEBUG)
    logger.info("Visits counter initialized from %s with value=%d", VISITS_FILE, initial_visits)
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title="DevOps Info Service",
    description="DevOps course info service",
    version="1.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    endpoint = _normalize_endpoint(request.url.path)

    http_requests_in_progress.inc()
    try:
        response = await call_next(request)
    finally:
        http_requests_in_progress.dec()

    duration = time.time() - start

    http_requests_total.labels(
        method=request.method,
        endpoint=endpoint,
        status=str(response.status_code),
    ).inc()

    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=endpoint,
    ).observe(duration)

    duration_ms = round(duration * 1000, 2)
    logger.info(
        "%s %s %s",
        request.method,
        request.url.path,
        response.status_code,
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "client_ip": request.client.host if request.client else None,
            "duration_ms": duration_ms,
        },
    )
    return response


@app.get("/")
async def root(request: Request):
    devops_info_endpoint_calls.labels(endpoint="/").inc()
    visits = visit_counter.increment()

    with devops_info_system_collection_seconds.time():
        system = get_system_info()

    uptime = get_uptime()
    return {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "FastAPI",
        },
        "system": system,
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
            "visits": visits,
        },
        "config": load_runtime_config(),
        "request": {
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "method": request.method,
            "path": request.url.path,
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
            {"path": "/visits", "method": "GET", "description": "Visits counter"},
        ],
    }


@app.get("/health")
async def health():
    devops_info_endpoint_calls.labels(endpoint="/health").inc()
    uptime = get_uptime()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime["seconds"],
    }


@app.get("/metrics")
async def metrics():
    devops_info_endpoint_calls.labels(endpoint="/metrics").inc()
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/visits")
async def visits():
    devops_info_endpoint_calls.labels(endpoint="/visits").inc()
    return {"visits": visit_counter.get(), "file": VISITS_FILE}


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "message": "Endpoint does not exist"},
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(
        "Internal server error on %s %s",
        request.method,
        request.url.path,
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
        },
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host=HOST, port=PORT, reload=DEBUG)
