import os
import time
import platform
import logging
import socket
import uvicorn
import sys
from pythonjsonlogger import jsonlogger
from datetime import datetime, timezone

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

# Configure logging

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
    root.setLevel(logging.INFO)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        log = logging.getLogger(name)
        log.handlers = [handler]
        log.propagate = False
        log.setLevel(logging.INFO)

setup_json_logging()
logger = logging.getLogger(__name__)

logger.info('Application starting...')

# Configuration from environment variables
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "FALSE").lower() == "true"

SERVICE_NAME = os.getenv("SERVICE_NAME", "devops-info-service")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
SERVICE_DESCRIPTION = os.getenv("SERVICE_DESCRIPTION",
                                "DevOps course info service")
FRAMEWORK = "FastAPI"

START_TIME = time.time()

app = FastAPI(
    title=SERVICE_NAME,
    version=SERVICE_VERSION,
    description=SERVICE_DESCRIPTION,
)


@app.middleware("http")
async def access_log_middleware(request: Request, call_next):
    start = time.perf_counter()
    client_ip = request.client.host if request.client else "unknown"

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception:
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.exception(
            "unhandled_exception",
            extra={
                "service": SERVICE_NAME,
                "version": SERVICE_VERSION,
                "hostname": socket.gethostname(),
                "method": request.method,
                "path": request.url.path,
                "status_code": 500,
                "client_ip": client_ip,
                "duration_ms": duration_ms,
            },
        )
        raise
    finally:
        if "status_code" in locals():
            duration_ms = int((time.perf_counter() - start) * 1000)
            logger.info(
                "http_request",
                extra={
                    "service": SERVICE_NAME,
                    "version": SERVICE_VERSION,
                    "hostname": socket.gethostname(),
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "client_ip": client_ip,
                    "duration_ms": duration_ms,
                },
            )


def get_uptime_seconds():
    """
    Calculate the uptime of the application.
    Returns a dictionary with total seconds and human-readable format.
    """
    delta = time.time() - START_TIME
    seconds = int(delta)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }


def iso_utc_now() -> str:
    """
    Get current time in ISO 8601 UTC format.
    """
    dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def system_info() -> dict:
    """
    Get system information such as platform, version, CPU count.
    """
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 0,
        "python_version": platform.python_version(),
    }


def client_ip_from_request(request: Request) -> str:
    """
    Extract client IP address from request.
    """
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


@app.get("/", response_class=JSONResponse)
async def root(request: Request):
    """
    Main endpoint that returns service, system, and runtime information.
    """
    up = get_uptime_seconds()

    return {
        "service": {
            "name": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "description": SERVICE_DESCRIPTION,
            "framework": FRAMEWORK,
        },
        "system": system_info(),
        "runtime": {
            "uptime_seconds": up['seconds'],
            "uptime_human": up['human'],
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
        ],
    }


@app.get("/health", response_class=JSONResponse)
async def health(request: Request):
    """
    Health check endpoint for monitoring.
    """
    up = get_uptime_seconds()

    return {
        "status": "healthy",
        "timestamp": iso_utc_now(),
        "uptime_seconds": up['seconds'],
    }


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


if __name__ == "__main__":
    uvicorn.run("app:app", host=HOST, port=PORT, reload=DEBUG)
