import logging
import time

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from config import DEBUG, HOST, PORT
from logger_config import setup_logger
from metrics import (
    http_requests_total,
    http_request_duration_seconds,
    http_requests_in_progress,
)
from routes import health_router, root_router, visits_router

setup_logger()
logger = logging.getLogger(__name__)

app = FastAPI(debug=DEBUG)
for router in [health_router, root_router, visits_router]:
    app.include_router(router=router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_and_track_requests(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)

    http_requests_in_progress.inc()
    start = time.perf_counter()
    try:
        response = await call_next(request)
    finally:
        duration = time.perf_counter() - start
        http_requests_in_progress.dec()

    duration_ms = round(duration * 1000, 2)
    endpoint = request.url.path
    method = request.method
    status = str(response.status_code)

    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(
        duration
    )

    logger.info(
        "HTTP request",
        extra={
            "method": method,
            "path": endpoint,
            "status_code": response.status_code,
            "client_ip": request.client.host if request.client else None,
            "duration_ms": duration_ms,
        },
    )
    return response


@app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.on_event("startup")
async def on_startup():
    logger.info("Application started", extra={"host": HOST, "port": PORT})


if __name__ == "__main__":
    uvicorn.run(app=app, port=PORT, host=HOST)
