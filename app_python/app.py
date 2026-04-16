"""
DevOps Info Service
Main application module
"""
import json
import logging
import os
import platform
import socket
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.routing import Match

app = FastAPI()


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        for field in ("method", "path", "status_code", "client_ip", "event"):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        default_keys = {
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
        }
        for key, value in record.__dict__.items():
            if key not in default_keys and key not in payload:
                payload[key] = value

        return json.dumps(payload)


# Logging configuration (stdout JSON for container log collectors)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
logger = logging.getLogger(__name__)

# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
SERVICE_NAME = os.getenv("SERVICE_NAME", "devops-info-service")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
SERVICE_DESCRIPTION = os.getenv("SERVICE_DESCRIPTION", "DevOps course info service")
SERVICE_FRAMEWORK = os.getenv("SERVICE_FRAMEWORK", "FastAPI")
APP_ENV = os.getenv("APP_ENV", "dev")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()
VISITS_FILE = os.getenv("VISITS_FILE", "/data/visits")
APP_CONFIG_PATH = os.getenv("APP_CONFIG_PATH", "/config/config.json")

# Application start time
START_TIME = datetime.now(timezone.utc)

# RED metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests processed by the application.",
    ["method", "endpoint", "status_code"],
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed.",
    ["method", "endpoint"],
)

# Application-specific metrics
devops_info_endpoint_calls = Counter(
    "devops_info_endpoint_calls_total",
    "Application endpoint calls grouped by normalized endpoint.",
    ["endpoint"],
)
devops_info_system_collection_seconds = Histogram(
    "devops_info_system_collection_seconds",
    "Time spent collecting system information for the main info endpoint.",
    buckets=(0.0005, 0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1),
)


class VisitsStore:
    """Persist a request counter in a plain text file."""

    def __init__(self, file_path: str):
        self.path = Path(file_path)
        self._lock = threading.Lock()

    def configure(self, file_path: str) -> None:
        with self._lock:
            self.path = Path(file_path)

    def ensure_parent(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read_unlocked(self) -> int:
        try:
            return int(self.path.read_text(encoding="utf-8").strip() or "0")
        except FileNotFoundError:
            return 0
        except ValueError:
            logger.warning(
                "Visits counter file contained invalid data, resetting to zero",
                extra={"event": "visits_counter_invalid", "path": str(self.path)},
            )
            return 0

    def read(self) -> int:
        with self._lock:
            return self._read_unlocked()

    def increment(self) -> int:
        with self._lock:
            current = self._read_unlocked() + 1
            self.ensure_parent()
            temp_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
            temp_path.write_text(f"{current}\n", encoding="utf-8")
            temp_path.replace(self.path)
            return current


class ConfigCache:
    """Load a JSON config file and refresh it when the mounted file changes."""

    def __init__(self, file_path: str):
        self.path = Path(file_path)
        self._lock = threading.Lock()
        self._mtime_ns = None
        self._cached = {}

    def configure(self, file_path: str) -> None:
        with self._lock:
            self.path = Path(file_path)
            self._mtime_ns = None
            self._cached = {}

    def get(self) -> dict:
        with self._lock:
            try:
                stat = self.path.stat()
            except FileNotFoundError:
                self._cached = {}
                self._mtime_ns = None
                return {}

            if self._mtime_ns == stat.st_mtime_ns:
                return self._cached

            try:
                self._cached = json.loads(self.path.read_text(encoding="utf-8"))
                self._mtime_ns = stat.st_mtime_ns
            except json.JSONDecodeError:
                logger.warning(
                    "Configuration file contained invalid JSON, ignoring it",
                    extra={"event": "config_invalid", "path": str(self.path)},
                )
                self._cached = {}
                self._mtime_ns = stat.st_mtime_ns
            return self._cached


visits_store = VisitsStore(VISITS_FILE)
config_cache = ConfigCache(APP_CONFIG_PATH)


def configure_runtime() -> None:
    """Refresh file-backed runtime dependencies from current environment variables."""
    global VISITS_FILE, APP_CONFIG_PATH

    VISITS_FILE = os.getenv("VISITS_FILE", "/data/visits")
    APP_CONFIG_PATH = os.getenv("APP_CONFIG_PATH", "/config/config.json")
    visits_store.configure(VISITS_FILE)
    config_cache.configure(APP_CONFIG_PATH)
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))


