import logging
import os
import platform
import socket
import json
from datetime import datetime, timezone
from typing import Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from metrics import *

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        if hasattr(record, "method"):
            log_record["method"] = record.method

        if hasattr(record, "path"):
            log_record["path"] = record.path

        if hasattr(record, "status_code"):
            log_record["status_code"] = record.status_code

        if hasattr(record, "client_ip"):
            log_record["client_ip"] = record.client_ip

        return json.dumps(log_record)


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())

logger = logging.getLogger("devops-app")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

app = FastAPI(
    title="DevOps Info Service",
    description="Service information and system monitoring API",
    version="1.0.0"
)

def normalize_endpoint(path: str) -> str:
    """Нормализует путь для метрик (избегает высокого cardinality)"""
    if path.startswith("/metrics"):
        return "/metrics"
    elif path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi.json"):
        return "/docs"
    elif path.startswith("/error-test"):
        return "/error-test"
    else:
        # Для всех остальных эндпоинтов используем сам путь
        return path

@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Увеличиваем счетчик активных запросов
    http_requests_in_progress.inc()

    # Получаем нормализованный endpoint
    endpoint = normalize_endpoint(request.url.path)

    start_time_req = datetime.now()
    client_ip = request.client.host if request.client else "unknown"

    try:
        response = await call_next(request)

        process_time = (datetime.now() - start_time_req).total_seconds()

        # Записываем метрики
        http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code
        ).inc()

        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(process_time)

        logger.info(
            "HTTP request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "client_ip": client_ip,
                "duration_seconds": process_time
            }
        )

        return response

    except Exception as exc:
        # Для ошибок тоже записываем метрики
        http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=500
        ).inc()

        logger.error(
            "HTTP error",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client_ip": client_ip
            }
        )
        raise exc
    finally:
        # Уменьшаем счетчик активных запросов
        http_requests_in_progress.dec()

@app.on_event("startup")
async def startup_event():
    logger.info("application startup")

@app.get("/error-test")
async def error_test(request: Request):
    raise RuntimeError("Test error log")

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=404,
        content={
            'error': 'Not Found',
            'message': 'Endpoint does not exist',
            'path': request.url.path
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            'error': 'Validation Error',
            'message': 'Invalid request parameters',
            'details': exc.errors()
        }
    )

start_time = datetime.now()

hostname = socket.gethostname()
platform_name = platform.system()
platform_version = platform.release()
architecture = platform.machine()
cpu_count = os.cpu_count() or 0
python_version = platform.python_version()


def get_uptime() -> Dict[str, str]:
    """Calculate service uptime"""
    try:
        delta = datetime.now() - start_time
        seconds = int(delta.total_seconds())
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60

        return {
            'seconds': seconds,
            'human': f"{hours} hour{'s' if hours != 1 else ''}, "
                     f"{minutes} minute{'s' if minutes != 1 else ''}"
        }
    except Exception as e:
        logger.error(f"Error calculating uptime: {e}")
        return {'seconds': 0, 'human': 'unknown'}


@app.get("/", response_class=JSONResponse)
async def get_service_info(request: Request):
    """Main endpoint - returns comprehensive service and system information"""
    # Увеличиваем счетчик вызовов эндпоинта
    endpoint_calls.labels(endpoint="/").inc()

    try:
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get('user-agent', 'unknown')

        # Измеряем время сбора системной информации
        with system_info_duration.time():
            uptime = get_uptime()

        response = {
            "service": {
                "name": "devops-info-service",
                "version": "1.0.0",
                "description": "DevOps course info service",
                "framework": "FastAPI"
            },
            "system": {
                "hostname": hostname,
                "platform": platform_name,
                "platform_version": platform_version,
                "architecture": architecture,
                "cpu_count": cpu_count,
                "python_version": python_version
            },
            "runtime": {
                "uptime_seconds": uptime['seconds'],
                "uptime_human": uptime['human'],
                "current_time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "timezone": "UTC"
            },
            "request": {
                "client_ip": client_ip,
                "user_agent": user_agent,
                "method": request.method,
                "path": request.url.path
            },
            "endpoints": [
                {"path": "/", "method": "GET", "description": "Service information"},
                {"path": "/health", "method": "GET", "description": "Health check"},
                {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
                {"path": "/docs", "method": "GET", "description": "Swagger documentation"},
                {"path": "/redoc", "method": "GET", "description": "ReDoc documentation"}
            ]
        }

        return response

    except Exception as e:
        logger.error(f"Error in main endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health", response_class=JSONResponse)
async def health_check():
    """Health check endpoint for monitoring and Kubernetes probes"""
    # Увеличиваем счетчик вызовов эндпоинта
    endpoint_calls.labels(endpoint="/health").inc()

    try:
        uptime = get_uptime()

        response = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "uptime_seconds": uptime['seconds'],
            "service": "devops-info-service",
            "version": "1.0.0"
        }

        return response

    except Exception as e:
        logger.error(f"Error in health check: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.get("/error-test")
async def error_test(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    logger.error(
        "Test error log",
        extra={
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": "ERROR",
            "method": request.method,
            "path": request.url.path,
            "status_code": 500,
            "client_ip": client_ip
        }
    )
    raise HTTPException(status_code=500, detail="Test error")


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

if __name__ == "__main__":
    import uvicorn

    logger.info(
        "application starting",
        extra={
            "host": HOST,
            "port": PORT,
            "debug": DEBUG
        }
    )

    logger.info(
        "debug mode configuration",
        extra={
            "debug": DEBUG
        }
    )

    uvicorn.run(
        "app:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="debug" if DEBUG else "info"
    )