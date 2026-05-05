from __future__ import annotations

import os
import platform
import socket
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import FastAPI, Request

APP_NAME = os.getenv("APP_NAME", "devops-info-service")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
APP_DESCRIPTION = os.getenv("APP_DESCRIPTION", "DevOps course info service")

START_TIME = time.time()

app = FastAPI(title=APP_NAME, version=APP_VERSION, description=APP_DESCRIPTION)


def _uptime_seconds() -> int:
    return int(time.time() - START_TIME)


def _uptime_human(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours} hours, {minutes} minutes"


@app.get("/", summary="Service information")
async def root(request: Request) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    uptime = _uptime_seconds()

    endpoints: List[Dict[str, str]] = [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"},
    ]

    return {
        "service": {
            "name": APP_NAME,
            "version": APP_VERSION,
            "description": APP_DESCRIPTION,
            "framework": "FastAPI",
        },
        "system": {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.platform(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
            "python_version": platform.python_version(),
        },
        "runtime": {
            "uptime_seconds": uptime,
            "uptime_human": _uptime_human(uptime),
            "current_time": now.isoformat(),
            "timezone": "UTC",
        },
        "request": {
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "method": request.method,
            "path": request.url.path,
        },
        "endpoints": endpoints,
    }


@app.get("/health", summary="Health check")
async def health() -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        "status": "healthy",
        "timestamp": now.isoformat(),
        "uptime_seconds": _uptime_seconds(),
    }
