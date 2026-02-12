import fastapi
from datetime import datetime, timezone
import uvicorn
import logging
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


app = fastapi.FastAPI()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

start_time = None


def get_uptime():
    global start_time
    if start_time is None:
        start_time = datetime.now()
    delta = datetime.now() - start_time
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }


def get_system():
    import platform
    import socket

    return {
        "hostname": socket.gethostname(),
        "platform_name": platform.system(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
    }


@app.middleware("http")
async def log_requests(request: fastapi.Request, call_next):
    start_time_middleware = datetime.now()

    logger.info(f"Request started: {request.method} {request.url.path}")
    logger.debug(f"Headers: {dict(request.headers)}")
    logger.debug(
        f"Client IP: {
            request.client.host if request.client else 'Unknown'}")

    try:
        response = await call_next(request)
        process_time = (
            datetime.now() - start_time_middleware).total_seconds() * 1000

        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"- Status: {response.status_code} "
            f"- Time: {process_time:.2f}ms"
        )

        return response

    except Exception as ex:
        logger.error(
            f"Request failed: {request.method} {request.url.path} - Error: {str(ex)}")
        raise


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
        request: fastapi.Request,
        exc: StarletteHTTPException):
    if exc.status_code == 404:
        logger.warning(
            f"404 Not Found: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'Unknown'}"
        )

        return JSONResponse(
            status_code=404,
            content={
                "error": "Not Found",
                "message": f"The requested URL {
                    request.url.path} was not found on this server.",
                "status_code": 404,
                "timestamp": datetime.now(
                    timezone.utc).isoformat(),
            })

    logger.error(f"HTTP Error {exc.status_code}: {str(exc.detail)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": str(exc.detail),
            "status_code": exc.status_code,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
        request: fastapi.Request,
        exc: RequestValidationError):
    logger.warning(
        f"Validation error: {
            exc.errors()} for request {
            request.method} {
                request.url.path}")

    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "Invalid request parameters",
            "details": exc.errors(),
            "status_code": 422,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: fastapi.Request, exc: Exception):
    logger.error(
        f"Unhandled exception: {str(exc)} "
        f"for request {request.method} {request.url.path}",
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
            "status_code": 500,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@app.get("/")
def main_page(request: fastapi.Request):
    logger.debug(f'Request: {request.method} {request.url.path}')
    time = get_uptime()
    return {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "FastAPI"
        },
        "system": get_system(),
        "runtime": time,
        "request": {
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
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
    logger.debug("Health check requested")
    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': get_uptime()['seconds']
    }


def start():
    import os
    global start_time

    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv("PORT", "5000"))
    DEBUG = os.getenv("DEBUG", 'False').lower() == "true"
    start_time = datetime.now()

    logger.info(f"Starting application on {HOST}:{PORT}")
    logger.info(f"Debug mode: {DEBUG}")

    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_config=None
    )


if __name__ == "__main__":
    start()
