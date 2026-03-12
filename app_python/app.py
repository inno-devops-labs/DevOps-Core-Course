import logging
import time

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from config import DEBUG, HOST, PORT
from logger_config import setup_logger
from routes import health_router, root_router

setup_logger()
logger = logging.getLogger(__name__)

app = FastAPI(debug=DEBUG)
for router in [health_router, root_router]:
    app.include_router(router=router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "HTTP request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "client_ip": request.client.host if request.client else None,
            "duration_ms": duration_ms,
        },
    )
    return response


@app.on_event("startup")
async def on_startup():
    logger.info("Application started", extra={"host": HOST, "port": PORT})


if __name__ == "__main__":
    uvicorn.run(app=app, port=PORT, host=HOST)
