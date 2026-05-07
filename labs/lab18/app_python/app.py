"""
DevOps Info Service
Main application module providing system information and health status.
Built with FastAPI for modern async support and automatic documentation.
"""
import json
import logging
import os
import platform
import socket
import tempfile
from pathlib import Path
from threading import Lock
from time import perf_counter
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)


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


# Configuration from environment variables
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
APP_ENV = os.getenv('APP_ENV', 'development')
APP_REGION = os.getenv('APP_REGION') or os.getenv('FLY_REGION', 'local')
LOG_LEVEL_NAME = os.getenv('LOG_LEVEL', 'INFO').upper()
CONFIG_PATH = os.getenv('CONFIG_PATH', '/config/config.json')
VISITS_FILE = os.getenv(
    'VISITS_FILE',
    os.path.join(
        os.getenv('DATA_DIR', os.path.join(os.getcwd(), 'data')),
        'visits',
    ),
)
TRACKED_SECRET_NAMES = tuple(
    name.strip()
    for name in os.getenv(
        'TRACKED_SECRET_NAMES',
        'APP_USERNAME,APP_PASSWORD',
    ).split(',')
    if name.strip()
)


# Configure JSON logging
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.handlers = [handler]
logging.root.setLevel(getattr(logging, LOG_LEVEL_NAME, logging.INFO))
logger = logging.getLogger(__name__)

for logger_name in ('uvicorn', 'uvicorn.error', 'uvicorn.access'):
    uvicorn_logger = logging.getLogger(logger_name)
    uvicorn_logger.handlers = [handler]
    uvicorn_logger.propagate = False

# Application start time for uptime calculation
START_TIME = datetime.now(timezone.utc)

# Service metadata
SERVICE_INFO = {
    'name': os.getenv('APP_NAME', 'devops-info-service'),
    'version': '1.0.0',
    'description': 'DevOps course info service',
    'framework': 'FastAPI'
}

# Available endpoints
ENDPOINTS = [
    {'path': '/', 'method': 'GET', 'description': 'Service information'},
    {
        'path': '/visits',
        'method': 'GET',
        'description': 'Persistent visits counter',
    },
    {'path': '/health', 'method': 'GET', 'description': 'Health check'},
    {'path': '/ready', 'method': 'GET', 'description': 'Readiness check'},
    {'path': '/metrics', 'method': 'GET', 'description': 'Prometheus metrics'}
]

IGNORED_METRIC_PATHS = {'/metrics'}

HTTP_REQUESTS_TOTAL = Counter(
    'http_requests_total',
    'Total HTTP requests processed by the application',
    ['method', 'endpoint', 'status_code']
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'status_code']
)
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed',
    ['method', 'endpoint']
)
DEVOPS_INFO_ENDPOINT_CALLS_TOTAL = Counter(
    'devops_info_endpoint_calls_total',
    'Application endpoint calls',
    ['endpoint']
)
DEVOPS_INFO_SYSTEM_INFO_COLLECTION_SECONDS = Histogram(
    'devops_info_system_info_collection_seconds',
    'Time spent collecting system information'
)

app = FastAPI(
    title="DevOps Info Service",
    description="A web service providing system information and health status",
    version="1.0.0"
)

logger.info("DevOps Info Service starting up", extra={
    "host": HOST,
    "port": PORT,
    "debug": DEBUG,
    "config_path": CONFIG_PATH,
    "visits_file": VISITS_FILE,
    "app_env": APP_ENV,
    "app_region": APP_REGION,
    "log_level": LOG_LEVEL_NAME,
})


class VisitCounterStore:
    """Persist a simple counter in a text file with atomic writes."""

    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self._lock = Lock()
        self._count = self._load_count()

    def _load_count(self):
        try:
            raw_value = self.file_path.read_text(encoding='utf-8').strip()
        except FileNotFoundError:
            return 0
        except OSError:
            logger.exception(
                'Failed to read visits file',
                extra={'visits_file': str(self.file_path)},
            )
            return 0

        if not raw_value:
            return 0

        try:
            return int(raw_value)
        except ValueError:
            logger.warning(
                'Invalid visits file content, resetting counter',
                extra={
                    'visits_file': str(self.file_path),
                    'raw_value': raw_value,
                },
            )
            return 0

    def _persist_count(self, count):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(
                'w',
                dir=self.file_path.parent,
                delete=False,
                encoding='utf-8',
            ) as handle:
                handle.write(str(count))
                handle.flush()
                os.fsync(handle.fileno())
                temp_file = handle.name
            os.replace(temp_file, self.file_path)
        finally:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)

    def get_count(self):
        with self._lock:
            return self._count

    def increment(self):
        with self._lock:
            self._count += 1
            self._persist_count(self._count)
            return self._count


