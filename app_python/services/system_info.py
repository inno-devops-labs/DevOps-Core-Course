from fastapi import Request
import os
import platform
import socket
from datetime import datetime, timezone

start_time = datetime.now(timezone.utc)


def get_system_info():
    hostname = socket.gethostname()
    platform_name = platform.system()
    platform_version = platform.platform()
    architecture = platform.machine()
    cpu_count = os.cpu_count()
    python_version = platform.python_version()

    return {
        "hostname": hostname,
        "platform": platform_name,
        "platform_version": platform_version,
        "architecture": architecture,
        "cpu_count": cpu_count,
        "python_version": python_version
    }


def get_uptime():
    delta = datetime.now(timezone.utc) - start_time
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }


def get_runtime_info():
    uptime_info = get_uptime()

    return {
        "uptime_seconds": uptime_info['seconds'],
        "uptime_human": uptime_info['human'],
        'current_time': datetime.now(timezone.utc).isoformat(),
        'timezone': datetime.now(timezone.utc).tzname()
    }


def get_service_info():
    return {
        "name": "devops-info-service",
        "version": "1.0.0",
        "description": "DevOps course info service",
        "framework": "FastAPI"
    }


def get_request_info(request: Request):
    return {
        "client_ip": request.client.host,
        "user_agent": request.headers.get('user-agent'),
        "method": request.method,
        "path": request.url.path
    }


def get_endpoints_info():
    return [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/visits", "method": "GET", "description": "Visit counter"},
        {"path": "/health", "method": "GET", "description": "Health check"}
    ]
