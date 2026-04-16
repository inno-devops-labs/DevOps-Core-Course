import json
import logging
import multiprocessing
import os
import platform
import socket
import time
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from pythonjsonlogger import jsonlogger

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)
_handler = logging.StreamHandler()
_handler.setFormatter(
    jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
)
logger.addHandler(_handler)

# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
)

# Application-specific metrics
endpoint_calls = Counter(
    "devops_info_endpoint_calls_total",
    "Total calls per endpoint",
    ["endpoint"],
)

system_info_duration = Histogram(
    "devops_info_system_collection_seconds",
    "Time spent collecting system info",
)

# ---------------------------------------------------------------------------

app = FastAPI()
START = datetime.now(timezone.utc)

# Visit counter initialization
VISITS_FILE = "/data/visits"
VISITS_DIR = Path("/data")


def get_visits_count():
    try:
        if Path(VISITS_FILE).exists():
            with open(VISITS_FILE, "r") as f:
                return int(f.read().strip())
    except Exception as e:
        logger.warning("Failed to read visits file", extra={"error": str(e)})
    return 0


def increment_visits():
    try:
        VISITS_DIR.mkdir(parents=True, exist_ok=True)
        count = get_visits_count() + 1
        with open(VISITS_FILE, "w") as f:
            f.write(str(count))
        return count
    except Exception as e:
        logger.warning("Failed to increment visits", extra={"error": str(e)})
        return 0


def uptime():
    s = int((datetime.now(timezone.utc) - START).total_seconds())
    h = s // 3600
    m = (s % 3600) // 60
    return s, f"{h} hours, {m} minutes"


def system_info():
    t0 = time.perf_counter()
    info = {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": multiprocessing.cpu_count(),
        "python_version": platform.python_version(),
    }
    system_info_duration.observe(time.perf_counter() - t0)
    return info


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    # Skip the /metrics endpoint itself to avoid noise
    if request.url.path == "/metrics":
        return await call_next(request)

    endpoint = request.url.path
    method = request.method

    http_requests_in_progress.inc()
    t0 = time.perf_counter()
    try:
        response = await call_next(request)
        status_code = str(response.status_code)
    except Exception:
        status_code = "500"
        raise
    finally:
        duration = time.perf_counter() - t0
        http_requests_in_progress.dec()
        http_requests_total.labels(
            method=method, endpoint=endpoint, status_code=status_code
        ).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(
            duration
        )

    logger.info(
        "http request",
        extra={
            "client_ip": request.client.host if request.client else "unknown",
            "method": method,
            "path": endpoint,
            "status_code": response.status_code,
            "duration_seconds": round(duration, 4),
        },
    )
    return response


@app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/", response_class=JSONResponse)
async def index(request: Request):
    endpoint_calls.labels(endpoint="/").inc()
    increment_visits()
    s, h = uptime()
    return {
        "service": {
            "name": os.getenv("SERVICE_NAME", "devops-info-service"),
            "version": os.getenv("SERVICE_VERSION", "1.0.0"),
            "description": os.getenv(
                "SERVICE_DESCRIPTION", "DevOps course info service"
            ),
            "framework": "FastAPI",
        },
        "system": system_info(),
        "runtime": {
            "uptime_seconds": s,
            "uptime_human": h,
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "request": {
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent", ""),
            "method": request.method,
            "path": request.url.path,
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/visits", "method": "GET", "description": "Visit count"},
            {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
        ],
    }


@app.get("/health", response_class=JSONResponse)
async def health():
    endpoint_calls.labels(endpoint="/health").inc()
    s, _ = uptime()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": s,
    }


@app.get("/visits", response_class=JSONResponse)
async def visits():
    endpoint_calls.labels(endpoint="/visits").inc()
    count = get_visits_count()
    return {
        "visits": count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port)
