"""DevOps Info Service implemented with FastAPI."""

from __future__ import annotations

import json
import logging
import os
import platform
import socket
import sys
import time
import fcntl
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

APP_START = datetime.now(timezone.utc)
SERVICE_NAME = os.getenv("SERVICE_NAME", "devops-info-service")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
SERVICE_DESCRIPTION = os.getenv("SERVICE_DESCRIPTION", "DevOps course info service")
SERVICE_VARIANT = os.getenv("SERVICE_VARIANT", "primary")
VISITS_FILE_PATH = os.getenv("VISITS_FILE_PATH", "/tmp/devops-info-service/visits")
APP_CONFIG_PATH = os.getenv("APP_CONFIG_PATH", "/config/config.json")
KNOWN_ENDPOINTS = frozenset({"/", "/health", "/ready", "/visits", "/metrics"})

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests handled by the service.",
    ["method", "endpoint", "status_code"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["method", "endpoint", "status_code"],
)
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed.",
    ["method", "endpoint"],
)
DEVOPS_INFO_ENDPOINT_CALLS_TOTAL = Counter(
    "devops_info_endpoint_calls_total",
    "Application endpoint invocations.",
    ["endpoint"],
)
DEVOPS_INFO_SYSTEM_INFO_COLLECTION_SECONDS = Histogram(
    "devops_info_system_info_collection_seconds",
    "Time spent collecting system information for the root endpoint.",
)


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per line for Loki."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": SERVICE_NAME,
        }

        for field in (
            "event",
            "method",
            "path",
            "status_code",
            "client_ip",
            "duration_ms",
            "user_agent",
            "host",
            "port",
            "debug",
        ):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True)


class VisitCounter:
    """Persist a simple visits counter to disk for Lab 12."""

    def __init__(self, file_path: str) -> None:
        self.path = Path(file_path)
        self._lock = Lock()
        self._initialize_file()

    def _ensure_parent_directory(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read_count(self, counter_file) -> int:
        counter_file.seek(0)
        raw_value = counter_file.read().strip()
        if not raw_value:
            return 0

        try:
            return int(raw_value)
        except ValueError:
            logger.warning(
                "visits_counter_reset",
                extra={
                    "event": "visits_counter",
                    "path": str(self.path),
                },
            )
            return 0

    def _write_count(self, counter_file, count: int) -> None:
        counter_file.seek(0)
        counter_file.truncate()
        counter_file.write(f"{count}\n")
        counter_file.flush()
        os.fsync(counter_file.fileno())

    def _initialize_file(self) -> None:
        self._ensure_parent_directory()
        with self.path.open("a+", encoding="utf-8") as counter_file:
            fcntl.flock(counter_file.fileno(), fcntl.LOCK_EX)
            count = self._read_count(counter_file)
            self._write_count(counter_file, count)
            fcntl.flock(counter_file.fileno(), fcntl.LOCK_UN)

    def increment(self) -> int:
        with self._lock:
            with self.path.open("r+", encoding="utf-8") as counter_file:
                fcntl.flock(counter_file.fileno(), fcntl.LOCK_EX)
                count = self._read_count(counter_file) + 1
                self._write_count(counter_file, count)
                fcntl.flock(counter_file.fileno(), fcntl.LOCK_UN)
                return count

    def get_count(self) -> int:
        with self._lock:
            with self.path.open("r+", encoding="utf-8") as counter_file:
                fcntl.flock(counter_file.fileno(), fcntl.LOCK_EX)
                count = self._read_count(counter_file)
                fcntl.flock(counter_file.fileno(), fcntl.LOCK_UN)
                return count


def configure_logging() -> logging.Logger:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = True
    logging.getLogger("uvicorn.error").handlers.clear()
    logging.getLogger("uvicorn.error").propagate = True

    return logging.getLogger("devops-info-service")


logger = configure_logging()

app = FastAPI(title=SERVICE_NAME, version=SERVICE_VERSION)
VISIT_COUNTER = VisitCounter(VISITS_FILE_PATH)


def get_uptime() -> dict[str, str | int]:
    """Return uptime in seconds and a human-readable string."""
    delta = datetime.now(timezone.utc) - APP_START
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {"seconds": seconds, "human": f"{hours} hours, {minutes} minutes"}


def get_metric_endpoint(request: Request) -> str:
    """Normalize request paths to stable Prometheus labels."""
    route = request.scope.get("route")
    route_path = getattr(route, "path", None)
    if route_path:
        return route_path
    if request.url.path in KNOWN_ENDPOINTS:
        return request.url.path
    return "unmatched"


def get_service_metadata() -> dict[str, str]:
    """Return service metadata that can be customized per deployment."""
    return {
        "name": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "description": SERVICE_DESCRIPTION,
        "framework": "FastAPI",
        "variant": SERVICE_VARIANT,
    }


def load_app_config() -> dict[str, object]:
    """Load optional JSON configuration from a mounted ConfigMap file."""
    try:
        with Path(APP_CONFIG_PATH).open(encoding="utf-8") as config_file:
            return {
                "path": APP_CONFIG_PATH,
                "loaded": True,
                "values": json.load(config_file),
            }
    except FileNotFoundError:
        return {
            "path": APP_CONFIG_PATH,
            "loaded": False,
            "values": {},
        }
    except json.JSONDecodeError as exc:
        logger.warning(
            "config_file_invalid",
            extra={
                "event": "config_file",
                "path": APP_CONFIG_PATH,
            },
        )
        return {
            "path": APP_CONFIG_PATH,
            "loaded": False,
            "values": {},
            "error": str(exc),
        }


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    in_progress_endpoint = get_metric_endpoint(request)
    client_ip = request.headers.get(
        "x-forwarded-for",
        request.client.host if request.client else "unknown",
    )
    user_agent = request.headers.get("user-agent", "")
    HTTP_REQUESTS_IN_PROGRESS.labels(
        method=request.method,
        endpoint=in_progress_endpoint,
    ).inc()

    try:
        response = await call_next(request)
        endpoint = get_metric_endpoint(request)
        status_code = str(response.status_code)
    except Exception:
        endpoint = in_progress_endpoint
        status_code = "500"
        duration_seconds = time.perf_counter() - start
        duration_ms = round(duration_seconds * 1000, 2)
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=status_code,
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=status_code,
        ).observe(duration_seconds)
        logger.exception(
            "request_failed",
            extra={
                "event": "http_request",
                "method": request.method,
                "path": request.url.path,
                "status_code": int(status_code),
                "client_ip": client_ip,
                "duration_ms": duration_ms,
                "user_agent": user_agent,
            },
        )
        raise
    finally:
        HTTP_REQUESTS_IN_PROGRESS.labels(
            method=request.method,
            endpoint=in_progress_endpoint,
        ).dec()

    duration_seconds = time.perf_counter() - start
    duration_ms = round(duration_seconds * 1000, 2)
    HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=status_code,
    ).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=status_code,
    ).observe(duration_seconds)
    log_method = logger.error if response.status_code >= 400 else logger.info
    log_method(
        "request_completed",
        extra={
            "event": "http_request",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "client_ip": client_ip,
            "duration_ms": duration_ms,
            "user_agent": user_agent,
        },
    )
    return response


