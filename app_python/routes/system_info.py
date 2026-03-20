from fastapi import APIRouter, Request
from datetime import datetime, timezone
from prometheus_client import Counter, Histogram
import services.system_info as system_info_service

router = APIRouter()

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
    with system_info_duration.time():
        result = {
            "service": system_info_service.get_service_info(),
            "system": system_info_service.get_system_info(),
            "runtime": system_info_service.get_runtime_info(),
            "request": system_info_service.get_request_info(request),
            "endpoints": system_info_service.get_endpoints_info()
        }
    return result


@router.get("/health")
async def health():
    endpoint_calls.labels(endpoint="/health").inc()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": system_info_service.get_uptime()['seconds']
    }
