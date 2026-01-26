"""
DevOps Info Service
Main application module providing system information and health endpoints.
"""
import os
import socket
import platform
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Application start time for uptime calculation
START_TIME = datetime.now(timezone.utc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(f'Application starting on {HOST}:{PORT}')
    yield
    logger.info('Application shutting down')


app = FastAPI(
    title="DevOps Info Service",
    version="1.0.0",
    description="DevOps course info service",
    lifespan=lifespan
)


def get_uptime() -> dict:
    """Calculate application uptime."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
    }


def get_system_info() -> dict:
    """Collect system information."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.platform(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count(),
        'python_version': platform.python_version()
    }


def get_service_info() -> dict:
    """Get service metadata."""
    return {
        'name': 'devops-info-service',
        'version': '1.0.0',
        'description': 'DevOps course info service',
        'framework': 'FastAPI'
    }


def get_endpoints() -> list:
    """Get available endpoints list."""
    return [
        {'path': '/', 'method': 'GET', 'description': 'Service information'},
        {'path': '/health', 'method': 'GET', 'description': 'Health check'}
    ]


@app.get('/')
async def index(request: Request):
    """Main endpoint - service and system information."""
    logger.debug(f'Request: {request.method} {request.url.path}')
    
    uptime = get_uptime()
    
    return {
        'service': get_service_info(),
        'system': get_system_info(),
        'runtime': {
            'uptime_seconds': uptime['seconds'],
            'uptime_human': uptime['human'],
            'current_time': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'timezone': 'UTC'
        },
        'request': {
            'client_ip': request.client.host if request.client else 'unknown',
            'user_agent': request.headers.get('user-agent', 'unknown'),
            'method': request.method,
            'path': str(request.url.path)
        },
        'endpoints': get_endpoints()
    }


@app.get('/health')
async def health():
    """Health check endpoint for monitoring."""
    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'uptime_seconds': get_uptime()['seconds']
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={
            'error': 'Not Found',
            'message': 'Endpoint does not exist'
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
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT, log_level='debug' if DEBUG else 'info')
