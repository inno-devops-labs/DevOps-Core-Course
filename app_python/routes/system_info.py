from fastapi import APIRouter, Request
import logging
from datetime import datetime, timezone
import services.system_info as system_info_service

router = APIRouter()

@router.get("/")
async def get_system_info(request: Request):
    return {
        "service": system_info_service.get_service_info(),
        "system": system_info_service.get_system_info(),
        "runtime": system_info_service.get_runtime_info(),
        "request": system_info_service.get_request_info(request),
        "endpoints": system_info_service.get_endpoints_info()
    }

@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": system_info_service.get_uptime()['seconds']
    }