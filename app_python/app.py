import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from routes.system_info import router as system_info_router
from config import HOST, PORT
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(system_info_router)


@app.exception_handler(404)
async def not_found(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "Endpoint does not exist"
        }
    )


@app.exception_handler(Exception)
async def internal_error(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    logger.info(f"Application started on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
