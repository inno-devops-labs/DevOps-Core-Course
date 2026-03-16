import os
import socket
import platform
import logging
import json
import time
from datetime import datetime, timezone
from typing import List, Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# JSON Logging Formatter
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name
        }
        if hasattr(record, 'method'):
            log_data['method'] = record.method
        if hasattr(record, 'path'):
            log_data['path'] = record.path
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
        if hasattr(record, 'client_ip'):
            log_data['client_ip'] = record.client_ip
        return json.dumps(log_data)

# Logging setup with JSON formatter
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
logger.addHandler(handler)
logger.propagate = False

# Application start time
START_TIME = datetime.now(timezone.utc)

# HTTP metrics — track every request by method, endpoint, and status code
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'status_code']
)
http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed'
)

# App-specific: counts calls to the system info endpoint (the main business action)
devops_info_requests_total = Counter(
    'devops_info_requests_total',
    'Total calls to the system info endpoint'
)
# App-specific: measures how long it takes to collect system information
devops_info_system_collection_seconds = Histogram(
    'devops_info_system_collection_seconds',
    'Time in seconds spent collecting system information'
)

# Pydantic models
class ServiceInfo(BaseModel):
    name: str
    version: str
    description: str
    framework: str

class SystemInfo(BaseModel):
    hostname: str
    platform: str
    platform_version: str
    architecture: str
    cpu_count: int
    python_version: str

class RuntimeInfo(BaseModel):
    uptime_seconds: int
    uptime_human: str
    current_time: str
    timezone: str

class RequestInfo(BaseModel):
    client_ip: str
    user_agent: str
    method: str
    path: str

class EndpointInfo(BaseModel):
    path: str
    method: str
    description: str

class MainResponse(BaseModel):
    service: ServiceInfo
    system: SystemInfo
    runtime: RuntimeInfo
    request: RequestInfo
    endpoints: List[EndpointInfo]

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    uptime_seconds: int

# FastAPI app
app = FastAPI(
    title="DevOps Info Service",
    description="Lab 1 - System and service information API",
    version="1.0.0"
)

# Middleware for request/response logging and metrics recording
@app.middleware("http")
async def log_requests(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    method = request.method
    path = str(request.url.path)

    http_requests_in_progress.inc()
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    http_requests_in_progress.dec()

    status_code = str(response.status_code)
    http_requests_total.labels(method=method, endpoint=path, status_code=status_code).inc()
    http_request_duration_seconds.labels(method=method, endpoint=path, status_code=status_code).observe(process_time)

    log_record = logger.makeRecord(
        logger.name, logging.INFO, "", 0,
        f"{method} {path} {response.status_code}",
        (), None
    )
    log_record.method = method
    log_record.path = path
    log_record.status_code = response.status_code
    log_record.client_ip = client_ip
    logger.handle(log_record)

    return response

# Helper functions
def get_uptime() -> Dict[str, Any]:
    """Calculate application uptime"""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    hours_text = f"{hours} hour{'s' if hours != 1 else ''}"
    minutes_text = f"{minutes} minute{'s' if minutes != 1 else ''}"
    return {
        'seconds': seconds,
        'human': f"{hours_text}, {minutes_text}"
    }

def get_system_info() -> SystemInfo:
    """Collect system information"""
    with devops_info_system_collection_seconds.time():
        return SystemInfo(
            hostname=socket.gethostname(),
            platform=platform.system(),
            platform_version=platform.version(),
            architecture=platform.machine(),
            cpu_count=os.cpu_count() or 0,
            python_version=platform.python_version()
        )

def get_service_info() -> ServiceInfo:
    """Get service metadata"""
    return ServiceInfo(
        name="devops-info-service",
        version="1.0.0",
        description="DevOps course info service",
        framework="FastAPI"
    )

def get_runtime_info() -> RuntimeInfo:
    """Get runtime information"""
    uptime = get_uptime()
    return RuntimeInfo(
        uptime_seconds=uptime['seconds'],
        uptime_human=uptime['human'],
        current_time=datetime.now(timezone.utc).isoformat(),
        timezone="UTC"
    )

def get_request_info(request: Request) -> RequestInfo:
    """Extract request information"""
    return RequestInfo(
        client_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get('user-agent', 'unknown'),
        method=request.method,
        path=str(request.url.path)
    )

def get_endpoints() -> List[EndpointInfo]:
    """List available endpoints"""
    return [
        EndpointInfo(
            path="/",
            method="GET",
            description="Service information"
        ),
        EndpointInfo(
            path="/health",
            method="GET",
            description="Health check"
        )
    ]

# Routes
@app.get("/", response_model=MainResponse)
async def root(request: Request):
    """
    Main endpoint - comprehensive service and system information
    """
    devops_info_requests_total.inc()
    response = MainResponse(
        service=get_service_info(),
        system=get_system_info(),
        runtime=get_runtime_info(),
        request=get_request_info(request),
        endpoints=get_endpoints()
    )
    return response

@app.get("/health", response_model=HealthResponse)
async def health():
    """
    Health check endpoint for monitoring and probes
    """
    uptime = get_uptime()
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        uptime_seconds=uptime['seconds']
    )

@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "Endpoint does not exist"
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors"""
    log_record = logger.makeRecord(
        logger.name, logging.ERROR, "", 0,
        f"Internal error: {exc}",
        (), None
    )
    log_record.method = request.method
    log_record.path = str(request.url.path)
    log_record.status_code = 500
    log_record.client_ip = request.client.host if request.client else "unknown"
    logger.handle(log_record)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    logger.info("DevOps Info Service starting")
    logger.info(f"Configuration: host={HOST}, port={PORT}, debug={DEBUG}")
    logger.info(f"Python version: {platform.python_version()}")
    logger.info(f"FastAPI docs available at: http://{HOST}:{PORT}/docs")

# Run application
if __name__ == "__main__":
    import uvicorn
    
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["default"]["fmt"] = "%(message)s"
    log_config["formatters"]["access"]["fmt"] = "%(message)s"
    
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="debug" if DEBUG else "info",
        log_config=log_config,
        access_log=False
    )