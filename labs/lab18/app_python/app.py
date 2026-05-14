"""
DevOps Info Service - FastAPI Application

A web service that provides comprehensive information about itself
and its runtime environment.
"""

import os
import platform
import socket
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Application start time for uptime calculation
start_time = datetime.now(timezone.utc)

# Initialize FastAPI app
app = FastAPI(
    title="DevOps Info Service",
    description="A service providing system and runtime information",
    version="1.0.0",
)


def get_system_info() -> Dict[str, Any]:
    """
    Get system information.

    Returns:
        Dictionary containing system information
    """
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.platform(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 0,
        "python_version": platform.python_version(),
    }


def get_uptime() -> Dict[str, Any]:
    """
    Calculate application uptime.

    Returns:
        Dictionary with uptime in seconds and human-readable format
    """
    delta = datetime.now(timezone.utc) - start_time
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        "seconds": seconds,
        "human": f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}",
    }


@app.get("/")
async def root(request: Request) -> Dict[str, Any]:
    """
    Main endpoint returning comprehensive service information.

    Returns:
        JSON response with service, system, runtime, request, and endpoints info
    """
    uptime = get_uptime()
    system_info = get_system_info()

    # Get request information
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    method = request.method
    path = request.url.path

    return {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "FastAPI",
        },
        "system": system_info,
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "timezone": "UTC",
        },
        "request": {
            "client_ip": client_ip,
            "user_agent": user_agent,
            "method": method,
            "path": path,
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {
                "path": "/docs",
                "method": "GET",
                "description": "Interactive API documentation",
            },
            {
                "path": "/redoc",
                "method": "GET",
                "description": "Alternative API documentation",
            },
            {"path": "/openapi.json", "method": "GET", "description": "OpenAPI schema"},
        ],
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring.

    Returns:
        JSON response with health status, timestamp, and uptime
    """
    uptime = get_uptime()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "uptime_seconds": uptime["seconds"],
    }


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with JSON responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if exc.status_code != 404 else "Not Found",
            "message": (
                exc.detail
                if exc.status_code != 404
                else f"Path {request.url.path} not found"
            ),
            "path": request.url.path,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with JSON responses."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "Invalid request data",
            "details": exc.errors(),
        },
    )


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "False").lower() == "true"

    # Pass the ASGI app object so this works when executed as a script from any path (e.g. Nix store).
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=debug,
        log_level="debug" if debug else "info",
    )
