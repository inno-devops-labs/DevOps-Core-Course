"""
DevOps Info Service
Main application module using FastAPI
"""
import json
import logging
import os
import platform
import socket
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest


# --- Prometheus metrics ---
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed'
)

endpoint_calls_total = Counter(
    'devops_info_endpoint_calls_total',
    'Total calls per named endpoint',
    ['endpoint']
)


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record):
        log_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add extra fields if present
        if hasattr(record, 'method'):
            log_data['method'] = record.method
        if hasattr(record, 'path'):
            log_data['path'] = record.path
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
        if hasattr(record, 'client_ip'):
            log_data['client_ip'] = record.client_ip

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data)


# Configure JSON logging
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Also configure root logger for uvicorn
root_logger = logging.getLogger()
root_logger.handlers = []
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

app = FastAPI(
    title="DevOps Info Service",
    description="DevOps course info service",
    version="1.0.0"
)

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
VISITS_FILE = Path(os.getenv('VISITS_FILE', './data/visits'))
VISITS_LOCK = Lock()

START_TIME = datetime.now(timezone.utc)


def ensure_visits_directory() -> None:
    """Ensure the visits file directory exists."""
    VISITS_FILE.parent.mkdir(parents=True, exist_ok=True)


def get_system_info() -> Dict[str, Any]:
    """Collect system information."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count(),
        'python_version': platform.python_version()
    }


def get_uptime() -> Dict[str, Any]:
    """Calculate application uptime."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }


def get_request_info(request: Request) -> Dict[str, str]:
    """Extract request information."""
    return {
        'client_ip': request.client.host if request.client else 'unknown',
        'user_agent': request.headers.get('user-agent', 'unknown'),
        'method': request.method,
        'path': request.url.path
    }


def get_endpoints() -> List[Dict[str, str]]:
    """List available endpoints."""
    return [
        {
            'path': '/',
            'method': 'GET',
            'description': 'Service information and increment visits counter'
        },
        {
            'path': '/health',
            'method': 'GET',
            'description': 'Health check'
        },
        {
            'path': '/visits',
            'method': 'GET',
            'description': 'Current persisted visits counter'
        }
    ]


def read_visits_count() -> int:
    """Read visits counter from file, defaulting to zero."""
    try:
        return int(VISITS_FILE.read_text(encoding='utf-8').strip() or '0')
    except FileNotFoundError:
        return 0
    except ValueError:
        logger.warning(
            'Visits file contains invalid value, resetting counter to zero',
            extra={'path': str(VISITS_FILE)}
        )
        return 0


def write_visits_count(count: int) -> None:
    """Persist visits counter using atomic replace."""
    ensure_visits_directory()
    temp_file = VISITS_FILE.with_suffix('.tmp')
    temp_file.write_text(str(count), encoding='utf-8')
    temp_file.replace(VISITS_FILE)


def increment_visits_count() -> int:
    """Increment visits counter in a thread-safe way and return new value."""
    with VISITS_LOCK:
        current_count = read_visits_count()
        new_count = current_count + 1
        write_visits_count(new_count)
        return new_count


@app.on_event('startup')
def initialize_visits_file() -> None:
    """Ensure visits file exists and is readable on startup."""
    with VISITS_LOCK:
        current_count = read_visits_count()
        write_visits_count(current_count)

    logger.info(
        'Visits counter initialized',
        extra={
            'path': str(VISITS_FILE),
            'visits_count': current_count
        }
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all HTTP requests and record Prometheus metrics."""
    # Normalize endpoint label (avoid high cardinality from dynamic paths)
    endpoint = request.url.path

    http_requests_in_progress.inc()
    start_time = datetime.now(timezone.utc)

    try:
        response = await call_next(request)
    finally:
        http_requests_in_progress.dec()

    duration = (datetime.now(timezone.utc) - start_time).total_seconds()

    http_requests_total.labels(
        method=request.method,
        endpoint=endpoint,
        status=str(response.status_code)
    ).inc()
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=endpoint
    ).observe(duration)

    logger.info(
        f"HTTP {request.method} {request.url.path} - {response.status_code}",
        extra={
            'method': request.method,
            'path': str(request.url.path),
            'status_code': response.status_code,
            'client_ip': request.client.host if request.client else 'unknown',
            'duration_seconds': duration
        }
    )

    return response


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
async def index(request: Request) -> Dict[str, Any]:
    """Main endpoint - service and system information."""
    endpoint_calls_total.labels(endpoint='/').inc()
    uptime = get_uptime()
    visits_count = increment_visits_count()

    return {
        'service': {
            'name': 'devops-info-service',
            'version': '1.0.0',
            'description': 'DevOps course info service',
            'framework': 'FastAPI'
        },
        'system': get_system_info(),
        'runtime': {
            'uptime_seconds': uptime['seconds'],
            'uptime_human': uptime['human'],
            'current_time': datetime.now(timezone.utc).isoformat(),
            'timezone': 'UTC'
        },
        'request': get_request_info(request),
        'visits': {
            'count': visits_count,
            'file': str(VISITS_FILE)
        },
        'endpoints': get_endpoints()
    }


@app.get("/visits")
def visits() -> Dict[str, Any]:
    """Return current persisted visits counter."""
    endpoint_calls_total.labels(endpoint='/visits').inc()
    with VISITS_LOCK:
        visits_count = read_visits_count()

    return {
        'visits': visits_count,
        'file': str(VISITS_FILE)
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Health check endpoint."""
    endpoint_calls_total.labels(endpoint='/health').inc()
    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': get_uptime()['seconds']
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={
            'error': 'Not Found',
            'message': 'Endpoint does not exist'
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle 500 errors."""
    logger.error(
        f"Internal server error: {str(exc)}",
        extra={
            'method': request.method,
            'path': str(request.url.path),
            'client_ip': request.client.host if request.client else 'unknown'
        },
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }
    )


if __name__ == "__main__":
    import uvicorn

    logger.info(
        'Starting DevOps Info Service',
        extra={
            'host': HOST,
            'port': PORT,
            'debug': DEBUG,
            'visits_file': str(VISITS_FILE)
        }
    )

    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        reload=False,
        log_level="debug" if DEBUG else "info"
    )
