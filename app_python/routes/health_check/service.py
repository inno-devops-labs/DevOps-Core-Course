import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends

from utils import APP_START_TIME
from routes.health_check.schemas import HealthResponse

logger = logging.getLogger(__name__)


class HealthCheckService:
    @staticmethod
    def get_uptime(start_time) -> tuple[int, str]:
        delta = datetime.now(tz=timezone.utc) - start_time
        seconds = int(delta.total_seconds())
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return seconds, f"{hours} hours, {minutes} minutes"

    async def health_check(self) -> HealthResponse:
        logger.info("Health check called")
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now(tz=timezone.utc),
            uptime_seconds=self.get_uptime(APP_START_TIME)[0],
        )


HealthCheckServiceDep = Annotated[HealthCheckService, Depends(HealthCheckService)]
