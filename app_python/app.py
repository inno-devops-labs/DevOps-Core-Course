import os
import socket
import platform
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() in ("1", "true", "yes")

# Logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("devops-info-service")
logger.info("Starting DevOps Info Service (FastAPI)")

# Application and start time
app = FastAPI(title="devops-info-service", version="1.0.0", debug=DEBUG)
START_TIME = datetime.now(timezone.utc)


def get_uptime() -> Dict[str, Any]:
    """Return uptime in seconds and human readable string."""

    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    human = f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
    return {"seconds": seconds, "human": human}


def get_system_info() -> Dict[str, Any]:
    """Collect static system information."""

    try:
        platform_version = platform.version()
    except Exception:
        platform_version = platform.release()

    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform_version,
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count() or 1,
        "python_version": platform.python_version(),
    }


def _format_iso_z(dt: datetime) -> str:
    """Return ISO8601 with trailing Z for UTC times."""

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def get_request_info(request: Request) -> Dict[str, Any]:
    """Extract request info (consider X-Forwarded-For)."""

    # Prefer X-Forwarded-For if present (for proxies), else use client.host
    xff = request.headers.get("x-forwarded-for")
    if xff:
        client_ip = xff.split(",")[0].strip()
    else:
        # request.client may be None in some test scenarios
        client_ip = request.client.host if request.client else "unknown"

    user_agent = request.headers.get("user-agent", "")
    return {
        "client_ip": client_ip,
        "user_agent": user_agent,
        "method": request.method,
        "path": request.url.path,
    }


ENDPOINTS = [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"},
]


@app.get("/", summary="Service and system information")
async def index(request: Request):
    """Main endpoint returning comprehensive info about service & runtime."""

    logger.debug(f"Request: {request.method} {request.url.path} from {request.client}")
    system = get_system_info()
    uptime = get_uptime()

    response = {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "FastAPI",
        },
        "system": system,
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": _format_iso_z(datetime.now(timezone.utc)),
            "timezone": "UTC",
        },
        "request": get_request_info(request),
        "endpoints": ENDPOINTS,
    }
    return JSONResponse(content=response)


@app.get("/health", summary="Health check")
async def health(request: Request):
    """Simple health endpoint (used for liveness/readiness)."""

    logger.debug(f"Request: {request.method} {request.url.path} from {request.client}")
    uptime = get_uptime()
    payload = {
        "status": "healthy",
        "timestamp": _format_iso_z(datetime.now(timezone.utc)),
        "uptime_seconds": uptime["seconds"],
    }
    return JSONResponse(content=payload)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(f"HTTP exception: {exc.detail} ({exc.status_code}) for {request.url.path}")
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error for {request.url.path}: {exc}")
    return JSONResponse(status_code=400, content={"error": "Invalid request", "details": str(exc)})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error for {request.url.path}: {exc}")
    return JSONResponse(status_code=500, content={"error": "Internal Server Error", "message": str(exc)})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host=HOST, port=PORT, reload=DEBUG)
