"""
DevOps Info Service
Main application module - FastAPI implementation
"""
import fcntl
import logging
import os
import platform
import socket
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel
from pythonjsonlogger import jsonlogger

from metrics import REQUEST_COUNT, REQUEST_LATENCY, ACTIVE_REQUESTS

# Visits counter configuration
VISITS_FILE = os.getenv('VISITS_FILE', '/data/visits')


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging."""

    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.now(timezone.utc).isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name


def setup_logging() -> logging.Logger:
    """Configure JSON structured logging."""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

    handler = logging.StreamHandler()
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level))
    logger.addHandler(handler)

    # Remove default handlers
    for hdlr in logger.handlers[:-1]:
        logger.removeHandler(hdlr)

    return logging.getLogger(__name__)


# Configure JSON logging
logger = setup_logging()

# Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '5000'))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

START_TIME = datetime.now(timezone.utc)


def read_visits() -> int:
    """Read visit count from file, default to 0."""
    try:
        if Path(VISITS_FILE).exists():
            with open(VISITS_FILE, 'r') as f:
                content = f.read().strip()
                return int(content) if content else 0
    except (ValueError, IOError, PermissionError):
        pass
    return 0


def write_visits(count: int) -> None:
    """Write visit count to file with file locking."""
    try:
        Path(VISITS_FILE).parent.mkdir(parents=True, exist_ok=True)
        with open(VISITS_FILE, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            f.write(str(count))
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except (IOError, PermissionError) as e:
        logger.warning(f'Failed to write visits file: {e}')


def increment_visits() -> int:
    """Increment and return new visit count."""
    count = read_visits()
    count += 1
    write_visits(count)
    return count


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    initial_visits = read_visits()
    logger.info(
        'Application starting',
        extra={
            'event': 'startup',
            'host': HOST,
            'port': PORT,
            'python_version': platform.python_version(),
            'debug': DEBUG,
            'initial_visits': initial_visits
        }
    )
    yield
    # Shutdown
    uptime = get_uptime()
    final_visits = read_visits()
    logger.info(
        'Application shutting down',
        extra={
            'event': 'shutdown',
            'uptime_seconds': uptime['seconds'],
            'uptime_human': uptime['human'],
            'final_visits': final_visits
        }
    )


app = FastAPI(
    title="DevOps Info Service",
    description="DevOps course info service providing system information",
    version="1.0.0",
    lifespan=lifespan
)


# Request logging and metrics middleware
@app.middleware('http')
async def log_requests(request: Request, call_next) -> Response:
    """Log all HTTP requests with timing and status, and track Prometheus metrics."""
    start_time = datetime.now(timezone.utc)

    # Get client IP - handle proxies
    client_ip = request.client.host if request.client else 'unknown'
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        client_ip = forwarded_for.split(',')[0].strip()

    # Normalize endpoint for metrics (prevent high cardinality)
    endpoint = request.url.path
    if endpoint not in ('/', '/health', '/metrics'):
        endpoint = '/other'

    # Track active requests
    ACTIVE_REQUESTS.labels(method=request.method, endpoint=endpoint).inc()

    # Log request
    logger.info(
        'HTTP request started',
        extra={
            'event': 'request_start',
            'method': request.method,
            'path': request.url.path,
            'query': str(request.query_params),
            'client_ip': client_ip,
            'user_agent': request.headers.get('user-agent', 'unknown')
        }
    )

    try:
        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        duration_ms = duration * 1000

        # Record Prometheus metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=str(response.status_code)
        ).inc()

        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)

        # Log response
        log_level = logging.WARNING if response.status_code >= 400 else logging.INFO
        logger.log(
            log_level,
            'HTTP request completed',
            extra={
                'event': 'request_end',
                'method': request.method,
                'path': request.url.path,
                'status_code': response.status_code,
                'duration_ms': round(duration_ms, 2),
                'client_ip': client_ip
            }
        )

        return response
    finally:
        # Decrement active requests
        ACTIVE_REQUESTS.labels(method=request.method, endpoint=endpoint).dec()


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
    visits: int


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
    Increments visit counter on each request.
    """
    visits = increment_visits()
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
            EndpointInfo(
                path='/visits',
                method='GET',
                description='Visit counter'
            ),
        ],
        visits=visits
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


@app.get('/metrics', include_in_schema=False)
async def metrics() -> Response:
    """
    Prometheus metrics endpoint.
    Exposes application metrics for scraping.
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get('/visits', include_in_schema=False)
async def get_visits() -> dict:
    """
    Visit counter endpoint - returns current visit count.
    The counter is persisted to /data/visits file.
    """
    count = read_visits()
    return {'visits': count}


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle 404 Not Found errors."""
    logger.warning(
        'Not found error',
        extra={
            'event': 'error_404',
            'method': request.method,
            'path': request.url.path,
            'client_ip': request.client.host if request.client else 'unknown'
        }
    )
    return JSONResponse(
        status_code=404,
        content={'error': 'Not Found', 'message': 'Endpoint does not exist'}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle 500 Internal Server errors."""
    logger.error(
        'Internal server error',
        extra={
            'event': 'error_500',
            'method': request.method,
            'path': request.url.path,
            'error': str(exc)
        },
        exc_info=True
    )
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
