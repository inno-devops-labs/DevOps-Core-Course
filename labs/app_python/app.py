"""
DevOps main application
"""

import platform
import socket
import fcntl
import os
import uvicorn
import logging
import argparse
import json
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import REGISTRY, CONTENT_TYPE_LATEST
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
import time

app = FastAPI()
VISITS_FILE = "/data/visits"

# Prometheus
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests currently being processed'
)

# Application specific
endpoint_calls = Counter(
    'devops_info_endpoint_calls',
    'Number of calls per endpoint',
    ['endpoint']
)

system_info_duration = Histogram(
    'devops_info_system_collection_seconds',
    'Time taken to collect system info'
)


def read_visits() -> int:
    try:
        with open(VISITS_FILE, "r") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            val = f.read().strip()
            fcntl.flock(f, fcntl.LOCK_UN)
            return int(val) if val else 0
    except FileNotFoundError:
        return 0
    except Exception as e:
        logger.error("Error reading visits file", extra={"error": str(e)})
        return 0


def write_visits(count: int) -> None:
    os.makedirs(os.path.dirname(VISITS_FILE), exist_ok=True)
    with open(VISITS_FILE, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(str(count))
        fcntl.flock(f, fcntl.LOCK_UN)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        http_requests_in_progress.inc()

        start_time = time.time()

        route = request.scope.get("route")
        endpoint = route.path if route else request.url.path

        try:
            response = await call_next(request)
        finally:
            http_requests_in_progress.dec()

        duration = time.time() - start_time
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)

        http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code
        ).inc()

        endpoint_calls.labels(endpoint=endpoint).inc()

        return response


# JSON Logging setup
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra"):
            log_record.update(record.extra)
        return json.dumps(log_record)


# Configure root logger
logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Configuration
parser = argparse.ArgumentParser()
parser.add_argument("--host", default=os.getenv('HOST', '0.0.0.0'))
parser.add_argument("--port", type=int, default=int(os.getenv('PORT', 8000)))
parser.add_argument("--debug", action="store_true",
                    default=os.getenv('DEBUG', 'False').lower() == 'true')
args = parser.parse_args()


HOST = args.host
PORT = args.port
DEBUG = args.debug

# Timer of application start
start_time = datetime.now()


# Request Logging Setup
class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        # Log request details
        logger.info(
            "HTTP Request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "client_ip": request.client.host,
                "duration_seconds": round(process_time, 3)
            }
        )
        return response


app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestLogMiddleware)


def get_service_info():
    """Returns service info"""
    logging.info("Service info")
    return {
        "name": "devops-info-service",
        "version": "1.0.0",
        "description": "DevOps course info service",
        "framework": "FastAPI"
    }


def get_system_info():
    """Returns system info"""
    with system_info_duration.time():
        logging.info("System info")
        return {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.architecture(),
            "cpu_count": os.cpu_count(),
            "python_version": platform.python_version()
        }


def get_runtime_info():
    """Returns runtime info"""
    logging.info("Runtime info")
    delta = datetime.now() - start_time
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        "uptime_seconds": seconds,
        "uptime_human": f"{hours} hours, {minutes} minutes",
        "current_time": datetime.now().isoformat(),
        "timezone": "UTC+3"
    }


def get_request_info(given_request: Request):
    """Returns info about request"""
    logging.info("Request info")
    return {
        "client_ip": given_request.client.host,
        "user_agent": given_request.headers.get("user-agent"),
        "method": given_request.method,
        "path": given_request.url.path
    }


def get_all_endpoints():
    """Returns all endpoints of application"""
    logging.info("List of all endpoints")
    routes = [{"path": route.path, "name": route.name} for route in app.routes]
    if not routes:
        raise HTTPException(status_code=404, detail="Endpoints were not found")
    return routes


@app.get("/health")
def get_health():
    """Returns health status"""
    logging.info("Health status")
    return {
        "status": "healthy",
        "timestamp": get_runtime_info()["current_time"],
        "uptime_seconds": get_runtime_info()["uptime_seconds"]
    }


@app.get("/ready")
def get_ready():
    """Returns ready status"""
    logging.info("Ready status")
    return {
        "status": "ready",
        "timestamp": get_runtime_info()["current_time"],
        "uptime_seconds": get_runtime_info()["uptime_seconds"]
    }


@app.get("/")
def get_status(request: Request):
    """Main endpoint. Returns info about system"""
    logging.info("Main endpoint (get_status)")
    return {
        "service": get_service_info(),
        "system": get_system_info(),
        "runtime": get_runtime_info(),
        "request": get_request_info(request),
        "endpoints": get_all_endpoints()
    }


@app.get("/metrics")
def get_metrics():
    """Expose Prometheus metrics"""
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/visit")
def visit():
    """Increment visit counter and return current count."""
    count = read_visits() + 1
    write_visits(count)
    logger.info("Visit incremented", extra={"count": count})
    return {"visits": count}


@app.get("/visits")
def get_visits():
    """Return current visit count without incrementing."""
    count = read_visits()
    return {"visits": count}


@app.on_event("startup")
def startup_event():
    logger.info(
        "Application startup",
        extra={
            "host": HOST,
            "port": PORT,
            "debug": DEBUG,
            "python_version": platform.python_version()
        }
    )

# Application execution
if __name__ == "__main__":
    if DEBUG:
        logging.basicConfig(level=logging.DEBUG)
    uvicorn.run(app, host=HOST, port=PORT)
