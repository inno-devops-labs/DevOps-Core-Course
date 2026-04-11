"""
DevOps Info Service
FastAPI application module.
"""

from __future__ import annotations

import json
import logging
import os
import platform
import socket
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.exceptions import HTTPException as StarletteHTTPException

_prometheus_registry = CollectorRegistry()

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
    registry=_prometheus_registry,
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=_prometheus_registry,
)
http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    registry=_prometheus_registry,
)
devops_info_endpoint_calls = Counter(
    "devops_info_endpoint_calls",
    "Endpoint calls for DevOps info service",
    ["endpoint"],
    registry=_prometheus_registry,
)
devops_info_system_collection_seconds = Histogram(
    "devops_info_system_collection_seconds",
    "System info collection time in seconds",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1),
    registry=_prometheus_registry,
)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
VISITS_FILE = os.getenv("VISITS_FILE", "/data/visits")

SERVICE_NAME = "devops-info-service"
SERVICE_VERSION = "1.0.0"
SERVICE_DESCRIPTION = "DevOps course info service"
SERVICE_FRAMEWORK = "FastAPI"

START_TIME = datetime.now(timezone.utc)

logger = logging.getLogger("devops-info-service")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.handlers = [handler]

app = FastAPI(
    title="DevOps Info Service",
    version=SERVICE_VERSION,
    description=SERVICE_DESCRIPTION,
)

_visits_lock = threading.Lock()


def _read_count_unlocked() -> int:
    path = Path(VISITS_FILE)
    if not path.is_file():
        return 0
    try:
        raw = path.read_text(encoding="utf-8").strip()
        return max(0, int(raw))
    except (ValueError, OSError):
        return 0


def _write_count_atomic(n: int) -> None:
    path = Path(VISITS_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(str(n))
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def increment_visits() -> int:
    with _visits_lock:
        n = _read_count_unlocked() + 1
        _write_count_atomic(n)
        return n


def get_visits() -> int:
    with _visits_lock:
        return _read_count_unlocked()


def _format_uptime(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    hour_label = "hour" if hours == 1 else "hours"
    minute_label = "minute" if minutes == 1 else "minutes"
    return f"{hours} {hour_label}, {minutes} {minute_label}"


def get_uptime() -> dict[str, int | str]:
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    return {
        "seconds": seconds,
        "human": _format_uptime(seconds),
    }


def get_system_info() -> dict[str, str | int]:
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.release(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 0,
        "python_version": platform.python_version(),
    }


def isoformat_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_endpoint(path: str) -> str:
    if path in ("/", "/health", "/metrics", "/visits"):
        return path
    return "other"


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    start_perf = time.perf_counter()
    endpoint = _normalize_endpoint(request.url.path)
    http_requests_in_progress.inc()
    req_ts = datetime.now(timezone.utc)
    logger.info(
        json.dumps(
            {
                "timestamp": isoformat_utc(req_ts),
                "level": "INFO",
                "service": SERVICE_NAME,
                "event": "request",
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
            }
        )
    )
    try:
        response = await call_next(request)
        status = str(response.status_code)
        http_requests_total.labels(
            method=request.method, endpoint=endpoint, status=status
        ).inc()
        http_request_duration_seconds.labels(
            method=request.method, endpoint=endpoint
        ).observe(time.perf_counter() - start_perf)
        logger.info(
            json.dumps(
                {
                    "timestamp": isoformat_utc(datetime.now(timezone.utc)),
                    "level": "INFO",
                    "service": SERVICE_NAME,
                    "event": "response",
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "client_ip": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown"),
                }
            )
        )
        return response
    finally:
        http_requests_in_progress.dec()


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={
                "error": "Not Found",
                "message": "Endpoint does not exist",
            },
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(
        json.dumps(
            {
                "timestamp": isoformat_utc(datetime.now(timezone.utc)),
                "level": "ERROR",
                "service": SERVICE_NAME,
                "event": "exception",
                "method": request.method,
                "path": request.url.path,
                "error": str(exc),
            }
        )
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        },
    )


@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(_prometheus_registry),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/visits")
async def visits():
    devops_info_endpoint_calls.labels(endpoint="/visits").inc()
    total = get_visits()
    return {"visits": total, "file": VISITS_FILE}


@app.get("/")
async def root(request: Request):
    devops_info_endpoint_calls.labels(endpoint="/").inc()
    visit_total = increment_visits()
    t0 = time.perf_counter()
    sys_info = get_system_info()
    devops_info_system_collection_seconds.observe(time.perf_counter() - t0)
    uptime = get_uptime()
    now = datetime.now(timezone.utc)

    response = {
        "service": {
            "name": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "description": SERVICE_DESCRIPTION,
            "framework": SERVICE_FRAMEWORK,
        },
        "system": sys_info,
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": isoformat_utc(now),
            "timezone": "UTC",
        },
        "visits": {
            "total": visit_total,
            "file": VISITS_FILE,
        },
        "request": {
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "method": request.method,
            "path": request.url.path,
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/visits", "method": "GET", "description": "Visit counter (read-only)"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
        ],
    }

    return response


@app.get("/health")
async def health():
    devops_info_endpoint_calls.labels(endpoint="/health").inc()
    uptime = get_uptime()
    return {
        "status": "healthy",
        "timestamp": isoformat_utc(datetime.now(timezone.utc)),
        "uptime_seconds": uptime["seconds"],
    }


if __name__ == "__main__":
    logger.info("Starting DevOps Info Service on %s:%s", HOST, PORT)
    uvicorn.run("app:app", host=HOST, port=PORT, reload=DEBUG, log_level="info")
