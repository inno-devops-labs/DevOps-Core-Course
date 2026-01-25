"""
DevOps Info Service
Main application module
"""
import logging
import os
import platform
import socket
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

app = FastAPI()

# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Application start time
start_time = datetime.now()


def get_service_info():
    """Get information about service."""
    logger.debug('Getting info about the service.')
    return {
        "name": "devops-info-service",
        "version": "1.0.0",
        "description": "DevOps course info service",
        "framework": "FastAPI",
    }


def get_system_info():
    """Get information about system."""
    logger.debug('Getting info about the system.')
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platformVersion": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }


def get_uptime():
    """Get uptime."""
    logger.debug('Getting uptime.')
    delta = datetime.now() - start_time
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {"seconds": seconds, "human": f"{hours} hours, {minutes} minutes"}


def get_runtime_info():
    """Get information about runtime."""
    logger.debug('Getting runtime info.')
    uptime = get_uptime()
    uptime_seconds, uptime_human = uptime["seconds"], uptime["human"]
    current_time = datetime.now(timezone.utc)

    return {
        "uptime_seconds": uptime_seconds,
        "uptime_human": uptime_human,
        "current_time": current_time,
        "timezone": "UTC",
    }


def get_request_info(request: Request):
    """Get information about request."""
    logger.debug('Getting info about request.')
    return {
        "client_ip": request.client.host,
        "user_agent": request.headers.get("user-agent"),
        "method": request.method,
        "path": request.url.path,
    }


def get_endpoints():
    """Get all existing ednpoints."""
    logger.debug('Getting list of all endpoints.')
    return [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"},
    ]


@app.get("/", status_code=status.HTTP_200_OK)
async def root(request: Request):
    """Main endpoint - service and system information."""
    logger.debug(f'Request: {request.method} {request.url.path}')
    return {
        "service": get_service_info(),
        "system": get_system_info(),
        "runtime": get_runtime_info(),
        "request": get_request_info(request),
        "endpoints": get_endpoints(),
    }


@app.get("/health", status_code=status.HTTP_200_OK)
async def health(request: Request):
    """Endpoint to check health."""
    logger.debug(f'Request: {request.method} {request.url.path}')
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc),
        "uptime_seconds": get_uptime()["seconds"],
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Exception 404 (Not found) that endpoint does not exists."""
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
        content={
            "error": "HTTP Error",
            "message": exc.detail if exc.detail else "Request failed",
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Exception 500 (Internal Server Error) - For any unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        },
    )


if __name__ == "__main__":
    """The entry point."""
    logger.info('Application starting...')

    uvicorn.run("app:app", host=HOST, port=PORT, reload=True)
