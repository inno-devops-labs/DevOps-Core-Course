from fastapi import APIRouter, Request

from models.root_responses import RootResponse
from services.system_info import (
    get_endpoints,
    get_request_info,
    get_runtime_info,
    get_service_info,
    get_system_info,
)
from services.visits_counter import increment, read_count

router = APIRouter()


@router.get("/", response_model=RootResponse)
def index(request: Request):
    increment()
    return RootResponse(
        service=get_service_info(),
        system=get_system_info(),
        runtime=get_runtime_info(),
        request=get_request_info(request),
        endpoints=get_endpoints(),
    )


@router.get("/visits")
def visits():
    return {"visits": read_count()}
