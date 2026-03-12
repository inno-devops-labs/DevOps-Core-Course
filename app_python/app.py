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
import time
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

START_TIME = datetime.now(timezone.utc)


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

# App init
app = FastAPI(
    title="DevOps Info Service",
    version="1.0.0",
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
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version()
    }


@app.on_event("startup")
async def startup_event():
    logger.info(
        "application started",
        extra={
            "event": "startup",
            "service": "devops-info-service",
            "version": "1.0.0",
        }
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    client_ip = request.client.host if request.client else "unknown"

    logger.info(
        "request started",
        extra={
            "event": "request_started",
            "method": request.method,
            "path": request.url.path,
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent"),
        }
    )

    try:
        response = await call_next(request)
        duration_ms = round((time.time() - start) * 1000, 2)

        logger.info(
            "request finished",
            extra={
                "event": "request_finished",
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "client_ip": client_ip,
                "duration_ms": duration_ms,
            }
        )
        return response

    except Exception:
        duration_ms = round((time.time() - start) * 1000, 2)
        logger.exception(
            "request failed",
            extra={
                "event": "request_failed",
                "method": request.method,
                "path": request.url.path,
                "client_ip": client_ip,
                "duration_ms": duration_ms,
            }
        )
        raise


# Main Endpoint: GET /
@app.get("/")
async def root(request: Request):
    uptime = get_uptime()

    return {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
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
            }
        ]
    }


# Health Check: GET /health
@app.get("/health")
def health():
    uptime = get_uptime()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime["seconds"]
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
    