"""
DevOps Info Service (JSON Logging)
Modified for Lab 7 to emit structured JSON logs suitable for Loki ingestion.
"""

import os
import socket
import platform
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# JSON logging setup
try:
    # import the JSON formatter class; probe correct module path
    from pythonjsonlogger.json import JsonFormatter
except ImportError:  # fallback if package missing
    JsonFormatter = None

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# clear default handlers
for handler in list(root_logger.handlers):
    root_logger.removeHandler(handler)

stream_handler = logging.StreamHandler()
if JsonFormatter:
    # use standard field names so they can be parsed easily by log collectors
    fmt = '%(asctime)s %(levelname)s %(name)s %(message)s'
    formatter = JsonFormatter(fmt)
else:
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)
root_logger.addHandler(stream_handler)

logger = logging.getLogger(__name__)

# Configuration from environment variables
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

app = FastAPI(
    title="DevOps Info Service",
    description="A DevOps service providing system and runtime information",
    version="1.0.0"
)

START_TIME = datetime.now(timezone.utc)


# helper functions

def get_system_info() -> Dict[str, Any]:
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': f"{platform.system()} {platform.release()}",
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count() or 1,
        'python_version': platform.python_version()
    }


def get_uptime_info() -> Dict[str, Any]:
    delta = datetime.now(timezone.utc) - START_TIME
    total_seconds = int(delta.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    human_readable = f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
    return {
        'uptime_seconds': total_seconds,
        'uptime_human': human_readable
    }


def get_endpoints_list() -> List[Dict[str, str]]:
    return [
        {'path': '/', 'method': 'GET', 'description': 'Service and system information'},
        {'path': '/health', 'method': 'GET', 'description': 'Health check endpoint'}
    ]


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = datetime.now(timezone.utc)
    response = await call_next(request)
    duration = (datetime.now(timezone.utc) - start).total_seconds()
    client_ip = request.client.host if request.client else None
    extra = {
        'timestamp': datetime.now(timezone.utc).isoformat() + 'Z',
        'method': request.method,
        'path': request.url.path,
        'status_code': response.status_code,
        'client_ip': client_ip,
        'duration': duration,
    }
    logger.info("request completed", extra=extra)
    return response


@app.get('/', response_class=JSONResponse)
async def index(request: Request) -> Dict[str, Any]:
    client_ip = request.client.host if request.client else None
    logger.info(
        "handling index",
        extra={
            'method': request.method,
            'path': request.url.path,
            'client_ip': client_ip
        }
    )
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
            'client_ip': client_ip,
            'user_agent': request.headers.get('user-agent', 'unknown'),
            'method': request.method,
            'path': request.url.path
        },
        'endpoints': get_endpoints_list()
    }


@app.get('/health', response_class=JSONResponse)
async def health(request: Request) -> Dict[str, Any]:
    logger.debug("health check invoked")
    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat() + 'Z',
        'uptime_seconds': get_uptime_info()['uptime_seconds']
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.warning(
        "not found",
        extra={'path': request.url.path, 'method': request.method}
    )
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
    logger.error("unexpected error", extra={'error': str(exc)})
    return JSONResponse(
        status_code=500,
        content={
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }
    )


@app.get('/docs', include_in_schema=False)
async def swagger_ui():
    from fastapi.openapi.docs import get_swagger_ui_html
    return get_swagger_ui_html(openapi_url='/openapi.json', title='DevOps Info Service')


logger.info(f"FastAPI application configured on {HOST}:{PORT}")
logger.info(f"Debug mode: {DEBUG}")


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app:app', host=HOST, port=PORT, log_level='info')