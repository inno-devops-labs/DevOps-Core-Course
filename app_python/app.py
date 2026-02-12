import os
import socket
import platform
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======== Parameters ========
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# ======== Setup ========
START_TIME = datetime.now(timezone.utc)     # UTC for simplicity

app = FastAPI()


# ======== Endpoints ========
@app.get("/")
def main_endpoint(request: Request):
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
            "current_time": get_current_time(),
            "timezone": "UTC",      # Static for simplicity
        },
        "request": {
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "method": request.method,
            "path": request.url.path,
        },
        "endpoints": [
            {"path": "/", "method": "GET",
             "description": "Service information"},
            {"path": "/health", "method": "GET",
             "description": "Health check"},
        ],
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": get_uptime()["seconds"],
    }


# ======== Functions ========
def get_system_info():
    hostname = socket.gethostname()
    platform_name = platform.system()
    architecture = platform.machine()
    cpu_count = os.cpu_count()
    python_version = platform.python_version()
    return {
        "hostname": hostname,
        "platform": platform_name,
        "architecture": architecture,
        "cpu_count": cpu_count,
        "python_version": python_version
    }


def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }


def get_current_time():
    return datetime.now(timezone.utc).isoformat()


# ======== Launch ========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host=HOST, port=PORT, reload=DEBUG)
