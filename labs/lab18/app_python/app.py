#!/usr/bin/env python3
from fastapi import FastAPI, Request
from datetime import datetime, timezone
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
import platform
import socket
import os
import logging
import sys
import json

DATA_DIR = "/tmp/app-data"
DATA_FILE = f"{DATA_DIR}/visits"
os.makedirs(DATA_DIR, exist_ok=True)

def read_visits():
    try:
        with open(DATA_FILE, "r") as f:
            return int(f.read())
    except:
        return 0


def write_visits(count: int):
    with open(DATA_FILE, "w") as f:
        f.write(str(count))


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "taskName",
            ):
                log_entry[key] = value
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)

app = FastAPI()
START_TIME = datetime.now(timezone.utc)

# Prometheus Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress", "HTTP requests currently being processed"
)

devops_info_endpoint_calls = Counter(
    "devops_info_endpoint_calls_total", "Calls per endpoint", ["endpoint"]
)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

logger.info(f"Application starting - Host: {HOST}, Port: {PORT}")


def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    secs = int(delta.total_seconds())
    hrs = secs // 3600
    mins = (secs % 3600) // 60
    return {"seconds": secs, "human": f"{hrs} hours, {mins} minutes"}


@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI application startup complete")
    logger.info(f"Python version: {platform.python_version()}")
    logger.info(f"Platform: {platform.system()} {platform.platform()}")
    logger.info(f"Hostname: {socket.gethostname()}")


@app.on_event("shutdown")
async def shutdown_event():
    uptime = get_uptime()
    logger.info(f"Application shutting down. Total uptime: {uptime['human']}")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now(timezone.utc)
    client_ip = request.client.host if request.client else "unknown"

    # Normalize endpoint (avoid high cardinality)
    endpoint = request.url.path

    http_requests_in_progress.inc()
    logger.info(
        f"Request started: {request.method} {endpoint} from {client_ip}"
    )

    try:
        response = await call_next(request)
        process_time = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds()

        # Record metrics
        http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=str(response.status_code),
        ).inc()

        http_request_duration_seconds.labels(
            method=request.method, endpoint=endpoint
        ).observe(process_time)

        devops_info_endpoint_calls.labels(endpoint=endpoint).inc()

        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "path": endpoint,
                "status_code": response.status_code,
                "client_ip": client_ip,
                "duration_seconds": round(process_time, 3),
            },
        )

        response.headers["X-Process-Time"] = str(process_time)
        return response

    except Exception as e:
        process_time = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds()
        http_requests_total.labels(
            method=request.method, endpoint=endpoint, status_code="500"
        ).inc()
        logger.error(
            "Request failed",
            extra={
                "method": request.method,
                "path": endpoint,
                "client_ip": client_ip,
                "duration_seconds": round(process_time, 3),
                "error": str(e),
            },
        )
        raise
    finally:
        http_requests_in_progress.dec()


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
def root(request: Request):
    visits = read_visits() + 1
    write_visits(visits)

    logger.debug("Home endpoint called")
    uptime = get_uptime()
    return {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
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
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "request": {
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "method": request.method,
            "path": request.url.path,
        },
        "endpoints": [
            {
                "path": "/",
                "method": "GET",
                "description": "Service information",
            },
            {
                "path": "/health",
                "method": "GET",
                "description": "Health check",
            },
        ],
    }


@app.get("/health")
def health():
    logger.debug("Health check endpoint called")
    uptime = get_uptime()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime["seconds"],
    }

@app.get("/visits")
def get_visits():
    return {"visits": read_visits()}

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
):
    client = request.client.host if request.client else "unknown"
    logger.warning(
        "HTTP exception",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "client_ip": client,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    client = request.client.host if request.client else "unknown"
    logger.error(
        "Unhandled exception",
        extra={
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "client_ip": client,
        },
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "path": request.url.path,
        },
    )


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting Uvicorn server on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)