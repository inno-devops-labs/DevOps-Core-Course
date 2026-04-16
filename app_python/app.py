"""
DevOps Info Service - Lab 01

Production-minded FastAPI application that exposes runtime and system details.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import platform
import socket
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, TextIO, Tuple

try:
    import fcntl
except ImportError:  # pragma: no cover - unavailable on Windows
    fcntl = None  # type: ignore[assignment]

try:
    import msvcrt
except ImportError:  # pragma: no cover - unavailable on Unix
    msvcrt = None  # type: ignore[assignment]

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.exceptions import HTTPException as StarletteHTTPException


class JSONFormatter(logging.Formatter):
    """Custom JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "method"):
            log_entry["method"] = record.method
        if hasattr(record, "path"):
            log_entry["path"] = record.path
        if hasattr(record, "status_code"):
            log_entry["status_code"] = record.status_code
        if hasattr(record, "client_ip"):
            log_entry["client_ip"] = record.client_ip
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


def _configure_logging() -> logging.Logger:
    """Configure application-wide logging with JSON output."""
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    return logging.getLogger(__name__)


logger = _configure_logging()


def _get_env_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable with a safe default."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _get_env_port(default: int) -> int:
    """Read the PORT environment variable safely."""
    raw_value = os.getenv("PORT")
    if not raw_value:
        return default
    try:
        return int(raw_value)
    except ValueError:
        logger.warning("Invalid PORT value '%s'. Falling back to %s.", raw_value, default)
        return default


HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = _get_env_port(default=5000)
DEBUG: bool = _get_env_bool("DEBUG", default=False)

SERVICE_INFO: Dict[str, str] = {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI",
}

ENDPOINTS = [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"},
    {"path": "/visits", "method": "GET", "description": "Visit counter"},
]

VISITS_FILE: str = os.getenv("VISITS_FILE", "/data/visits")
_VISITS_THREAD_LOCK = threading.Lock()

START_TIME: datetime = datetime.now(timezone.utc)

app = FastAPI(
    title="DevOps Info Service",
    version=SERVICE_INFO["version"],
    description=SERVICE_INFO["description"],
)

# ---------------------------------------------------------------------------
# Prometheus Metrics
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
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
)
devops_info_endpoint_calls = Counter(
    "devops_info_endpoint_calls_total",
    "Endpoint-specific call counter",
    ["endpoint"],
)
devops_info_system_collection_seconds = Histogram(
    "devops_info_system_collection_seconds",
    "Time spent collecting system information",
)


def _iso_utc_now() -> str:
    """Return the current time in ISO 8601 format with a UTC 'Z' suffix."""
    now_utc = datetime.now(timezone.utc)
    return now_utc.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _format_uptime(seconds: int) -> str:
    """Return a human-readable uptime string."""
    days, remainder = divmod(seconds, 86_400)
    hours, remainder = divmod(remainder, 3_600)
    minutes, secs = divmod(remainder, 60)

    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours or days:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    parts.append(f"{secs} second{'s' if secs != 1 else ''}")
    return ", ".join(parts)


