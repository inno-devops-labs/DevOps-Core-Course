import logging
import multiprocessing
import os
import platform
import socket
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
app = FastAPI()
START = datetime.now(timezone.utc)


def uptime():
    s = int((datetime.now(timezone.utc) - START).total_seconds())
    h = s // 3600
    m = (s % 3600) // 60
    return s, f"{h} hours, {m} minutes"


def system_info():
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": multiprocessing.cpu_count(),
        "python_version": platform.python_version(),
    }


@app.middleware("http")
async def log_requests(request: Request, call_next):
    client = request.client.host if request.client else None
    ua = request.headers.get("user-agent", "")
    resp = await call_next(request)
    logging.info(
        "%s %s %s %s", client, request.method, request.url.path, resp.status_code
    )
    return resp


@app.get("/", response_class=JSONResponse)
async def index(request: Request):
    s, h = uptime()
    return {
        "service": {
            "name": os.getenv("SERVICE_NAME", "devops-info-service"),
            "version": os.getenv("SERVICE_VERSION", "1.0.0"),
            "description": os.getenv(
                "SERVICE_DESCRIPTION", "DevOps course info service"
            ),
            "framework": "FastAPI",
        },
        "system": system_info(),
        "runtime": {
            "uptime_seconds": s,
            "uptime_human": h,
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC",
        },
        "request": {
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent", ""),
            "method": request.method,
            "path": request.url.path,
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
        ],
    }


@app.get("/health", response_class=JSONResponse)
async def health():
    s, _ = uptime()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": s,
    }


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port)
