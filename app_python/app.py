"""
DevOps Info Service - Lab 01

Production-minded FastAPI application that exposes runtime and system details.
"""

from __future__ import annotations

import logging
import os
import platform
import socket
import time
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def _configure_logging() -> logging.Logger:
    """Configure application-wide logging and return a module logger."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
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
]

START_TIME: datetime = datetime.now(timezone.utc)

app = FastAPI(
    title="DevOps Info Service",
    version=SERVICE_INFO["version"],
    description=SERVICE_INFO["description"],
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
async def log_request(request: Request, call_next):
    """Log incoming requests with basic metadata."""
    client_ip = request.client.host if request.client else "unknown"
    logger.info("Request received: %s %s from %s", request.method, request.url.path, client_ip)
    response = await call_next(request)
    return response


@app.get("/", summary="Service information")
async def index(request: Request):
    """Main endpoint returning service, system, runtime, and request info."""
    response = {
        "service": SERVICE_INFO,
        "system": get_system_info(),
        "runtime": get_runtime_info(),
        "request": get_request_info(request),
        "endpoints": ENDPOINTS,
    }
    return response


@app.get("/health", summary="Health check")
async def health():
    """Health endpoint suitable for probes and monitoring."""
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
    logger.info("Starting DevOps Info Service on %s:%s (debug=%s)", HOST, PORT, DEBUG)
    uvicorn.run(app, host=HOST, port=PORT, log_level=log_level)
