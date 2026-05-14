import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
import uvicorn
from pythonjsonlogger.json import JsonFormatter
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

from core.runtime import set_start_time
from routes.router import api_router
from config import settings
import logging

SERVICE_TITLE = "devops-info-service"
SERVICE_VERSION = "1.0.0"
SERVICE_DESCRIPTION = "DevOps course info service"
SERVICE_FRAMEWORK = "FastAPI"

LOG_FORMAT = os.getenv("LOG_FORMAT", "json")

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
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
    "Time to collect system info",
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

if LOG_FORMAT == "json":
    handler = logging.StreamHandler()
    formatter = JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
    handler.setFormatter(formatter)
    logger.handlers = [handler]

    for uv_logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        uv_logger = logging.getLogger(uv_logger_name)
        uv_logger.handlers = [handler]
else:
    from colorlog import ColoredFormatter

    handler = logging.StreamHandler()
    formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )
    handler.setFormatter(formatter)
    logger.handlers = [handler]


@asynccontextmanager
async def lifespan(app: FastAPI):
    set_start_time()
    logging.info(
        "Application started",
        extra={
            "event": "startup",
            "service": SERVICE_TITLE,
            "version": SERVICE_VERSION,
        },
    )
    yield
    logging.info("Application stopped", extra={"event": "shutdown"})


app = FastAPI(
    title=SERVICE_TITLE,
    version=SERVICE_VERSION,
    description=SERVICE_DESCRIPTION,
    lifespan=lifespan,
)


@app.middleware("http")
async def log_and_track_requests(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)

    http_requests_in_progress.inc()
    start = time.time()

    response = await call_next(request)

    duration = time.time() - start
    duration_ms = round(duration * 1000, 2)

    endpoint = request.url.path or "/"
    method = request.method
    status = str(response.status_code)

    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    http_requests_in_progress.dec()
    devops_info_endpoint_calls.labels(endpoint=endpoint).inc()

    logging.info(
        "HTTP request",
        extra={
            "event": "http_request",
            "method": method,
            "path": endpoint,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "client_ip": request.client.host if request.client else "unknown",
        },
    )
    return response


@app.get("/metrics", include_in_schema=False)
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(api_router)


if __name__ == "__main__":
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
