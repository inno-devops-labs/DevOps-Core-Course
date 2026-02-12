"""
DevOps Info Service
Main application module - FastAPI implementation
"""
import logging
import os
import platform
import socket
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '5000'))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

START_TIME = datetime.now(timezone.utc)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info(f'DevOps Info Service starting on {HOST}:{PORT}')
    logger.info(f'Python version: {platform.python_version()}')
    yield
    # Shutdown
    uptime = get_uptime()
    logger.info(f'DevOps Info Service shutting down (uptime: {uptime["human"]})')


app = FastAPI(
    title="DevOps Info Service",
    description="DevOps course info service providing system information",
    version="1.0.0",
    lifespan=lifespan
)


# Pydantic models for response structure
class ServiceMetadata(BaseModel):
    name: str
    version: str
    description: str
    framework: str


class SystemInfo(BaseModel):
    hostname: str
    platform: str
    platform_version: str
    architecture: str
    cpu_count: int
    python_version: str


class RuntimeInfo(BaseModel):
    uptime_seconds: int
    uptime_human: str
    current_time: str
    timezone: str


class RequestInfo(BaseModel):
    client_ip: str
    user_agent: str
    method: str
    path: str


class EndpointInfo(BaseModel):
    path: str
    method: str
    description: str


class ServiceResponse(BaseModel):
    service: ServiceMetadata
    system: SystemInfo
    runtime: RuntimeInfo
    request: RequestInfo
    endpoints: list[EndpointInfo]


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    uptime_seconds: int


def get_uptime() -> dict[str, Any]:
    """Calculate application uptime in seconds and human-readable format."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    human_parts = []
    if hours:
        human_parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        human_parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if secs and not human_parts:
        human_parts.append(f"{secs} second{'s' if secs != 1 else ''}")

    return {
        'seconds': seconds,
        'human': ', '.join(human_parts) if human_parts else '0 seconds'
    }


def get_system_info() -> dict[str, Any]:
    """Collect system information using platform module."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.platform(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count() or 0,
        'python_version': platform.python_version()
    }


@app.get('/', response_model=ServiceResponse, include_in_schema=False)
async def main(request: Request) -> ServiceResponse:
    """
    Main endpoint - returns comprehensive service and system information.
    """
    uptime = get_uptime()
    system = get_system_info()

    # Get client IP - handle proxies
    client_ip = request.client.host if request.client else 'unknown'
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        client_ip = forwarded_for.split(',')[0].strip()

    return ServiceResponse(
        service=ServiceMetadata(
            name='devops-info-service',
            version='1.0.0',
            description='DevOps course info service',
            framework='FastAPI'
        ),
        system=SystemInfo(**system),
        runtime=RuntimeInfo(
            uptime_seconds=uptime['seconds'],
            uptime_human=uptime['human'],
            current_time=datetime.now(timezone.utc).isoformat(),
            timezone=str(timezone.utc)
        ),
        request=RequestInfo(
            client_ip=client_ip,
            user_agent=request.headers.get('user-agent', 'unknown'),
            method=request.method,
            path=request.url.path
        ),
        endpoints=[
            EndpointInfo(
                path='/',
                method='GET',
                description='Service information'
            ),
            EndpointInfo(
                path='/health',
                method='GET',
                description='Health check'
            ),
        ]
    )


@app.get('/health', response_model=HealthResponse, include_in_schema=False)
async def health() -> HealthResponse:
    """
    Health check endpoint - returns service health status.
    Used for Kubernetes liveness/readiness probes.
    """
    uptime = get_uptime()

    return HealthResponse(
        status='healthy',
        timestamp=datetime.now(timezone.utc).isoformat(),
        uptime_seconds=uptime['seconds']
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle 404 Not Found errors."""
    logger.warning(f'Not found: {request.method} {request.url.path}')
    return JSONResponse(
        status_code=404,
        content={'error': 'Not Found', 'message': 'Endpoint does not exist'}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle 500 Internal Server errors."""
    logger.error(f'Internal error: {exc}', exc_info=True)
    return JSONResponse(
        status_code=500,
        content={'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}
    )


if __name__ == '__main__':
    uvicorn.run(
        'app:app',
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level='info'
    )
