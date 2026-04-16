from fastapi import APIRouter
from pydantic import BaseModel
import visits_counter

router = APIRouter()


class VisitsResponse(BaseModel):
    visits: int


@router.get("/visits", description="Total visit count for the root endpoint")
async def get_visits() -> VisitsResponse:
    return VisitsResponse(visits=visits_counter.get_count())
