import logging

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from config import HOST, PORT
from routes.root import router as root_router
from routes.health import router as health_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="DevOps Info Service", version="1.0.0")

app.include_router(root_router)
app.include_router(health_router)


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "message": "Endpoint does not exist"},
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error("Internal server error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        },
    )


if __name__ == "__main__":
    logger.info("Starting DevOps Info Service on %s:%d", HOST, PORT)
    uvicorn.run(app, host=HOST, port=PORT)
