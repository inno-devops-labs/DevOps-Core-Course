"""
DevOps Info Service
FastAPI web application providing system and runtime information.
"""

import os
import socket
import platform
import logging
import sys
from datetime import datetime, timezone
import time

from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, Request
from pythonjsonlogger import jsonlogger
import uvicorn


HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))


# Configure JSON logging
logger = logging.getLogger("devops-info-service")
logger.setLevel(logging.INFO)
logger.handlers.clear()

log_handler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(message)s %(method)s %(path)s %(client_ip)s %(status_code)s"
)
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)
logger.propagate = False

# Prometheus metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
)

DEVOPS_INFO_ENDPOINT_CALLS_TOTAL = Counter(
    "devops_info_endpoint_calls_total",
    "Total endpoint calls in DevOps Info Service",
    ["endpoint"],
)

DEVOPS_INFO_SYSTEM_COLLECTION_SECONDS = Histogram(
    "devops_info_system_collection_seconds",
    "System information collection duration in seconds",
)

START_TIME = datetime.now(timezone.utc)
app = FastAPI(title="DevOps Info Service")

logger.info(
    "Application initialized",
    extra={
        "method": "",
        "path": "",
        "client_ip": "",
        "status_code": "",
    },
)


def get_uptime():
    """Calculate application uptime."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return seconds, f"{hours} hours, {minutes} minutes"

def normalize_endpoint(path: str) -> str:
    if path in ["/", "/health", "/metrics"]:
        return path
    return "other"

def get_system_info():
    """Collect system information."""
    start = time.time()

    info = {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.release(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }

    DEVOPS_INFO_SYSTEM_COLLECTION_SECONDS.observe(time.time() - start)
    return info


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every HTTP request in JSON format and collect Prometheus metrics."""
    endpoint = normalize_endpoint(request.url.path)
    method = request.method

    HTTP_REQUESTS_IN_PROGRESS.inc()
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint=endpoint).inc()

    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    status = str(response.status_code)

    HTTP_REQUESTS_TOTAL.labels(
        method=method,
        endpoint=endpoint,
        status=status,
    ).inc()

    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=method,
        endpoint=endpoint,
    ).observe(duration)

    HTTP_REQUESTS_IN_PROGRESS.dec()

    logger.info(
        "HTTP request processed",
        extra={
            "method": method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "",
            "status_code": response.status_code,
        },
    )

    return response


@app.get("/")
async def index(request: Request):
    """Main endpoint returning service and system information."""
    uptime_seconds, uptime_human = get_uptime()

    return {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "FastAPI",
        },
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": uptime_seconds,
            "uptime_human": uptime_human,
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "request": {
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "method": request.method,
            "path": request.url.path,
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
        ],
    }


@app.get("/health")
async def health():
    """Health check endpoint for monitoring."""
    uptime_seconds, _ = get_uptime()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_seconds,
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.exception_handler(404)
async def not_found(request: Request, exc):
    """Handle 404 errors."""
    logger.warning(
        "Endpoint not found",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "",
            "status_code": 404,
        },
    )
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "message": "Endpoint does not exist"},
    )


@app.exception_handler(500)
async def internal_error(request: Request, exc):
    """Handle unexpected server errors."""
    logger.error(
        "Internal server error",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "",
            "status_code": 500,
        },
    )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": "An unexpected error occurred"},
    )


if __name__ == "__main__":
    logger.info(
        "Starting server",
        extra={
            "method": "",
            "path": "",
            "client_ip": "",
            "status_code": "",
        },
    )
    uvicorn.run(app, host=HOST, port=PORT)
