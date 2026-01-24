from math import log
import os
import re
import time
import fastapi
import platform
import socket
from datetime import datetime, timezone
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8080))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"


def get_uptime_human(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{int(hours)} hour, {int(minutes)} minutes"


def get_metadata(request: Request):
    uptime_seconds = int(time.time() - START_TIME)
    return {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "FastAPI",
        },
        "system": {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.release(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
            "python_version": platform.python_version(),
        },
        "runtime": {
            "uptime_seconds": uptime_seconds,
            "uptime_human": get_uptime_human(uptime_seconds),
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "request": {
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "method": request.method,
            "path": request.url.path,
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
        ],
    }


app = fastapi.FastAPI()


@app.get("/")
def get_info(request: Request):
    logger.info("Info requested")
    return get_metadata(request)


@app.get("/health")
def health_check():
    logger.info("Health check requested")
    return get_health()


def get_health():
    uptime_seconds = int(time.time() - START_TIME)
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_seconds,
    }


@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(f"404 Not Found: {request.url.path}")
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "message": "Endpoint does not exist"},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        },
    )


if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server at http://{HOST}:{PORT}, debug={DEBUG}")
    uvicorn.run(app, host=HOST, port=PORT, reload=DEBUG)
