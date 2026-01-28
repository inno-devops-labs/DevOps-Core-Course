from fastapi import APIRouter
from routes.healthcheck.service import HealthCheckServiceDep
from routes.healthcheck.schemas import HealthCheckResponse

health_check_router = APIRouter(prefix="/health", tags=["health"])


@health_check_router.get('')
async def health_check(service: HealthCheckServiceDep) -> HealthCheckResponse:
    return service.health_check()
