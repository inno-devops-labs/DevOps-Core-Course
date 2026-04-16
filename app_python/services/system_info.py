import os
import socket
import platform
import time
from datetime import datetime, timezone

from fastapi import Request

from models.root_responses import (
    EndpointInfo,
    RequestInfo,
    RuntimeInfo,
    ServiceInfo,
    SystemInfo,
)
from services.uptime import get_uptime


def get_service_info() -> ServiceInfo:
    return ServiceInfo(
        name="devops-info-service",
        version="1.0.0",
        description="DevOps course info service",
        framework="FastAPI",
    )


def get_system_info() -> SystemInfo:
    start_time = time.time()
    
    result = SystemInfo(
        hostname=socket.gethostname(),
        platform=platform.system(),
        platform_version=platform.platform(),
        architecture=platform.machine(),
        cpu_count=os.cpu_count() or 0,
        python_version=platform.python_version(),
    )
    
    # Record collection time if metrics are available
    try:
        from metrics import system_info_collection_duration
        duration = time.time() - start_time
        system_info_collection_duration.observe(duration)
    except (ImportError, AttributeError):
        # Metrics not available, skip recording
        pass
        
    return result


def get_runtime_info() -> RuntimeInfo:
    uptime = get_uptime()
    return RuntimeInfo(
        uptime_seconds=uptime["seconds"],
        uptime_human=uptime["human"],
        current_time=datetime.now(timezone.utc).isoformat(),
        timezone="UTC",
    )


def get_request_info(request: Request) -> RequestInfo:
    return RequestInfo(
        client_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        method=request.method,
        path=str(request.url.path),
    )


def get_endpoints() -> list[EndpointInfo]:
    return [
        EndpointInfo(
            path="/", method="GET", description="Service information"
        ),
        EndpointInfo(
            path="/health", method="GET", description="Health check"
        ),
        EndpointInfo(
            path="/visits", method="GET", description="Persisted visit counter"
        ),
    ]
