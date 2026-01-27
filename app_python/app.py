from typing import Union

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
import platform
import socket
from datetime import datetime, timezone
import logging

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

logging.basicConfig(
    level=logging.INFO if not DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


app = FastAPI()
start_time = datetime.now()


@app.get("/")
def read_root(request: Request):
    logger.debug(f'Request: {request.method} {request.url}')
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

# Custom error handler for 500 Internal Server Error


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
