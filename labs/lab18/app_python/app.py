from fastapi import FastAPI, Request, Response
import platform
import socket
from datetime import datetime
import os
import uvicorn
import logging
import sys
from pythonjsonlogger.json import JsonFormatter
import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

DATA_FILE = "/data/visits.txt"

def read_counter() -> int:
    if not os.path.exists(DATA_FILE):
        return 0
    with open(DATA_FILE, "r") as f:
        try:
            return int(f.read().strip())
        except:
            return 0


def write_counter(value: int):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        f.write(str(value))

logger = logging.getLogger("devops-info-service")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)

formatter = JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s"
)

handler.setFormatter(formatter)
logger.addHandler(handler)


HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5001))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

app = FastAPI(
    title="Python Web Application",
    description="Simple production-ready Python"
    "web service with comprehensive system information",
    version="1.0",
)

start_time = datetime.now()

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"]
)

active_requests = Gauge(
    "active_requests",
    "Number of active requests"
)

endpoint_calls = Counter(
    "devops_info_endpoint_calls",
    "Endpoint calls",
    ["endpoint"]
)

system_info_duration = Histogram(
    "devops_info_system_collection_seconds",
    "System info collection time"
)

@app.middleware("http")
async def log_requests(request: Request, call_next):

    client_ip = request.client.host if request.client else "unknown"
    active_requests.inc()
    start = time.time()

    logger.info({
        "event": "request_started",
        "method": request.method,
        "path": request.url.path,
        "client_ip": client_ip
    })

    response = await call_next(request)
    duration = time.time() - start

    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    ).inc()

    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    active_requests.dec()

    logger.info({
        "event": "request_finished",
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "client_ip": client_ip,
        "duration": duration
    })

    return response


def get_service_info() -> dict[str, str]:
    """Return basic service information."""
    logger.info("Gathering service information")
    return {
        "name": app.title,
        "version": app.version,
        "description": app.description,
        "framework": "FastAPI",
    }


def get_system_info() -> dict[str, str | int | None]:
    """Return basic system information."""
    logger.info("Gathering system information")

    with system_info_duration.time():
        return {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
            "python_version": platform.python_version(),
        }


def get_runtime_info() -> dict[str, str | int | None]:
    """Return runtime information such as uptime and current time."""
    logger.info("Gathering runtime information")
    current_time = datetime.now()
    uptime = current_time - start_time
    return {
        "uptime_seconds": int(uptime.total_seconds()),
        "uptime_human": f"{int(uptime.total_seconds() // 3600)} hours, {int((uptime.total_seconds() % 3600) // 60)} minutes",
        "current_time": current_time.isoformat(),
        "timezone": current_time.astimezone().tzname(),
    }


def get_request_info(request: Request) -> dict[str, str]:
    """Return information about the incoming request."""
    logger.info("Gathering request information")
    return {
        "client_ip": request.client.host if request.client else "Unknown",
        "user_agent": request.headers.get("user-agent", "Unknown"),
        "method": request.method,
        "path": request.url.path,
    }


def get_endpoints_info() -> list[dict[str, str]]:
    """Return a list of available endpoints."""
    logger.info("Gathering endpoints information")
    return [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"},
        {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
    ]


@app.get("/")
async def root(request: Request):
    """
    Return comprehensive service and system information.
    """
    logger.info("Root endpoint requested")
    endpoint_calls.labels(endpoint="/").inc()

    cnt = read_counter()
    cnt += 1
    write_counter(cnt)

    return {
        "visits": cnt,
        "service": get_service_info(),
        "system": get_system_info(),
        "runtime": get_runtime_info(),
        "request": get_request_info(request),
        "endpoints": get_endpoints_info(),
    }


@app.get("/visits")
async def visits() -> dict[str, int]:
    """Return the number of visits to the root endpoint."""
    cnt = read_counter()
    return {"visits": cnt}


@app.get("/health")
async def health():
    """
    Health check endpoint.
    """
    logger.info("Health check requested")
    endpoint_calls.labels(endpoint="/health").inc()
    runtime_info = get_runtime_info()
    return {
        "status": "healthy",
        "timestamp": runtime_info["current_time"],
        "uptime_seconds": runtime_info["uptime_seconds"],
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    logger.info(f"Starting FastAPI app on {HOST}:{PORT}, debug={DEBUG}")
    uvicorn.run(app, host=HOST, port=PORT, reload=DEBUG)
