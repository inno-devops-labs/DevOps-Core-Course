from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
from core.runtime import set_start_time
from routes.router import api_router
from colorlog import ColoredFormatter
import logging
from config import settings

SERVICE_TITLE = "devops-info-service"
SERVICE_VERSION = "1.0.0"
SERVICE_DESCRIPTION = "DevOps course info service"
SERVICE_FRAMEWORK = "FastAPI"


handler = logging.StreamHandler()

formatter = ColoredFormatter(
    "%(log_color)s%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    },
)

handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[handler],
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    set_start_time()
    logging.info(f"Starting {SERVICE_TITLE}")
    yield

app = FastAPI(
    title=SERVICE_TITLE,
    version=SERVICE_VERSION,
    description=SERVICE_DESCRIPTION,
    lifespan=lifespan,
)

app.include_router(api_router)


if __name__ == '__main__':
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
