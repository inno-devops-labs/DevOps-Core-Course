"""DevOps Info Service implemented with FastAPI."""

from __future__ import annotations

import os
import platform
import socket
from datetime import datetime, timezone

from fastapi import FastAPI, Request

APP_START = datetime.now(timezone.utc)

app = FastAPI(title="DevOps Info Service", version="1.0.0")


def get_uptime() -> dict[str, str | int]:
    """Return uptime in seconds and a human-readable string."""
    delta = datetime.now(timezone.utc) - APP_START
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {"seconds": seconds, "human": f"{hours} hours, {minutes} minutes"}


@app.get("/", summary="Service information")
async def index(request: Request):
    now = datetime.now(timezone.utc)
    uptime = get_uptime()
    return {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "FastAPI",
        },
        "system": {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
            "python_version": platform.python_version(),
        },
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": now.isoformat(),
            "timezone": "UTC",
        },
        "request": {
            "client_ip": request.headers.get("x-forwarded-for", request.client.host if request.client else None),
            "user_agent": request.headers.get("user-agent", ""),
            "method": request.method,
            "path": request.url.path,
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
        ],
    }


@app.get("/health", summary="Health check")
async def health():
    uptime = get_uptime()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime["seconds"],
    }


def main():
    """Run the FastAPI app with uvicorn using environment configuration."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "False").lower() == "true"

    import uvicorn

    # When reload is enabled uvicorn expects an import string, not the app object.
    target = "app:app" if debug else app
    uvicorn.run(target, host=host, port=port, reload=debug)


if __name__ == "__main__":
    main()
