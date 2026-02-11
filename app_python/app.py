"""
DevOps Info Service
FastAPI application
"""
import os
import socket
import platform
import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# App init
app = FastAPI(
    title="DevOps Info Service",
    version="1.0.0",
    description="DevOps course info service"
)

# Application start time
START_TIME = datetime.now(timezone.utc)


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


# Main Endpoint: GET /
@app.get("/")
async def root(request: Request):
    logger.info(f"Request: {request.method} {request.url.path}")

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
            {"path": "/",
             "method": "GET",
             "description": "Service information"},
            {"path": "/health",
             "method": "GET",
             "description": "Health check"}
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


# Error Handling
@app.exception_handler(404)
async def not_found(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "Endpoint does not exist"
        }
    )


@app.exception_handler(500)
async def internal_error(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )
