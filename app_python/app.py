from __future__ import annotations

import json
import os
import platform
import socket
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, List

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

APP_NAME = os.getenv("APP_NAME", "devops-info-service")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
APP_DESCRIPTION = os.getenv("APP_DESCRIPTION", "DevOps course info service")
VISITS_FILE = Path(os.getenv("VISITS_FILE", "/data/visits"))

START_TIME = time.time()
_VISITS_LOCK = threading.Lock()

app = FastAPI(title=APP_NAME, version=APP_VERSION, description=APP_DESCRIPTION)

REQUEST_COUNT = Counter(
    "app_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "app_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.001, 0.01, 0.05, 0.1, 0.3, 0.5, 1.0, 2.0, 5.0),
)

IN_PROGRESS = Gauge(
    "app_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method", "endpoint"],
)


def _uptime_seconds() -> int:
    return int(time.time() - START_TIME)


def _uptime_human(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours} hours, {minutes} minutes"


def _ensure_visits_file() -> None:
    VISITS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not VISITS_FILE.exists():
        _write_visits_count(0)


def _read_visits_count() -> int:
    try:
        value = VISITS_FILE.read_text(encoding="utf-8").strip()
        return int(value) if value else 0
    except FileNotFoundError:
        return 0
    except ValueError:
        return 0


def _write_visits_count(count: int) -> None:
    VISITS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=VISITS_FILE.parent, delete=False, encoding="utf-8") as tmp:
        tmp.write(str(count))
        tmp_path = Path(tmp.name)
    tmp_path.replace(VISITS_FILE)


def _increment_visits_count() -> int:
    with _VISITS_LOCK:
        current_count = _read_visits_count()
        new_count = current_count + 1
        _write_visits_count(new_count)
        return new_count


@app.on_event("startup")
async def startup_event() -> None:
    _ensure_visits_file()


@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    path = request.url.path
    method = request.method

    if path == "/metrics":
        return await call_next(request)

    IN_PROGRESS.labels(method=method, endpoint=path).inc()
    start_time = perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration = perf_counter() - start_time
        REQUEST_COUNT.labels(
            method=method,
            endpoint=path,
            status_code=str(status_code),
        ).inc()
        REQUEST_LATENCY.labels(
            method=method,
            endpoint=path,
        ).observe(duration)
        IN_PROGRESS.labels(method=method, endpoint=path).dec()


@app.get("/", summary="Service information")
async def root(request: Request) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    uptime = _uptime_seconds()
    visits = _increment_visits_count()

    endpoints: List[Dict[str, str]] = [
        {"path": "/", "method": "GET", "description": "Service information and increment visits counter"},
        {"path": "/visits", "method": "GET", "description": "Current visits counter"},
        {"path": "/health", "method": "GET", "description": "Health check"},
        {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
    ]

    return {
        "service": {
            "name": APP_NAME,
            "version": APP_VERSION,
            "description": APP_DESCRIPTION,
            "framework": "FastAPI",
        },
        "system": {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.platform(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
            "python_version": platform.python_version(),
        },
        "runtime": {
            "uptime_seconds": uptime,
            "uptime_human": _uptime_human(uptime),
            "current_time": now.isoformat(),
            "timezone": "UTC",
        },
        "request": {
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "method": request.method,
            "path": request.url.path,
        },
        "visits": {
            "count": visits,
            "file": str(VISITS_FILE),
        },
        "endpoints": endpoints,
    }


@app.get("/visits", summary="Visits counter")
async def visits() -> Dict[str, Any]:
    return {
        "visits": _read_visits_count(),
        "file": str(VISITS_FILE),
    }


@app.get("/health", summary="Health check")
async def health() -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        "status": "healthy",
        "timestamp": now.isoformat(),
        "uptime_seconds": _uptime_seconds(),
    }


@app.get("/metrics", summary="Prometheus metrics")
async def metrics() -> Response:
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
