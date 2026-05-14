from fastapi import APIRouter
from routes.healthcheck.router import health_check_router
from routes.root.router import root_router
from routes.visits.router import visits_router

api_router = APIRouter()

for router in (root_router, health_check_router, visits_router):
    api_router.include_router(router)
