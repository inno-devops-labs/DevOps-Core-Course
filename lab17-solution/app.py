"""
DevOps Info Service
Main application module using FastAPI

This service provides comprehensive information about itself and its runtime environment.
It exposes two main endpoints: / for service info and /health for monitoring.
"""

import os
import socket
import platform
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8080))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Create FastAPI application
app = FastAPI(
    title="DevOps Info Service",
    description="A DevOps service providing system and runtime information",
    version="1.0.0"
)

# Application start time for uptime calculation
START_TIME = datetime.now(timezone.utc)


def get_system_info() -> Dict[str, Any]:
    """
    Collect system information.
    
    Returns:
        Dictionary containing hostname, platform, version, architecture, 
        CPU count, and Python version.
    """
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': f"{platform.system()} {platform.release()}",
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count() or 1,
        'python_version': platform.python_version()
    }


def get_uptime_info() -> Dict[str, Any]:
    """
    Calculate uptime since application start.
    
    Returns:
        Dictionary with uptime in seconds and human-readable format.
    """
    delta = datetime.now(timezone.utc) - START_TIME
    total_seconds = int(delta.total_seconds())
    
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    human_readable = f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
    
    return {
        'uptime_seconds': total_seconds,
        'uptime_human': human_readable
    }


def get_endpoints_list() -> List[Dict[str, str]]:
    """
    Generate list of available endpoints.
    
    Returns:
        List of endpoint dictionaries with path, method, and description.
    """
    return [
        {
            'path': '/',
            'method': 'GET',
            'description': 'Service and system information'
        },
        {
            'path': '/health',
            'method': 'GET',
            'description': 'Health check endpoint'
        }
    ]


@app.get('/', response_class=JSONResponse)
async def index(request: Request) -> Dict[str, Any]:
    """
    Main endpoint returning comprehensive service and system information.
    
    Args:
        request: FastAPI request object
        
    Returns:
        JSON response with service info, system info, runtime info, request info,
        and available endpoints.
    """
    logger.info(f"Request: {request.method} {request.url.path} from {request.client.host}")
    
    return {
        'service': {
            'name': 'devops-info-service',
            'version': '1.0.0',
            'description': 'DevOps course info service',
            'framework': 'FastAPI'
        },
        'system': get_system_info(),
        'runtime': {
            **get_uptime_info(),
            'current_time': datetime.now(timezone.utc).isoformat() + 'Z',
            'timezone': 'UTC'
        },
        'request': {
            'client_ip': request.client.host,
            'user_agent': request.headers.get('user-agent', 'unknown'),
            'method': request.method,
            'path': request.url.path
        },
        'endpoints': get_endpoints_list()
    }


@app.get('/health', response_class=JSONResponse)
async def health(request: Request) -> Dict[str, Any]:
    """
    Health check endpoint for monitoring and liveness probes.
    
    Args:
        request: FastAPI request object
        
    Returns:
        JSON response with health status, timestamp, and uptime.
    """
    logger.debug(f"Health check: {request.method} {request.url.path}")
    
    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat() + 'Z',
        'uptime_seconds': get_uptime_info()['uptime_seconds']
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle 404 Not Found errors with JSON response."""
    logger.warning(f"Not found: {request.method} {request.url.path}")
    return JSONResponse(
        status_code=404,
        content={
            'error': 'Not Found',
            'message': 'Endpoint does not exist',
            'path': request.url.path
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors with JSON response."""
    logger.error(f"Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }
    )


@app.get('/docs', include_in_schema=False)
async def swagger_ui():
    """Swagger UI documentation endpoint."""
    from fastapi.openapi.docs import get_swagger_ui_html
    return get_swagger_ui_html(openapi_url='/openapi.json', title='DevOps Info Service')


# Log configuration when module loads
logger.info(f"FastAPI application configured on {HOST}:{PORT}")
logger.info(f"Debug mode: {DEBUG}")


if __name__ == '__main__':
    import uvicorn
    
    logger.info(f"Starting Uvicorn server on {HOST}:{PORT}")
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level='info'
    )