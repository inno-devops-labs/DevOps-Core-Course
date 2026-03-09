import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
import uvicorn
from pythonjsonlogger.json import JsonFormatter

from core.runtime import set_start_time
from routes.router import api_router
from config import settings
import logging

SERVICE_TITLE = "devops-info-service"
SERVICE_VERSION = "1.0.0"
SERVICE_DESCRIPTION = "DevOps course info service"
SERVICE_FRAMEWORK = "FastAPI"

LOG_FORMAT = os.getenv("LOG_FORMAT", "json")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

if LOG_FORMAT == "json":
    handler = logging.StreamHandler()
    formatter = JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
    handler.setFormatter(formatter)
    logger.handlers = [handler]

    for uv_logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        uv_logger = logging.getLogger(uv_logger_name)
        uv_logger.handlers = [handler]
else:
    from colorlog import ColoredFormatter

    handler = logging.StreamHandler()
    formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )
    handler.setFormatter(formatter)
    logger.handlers = [handler]


@asynccontextmanager
async def lifespan(app: FastAPI):
    set_start_time()
    logging.info(
        "Application started",
        extra={
            "event": "startup",
            "service": SERVICE_TITLE,
            "version": SERVICE_VERSION,
        },
    )
    yield
    logging.info("Application stopped", extra={"event": "shutdown"})


app = FastAPI(
    title=SERVICE_TITLE,
    version=SERVICE_VERSION,
    description=SERVICE_DESCRIPTION,
    lifespan=lifespan,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 2)

    logging.info(
        "HTTP request",
        extra={
            "event": "http_request",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "client_ip": request.client.host if request.client else "unknown",
        },
    )
    return response


app.include_router(api_router)


if __name__ == "__main__":
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
