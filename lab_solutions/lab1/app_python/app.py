import os
import logging
import json
import platform
import socket
import sys
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import Response


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
async def log_requests(request: Request, call_next):
    started_at = datetime.now(timezone.utc)
    client_ip = request.client.host if request.client else "unknown"

    try:
        response: Response = await call_next(request)
    except Exception:
        logger.exception(
            "request_failed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client_ip": client_ip,
                "status_code": 500,
            },
        )
        raise

    elapsed_ms = int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)
    logger.info(
        "request_completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "client_ip": client_ip,
            "duration_ms": elapsed_ms,
        },
    )
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


if __name__ == "__main__":
    import uvicorn

    logger.info(
        "starting_application",
        extra={"host": HOST, "port": PORT, "debug": DEBUG},
    )
    uvicorn.run(
        "app:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="debug" if DEBUG else "info",
    )
