from fastapi import APIRouter
from routes.root.schemas import InfoResponse
from routes.root.service import SysInfoServiceDep

router = APIRouter()


@router.get("/", description="Service information")
async def get_info(
    service: SysInfoServiceDep,
) -> InfoResponse:
    return await service.get_info()
