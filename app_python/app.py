"""
DevOps Info Service
Main application module using FastAPI
"""
import os
import socket
import platform
from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app with metadata
app = FastAPI(
    title="DevOps Info Service",
    description="A comprehensive service providing system information and health status for DevOps monitoring",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Application start time
START_TIME = datetime.now(timezone.utc)

def get_system_info() -> Dict[str, Any]:
    """
    Collect system information.

    Returns:
        Dictionary containing hostname, platform, architecture, CPU count, and Python version
    """
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count(),
        'python_version': platform.python_version()
    }

def get_uptime() -> Dict[str, Any]:
    """
    Calculate application uptime.

    Returns:
        Dictionary with uptime in seconds and human-readable format
    """
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }

def get_request_info(request: Request) -> Dict[str, str]:
    """
    Extract request information.

    Args:
        request: FastAPI Request object

    Returns:
        Dictionary containing client IP, user agent, method, and path
    """
    return {
        'client_ip': request.client.host if request.client else 'unknown',
        'user_agent': request.headers.get('user-agent', 'Unknown'),
        'method': request.method,
        'path': request.url.path
    }

@app.get(
    "/",
    summary="Service Information",
    description="Returns comprehensive service and system information including metadata, system specs, runtime metrics, and request details",
    response_description="Complete service information with nested objects for service, system, runtime, request, and endpoints",
    tags=["Information"]
)
async def index(request: Request):
    """
    Main endpoint providing comprehensive service and system information.

    This endpoint returns detailed information about:
    - Service metadata (name, version, description, framework)
    - System information (hostname, platform, architecture, CPU count)
    - Runtime metrics (uptime, current time, timezone)
    - Request details (client IP, user agent, HTTP method, path)
    - Available API endpoints

    Args:
        request: Incoming HTTP request

    Returns:
        JSONResponse with complete service information
    """
    logger.debug(f'Request: {request.method} {request.url.path}')

    uptime = get_uptime()
    system_info = get_system_info()
    request_info = get_request_info(request)

    response = {
        'service': {
            'name': 'devops-info-service',
            'version': '1.0.0',
            'description': 'DevOps course info service',
            'framework': 'FastAPI'
        },
        'system': system_info,
        'runtime': {
            'uptime_seconds': uptime['seconds'],
            'uptime_human': uptime['human'],
            'current_time': datetime.now(timezone.utc).isoformat(),
            'timezone': 'UTC'
        },
        'request': request_info,
        'endpoints': [
            {'path': '/', 'method': 'GET', 'description': 'Service information'},
            {'path': '/health', 'method': 'GET', 'description': 'Health check'},
            {'path': '/docs', 'method': 'GET', 'description': 'Interactive API documentation (Swagger UI)'},
            {'path': '/redoc', 'method': 'GET', 'description': 'Alternative API documentation (ReDoc)'}
        ]
    }

    return JSONResponse(content=response)

@app.get(
    "/health",
    summary="Health Check",
    description="Simple health check endpoint for monitoring systems and Kubernetes probes. Always returns 200 OK when service is running.",
    response_description="Health status with timestamp and uptime",
    tags=["Monitoring"]
)
async def health():
    """
    Health check endpoint for monitoring and orchestration.

    This endpoint is designed for:
    - Kubernetes liveness/readiness probes
    - Load balancer health checks
    - Monitoring systems (Prometheus, Datadog, etc.)

    Returns:
        JSONResponse with status, timestamp, and uptime in seconds
    """
    logger.debug('Health check requested')

    uptime = get_uptime()

    return JSONResponse(content={
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': uptime['seconds']
    })

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={
            'error': 'Not Found',
            'message': 'Endpoint does not exist',
            'path': request.url.path
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors."""
    logger.error(f'Internal error: {exc}')
    return JSONResponse(
        status_code=500,
        content={
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }
    )

if __name__ == '__main__':
    logger.info(f'Starting DevOps Info Service on {HOST}:{PORT}')
    logger.info(f'API Documentation available at http://{HOST}:{PORT}/docs')
    logger.info(f'Alternative docs available at http://{HOST}:{PORT}/redoc')
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="debug" if DEBUG else "info"
    )
