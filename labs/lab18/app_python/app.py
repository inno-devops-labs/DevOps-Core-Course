import os
import time
import json
import platform
import logging
import socket
import uvicorn
import sys
import asyncio
import tempfile
from pathlib import Path
from pythonjsonlogger import jsonlogger
from datetime import datetime, timezone

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response


class DefaultFieldsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "service"):
            record.service = os.getenv("SERVICE_NAME", "devops-info-service")
        if not hasattr(record, "version"):
            record.version = os.getenv("SERVICE_VERSION", "1.0.0")
        if not hasattr(record, "hostname"):
            record.hostname = socket.gethostname()

        for key in ("method", "path", "status_code", "client_ip", "duration_ms"):
            if not hasattr(record, key):
                setattr(record, key, None)

        return True


def setup_json_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s "
        "%(service)s %(version)s %(hostname)s "
        "%(method)s %(path)s %(status_code)s %(client_ip)s %(duration_ms)s"
    )
    handler.setFormatter(formatter)
    handler.addFilter(DefaultFieldsFilter())

    root = logging.getLogger()
    root.handlers = [handler]

    log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    root.setLevel(log_level)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        log = logging.getLogger(name)
        log.handlers = [handler]
        log.propagate = False
        log.setLevel(log_level)


setup_json_logging()
logger = logging.getLogger(__name__)
logger.info("Application starting...")

# Configuration from environment variables
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "FALSE").lower() == "true"

SERVICE_NAME = os.getenv("SERVICE_NAME", "devops-info-service")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
SERVICE_DESCRIPTION = os.getenv("SERVICE_DESCRIPTION", "DevOps course info service")
FRAMEWORK = "FastAPI"
APP_ENV = os.getenv("APP_ENV", "dev")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
VISITS_FILE = Path(os.getenv("VISITS_FILE", str(DATA_DIR / "visits")))
CONFIG_FILE = Path(os.getenv("CONFIG_FILE", "/config/config.json"))

START_TIME = time.time()
VISITS_LOCK = asyncio.Lock()

app = FastAPI(
    title=SERVICE_NAME,
    version=SERVICE_VERSION,
    description=SERVICE_DESCRIPTION,
)

# RED metrics
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

# App-specific example metrics
devops_endpoint_calls = Counter(
    "devops_info_endpoint_calls",
    "DevOps info service endpoint calls",
    ["endpoint"],
)

system_info_duration = Histogram(
    "devops_info_system_collection_seconds",
    "Time spent collecting system info (seconds)",
)


@app.on_event("startup")
async def startup_event() -> None:
    ensure_visits_file()
    logger.info(
        "visits_counter_ready",
        extra={
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "hostname": socket.gethostname(),
        },
    )


def ensure_visits_file() -> None:
    VISITS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not VISITS_FILE.exists():
        atomic_write_text(VISITS_FILE, "0\n")


def atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8") as tmp:
        tmp.write(value)
        tmp.flush()
        os.fsync(tmp.fileno())
        temp_name = tmp.name
    os.replace(temp_name, path)


def read_visits_count() -> int:
    ensure_visits_file()
    try:
        raw = VISITS_FILE.read_text(encoding="utf-8").strip()
        return int(raw or "0")
    except (OSError, ValueError):
        return 0


def write_visits_count(value: int) -> None:
    atomic_write_text(VISITS_FILE, f"{value}\n")


async def increment_visits_count() -> int:
    async with VISITS_LOCK:
        current = read_visits_count()
        updated = current + 1
        write_visits_count(updated)
        return updated


def load_config_file() -> dict:
    if not CONFIG_FILE.exists():
        return {
            "config_file": str(CONFIG_FILE),
            "loaded": False,
            "reason": "config file not found",
        }

    try:
        content = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return {
            "config_file": str(CONFIG_FILE),
            "loaded": True,
            "content": content,
        }
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "config_file": str(CONFIG_FILE),
            "loaded": False,
            "reason": f"failed to load config: {exc}",
        }


