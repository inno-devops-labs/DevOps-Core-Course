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
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

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
            "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName", "processName",
            "process", "message",
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
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
SERVICE_NAME = os.getenv('SERVICE_NAME', 'devops-info-service')
SERVICE_VERSION = os.getenv('SERVICE_VERSION', '1.0.0')
SERVICE_DESCRIPTION = os.getenv('SERVICE_DESCRIPTION', 'DevOps course info service')
SERVICE_FRAMEWORK = os.getenv('SERVICE_FRAMEWORK', 'FastAPI')
VISITS_FILE = Path(os.getenv('VISITS_FILE', '/tmp/devops-info-service/visits'))
VISITS_LOCK = threading.Lock()

# Application start time
START_TIME = datetime.now(timezone.utc)


def read_visits() -> int:
    try:
        return int(VISITS_FILE.read_text(encoding="utf-8").strip() or "0")
    except (FileNotFoundError, ValueError):
        return 0


def write_visits(count: int) -> None:
    VISITS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = VISITS_FILE.with_name(f"{VISITS_FILE.name}.tmp")
    tmp_file.write_text(str(count), encoding="utf-8")
    tmp_file.replace(VISITS_FILE)


def increment_visits() -> int:
    with VISITS_LOCK:
        count = read_visits() + 1
        write_visits(count)
        return count


def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        "seconds": seconds,
        "human": f"{hours} hours, {minutes} minutes",
    }


@app.on_event("startup")
async def on_startup():
    logger.info(
        "Application startup complete",
        extra={
            "event": "startup",
            "host": HOST,
            "port": PORT,
            "debug": DEBUG,
        },
    )


@app.middleware("http")
async def request_log_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "Unhandled request exception",
            extra={
                "event": "http_request",
                "method": request.method,
                "path": request.url.path,
                "client_ip": client_ip,
            },
        )
        raise

    logger.info(
        "HTTP request processed",
        extra={
            "event": "http_request",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "client_ip": client_ip,
        },
    )
    return response


@app.get("/")
@app.get("/app1")
@app.get("/app1/")
async def get_user_info(request: Request):
    """Main endpoint - service and system information."""
    uptime = get_uptime()
    visits = increment_visits()
    return {
        "service": {
            "name": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "description": SERVICE_DESCRIPTION,
            "framework": SERVICE_FRAMEWORK
        },
        "system": {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
            "python_version": platform.python_version()
        },
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": datetime.now().isoformat(),
            "timezone": str(datetime.now().astimezone().tzinfo)
        },
        "visits": {
            "count": visits,
            "file": str(VISITS_FILE),
        },
        "request": {
            "client_ip": request.client.host,
            "user_agent": request.headers.get('user-agent'),
            "method": request.method,
            "path": request.url.path
        },
    }


@app.get("/visits")
@app.get("/app1/visits")
def visits():
    return {
        "visits": read_visits(),
        "file": str(VISITS_FILE),
        "hostname": socket.gethostname(),
    }


@app.get("/health")
@app.get("/app1/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": get_uptime()["seconds"],
    }


@app.get("/ready")
@app.get("/app1/ready")
def ready():
    return {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": SERVICE_NAME,
    }


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
            "message": "Endpoint does not exist" if exc.status_code == 404 else "An error occurred",
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
