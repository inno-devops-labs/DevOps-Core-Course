import logging
import json
from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from routes.system_info import router as system_info_router
from config import HOST, PORT
import uvicorn


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if hasattr(record, "extra_fields"):
            log_obj.update(record.extra_fields)
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.handlers = [handler]
logging.root.setLevel(logging.INFO)

logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(system_info_router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    extra = {
        "event": "http_request",
        "method": request.method,
        "path": str(request.url.path),
        "status_code": response.status_code,
        "client_ip": request.client.host,
    }
    log_record = logger.makeRecord(
        logger.name, logging.INFO, "", 0,
        "http_request", (), None
    )
    log_record.extra_fields = extra
    logger.handle(log_record)
    return response


@app.exception_handler(404)
async def not_found(request: Request, exc: HTTPException):
    logger.error(f"Not found: {request.method} {request.url.path}")
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "Endpoint does not exist"
        }
    )


@app.exception_handler(Exception)
async def internal_error(request: Request, exc: Exception):
    logger.error(f"Internal error: {exc}", exc_info=True)
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
