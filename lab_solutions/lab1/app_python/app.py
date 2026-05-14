import os
import logging
import json
import platform
import socket
import sys
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import Response
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST, REGISTRY


HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
logger.propagate = False


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for Loki-friendly structured logging."""

    standard_keys = {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key not in self.standard_keys and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    root_logger.addHandler(handler)

    logger.handlers.clear()
    logger.addHandler(handler)


setup_logging()


START_TIME = datetime.now(timezone.utc)


# Prometheus Metrics - wrapped in try-except for reload safety
def _get_or_create_metric(metric_class, name, documentation, labelnames=None, **kwargs):
    """Get existing metric from registry or create new one."""
    # Check if metric already exists
    for collector in list(REGISTRY._collector_to_names.keys()):
        if hasattr(collector, '_name') and collector._name == name:
            return collector
    # Create new metric
    if labelnames:
        return metric_class(name, documentation, labelnames, **kwargs)
    return metric_class(name, documentation, **kwargs)


http_requests_total = _get_or_create_metric(
    Counter,
    "http_requests_total",
    "Total HTTP requests",
    labelnames=["method", "endpoint", "status"],
)

http_request_duration_seconds = _get_or_create_metric(
    Histogram,
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    labelnames=["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
)

http_requests_in_progress = _get_or_create_metric(
    Gauge,
    "http_requests_in_progress",
    "HTTP requests currently being processed",
)


app = FastAPI(title="DevOps Info Service", version="1.0.0")


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
        "platform_version": platform.platform(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 0,
        "python_version": platform.python_version(),
    }


def get_request_info(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    return {
        "client_ip": client_ip,
        "user_agent": user_agent,
        "method": request.method,
        "path": request.url.path,
    }


def get_runtime_info():
    now = datetime.now(timezone.utc)
    return {
        "uptime_seconds": get_uptime()["seconds"],
        "uptime_human": get_uptime()["human"],
        "current_time": now.isoformat().replace("+00:00", "Z"),
        "timezone": now.tzname() or "UTC",
    }


@app.on_event("startup")
async def on_startup():
    logger.info(
        "application_startup",
        extra={"host": HOST, "port": PORT, "debug": DEBUG, "service": "devops-info-service"},
    )


@app.middleware("http")
async def log_and_track_requests(request: Request, call_next):
    started_at = datetime.now(timezone.utc)
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    endpoint = request.url.path

    http_requests_in_progress.inc()

    try:
        response: Response = await call_next(request)
    except Exception:
        elapsed_ms = int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)
        logger.exception(
            "request_failed",
            extra={
                "method": request.method,
                "path": endpoint,
                "client_ip": client_ip,
                "status_code": 500,
            },
        )
        http_requests_total.labels(method=request.method, endpoint=endpoint, status="500").inc()
        http_request_duration_seconds.labels(method=request.method, endpoint=endpoint).observe(
            time.time() - start_time
        )
        http_requests_in_progress.dec()
        raise

    elapsed_ms = int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)
    elapsed_seconds = time.time() - start_time

    logger.info(
        "request_completed",
        extra={
            "method": request.method,
            "path": endpoint,
            "status_code": response.status_code,
            "client_ip": client_ip,
            "duration_ms": elapsed_ms,
        },
    )

    # Record metrics
    http_requests_total.labels(
        method=request.method, endpoint=endpoint, status=response.status_code
    ).inc()
    http_request_duration_seconds.labels(method=request.method, endpoint=endpoint).observe(
        elapsed_seconds
    )
    http_requests_in_progress.dec()

    return response


@app.get("/")
async def index(request: Request):
    return {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "FastAPI",
        },
        "system": get_system_info(),
        "runtime": get_runtime_info(),
        "request": get_request_info(request),
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
        ],
    }


@app.get("/health")
async def health():
    now = datetime.now(timezone.utc)
    return {
        "status": "healthy",
        "timestamp": now.isoformat().replace("+00:00", "Z"),
        "uptime_seconds": get_uptime()["seconds"],
    }


@app.get("/error")
async def error_endpoint():
    """Test endpoint that intentionally raises an error for log testing."""
    raise ValueError("This is a deliberate test error for logging purposes")


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn

    logger.info(
        "starting_application",
        extra={"host": HOST, "port": PORT, "debug": DEBUG},
    )
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="debug" if DEBUG else "info",
    )
