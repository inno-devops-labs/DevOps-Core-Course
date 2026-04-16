"""
DevOps Info Service
FastAPI application
"""
import os
import socket
import platform
import logging
import sys
import json
import fcntl
from pathlib import Path
import time
from datetime import datetime, timezone


from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, Gauge
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

START_TIME = datetime.now(timezone.utc)
APP_NAME = "devops-info-service"
APP_VERSION = os.getenv("RELEASE_VERSION", "1.0.0")

APP_ENV = os.getenv("APP_ENV", "dev")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")

CONFIG_PATH = Path(os.getenv("CONFIG_PATH", "/config/config.json"))
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
VISITS_FILE = Path(os.getenv("VISITS_FILE", str(DATA_DIR / "visits")))


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        extra_fields = [
            "method",
            "path",
            "status_code",
            "client_ip",
            "user_agent",
            "duration_ms",
            "event",
            "service",
            "version",
        ]

        for field in extra_fields:
            value = getattr(record, field, None)
            if value is not None:
                log_record[field] = value

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record, ensure_ascii=False)


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)


setup_logging()
logger = logging.getLogger("devops-info-service")

# Prometheus metrics

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status_code"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
)

endpoint_calls_total = Counter(
    "devops_info_endpoint_calls_total",
    "Number of calls to business endpoints",
    ["endpoint"],
)

system_info_collection_seconds = Histogram(
    "devops_info_system_collection_seconds",
    "Time spent collecting system information",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)


def normalize_endpoint(request: Request) -> str:
    route = request.scope.get("route")
    if route and hasattr(route, "path"):
        return route.path

    path = request.url.path
    if path.startswith("/docs"):
        return "/docs"
    if path.startswith("/openapi.json"):
        return "/openapi.json"
    return path


# App init
app = FastAPI(
    title="DevOps Info Service",
    version=APP_VERSION,
    description="DevOps course info service"
)


def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        "seconds": seconds,
        "human": f"{hours} hours, {minutes} minutes"
    }


def get_system_info():
    start = time.perf_counter()
    info = {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version()
    }
    duration = time.perf_counter() - start
    system_info_collection_seconds.observe(duration)
    return info


def ensure_visits_file() -> None:
    VISITS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not VISITS_FILE.exists():
        VISITS_FILE.write_text("0", encoding="utf-8")


def read_config_file():
    if not CONFIG_PATH.exists():
        return {}

    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        logger.exception(
            "failed to read config file",
            extra={
                "event": "config_read_failed",
                "path": str(CONFIG_PATH),
            }
        )
        return {}


def read_visits() -> int:
    ensure_visits_file()

    with VISITS_FILE.open("a+", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        f.seek(0)
        raw = f.read().strip()

        try:
            count = int(raw) if raw else 0
        except ValueError:
            count = 0

        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        return count


def increment_visits() -> int:
    ensure_visits_file()

    with VISITS_FILE.open("a+", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        f.seek(0)
        raw = f.read().strip()

        try:
            count = int(raw) if raw else 0
        except ValueError:
            count = 0

        count += 1

        f.seek(0)
        f.truncate()
        f.write(str(count))
        f.flush()
        os.fsync(f.fileno())

        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        return count


@app.on_event("startup")
async def startup_event():
    ensure_visits_file()

    logger.info(
        "application started",
        extra={
            "event": "startup",
            "service": APP_NAME,
            "version": APP_VERSION,
        }
    )

    logger.info(
        "application paths initialized",
        extra={
            "event": "paths_initialized",
            "service": APP_NAME,
            "version": APP_VERSION,
            "path": str(VISITS_FILE),
        }
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    client_ip = request.client.host if request.client else "unknown"
    method = request.method
    endpoint = normalize_endpoint(request)

    http_requests_in_progress.inc()

    logger.info(
        "request started",
        extra={
            "event": "request_started",
            "method": method,
            "path": request.url.path,
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent"),
        }
    )

    status_code = "500"

    try:
        response = await call_next(request)
        status_code = str(response.status_code)
        return response

    except Exception:
        logger.exception(
            "request failed",
            extra={
                "event": "request_failed",
                "method": method,
                "path": request.url.path,
                "client_ip": client_ip,
            }
        )
        raise

    finally:
        duration_seconds = time.perf_counter() - start
        duration_ms = round(duration_seconds * 1000, 2)

        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
        ).inc()

        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
        ).observe(duration_seconds)

        http_requests_in_progress.dec()

        logger.info(
            "request finished",
            extra={
                "event": "request_finished",
                "method": method,
                "path": request.url.path,
                "status_code": int(status_code),
                "client_ip": client_ip,
                "duration_ms": duration_ms,
            }
        )


@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# Main Endpoint: GET /
@app.get("/")
async def root(request: Request):
    endpoint_calls_total.labels(endpoint="/").inc()

    current_visits = increment_visits()
    uptime = get_uptime()
    file_config = read_config_file()

    return {
        "service": {
            "name": APP_NAME,
            "version": APP_VERSION,
            "description": "DevOps course info service",
            "framework": "FastAPI"
        },
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC"
        },
        "request": {
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent"),
            "method": request.method,
            "path": request.url.path
        },
        "configuration": {
            "app_env": APP_ENV,
            "log_level": LOG_LEVEL,
            "config_path": str(CONFIG_PATH),
            "config_loaded": CONFIG_PATH.exists(),
            "file_config": file_config
        },
        "visits": {
            "count": current_visits,
            "file": str(VISITS_FILE)
        },
        "endpoints": [
            {
                "path": "/",
                "method": "GET",
                "description": "Service information"
            },
            {
                "path": "/health",
                "method": "GET",
                "description": "Health check"
            },
            {
                "path": "/metrics",
                "method": "GET",
                "description": "Prometheus metrics"
            },
            {
                "path": "/visits",
                "method": "GET",
                "description": "Current visits counter"
            }
        ]
    }


# Health Check: GET /health
@app.get("/health")
def health():
    endpoint_calls_total.labels(endpoint="/health").inc()
    uptime = get_uptime()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime["seconds"]
    }


@app.get("/visits")
def visits():
    endpoint_calls_total.labels(endpoint="/visits").inc()
    return {
        "visits": read_visits(),
        "file": str(VISITS_FILE)
    }


@app.exception_handler(404)
async def not_found(request: Request, exc):
    logger.warning(
        "endpoint not found",
        extra={
            "event": "not_found",
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
            "status_code": 404,
        }
    )
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "Endpoint does not exist"
        }
    )


@app.exception_handler(500)
async def internal_error(request: Request, exc):
    logger.exception(
        "internal server error",
        extra={
            "event": "internal_error",
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
            "status_code": 500,
        }
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )
