#!/usr/bin/env python3

import aiofiles
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
import os
import platform
import socket
from datetime import datetime, timezone
import logging
import json
import time
import uuid
from contextlib import asynccontextmanager
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import asyncio


HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
DATA_DIR = os.getenv('DATA_DIR', '/data')
VISITS_FILE = os.path.join(DATA_DIR, 'visits.json')


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "app": "devops-python",
            "logger": record.name
        }
        if hasattr(record, "extra_info"):
            log_record.update(record.extra_info)
        return json.dumps(log_record)


logger = logging.getLogger("app")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)
logger.propagate = False

app = FastAPI()
start_time = datetime.now()

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed'
)

# Application-specific metrics

uptime_seconds = Gauge(
    'app_uptime_seconds',
    'Application uptime in seconds'
)

endpoint_response_size_bytes = Histogram(
    'endpoint_response_size_bytes',
    'Response payload size in bytes',
    ['endpoint']
)


@app.middleware("http")
async def dispatch(request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)

    http_requests_in_progress.inc()

    start_time = time.time()
    status_code = 500
    response = None
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        http_requests_in_progress.dec()
        raise
    finally:
        duration = time.time() - start_time

        http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=status_code
        ).inc()

        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)

        if response and hasattr(response, 'body'):
            response_size = len(response.body)
            endpoint_response_size_bytes.labels(
                endpoint=request.url.path).observe(response_size)

        http_requests_in_progress.dec()

    return response


async def ensure_data_dir():
    """Ensure data directory exists"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
        logger.info(f"Created data directory: {DATA_DIR}")


async def initialize_visits_file():
    try:
        if not os.path.exists(VISITS_FILE):
            await ensure_data_dir()
            initial_data = {
                "count": 0,
            }
            async with aiofiles.open(VISITS_FILE, 'w') as f:
                await f.write(json.dumps(initial_data, indent=2))
            logger.info(f"Initialized visits file: {VISITS_FILE}")
    except Exception as e:
        logger.error(f"Failed to initialize visits file: {str(e)}")


async def read_visits_from_file():
    try:
        if not os.path.exists(VISITS_FILE):
            return 0

        async with aiofiles.open(VISITS_FILE, 'r') as f:
            content = await f.read()
            data = json.loads(content)
            return data.get('count', 0)
    except Exception as e:
        logger.error(f"Failed to read visits from file: {str(e)}")
        return 0


async def increment_and_save_visits():
    try:
        current_count = await read_visits_from_file()

        new_count = current_count + 1

        updated_data = {
            "count": new_count,
        }

        async with aiofiles.open(VISITS_FILE, 'w') as f:
            await f.write(json.dumps(updated_data, indent=2))

        logger.debug(f"Visits incremented from {current_count} to {new_count}")

        return new_count
    except Exception as e:
        logger.error(f"Failed to increment visits: {str(e)}")
        return None


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()

    log_context = {
        "request_id": request_id,
        "client_ip": request.client.host if request.client else "unknown",
        "method": request.method,
        "path": request.url.path
    }

    try:
        response = await call_next(request)
        process_time = int((time.time() - start_time) * 1000)

        log_context.update({
            "status_code": response.status_code,
            "duration_ms": process_time
        })

        logger.info(f"Request handled: {request.method} {request.url.path}",
                    extra={"extra_info": log_context})

        return response

    except Exception as e:
        process_time = int((time.time() - start_time) * 1000)
        log_context.update({
            "status_code": 500,
            "duration_ms": process_time,
            "error": str(e)
        })
        logger.error(f"Request failed: {str(e)}",
                     extra={"extra_info": log_context})
        raise e


@asynccontextmanager
async def lifespan(app: FastAPI):
    startup_config = {
        "version": "1.3.0",
        "mode": "production",
        "log_level": "INFO"
    }
    logger.info("Application starting up", extra={
                "extra_info": {"config": startup_config}})

    await ensure_data_dir()
    await initialize_visits_file()

    async def update_uptime():
        while True:
            uptime_seconds.set(get_uptime()['seconds'])
            await asyncio.sleep(5)  # Update every 5 seconds

    uptime_task = asyncio.create_task(update_uptime())

    yield

    logger.info("Application shutting down")
    uptime_task.cancel()


@app.get('/metrics')
def metrics():
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/visits")
async def get_visits(request: Request):
    logger.debug(f'Request: {request.method} {request.url}')

    visits_count = await read_visits_from_file()

    return {
        'visits': visits_count,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


@app.get("/")
async def read_root(request: Request):
    logger.debug(f'Request: {request.method} {request.url}')

    await increment_and_save_visits()

    hostname = socket.gethostname()
    platform_name = platform.system()
    platform_ver = platform.release()
    architecture = platform.machine()
    cpu_cores = os.cpu_count()
    python_version = platform.python_version()
    url_list = [{"path": route.path, "description": route.name,
                 "methods": route.methods} for route in app.routes]
    return {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "FastAPI"
        },
        "system": {
            "hostname": hostname,
            "platform": platform_name,
            "platform_version": platform_ver,
            "architecture": architecture,
            "cpu_count": cpu_cores,
            "python_version": python_version
        },
        "runtime": {
            "uptime_seconds": get_uptime()['seconds'],
            "uptime_human": get_uptime()['human'],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC"
        },
        "request": {
            "client_ip": request.client.host,
            "user_agent": request.headers.get('user-agent'),
            "method": request.method,
            "path": request.url.path
        },
        "endpoints": url_list
    }


@app.get("/health")
def health(request: Request):
    logger.debug(f'Request: {request.method} {request.url}')
    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': get_uptime()['seconds']
    }


def get_uptime():
    delta = datetime.now() - start_time
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }


@app.exception_handler(404)
async def not_found(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            'error': 'Not Found',
            'message': 'Endpoint does not exist'
        }
    )


@app.exception_handler(500)
async def internal_error(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }
    )

if __name__ == "__main__":
    import uvicorn
    logger.info('Application starting...')
    uvicorn.run(app, host=HOST, port=PORT,
                log_level='debug' if DEBUG else 'info')
