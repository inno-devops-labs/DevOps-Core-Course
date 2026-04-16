"""
DevOps Info Service - FastAPI Application

A web service that provides comprehensive information about itself
and its runtime environment.
"""

import json
import os
import platform
import re
import socket
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.exceptions import HTTPException as StarletteHTTPException

# Application start time for uptime calculation
start_time = datetime.now(timezone.utc)

# Initialize FastAPI app
app = FastAPI(
    title="DevOps Info Service",
    description="A service providing system and runtime information",
    version="1.0.0",
)

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
    ["method", "endpoint"],
)
endpoint_calls = Counter(
    "devops_info_endpoint_calls_total",
    "Total endpoint calls for business paths",
    ["endpoint"],
)
system_info_duration = Histogram(
    "devops_info_system_collection_seconds",
    "System information collection duration in seconds",
)

# Persistence paths (Lab 12)
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
VISITS_PATH = DATA_DIR / "visits"

# Config file mount (Lab 12)
CONFIG_PATH = Path(os.getenv("CONFIG_PATH", "/config/config.json"))

_visits_lock = threading.Lock()
_visits_count = 0


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=str(path.parent), delete=False
    ) as tmp:
        tmp.write(content)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def _read_visits_from_disk() -> int:
    try:
        raw = VISITS_PATH.read_text(encoding="utf-8").strip()
        return int(raw) if raw else 0
    except FileNotFoundError:
        return 0
    except (ValueError, OSError):
        return 0


def _write_visits_to_disk(value: int) -> None:
    _atomic_write_text(VISITS_PATH, f"{value}\n")


def _load_app_config() -> Dict[str, Any]:
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, OSError):
        return {}


app_config: Dict[str, Any] = {}


@app.on_event("startup")
def _startup_load_state() -> None:
    global _visits_count, app_config
    app_config = _load_app_config()
    _visits_count = _read_visits_from_disk()


def normalize_endpoint(path: str) -> str:
    """Normalize path labels to keep metric cardinality bounded."""
    if path in {"/", "/health", "/ready", "/metrics"}:
        return path
    normalized = re.sub(r"/[0-9]+", "/{id}", path)
    normalized = re.sub(
        r"/[0-9a-fA-F]{8}-[0-9a-fA-F-]{27,36}",
        "/{id}",
        normalized,
    )
    return normalized


def get_system_info() -> Dict[str, Any]:
    """
    Get system information.

    Returns:
        Dictionary containing system information
    """
    start = time.perf_counter()
    try:
        return {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.platform(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count() or 0,
            "python_version": platform.python_version(),
        }
    finally:
        system_info_duration.observe(time.perf_counter() - start)


def get_uptime() -> Dict[str, Any]:
    """
    Calculate application uptime.

    Returns:
        Dictionary with uptime in seconds and human-readable format
    """
    delta = datetime.now(timezone.utc) - start_time
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        "seconds": seconds,
        "human": f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}",
    }


@app.middleware("http")
async def record_metrics(request: Request, call_next):
    """Collect RED metrics for every request."""
    method = request.method
    endpoint = normalize_endpoint(request.url.path)
    start = time.perf_counter()
    status_code = "500"
    http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
    try:
        response = await call_next(request)
        status_code = str(response.status_code)
        return response
    finally:
        duration = time.perf_counter() - start
        http_requests_total.labels(
            method=method, endpoint=endpoint, status_code=status_code
        ).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(
            duration
        )
        http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()


@app.get("/")
async def root(request: Request) -> Dict[str, Any]:
    """
    Main endpoint returning comprehensive service information.

    Returns:
        JSON response with service, system, runtime, request, and endpoints info
    """
    endpoint_calls.labels(endpoint="/").inc()
    global _visits_count
    with _visits_lock:
        _visits_count += 1
        try:
            _write_visits_to_disk(_visits_count)
        except OSError:
            # If persistence is misconfigured, keep serving responses; /visits will still
            # reflect in-memory value for this process.
            pass
    uptime = get_uptime()
    system_info = get_system_info()

    # Get request information
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    method = request.method
    path = request.url.path

    return {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "FastAPI",
        },
        "config": {
            "app_name": app_config.get("app_name", "devops-info-service"),
            "environment": app_config.get("environment", os.getenv("APP_ENV", "dev")),
            "feature_flags": app_config.get("feature_flags", {}),
        },
        "system": system_info,
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "timezone": "UTC",
        },
        "request": {
            "client_ip": client_ip,
            "user_agent": user_agent,
            "method": method,
            "path": path,
        },
        "visits": {"count": _visits_count},
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/visits", "method": "GET", "description": "Visits counter"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/ready", "method": "GET", "description": "Readiness probe"},
            {
                "path": "/docs",
                "method": "GET",
                "description": "Interactive API documentation",
            },
            {
                "path": "/redoc",
                "method": "GET",
                "description": "Alternative API documentation",
            },
            {"path": "/openapi.json", "method": "GET", "description": "OpenAPI schema"},
            {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
        ],
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring.

    Returns:
        JSON response with health status, timestamp, and uptime
    """
    endpoint_calls.labels(endpoint="/health").inc()
    uptime = get_uptime()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "uptime_seconds": uptime["seconds"],
    }


@app.get("/ready")
async def ready() -> Dict[str, str]:
    """Lightweight readiness for Kubernetes (traffic only when OK)."""
    endpoint_calls.labels(endpoint="/ready").inc()
    return {"status": "ready"}


@app.get("/visits")
async def visits() -> Dict[str, int]:
    global _visits_count
    with _visits_lock:
        # Reconcile with disk in case the file was updated before this process started.
        disk_value = _read_visits_from_disk()
        if disk_value > _visits_count:
            _visits_count = disk_value
        return {"visits": _visits_count}


@app.get("/metrics")
async def metrics() -> Response:
    endpoint_calls.labels(endpoint="/metrics").inc()
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with JSON responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if exc.status_code != 404 else "Not Found",
            "message": (
                exc.detail
                if exc.status_code != 404
                else f"Path {request.url.path} not found"
            ),
            "path": request.url.path,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with JSON responses."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "Invalid request data",
            "details": exc.errors(),
        },
    )


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "False").lower() == "true"

    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=debug,
        log_level="debug" if debug else "info",
    )
