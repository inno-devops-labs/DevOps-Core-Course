from fastapi import APIRouter, Request
from routes.root.service import RootServiceDep
from routes.root.schemas import SystemInfoResponse

root_router = APIRouter()


@root_router.get('/')
async def health_check(service: RootServiceDep, request: Request) -> SystemInfoResponse:
    return service.system_info(request)
