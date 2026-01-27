import logging
import socket
import platform
from datetime import datetime, timezone
import os
from typing import Annotated

from fastapi import Request, Depends
from fastapi.routing import APIRoute

from utils import APP_START_TIME
from health_check.schemas import (
    InfoResponse,
    EndpointInfo,
    ServiceInfo,
    SystemInfo,
    RuntimeInfo,
    RequestInfo,
    HealthResponse,
)

logger = logging.getLogger(__name__)


class HealthCheckService:
    @staticmethod
    def get_uptime(start_time) -> tuple[int, str]:
        delta = datetime.now(tz=timezone.utc) - start_time
        seconds = int(delta.total_seconds())
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return seconds, f"{hours} hours, {minutes} minutes"

    async def get_info(self, request: Request) -> InfoResponse:
        try:
            logger.info("Starting to find info")

            hostname = socket.gethostname()
            platform_name = platform.system()
            architecture = platform.machine()
            python_version = platform.python_version()
            cpu_count = os.cpu_count()
            platform_version = platform.version()

            current_time = datetime.now(tz=timezone.utc)
            uptime_seconds, uptime_human = self.get_uptime(APP_START_TIME)

            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent")
            method = request.method
            path = request.url.path

            endpoints = []
            for route in request.app.routes:
                if isinstance(route, APIRoute):
                    for method in route.methods:
                        endpoints.append(
                            EndpointInfo(
                                path=route.path,
                                method=method,
                                description=route.description,
                            )
                        )

            return InfoResponse(
                service=ServiceInfo(
                    name="devops-info-service",
                    version="1.0.0",
                    description="DevOps course info service",
                    framework="Fastapi",
                ),
                system=SystemInfo(
                    hostname=hostname,
                    platform=platform_name,
                    platform_version=platform_version,
                    architecture=architecture,
                    cpu_count=cpu_count,
                    python_version=python_version,
                ),
                runtime=RuntimeInfo(
                    uptime_seconds=uptime_seconds,
                    uptime_human=uptime_human,
                    current_time=current_time,
                    timezone="UTC",
                ),
                request=RequestInfo(
                    client_ip=client_ip, user_agent=user_agent, method=method, path=path
                ),
                endpoints=endpoints,
            )
        except Exception as e:
            logger.exception(e)
            raise

    async def health_check(self) -> HealthResponse:
        logger.info("Health check called")
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now(tz=timezone.utc),
            uptime_seconds=self.get_uptime(APP_START_TIME)[0],
        )


HealthCheckServiceDep = Annotated[HealthCheckService, Depends(HealthCheckService)]
