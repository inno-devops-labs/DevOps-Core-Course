from fastapi import APIRouter, Request
from datetime import datetime, timezone
from prometheus_client import Counter, Histogram
import os
import tempfile
import threading

import services.system_info as system_info_service

router = APIRouter()


def _default_visits_file() -> str:
    if os.path.isdir("/data") and os.access("/data", os.W_OK):
        return "/data/visits"
    return os.path.join(tempfile.gettempdir(), "devops-info-service-visits")


VISITS_FILE = os.getenv("VISITS_FILE", _default_visits_file())

_visits_lock = threading.Lock()


def _read_visits() -> int:
    try:
        with open(VISITS_FILE, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def _write_visits(count: int):
    os.makedirs(os.path.dirname(VISITS_FILE), exist_ok=True)
    with open(VISITS_FILE, "w") as f:
        f.write(str(count))


# Application-specific metrics
endpoint_calls = Counter(
    'devops_info_endpoint_calls',
    'Endpoint calls',
    ['endpoint']
)

system_info_duration = Histogram(
    'devops_info_system_collection_seconds',
    'System info collection time'
)


@router.get("/")
async def get_system_info(request: Request):
    endpoint_calls.labels(endpoint="/").inc()

    with _visits_lock:
        count = _read_visits() + 1
        _write_visits(count)

    with system_info_duration.time():
        result = {
            "service": system_info_service.get_service_info(),
            "system": system_info_service.get_system_info(),
            "runtime": system_info_service.get_runtime_info(),
            "request": system_info_service.get_request_info(request),
            "endpoints": system_info_service.get_endpoints_info()
        }
    return result


@router.get("/visits")
async def get_visits():
    endpoint_calls.labels(endpoint="/visits").inc()
    return {"visits": _read_visits()}


@router.get("/health")
async def health():
    endpoint_calls.labels(endpoint="/health").inc()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": system_info_service.get_uptime()['seconds']
    }
