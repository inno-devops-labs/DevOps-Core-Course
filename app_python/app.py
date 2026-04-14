import os
import socket
import platform
import logging
import json
import time
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() in ("1", "true", "yes")
VISITS_FILE = os.getenv("VISITS_FILE", "/data/visits")
_visits_lock = threading.Lock()
_in_memory_visits_count = 0

# Custom JSON formatter
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        # Add extra fields
        if hasattr(record, 'service'):
            log_entry['service'] = record.service
        if hasattr(record, 'version'):
            log_entry['version'] = record.version
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
        if hasattr(record, 'path'):
            log_entry['path'] = record.path
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        if hasattr(record, 'client_ip'):
            log_entry['client_ip'] = record.client_ip
        if hasattr(record, 'user_agent'):
            log_entry['user_agent'] = record.user_agent
        if hasattr(record, 'process_time_ms'):
            log_entry['process_time_ms'] = record.process_time_ms
        return json.dumps(log_entry)

# Logging
logger = logging.getLogger("devops-info-service")
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

formatter = JSONFormatter(datefmt="%Y-%m-%dT%H:%M:%SZ")

handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info("Starting DevOps Info Service (FastAPI)", extra={"service": "devops-info-service", "version": "1.0.0"})

# Application and start time
app = FastAPI(title="devops-info-service", version="1.0.0", debug=DEBUG)
START_TIME = datetime.now(timezone.utc)

# Middleware for request logging
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = datetime.now(timezone.utc)
        response = await call_next(request)
        process_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        req_info = get_request_info(request)
        logger.info(
            "HTTP Request",
            extra={
                "method": req_info["method"],
                "path": req_info["path"],
                "status_code": response.status_code,
                "client_ip": req_info["client_ip"],
                "user_agent": req_info["user_agent"],
                "process_time_ms": round(process_time, 2)
            }
        )
        return response

app.add_middleware(RequestLoggingMiddleware)


def get_uptime() -> Dict[str, Any]:
    """Return uptime in seconds and human readable string."""

    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    human = f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
    return {"seconds": seconds, "human": human}


def get_system_info() -> Dict[str, Any]:
    """Collect static system information."""

    try:
        platform_version = platform.version()
    except Exception:
        platform_version = platform.release()

    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform_version,
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 1,
        "python_version": platform.python_version(),
    }


def _format_iso_z(dt: datetime) -> str:
    """Return ISO8601 with trailing Z for UTC times."""

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def get_request_info(request: Request) -> Dict[str, Any]:
    """Extract request info (consider X-Forwarded-For)."""

    # Prefer X-Forwarded-For if present (for proxies), else use client.host
    xff = request.headers.get("x-forwarded-for")
    if xff:
        client_ip = xff.split(",")[0].strip()
    else:
        # request.client may be None in some test scenarios
        client_ip = request.client.host if request.client else "unknown"

    user_agent = request.headers.get("user-agent", "")
    return {
        "client_ip": client_ip,
        "user_agent": user_agent,
        "method": request.method,
        "path": request.url.path,
    }


def _get_visits_path() -> Path:
    return Path(os.getenv("VISITS_FILE", VISITS_FILE))


def _read_visits_count() -> int:
    global _in_memory_visits_count
    visits_path = _get_visits_path()
    try:
        content = visits_path.read_text(encoding="utf-8").strip()
        return int(content) if content else 0
    except FileNotFoundError:
        return _in_memory_visits_count
    except (ValueError, OSError):
        return _in_memory_visits_count


def _write_visits_count(value: int) -> None:
    visits_path = _get_visits_path()
    visits_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = visits_path.with_suffix(".tmp")
    tmp_path.write_text(str(value), encoding="utf-8")
    os.replace(tmp_path, visits_path)


def increment_visits_count() -> int:
    global _in_memory_visits_count
    with _visits_lock:
        current = _read_visits_count()
        updated = current + 1
        _in_memory_visits_count = updated
        try:
            _write_visits_count(updated)
        except OSError:
            logger.warning("Visits counter fallback to in-memory storage", extra={"path": str(_get_visits_path())})
        return updated


def get_visits_count() -> int:
    with _visits_lock:
        return _read_visits_count()


ENDPOINTS = [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"},
    {"path": "/visits", "method": "GET", "description": "Visits counter"},
    {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
]

# Prometheus metrics
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

# Application-specific metrics
endpoint_calls = Counter(
    "devops_info_endpoint_calls_total",
    "DevOps info service endpoint calls",
    ["endpoint"],
)

system_info_collection_seconds = Histogram(
    "devops_info_system_collection_seconds",
    "System info collection time in seconds",
)


def _get_endpoint_label(request: Request) -> str:
    route = request.scope.get("route")
    if route and hasattr(route, "path"):
        return route.path
    return request.url.path


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method
        endpoint = _get_endpoint_label(request)
        start = time.perf_counter()
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except StarletteHTTPException as exc:
            status_code = exc.status_code
            raise
        except RequestValidationError:
            status_code = 400
            raise
        finally:
            duration = time.perf_counter() - start
            http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
            http_requests_total.labels(method=method, endpoint=endpoint, status_code=str(status_code)).inc()
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()


app.add_middleware(MetricsMiddleware)


@app.get("/", summary="Service and system information")
async def index(request: Request):
    """Main endpoint returning comprehensive info about service & runtime."""

    logger.info("Index endpoint accessed", extra={"endpoint": "/", "method": "GET"})
    endpoint_calls.labels(endpoint="/").inc()
    visits = increment_visits_count()
    with system_info_collection_seconds.time():
        system = get_system_info()
    uptime = get_uptime()

    response = {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "FastAPI",
        },
        "system": system,
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": _format_iso_z(datetime.now(timezone.utc)),
            "timezone": "UTC",
        },
        "request": get_request_info(request),
        "visits": {"count": visits},
        "endpoints": ENDPOINTS,
    }
    return JSONResponse(content=response)


@app.get("/health", summary="Health check")
async def health(request: Request):
    """Simple health endpoint (used for liveness/readiness)."""

    logger.info("Health check endpoint accessed", extra={"endpoint": "/health", "method": "GET"})
    endpoint_calls.labels(endpoint="/health").inc()
    uptime = get_uptime()
    payload = {
        "status": "healthy",
        "timestamp": _format_iso_z(datetime.now(timezone.utc)),
        "uptime_seconds": uptime["seconds"],
    }
    return JSONResponse(content=payload)


@app.get("/visits", summary="Visits counter")
async def visits(request: Request):
    logger.info("Visits endpoint accessed", extra={"endpoint": "/visits", "method": "GET"})
    endpoint_calls.labels(endpoint="/visits").inc()
    payload = {
        "visits": get_visits_count(),
        "file_path": str(_get_visits_path()),
        "timestamp": _format_iso_z(datetime.now(timezone.utc)),
    }
    return JSONResponse(content=payload)


@app.get("/metrics", summary="Prometheus metrics")
async def metrics():
    payload = generate_latest()
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning("HTTP exception", extra={"status_code": exc.status_code, "detail": exc.detail, "path": request.url.path})
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error("Validation error", extra={"path": request.url.path, "details": str(exc)})
    return JSONResponse(status_code=400, content={"error": "Invalid request", "details": str(exc)})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error", extra={"path": request.url.path, "error": str(exc)})
    return JSONResponse(status_code=500, content={"error": "Internal Server Error", "message": str(exc)})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT, reload=DEBUG)
