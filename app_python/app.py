"""
DevOps Info Service
Main application module
"""
import os
import platform
import time
import socket
import psutil
from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import uvicorn

# ========== CONFIGURATION ==========
# Read environment variables with defaults
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '5000'))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Optional additional configurations
LOG_LEVEL = os.getenv('LOG_LEVEL', 'info')
SERVICE_NAME = os.getenv('SERVICE_NAME', 'devops-info-service')
SERVICE_VERSION = os.getenv('SERVICE_VERSION', '1.0.0')

# Track startup time for uptime calculation
start_time = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global start_time
    start_time = time.time()
    
    # Print configuration at startup (optional but helpful)
    print(f"🚀 Starting {SERVICE_NAME} v{SERVICE_VERSION}")
    print(f"📍 Host: {HOST}")
    print(f"🔌 Port: {PORT}")
    print(f"🐛 Debug: {DEBUG}")
    print(f"📝 Log Level: {LOG_LEVEL}")
    
    yield
    # Shutdown (if needed)
    print("👋 Shutting down service...")

app = FastAPI(
    title=SERVICE_NAME,
    version=SERVICE_VERSION,
    description="DevOps course info service",
    lifespan=lifespan,
    debug=DEBUG  # Pass debug mode to FastAPI
)

def get_uptime():
    """Calculate uptime in seconds and human-readable format"""
    uptime_seconds = int(time.time() - start_time)
    
    # Convert to human-readable format
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    
    if hours > 0:
        uptime_human = f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
    else:
        uptime_human = f"{minutes} minute{'s' if minutes != 1 else ''}"
    
    return uptime_seconds, uptime_human

def get_system_info():
    """Gather system information dynamically"""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": psutil.cpu_count(),
        "python_version": platform.python_version()
    }

def get_service_info():
    """Return static service information"""
    return {
        "name": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "description": "DevOps course info service",
        "framework": "FastAPI"
    }

def get_runtime_info():
    """Get runtime information including uptime and current time"""
    uptime_seconds, uptime_human = get_uptime()
    return {
        "uptime_seconds": uptime_seconds,
        "uptime_human": uptime_human,
        "current_time": datetime.utcnow().isoformat() + "Z",
        "timezone": "UTC"
    }

def get_request_info(request: Request):
    """Extract information from the current request"""
    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get('user-agent', 'Unknown')
    
    return {
        "client_ip": client_ip,
        "user_agent": user_agent,
        "method": request.method,
        "path": request.url.path
    }

def get_endpoints():
    """Define available endpoints"""
    return [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"},
        {"path": "/docs", "method": "GET", "description": "OpenAPI documentation"},
        {"path": "/openapi.json", "method": "GET", "description": "OpenAPI specification"},
        {"path": "/config", "method": "GET", "description": "Current configuration"}
    ]

@app.get("/", response_model=Dict[str, Any])
async def get_info(request: Request):
    """Main endpoint returning comprehensive service and system information"""
    response = {
        "service": get_service_info(),
        "system": get_system_info(),
        "runtime": get_runtime_info(),
        "request": get_request_info(request),
        "endpoints": get_endpoints()
    }
    return response

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    uptime_seconds, _ = get_uptime()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uptime_seconds": uptime_seconds
    }

# New endpoint to show current configuration
@app.get("/config")
async def show_config():
    """Display current configuration from environment variables"""
    return {
        "host": HOST,
        "port": PORT,
        "debug": DEBUG,
        "log_level": LOG_LEVEL,
        "service_name": SERVICE_NAME,
        "service_version": SERVICE_VERSION
    }
    
#Error Handling Implementation    
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500
    
# Logging Implementation    
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info('Application starting...')
logger.debug(f'Request: {request.method} {request.path}')    

# Optional: Models for OpenAPI documentation
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    uptime_seconds: int

class ConfigResponse(BaseModel):
    host: str
    port: int
    debug: bool
    log_level: str
    service_name: str
    service_version: str

if __name__ == "__main__":
    # Run with configuration from environment variables
    uvicorn.run(
        "app:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,  # Auto-reload in debug mode
        log_level=LOG_LEVEL
    )