VISIT_COUNTER = VisitCounterStore(VISITS_FILE)


def normalize_endpoint(request: Request):
    """Normalize endpoint labels to avoid high-cardinality metrics."""
    route = request.scope.get('route')
    route_path = getattr(route, 'path', None)
    if route_path:
        return route_path

    if request.url.path in {'/', '/health', '/metrics', '/visits'}:
        return request.url.path

    if request.url.path == '/ready':
        return request.url.path

    return '/unknown'


@app.middleware("http")
async def collect_http_metrics(request: Request, call_next):
    """Collect RED metrics for HTTP requests."""
    endpoint = normalize_endpoint(request)
    if endpoint in IGNORED_METRIC_PATHS:
        return await call_next(request)

    method = request.method
    in_progress = HTTP_REQUESTS_IN_PROGRESS.labels(
        method=method,
        endpoint=endpoint,
    )
    in_progress.inc()
    start_time = perf_counter()
    status_code = '500'

    try:
        response = await call_next(request)
        status_code = str(response.status_code)
        return response
    finally:
        duration = perf_counter() - start_time
        HTTP_REQUESTS_TOTAL.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
        ).observe(duration)
        in_progress.dec()


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
    response_message = (
        f"Response {response.status_code} "
        f"for {request.method} {request.url.path}"
    )
    logger.info(
        response_message,
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
    with DEVOPS_INFO_SYSTEM_INFO_COLLECTION_SECONDS.time():
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


def load_config_file():
    """Load the mounted application configuration file on demand."""
    config = {
        'path': CONFIG_PATH,
        'loaded': False,
        'data': None,
    }

    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as handle:
            config['data'] = json.load(handle)
    except FileNotFoundError:
        return config
    except json.JSONDecodeError:
        logger.exception(
            'Failed to parse config file',
            extra={'config_path': CONFIG_PATH},
        )
        config['error'] = 'invalid-json'
        return config
    except OSError:
        logger.exception(
            'Failed to read config file',
            extra={'config_path': CONFIG_PATH},
        )
        config['error'] = 'read-error'
        return config

    config['loaded'] = True
    return config


def get_app_configuration():
    """Return configuration visible to the application."""
    return {
        'file': load_config_file(),
        'environment': {
            'app_env': APP_ENV,
            'app_region': APP_REGION,
            'log_level': LOG_LEVEL_NAME,
        },
        'platform': {
            'provider': 'fly.io' if os.getenv('FLY_APP_NAME') else 'local',
            'fly_app_name': os.getenv('FLY_APP_NAME'),
            'fly_region': os.getenv('FLY_REGION'),
        },
        'secrets': {
            name: bool(os.getenv(name))
            for name in TRACKED_SECRET_NAMES
        },
        'paths': {
            'config': CONFIG_PATH,
            'visits': VISITS_FILE,
        }
    }


@app.get('/')
async def index(request: Request):
    """Main endpoint - service and system information."""
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint='/').inc()
    visits_count = VISIT_COUNTER.increment()
    return {
        'service': SERVICE_INFO,
        'system': get_system_info(),
        'runtime': get_runtime_info(),
        'request': get_request_info(request),
        'configuration': get_app_configuration(),
        'visits': {
            'count': visits_count,
            'file': VISITS_FILE,
        },
        'endpoints': ENDPOINTS
    }


@app.get('/visits')
async def visits():
    """Return the current persisted visits count without incrementing it."""
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint='/visits').inc()
    return {
        'count': VISIT_COUNTER.get_count(),
        'file': VISITS_FILE,
    }


@app.get('/health')
async def health():
    """Health check endpoint for monitoring."""
    logger.debug('Health check requested')
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint='/health').inc()

    uptime = get_uptime()
    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': uptime['seconds']
    }


@app.get('/ready')
async def ready():
    """Readiness endpoint for orchestrators."""
    DEVOPS_INFO_ENDPOINT_CALLS_TOTAL.labels(endpoint='/ready').inc()
    return {
        'status': 'ready',
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }


@app.get('/metrics')
async def metrics():
    """Expose Prometheus metrics for scraping."""
    return Response(
        content=generate_latest(),
        headers={'Content-Type': CONTENT_TYPE_LATEST},
    )


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
    uvicorn.run(
        'app:app',
        host=HOST,
        port=PORT,
        reload=DEBUG,
        access_log=False,
        log_config=None,
    )
