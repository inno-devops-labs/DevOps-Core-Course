from datetime import datetime, timezone

from fastapi import APIRouter

from models.health_responses import HealthResponse
from services.uptime import get_uptime

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        uptime_seconds=get_uptime()["seconds"],
    )
