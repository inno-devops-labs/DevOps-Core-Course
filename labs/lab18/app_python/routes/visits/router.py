from fastapi import APIRouter
from visits import read_visits

visits_router = APIRouter(tags=["visits"])


@visits_router.get("/visits")
async def get_visits():
    return {"visits": read_visits()}