@app.get("/", summary="Service information")
async def index(request: Request):
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint="/").inc()
    visit_count = VISIT_COUNTER.increment()
    app_config = load_app_config()

    with DEVOPS_INFO_SYSTEM_INFO_COLLECTION_SECONDS.time():
        now = datetime.now(timezone.utc)
        uptime = get_uptime()
        return {
            "service": get_service_metadata(),
            "system": {
                "hostname": socket.gethostname(),
                "platform": platform.system(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "cpu_count": os.cpu_count(),
                "python_version": platform.python_version(),
            },
            "runtime": {
                "uptime_seconds": uptime["seconds"],
                "uptime_human": uptime["human"],
                "current_time": now.isoformat(),
                "timezone": "UTC",
            },
            "request": {
                "client_ip": request.headers.get(
                    "x-forwarded-for",
                    request.client.host if request.client else None,
                ),
                "user_agent": request.headers.get("user-agent", ""),
                "method": request.method,
                "path": request.url.path,
            },
            "visits": {
                "count": visit_count,
                "path": VISITS_FILE_PATH,
            },
            "configuration": app_config,
            "endpoints": [
                {"path": "/", "method": "GET", "description": "Service information"},
                {"path": "/health", "method": "GET", "description": "Liveness probe"},
                {"path": "/ready", "method": "GET", "description": "Readiness probe"},
                {"path": "/visits", "method": "GET", "description": "Persistent visits counter"},
                {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
            ],
        }


@app.get("/health", summary="Liveness check")
async def health():
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint="/health").inc()
    uptime = get_uptime()
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime["seconds"],
    }


@app.get("/ready", summary="Readiness check")
async def ready():
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint="/ready").inc()
    return {
        "status": "ready",
        "service": SERVICE_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/visits", summary="Current visits counter")
async def visits():
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint="/visits").inc()
    return {
        "visits": VISIT_COUNTER.get_count(),
        "path": VISITS_FILE_PATH,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/metrics", summary="Prometheus metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def main():
    """Run the FastAPI app with uvicorn using environment configuration."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "False").lower() == "true"

    logger.info(
        "application_starting",
        extra={
            "event": "startup",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "host": host,
            "port": port,
            "debug": debug,
        },
    )

    import uvicorn

    target = "app:app" if debug else app
    uvicorn.run(target, host=host, port=port, reload=debug)


if __name__ == "__main__":
    main()