def get_uptime_seconds() -> dict:
    delta = time.time() - START_TIME
    seconds = int(delta)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        "seconds": seconds,
        "human": f"{hours} hours, {minutes} minutes",
    }


def iso_utc_now() -> str:
    dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def system_info() -> dict:
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 0,
        "python_version": platform.python_version(),
    }


def client_ip_from_request(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


@app.middleware("http")
async def telemetry_middleware(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)

    method = request.method
    client_ip = request.client.host if request.client else "unknown"
    endpoint = request.url.path

    start = time.perf_counter()
    status = "500"

    http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

    try:
        response = await call_next(request)
        status = str(response.status_code)
        return response
    finally:
        duration = time.perf_counter() - start
        duration_ms = int(duration * 1000)

        http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
        http_requests_total.labels(method=method, endpoint=endpoint, status_code=status).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)

        logger.info(
            "http_request",
            extra={
                "service": SERVICE_NAME,
                "version": SERVICE_VERSION,
                "hostname": socket.gethostname(),
                "method": method,
                "path": endpoint,
                "status_code": int(status),
                "client_ip": client_ip,
                "duration_ms": duration_ms,
            },
        )


@app.get("/", response_class=JSONResponse)
async def root(request: Request):
    devops_endpoint_calls.labels(endpoint="/").inc()

    with system_info_duration.time():
        sysinfo = system_info()

    visit_count = await increment_visits_count()
    up = get_uptime_seconds()

    return {
        "service": {
            "name": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "description": SERVICE_DESCRIPTION,
            "framework": FRAMEWORK,
        },
        "application": {
            "environment": APP_ENV,
            "log_level": LOG_LEVEL,
        },
        "config": load_config_file(),
        "persistence": {
            "visits_file": str(VISITS_FILE),
            "visits_count": visit_count,
        },
        "system": sysinfo,
        "runtime": {
            "uptime_seconds": up["seconds"],
            "uptime_human": up["human"],
            "current_time": iso_utc_now(),
            "timezone": "UTC",
        },
        "request": {
            "client_ip": client_ip_from_request(request),
            "user_agent": request.headers.get("user-agent", "unknown"),
            "method": request.method,
            "path": request.url.path,
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/visits", "method": "GET", "description": "Current visits counter"},
            {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
        ],
    }


@app.get("/visits", response_class=JSONResponse)
async def visits():
    return {
        "visits": read_visits_count(),
        "visits_file": str(VISITS_FILE),
    }


@app.get("/health", response_class=JSONResponse)
async def health(request: Request):
    up = get_uptime_seconds()
    return {
        "status": "healthy",
        "timestamp": iso_utc_now(),
        "uptime_seconds": up["seconds"],
        "request_path": request.url.path,
    }


@app.get("/debug/error")
async def debug_error(code: int = 500):
    if code not in (400, 404, 500):
        raise HTTPException(status_code=400, detail="allowed: 400,404,500")
    raise HTTPException(status_code=code, detail=f"Simulated {code}")


@app.get("/debug/slow")
async def debug_slow(seconds: float = 5.0):
    await asyncio.sleep(seconds)
    return {"message": "Slow request finished", "slept_seconds": seconds}


@app.exception_handler(500)
async def internal_server_error(request: Request, exc: HTTPException):
    logger.error(f"500 Error: {str(exc)} for {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "error": str(exc)},
    )


@app.exception_handler(404)
async def not_found_exception(request: Request, exc: HTTPException):
    logger.warning(
        "not_found",
        extra={
            "timestamp": iso_utc_now(),
            "level": "WARNING",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "hostname": socket.gethostname(),
            "method": request.method,
            "path": request.url.path,
            "status_code": 404,
            "client_ip": request.client.host if request.client else "unknown",
        },
    )
    return JSONResponse(
        status_code=404,
        content={"message": "Endpoint not found", "error": str(exc)},
    )


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, reload=DEBUG)
