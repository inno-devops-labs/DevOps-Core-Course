from fastapi import Depends, HTTPException
from typing import Annotated
from datetime import datetime
from core.runtime import get_uptime
from routes.healthcheck.schemas import HealthCheckResponse
import logging


class HealthCheckService:
    def health_check(self) -> HealthCheckResponse:
        logging.info("Performing health check")
        try:
            return HealthCheckResponse(
                status="healthy",
                timestamp=datetime.now().isoformat(),
                uptime_seconds=get_uptime()['seconds']
            )
        except Exception as e:
            logging.error(f"Health check failed: {e}")
            raise HTTPException(status_code=500, detail="Health check failed")


HealthCheckServiceDep = Annotated[HealthCheckService, Depends()]
