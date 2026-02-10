"""
DevOps Info Service
FastAPI application module.
"""

from __future__ import annotations

import logging
import os
import platform
import socket
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Config
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

SERVICE_NAME = "devops-info-service"
SERVICE_VERSION = "1.0.0"
SERVICE_DESCRIPTION = "DevOps course info service"
SERVICE_FRAMEWORK = "FastAPI"

START_TIME = datetime.now(timezone.utc)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("devops-info-service")

app = FastAPI(
    title="DevOps Info Service",
    version=SERVICE_VERSION,
    description=SERVICE_DESCRIPTION,
)


def _format_uptime(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    hour_label = "hour" if hours == 1 else "hours"
    minute_label = "minute" if minutes == 1 else "minutes"
    return f"{hours} {hour_label}, {minutes} {minute_label}"


def get_uptime() -> dict[str, int | str]:
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    return {
        "seconds": seconds,
        "human": _format_uptime(seconds),
    }


def get_system_info() -> dict[str, str | int]:
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.release(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 0,
        "python_version": platform.python_version(),
    }


def isoformat_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("Request: %s %s", request.method, request.url.path)
    response = await call_next(request)
    logger.info("Response: %s %s -> %s", request.method, request.url.path, response.status_code)
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={
                "error": "Not Found",
                "message": "Endpoint does not exist",
            },
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        },
    )


@app.get("/")
async def root(request: Request):
    uptime = get_uptime()
    now = datetime.now(timezone.utc)

    response = {
        "service": {
            "name": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "description": SERVICE_DESCRIPTION,
            "framework": SERVICE_FRAMEWORK,
        },
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": isoformat_utc(now),
            "timezone": "UTC",
        },
        "request": {
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "method": request.method,
            "path": request.url.path,
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
        ],
    }

    return response


@app.get("/health")
async def health():
    uptime = get_uptime()
    return {
        "status": "healthy",
        "timestamp": isoformat_utc(datetime.now(timezone.utc)),
        "uptime_seconds": uptime["seconds"],
    }


if __name__ == "__main__":
    logger.info("Starting DevOps Info Service on %s:%s", HOST, PORT)
    uvicorn.run("app:app", host=HOST, port=PORT, reload=DEBUG, log_level="info")
