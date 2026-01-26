"""
DevOps Info Service
Main application module

@author: egorTorshin
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import platform
import socket
from datetime import datetime, timezone
import os
import logging

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

app = FastAPI()

logger.info(f'Starting DevOps Info Service on {HOST}:{PORT}')

# Uptime calculation
START_TIME = datetime.now()

def get_uptime():
    """Collect system information."""
    delta = datetime.now() - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }

@app.get("/")
def get_user_system_info(request: Request):
    logger.info(f'Request: {request.method} {request.url.path} from {request.client.host}')
    uptime_data = get_uptime()
    return {
        'service': {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
             "framework": "FastAPI"
        },
        'system': {
            'hostname': socket.gethostname(),
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'cpu_count': os.cpu_count(),
            'python_version': platform.python_version(),
        },
        "runtime": {
            "uptime_seconds": uptime_data['seconds'],
            "uptime_human": uptime_data['human'],
            "current_time": datetime.now().isoformat(),
            "timezone": str(datetime.now().astimezone().tzinfo)
        },
        "request": {
            "client_ip": request.client.host,
            "user_agent": request.headers.get('user-agent'),
            "method": request.method,
            "path": request.url.path
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"}
        ]
    }

@app.get("/health")
def health():
    logger.debug('Health check endpoint called')
    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': get_uptime()['seconds']
    }

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(f'HTTP {exc.status_code} error: {exc.detail}')
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'error': exc.detail,
            'message': 'Endpoint does not exist' if exc.status_code == 404 else 'An error occurred'
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f'Internal server error: {str(exc)}', exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }
    )

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on {HOST}:{PORT}")
    logger.info(f"Debug mode: {DEBUG}")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