def get_uptime() -> Tuple[int, str]:
    """Return uptime in seconds and a human-readable string."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = max(int(delta.total_seconds()), 0)
    return seconds, _format_uptime(seconds)


def get_system_info() -> Dict[str, Any]:
    """Collect system information about the runtime environment."""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 0,
        "python_version": platform.python_version(),
    }


def get_runtime_info() -> Dict[str, Any]:
    """Collect runtime information such as uptime and timezone."""
    uptime_seconds, uptime_human = get_uptime()
    local_tz = datetime.now().astimezone().tzinfo
    return {
        "uptime_seconds": uptime_seconds,
        "uptime_human": uptime_human,
        "current_time": _iso_utc_now(),
        "timezone": str(local_tz) if local_tz else time.tzname[0],
    }


def get_request_info(request: Request) -> Dict[str, Any]:
    """Collect request-specific details useful for debugging and observability."""
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    client_host = request.client.host if request.client else ""
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else client_host
    return {
        "client_ip": client_ip or "unknown",
        "user_agent": request.headers.get("User-Agent", "unknown"),
        "method": request.method,
        "path": request.url.path,
    }


@app.middleware("http")
async def log_and_instrument_request(request: Request, call_next):
    """Log incoming requests and record Prometheus metrics."""
    # Skip metrics endpoint from instrumentation to avoid recursion
    if request.url.path == "/metrics":
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        "Request received",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": client_ip,
        },
    )

    http_requests_in_progress.inc()
    start = time.monotonic()
    response = await call_next(request)
    duration = time.monotonic() - start
    http_requests_in_progress.dec()

    endpoint = request.url.path
    http_requests_total.labels(
        method=request.method,
        endpoint=endpoint,
        status=str(response.status_code),
    ).inc()
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=endpoint,
    ).observe(duration)

    logger.info(
        "Response sent",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "client_ip": client_ip,
        },
    )
    return response


def _read_visits() -> int:
    """Read the current visit count from disk. Returns 0 if file is missing or corrupt."""
    try:
        with open(VISITS_FILE, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


@contextlib.contextmanager
def _exclusive_file_lock(file_obj: TextIO) -> Iterator[None]:
    """
    Cross-platform exclusive lock for the visits counter file.

    - Unix: uses fcntl.flock
    - Windows: uses msvcrt.locking with an in-process mutex
    - Fallback: in-process mutex only
    """
    if fcntl is not None:
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)
        return

    if msvcrt is not None:
        with _VISITS_THREAD_LOCK:
            file_obj.seek(0)
            msvcrt.locking(file_obj.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                file_obj.seek(0)
                msvcrt.locking(file_obj.fileno(), msvcrt.LK_UNLCK, 1)
        return

    with _VISITS_THREAD_LOCK:
        yield


def _increment_visits() -> int:
    """Atomically increment the visit counter and return the new value."""
    visits_dir = os.path.dirname(VISITS_FILE)
    if visits_dir:
        os.makedirs(visits_dir, exist_ok=True)

    with open(VISITS_FILE, "a+", encoding="utf-8") as f:
        with _exclusive_file_lock(f):
            f.seek(0)
            raw = f.read().strip()
            count = int(raw) + 1 if raw else 1
            f.seek(0)
            f.truncate()
            f.write(str(count))
            f.flush()
            os.fsync(f.fileno())
    return count


@app.get("/metrics", summary="Prometheus metrics", include_in_schema=False)
async def metrics():
    """Expose Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/", summary="Service information")
async def index(request: Request):
    """Main endpoint returning service, system, runtime, and request info."""
    devops_info_endpoint_calls.labels(endpoint="/").inc()
    visits = _increment_visits()
    with devops_info_system_collection_seconds.time():
        response = {
            "service": SERVICE_INFO,
            "system": get_system_info(),
            "runtime": get_runtime_info(),
            "request": get_request_info(request),
            "endpoints": ENDPOINTS,
            "visits": visits,
        }
    return response


@app.get("/visits", summary="Visit counter")
async def visits_endpoint():
    """Return the total number of visits to the root endpoint."""
    devops_info_endpoint_calls.labels(endpoint="/visits").inc()
    return {"visits": _read_visits()}


@app.get("/health", summary="Health check")
async def health():
    """Health endpoint suitable for probes and monitoring."""
    devops_info_endpoint_calls.labels(endpoint="/health").inc()
    uptime_seconds, _ = get_uptime()
    payload = {
        "status": "healthy",
        "timestamp": _iso_utc_now(),
        "uptime_seconds": uptime_seconds,
    }
    return payload


@app.exception_handler(StarletteHTTPException)
async def handle_http_exception(request: Request, exc: StarletteHTTPException):
    """Return a JSON 404 response while preserving default handling for others."""
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={
                "error": "Not Found",
                "message": "Endpoint does not exist",
                "path": request.url.path,
            },
        )
    return await http_exception_handler(request, exc)


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    """Return a JSON 500 response."""
    logger.exception("Unhandled exception on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        },
    )


if __name__ == "__main__":
    log_level = "debug" if DEBUG else "info"
    logger.info(
        "Starting DevOps Info Service",
        extra={
            "method": "STARTUP",
            "path": f"{HOST}:{PORT}",
            "client_ip": "localhost",
        },
    )
    uvicorn.run(app, host=HOST, port=PORT, log_level=log_level)
