from fastapi import APIRouter, Request
from health_check.schemas import InfoResponse, HealthResponse
from health_check.service import HealthCheckServiceDep

router = APIRouter()


@router.get("/", description="Service information")
async def get_info(
    service: HealthCheckServiceDep,
    request: Request,
) -> InfoResponse:
    return await service.get_info(request=request)


@router.get("/health", description="Health check")
async def health_check(service: HealthCheckServiceDep) -> HealthResponse:
    return await service.health_check()
