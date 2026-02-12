from fastapi import APIRouter
from routes.health_check.schemas import HealthResponse
from routes.health_check.service import HealthCheckServiceDep

router = APIRouter()

@router.get("/health", description="Health check")
async def health_check(service: HealthCheckServiceDep) -> HealthResponse:
    return await service.health_check()
