import logging
import json
import os
import platform
import socket
import time
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"


class JSONFormatter(logging.Formatter):
    """Format log records as structured JSON for Loki/Promtail."""

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        log = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include any custom attributes (e.g., request context) that don't start with "_"
        for key, value in record.__dict__.items():
            if key.startswith("_"):
                continue
            if key in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
            }:
                continue
            log[key] = value

        if record.exc_info:
            log["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(log, ensure_ascii=False)


root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Remove default handlers configured by other libraries/tests
for handler in list(root_logger.handlers):
    root_logger.removeHandler(handler)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(JSONFormatter())
root_logger.addHandler(stream_handler)

logger = logging.getLogger(__name__)

app = FastAPI(title="DevOps Info Service")
START_TIME = datetime.now(timezone.utc)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log each HTTP request and response in JSON format."""
    start_time = time.time()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.time() - start_time) * 1000
        logger.exception(
            "Request failed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
                "duration_ms": round(duration_ms, 2),
            },
        )
        raise

    duration_ms = (time.time() - start_time) * 1000
    logger.info(
        "Request handled",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "client_ip": request.client.host if request.client else None,
            "duration_ms": round(duration_ms, 2),
        },
    )
    return response

def get_runtime_info():
    """Calculate uptime and current time metrics."""
    now = datetime.now(timezone.utc)
    delta = now - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    return {
        "uptime_seconds": seconds,
        "uptime_human": f"{hours} hours, {minutes} minutes",
        "current_time": now.isoformat(),
        "timezone": "UTC",
    }
@app.get("/", tags=["Info"])
async def read_root(request: Request):
    """Main endpoint returning comprehensive service and system information."""
    logger.info(
        "Root endpoint called",
        extra={
            "client_ip": request.client.host if request.client else None,
            "method": request.method,
            "path": request.url.path,
        },
    )
    try:
        return {
            "service": {
                "name": "devops-info-service",
                "version": "1.0.0",
                "description": "DevOps course info service",
                "framework": "FastAPI"
            },
            "system": {
                "hostname": socket.gethostname(),
                "platform": platform.system(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "cpu_count": os.cpu_count() or "unknown",
                "python_version": platform.python_version(),
            },
            "runtime": get_runtime_info(),
            "request": {
                "client_ip": request.client.host,
                "user_agent": request.headers.get("User-Agent"),
                "method": request.method,
                "path": request.url.path
            },
            "endpoints": [
                {"path": "/", "method": "GET", "description": "Service information"},
                {"path": "/health", "method": "GET", "description": "Health check"},
            ],
        }
    except Exception as e:
        logger.error(
            "Error in root endpoint",
            extra={"error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/health", tags=["Monitoring"])
async def health():
    """Simple health check endpoint for monitoring."""
    runtime = get_runtime_info()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": runtime["uptime_seconds"],
    }

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "message": f"Endpoint {request.url.path} does not exist"}
    )

if __name__ == "__main__":
    logger.info(
        "Starting service",
        extra={
            "host": HOST,
            "port": PORT,
            "debug": DEBUG,
        },
    )
    uvicorn.run("app:app", host=HOST, port=PORT, reload=DEBUG)