def get_live_configuration() -> dict:
    return {
        "environment": {
            "APP_ENV": os.getenv("APP_ENV", APP_ENV),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", LOG_LEVEL.lower()),
            "APP_DISPLAY_NAME": os.getenv("APP_DISPLAY_NAME", SERVICE_NAME),
            "FEATURE_VISITS_ENABLED": os.getenv("FEATURE_VISITS_ENABLED", "true"),
            "FEATURE_CONFIG_HOT_RELOAD": os.getenv(
                "FEATURE_CONFIG_HOT_RELOAD",
                "true",
            ),
        },
        "file": config_cache.get(),
        "paths": {
            "visits_file": str(visits_store.path),
            "config_file": str(config_cache.path),
        },
    }


configure_runtime()


def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        "seconds": seconds,
        "human": f"{hours} hours, {minutes} minutes",
    }


def get_endpoint_label(request: Request) -> str:
    for route in request.app.router.routes:
        match, _ = route.matches(request.scope)
        if match == Match.FULL:
            return getattr(route, "path", request.url.path)
    return request.url.path


def is_metrics_endpoint(endpoint: str) -> bool:
    return endpoint in {"/metrics", "/app1/metrics"}


@app.on_event("startup")
async def on_startup():
    visits_store.ensure_parent()
    logger.info(
        "Application startup complete",
        extra={
            "event": "startup",
            "host": HOST,
            "port": PORT,
            "debug": DEBUG,
            "visits_file": str(visits_store.path),
            "config_file": str(config_cache.path),
        },
    )


@app.middleware("http")
async def request_log_and_metrics_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    method = request.method
    endpoint = get_endpoint_label(request)
    start_time = time.perf_counter()
    status_code = 500

    http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception:
        logger.exception(
            "Unhandled request exception",
            extra={
                "event": "http_request",
                "method": method,
                "path": request.url.path,
                "client_ip": client_ip,
            },
        )
        raise
    finally:
        duration = time.perf_counter() - start_time
        if not is_metrics_endpoint(endpoint):
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=str(status_code),
            ).inc()
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
            ).observe(duration)
        http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()

    logger.info(
        "HTTP request processed",
        extra={
            "event": "http_request",
            "method": method,
            "path": request.url.path,
            "status_code": status_code,
            "client_ip": client_ip,
        },
    )
    return response


@app.get("/")
@app.get("/app1")
@app.get("/app1/")
async def get_user_info(request: Request):
    """Main endpoint - service and system information."""
    endpoint = get_endpoint_label(request)
    devops_info_endpoint_calls.labels(endpoint=endpoint).inc()
    visits_count = visits_store.increment()

    with devops_info_system_collection_seconds.time():
        system = {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
            "python_version": platform.python_version(),
        }

    uptime = get_uptime()
    return {
        "service": {
            "name": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "description": SERVICE_DESCRIPTION,
            "framework": SERVICE_FRAMEWORK,
        },
        "system": system,
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": datetime.now().isoformat(),
            "timezone": str(datetime.now().astimezone().tzinfo),
        },
        "request": {
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent"),
            "method": request.method,
            "path": request.url.path,
        },
        "visits": {
            "count": visits_count,
            "storage": str(visits_store.path),
        },
        "configuration": get_live_configuration(),
    }


@app.get("/visits")
@app.get("/app1/visits")
def get_visits(request: Request):
    endpoint = get_endpoint_label(request)
    devops_info_endpoint_calls.labels(endpoint=endpoint).inc()
    return {
        "visits": visits_store.read(),
        "storage": str(visits_store.path),
    }


@app.get("/health")
@app.get("/app1/health")
def health(request: Request):
    endpoint = get_endpoint_label(request)
    devops_info_endpoint_calls.labels(endpoint=endpoint).inc()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": get_uptime()["seconds"],
    }


@app.get("/ready")
@app.get("/app1/ready")
def ready(request: Request):
    endpoint = get_endpoint_label(request)
    devops_info_endpoint_calls.labels(endpoint=endpoint).inc()
    return {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": SERVICE_NAME,
    }


@app.get("/metrics")
@app.get("/app1/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    client_ip = request.client.host if request.client else "unknown"
    logger.warning(
        f"HTTP {exc.status_code} error: {exc.detail}",
        extra={
            "event": "http_error",
            "method": request.method,
            "path": request.url.path,
            "status_code": exc.status_code,
            "client_ip": client_ip,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "message": (
                "Endpoint does not exist"
                if exc.status_code == 404
                else "An error occurred"
            ),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    client_ip = request.client.host if request.client else "unknown"
    logger.error(
        f"Internal server error: {str(exc)}",
        extra={
            "event": "http_error",
            "method": request.method,
            "path": request.url.path,
            "status_code": 500,
            "client_ip": client_ip,
        },
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        },
    )


if __name__ == "__main__":
    logger.info("Application starting", extra={"event": "startup"})
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning", access_log=False)
