"""
DevOps Info Service
Main application module providing system information and health status.
Built with FastAPI for modern async support and automatic documentation.
"""
import os
import json
import socket
import platform
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


STANDARD_LOG_RECORD_FIELDS = {
    'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
    'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs',
    'message', 'msg', 'name', 'pathname', 'process', 'processName',
    'relativeCreated', 'stack_info', 'thread', 'threadName', 'taskName'
}


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured logging."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key in STANDARD_LOG_RECORD_FIELDS or key.startswith('_'):
                continue
            try:
                json.dumps(value)
                log_entry[key] = value
            except TypeError:
                log_entry[key] = str(value)
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


# Configure JSON logging
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.handlers = [handler]
logging.root.setLevel(logging.INFO)
logger = logging.getLogger(__name__)

for logger_name in ('uvicorn', 'uvicorn.error', 'uvicorn.access'):
    uvicorn_logger = logging.getLogger(logger_name)
    uvicorn_logger.handlers = [handler]
    uvicorn_logger.propagate = False

# Configuration from environment variables
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Application start time for uptime calculation
START_TIME = datetime.now(timezone.utc)

# Service metadata
SERVICE_INFO = {
    'name': 'devops-info-service',
    'version': '1.0.0',
    'description': 'DevOps course info service',
    'framework': 'FastAPI'
}

# Available endpoints
ENDPOINTS = [
    {'path': '/', 'method': 'GET', 'description': 'Service information'},
    {'path': '/health', 'method': 'GET', 'description': 'Health check'}
]

app = FastAPI(
    title="DevOps Info Service",
    description="A web service providing system information and health status",
    version="1.0.0"
)

logger.info("DevOps Info Service starting up", extra={
    "host": HOST, "port": PORT, "debug": DEBUG
})


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and responses."""
    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        f"{request.method} {request.url.path} from {client_ip}",
        extra={
            "method": request.method,
            "path": str(request.url.path),
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent", "Unknown"),
        },
    )
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            f"Unhandled exception during {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": str(request.url.path),
                "client_ip": client_ip,
            },
        )
        raise
    logger.info(
        f"Response {response.status_code} for {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": str(request.url.path),
            "client_ip": client_ip,
            "status_code": response.status_code,
        },
    )
    return response


def get_uptime():
    """Calculate application uptime."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    # Build human-readable string
    parts = []
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if secs > 0 or not parts:
        parts.append(f"{secs} second{'s' if secs != 1 else ''}")

    return {
        'seconds': seconds,
        'human': ', '.join(parts)
    }


def get_system_info():
    """Collect system information."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.platform(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count(),
        'python_version': platform.python_version()
    }


def get_runtime_info():
    """Get runtime information."""
    uptime = get_uptime()
    return {
        'uptime_seconds': uptime['seconds'],
        'uptime_human': uptime['human'],
        'current_time': datetime.now(timezone.utc).isoformat(),
        'timezone': 'UTC'
    }


def get_request_info(request: Request):
    """Get request information."""
    client_ip = request.client.host if request.client else 'unknown'
    return {
        'client_ip': client_ip,
        'user_agent': request.headers.get('user-agent', 'Unknown'),
        'method': request.method,
        'path': str(request.url.path)
    }


@app.get('/')
async def index(request: Request):
    """Main endpoint - service and system information."""
    return {
        'service': SERVICE_INFO,
        'system': get_system_info(),
        'runtime': get_runtime_info(),
        'request': get_request_info(request),
        'endpoints': ENDPOINTS
    }


@app.get('/health')
async def health():
    """Health check endpoint for monitoring."""
    logger.debug('Health check requested')

    uptime = get_uptime()
    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': uptime['seconds']
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    logger.warning(
        f'404 Not Found: {request.url.path}',
        extra={
            'method': request.method,
            'path': str(request.url.path),
            'status_code': 404,
            'client_ip': request.client.host if request.client else 'unknown',
        },
    )
    return JSONResponse(
        status_code=404,
        content={
            'error': 'Not Found',
            'message': 'Endpoint does not exist',
            'path': str(request.url.path)
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors."""
    logger.error(
        f'500 Internal Server Error: {str(exc)}',
        extra={
            'method': request.method,
            'path': str(request.url.path),
            'status_code': 500,
            'client_ip': request.client.host if request.client else 'unknown',
        },
    )
    return JSONResponse(
        status_code=500,
        content={
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }
    )


if __name__ == '__main__':
    import uvicorn
    logger.info(f'Starting DevOps Info Service on {HOST}:{PORT}')
    logger.info(f'Debug mode: {DEBUG}')
    uvicorn.run('app:app', host=HOST, port=PORT, reload=DEBUG, access_log=False, log_config=None)
