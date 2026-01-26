"""
DevOps Info Service
Main application module
"""
import os
import socket
import platform
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '5000'))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Application start time
START_TIME = datetime.now(timezone.utc)


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
        {"path": "/health", "method": "GET", "description": "Health check"}
    ]


@app.get("/", response_model=Dict[str, Any])
async def get_service_information(request: Request) -> Dict[str, Any]:
    """
    Main endpoint - returns service and system information.
    
    Returns:
        JSON object containing service metadata, system info, runtime info,
        request details, and available endpoints.
    """
    logger.info(f"GET / requested from {request.client.host if request.client else 'unknown'}")
    
    return {
        "service": get_service_info(),
        "system": get_system_info(),
        "runtime": get_runtime_info(),
        "request": get_request_info(request),
        "endpoints": get_endpoints_list()
    }


@app.get("/health", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring and service discovery.
    
    Returns:
        JSON object with health status, timestamp, and uptime.
        Always returns HTTP 200 when service is running.
    """
    logger.debug("Health check requested")
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": get_uptime()['seconds'],
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 Not Found errors."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"Endpoint {request.url.path} does not exist",
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 Internal Server errors."""
    logger.error(f"Internal server error: {exc}")
    
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

    logger.info(f"Starting Service on {HOST}:{PORT}")
    
    uvicorn.run(
        "app:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="info" if DEBUG else "warning"
    )

    
