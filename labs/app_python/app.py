import os
import time
import json
import fastapi
import platform
import socket
from datetime import datetime, timezone
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import sys


# JSON Logging Formatter for structured logging
class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging compatible with Loki"""

    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


# Configure logging based on LOG_FORMAT environment variable
LOG_FORMAT = os.getenv("LOG_FORMAT", "text").lower()

if LOG_FORMAT == "json":
    # JSON format for production/monitoring
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logging.root.handlers = []
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.INFO)
else:
    # Human-readable format for development
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
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


# Helper function for structured request logging
def log_request(request: Request, message: str, level: str = "INFO", **extra):
    """Log request with contextual information"""
    log_data = {
        "method": request.method,
        "path": str(request.url.path),
        "client_ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
        **extra,
    }

    # Create log record with extra data
    record = logging.LogRecord(
        name=logger.name,
        level=getattr(logging, level),
        pathname=__file__,
        lineno=0,
        msg=message,
        args=(),
        exc_info=None,
    )
    record.extra_data = log_data

    if LOG_FORMAT == "json":
        logger.handle(record)
    else:
        logger.log(getattr(logging, level), f"{message} - {log_data}")


@app.on_event("startup")
async def startup_event():
    """Log application startup"""
    logger.info(
        f"Application starting - host={HOST}, port={PORT}, log_format={LOG_FORMAT}"
    )


@app.get("/")
def get_info(request: Request):
    log_request(request, "Info endpoint requested", status_code=200)
    return get_metadata(request)


@app.get("/health")
def health_check(request: Request):
    log_request(request, "Health check requested", status_code=200)
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
    log_request(request, "Endpoint not found", level="WARNING", status_code=404)
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "message": "Endpoint does not exist"},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log_request(
        request,
        f"Unhandled exception: {str(exc)}",
        level="ERROR",
        status_code=500,
        exception_type=type(exc).__name__,
    )
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

    # Disable uvicorn's access logging (we log requests ourselves)
    # This keeps only our JSON logs clean
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        reload=DEBUG,
        access_log=False,  # Disable uvicorn access logs
        log_level="warning",  # Only show warnings/errors from uvicorn
    )
