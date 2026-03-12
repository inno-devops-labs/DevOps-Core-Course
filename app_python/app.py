import os
import socket
import platform
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pythonjsonlogger import jsonlogger  # <-- new import

# Application configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# --- Configure JSON logging ---
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    fmt='%(asctime)s %(levelname)s %(name)s %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S%z'
)
logHandler.setFormatter(formatter)

# Get the root logger and add the handler
root_logger = logging.getLogger()
root_logger.addHandler(logHandler)
root_logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

# Create a logger for this module
logger = logging.getLogger(__name__)

# --- Application start time ---
START_TIME = datetime.now(timezone.utc)

# --- Create FastAPI application ---
app = FastAPI(
    title="DevOps Info Service",
    version="1.0.0",
    description="DevOps course information service",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Middleware to log each request ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Process the request and get response
    response = await call_next(request)

    # Log request details
    logger.info(
        "HTTP Request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
            "status_code": response.status_code,
        }
    )
    return response

# --- Helper functions (unchanged) ---
def get_system_info() -> Dict[str, Any]:
    """Collect and return system information."""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }

def get_uptime() -> Dict[str, Any]:
    """Calculate application uptime."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        "seconds": seconds,
        "human": f"{hours} hours, {minutes} minutes"
    }

def get_request_info(request: Request) -> Dict[str, Any]:
    """Extract request information (used in root endpoint)."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "Unknown")
    return {
        "client_ip": client_ip,
        "user_agent": user_agent,
        "method": request.method,
        "path": request.url.path,
    }

# --- Endpoints ---
@app.get("/", response_model=Dict[str, Any])
async def root(request: Request) -> Dict[str, Any]:
    """
    Main endpoint returning comprehensive service and system information.
    """
    # This log will be in JSON (the middleware already logs the request)
    logger.debug("Root endpoint processing")
    return {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "FastAPI",
        },
        "system": get_system_info(),
        "runtime": {
            "uptime_seconds": get_uptime()["seconds"],
            "uptime_human": get_uptime()["human"],
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "request": get_request_info(request),
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
        ],
    }

@app.get("/health", response_model=Dict[str, Any])
async def health() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring and Kubernetes probes.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": get_uptime()["seconds"],
    }

@app.exception_handler(404)
async def not_found(request: Request, exc):
    """Handle 404 errors."""
    logger.warning("404 Not Found", extra={"path": request.url.path})
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested endpoint {request.url.path} does not exist"
        }
    )

@app.exception_handler(500)
async def internal_error(request: Request, exc):
    """Handle 500 errors."""
    logger.error("Internal server error", exc_info=True, extra={"path": request.url.path})
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )

def main():
    """Application entry point."""
    logger.info("Starting DevOps Info Service", extra={"host": HOST, "port": PORT})
    logger.info(f"Debug mode: {DEBUG}")  # simple string, but JSON formatter will include it as message

    import uvicorn
    uvicorn.run(
        "app:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="debug" if DEBUG else "info"
    )

if __name__ == "__main__":
    main()