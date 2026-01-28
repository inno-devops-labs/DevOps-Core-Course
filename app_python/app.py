import logging
import os
import platform
import socket
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI, Request, HTTPException

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="DevOps Info Service")
START_TIME = datetime.now(timezone.utc)

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
    logger.info(f"Root endpoint called by {request.client.host}")
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
        logger.error(f"Error in root endpoint: {e}")
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
async def custom_404_handler(request: Request, __):
    return {"error": "Not Found", "message": f"Endpoint {request.url.path} does not exist"}, 404

if __name__ == "__main__":
    logger.info(f"Starting service on {HOST}:{PORT}")
    uvicorn.run("app:app", host=HOST, port=PORT, reload=DEBUG)
