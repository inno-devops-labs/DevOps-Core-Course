import os
import socket
import platform
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Logging setup
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Application start time
START_TIME = datetime.now(timezone.utc)

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

# Helper functions
def get_uptime() -> Dict[str, Any]:
    """Calculate application uptime"""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
    }

def get_system_info() -> SystemInfo:
    """Collect system information"""
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
    logger.info(f"Request: {request.method} {request.url.path} from {request.client.host if request.client else 'unknown'}")
    
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
    logger.debug("Health check requested")
    
    uptime = get_uptime()
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        uptime_seconds=uptime['seconds']
    )

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
    logger.error(f"Internal error: {exc}")
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
    logger.info("=" * 50)
    logger.info("DevOps Info Service starting...")
    logger.info(f"Host: {HOST}")
    logger.info(f"Port: {PORT}")
    logger.info(f"Debug: {DEBUG}")
    logger.info(f"Python: {platform.python_version()}")
    logger.info(f"FastAPI docs: http://{HOST}:{PORT}/docs")
    logger.info("=" * 50)

# Run application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="debug" if DEBUG else "info"
    )