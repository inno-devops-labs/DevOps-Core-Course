#!/usr/bin/env python3
"""
DevOps Info Service
Main application module
"""
import os
import socket
import platform
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

from pythonjsonlogger import jsonlogger

from prometheus_client import (
    Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
)

# Define metrics
http_requests = Counter(
    "http_requests",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"]
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed"
)

devops_info_system_collection_seconds = Histogram(
    "devops_info_system_collection_seconds",
    "System info collection time"
)


logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    fmt='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S%z',
    rename_fields={
        'asctime': 'timestamp',
        'levelname': 'level'
    }
)
logHandler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=[logHandler])
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    method = request.method
    endpoint = request.url.path
    if endpoint == "/metrics":
        return await call_next(request)

    http_requests_in_progress.inc()
    start_time = time.time()
    try:
        response = await call_next(request)
        status = str(response.status_code)
        return response
    except Exception as e:
        status = "500"
        raise e
    finally:
        duration = time.time() - start_time
        http_requests.labels(
            method=method, endpoint=endpoint, status=status).inc()
        http_request_duration_seconds.labels(
            method=method, endpoint=endpoint).observe(duration)
        http_requests_in_progress.dec()


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request.state.start_time = start_time

        client_ip = request.client.host if request.client else "unknown"
        if "x-forwarded-for" in request.headers:
            client_ip = \
                 request.headers["x-forwarded-for"].split(",")[0].strip()

        try:
            response = await call_next(request)
        except Exception:
            duration = time.time() - start_time
            logger.error("HTTP request error", extra={
                "method": request.method,
                "path": request.url.path,
                "client_ip": client_ip,
                "status_code": 500,
                "duration": round(duration, 4)
            })
            raise

        duration = time.time() - start_time
        logger.info("HTTP request", extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "client_ip": client_ip,
            "duration": round(duration, 4)
        })
        return response


app.add_middleware(LoggingMiddleware)


HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '5000'))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

START_TIME = datetime.now(timezone.utc)

logger.info("Application starting", extra={
    "event": "startup",
    "host": HOST,
    "port": PORT,
    "debug": DEBUG
})

DATA_DIR = os.getenv('DATA_DIR', './data')
VISITS_FILE = os.path.join(DATA_DIR, 'visits')


def get_visits() -> int:
    try:
        with open(VISITS_FILE, 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def increment_visits() -> int:
    os.makedirs(DATA_DIR, exist_ok=True)
    count = get_visits() + 1
    with open(VISITS_FILE, 'w') as f:
        f.write(str(count))
    return count


def get_uptime() -> Dict[str, Any]:
    """Calculate application uptime since start"""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }


def get_system_info() -> Dict[str, Any]:
    """Collect system information."""
    with devops_info_system_collection_seconds.time():
        system_info = {
            'hostname': socket.gethostname(),
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'cpu_count': os.cpu_count() or 0,
            'python_version': platform.python_version()
        }
        return system_info


def get_runtime_info() -> Dict[str, Any]:
    """Collect runtime information."""
    return {
        'uptime_seconds': get_uptime()['seconds'],
        'uptime_human': get_uptime()['human'],
        'current_time': datetime.now().isoformat(),
        'timezone': 'UTC'
    }


def get_service_info() -> Dict[str, Any]:
    """Collect service information."""
    return {
        'name': 'devops-info-service',
        'version': '1.0.0',
        'description': 'DevOps course info service',
        'framework': 'FastAPI'
    }


def get_request_info(request: Request) -> Dict[str, Any]:
    """Collect information about the current request."""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get('user-agent', 'unknown')
    return {
        'client_ip': client_ip,
        'user_agent': user_agent,
        'method': request.method,
        'path': request.url.path
    }


def get_endpoints_list() -> list:
    """Get list of available endpoints."""
    return [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"},
        {
            "path": "/metrics",
            "method": "GET",
            "description": "Prometheus metrics"
        },
        {"path": "/visits", "method": "GET", "description": "Visit count"}
    ]


@app.get("/metrics")
async def metrics():
    """Expose Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/", response_model=Dict[str, Any])
async def get_service_information(request: Request) -> Dict[str, Any]:
    """
    Main endpoint - returns service and system information.
    """
    current_visits = increment_visits()
    return {
        "service": get_service_info(),
        "system": get_system_info(),
        "runtime": get_runtime_info(),
        "request": get_request_info(request),
        "endpoints": get_endpoints_list(),
        "visits": current_visits
    }


@app.get("/visits", response_model=Dict[str, int])
async def get_visits_endpoint() -> Dict[str, int]:
    """Return the current number of visits."""
    return {
        "visits": get_visits()
    }


@app.get("/health", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring and service discovery.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": get_uptime()['seconds'],
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 Not Found errors."""
    client_ip = request.client.host if request.client else "unknown"
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()

    duration = None
    if hasattr(request.state, "start_time"):
        duration = round(time.time() - request.state.start_time, 4)

    logger.warning("Not found", extra={
        "method": request.method,
        "path": request.url.path,
        "client_ip": client_ip,
        "status_code": 404,
        "duration": duration
    })

    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"Endpoint {request.url.path} does not exist",
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions (including 500)."""
    client_ip = request.client.host if request.client else "unknown"
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()

    duration = None
    if hasattr(request.state, "start_time"):
        duration = round(time.time() - request.state.start_time, 4)

    logger.error("Unhandled exception", exc_info=True, extra={
        "method": request.method,
        "path": request.url.path,
        "client_ip": client_ip,
        "status_code": 500,
        "duration": duration
    })

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting server", extra={
        "event": "serve",
        "host": HOST,
        "port": PORT,
        "debug": DEBUG
    })

    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info" if DEBUG else "warning"
    )
