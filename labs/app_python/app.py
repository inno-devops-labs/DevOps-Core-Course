"""
DevOps main application
"""

import platform
import socket
import os
import requests
import uvicorn
import logging
import argparse
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

# Configuration
parser = argparse.ArgumentParser()
parser.add_argument("--host", default=os.getenv('HOST', '0.0.0.0'))
parser.add_argument("--port", type=int, default=int(os.getenv('PORT', 8000)))
parser.add_argument("--debug", action="store_true", default=os.getenv('DEBUG', 'False').lower() == 'true')
args = parser.parse_args()


HOST = args.host
PORT = args.port
DEBUG = args.debug

# Timer of application start
start_time = datetime.now()


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


# Application execution
if __name__ == "__main__":
    if DEBUG:
        logging.basicConfig(level=logging.DEBUG)
    uvicorn.run(app, host=HOST, port=PORT)
