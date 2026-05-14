import logging
import socket
import platform
from datetime import datetime, timezone
import os
from typing import Annotated

from fastapi import Request, Depends
from fastapi.routing import APIRoute

from utils import APP_START_TIME
from metrics import endpoint_calls, system_info_duration
import visits_counter
from routes.root.schemas import (
    InfoResponse,
    EndpointInfo,
    ServiceInfo,
    SystemInfo,
    RuntimeInfo,
    RequestInfo,
)

logger = logging.getLogger(__name__)


class SysInfoService:
    def __init__(self, request: Request):
        self.request = request

    @staticmethod
    def _get_uptime(start_time) -> tuple[int, str]:
        delta = datetime.now(tz=timezone.utc) - start_time
        seconds = int(delta.total_seconds())
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return seconds, f"{hours} hours, {minutes} minutes"

    @staticmethod
    def _get_service_info() -> ServiceInfo:
        logger.info("Starting to find service info")

        return ServiceInfo(
            name="devops-info-service",
            version="1.0.0",
            description="DevOps course info service",
            framework="Fastapi",
        )

    def _get_system_info(self) -> SystemInfo:
        hostname = socket.gethostname()
        platform_name = platform.system()
        architecture = platform.machine()
        python_version = platform.python_version()
        cpu_count = os.cpu_count()
        platform_version = platform.version()

        return SystemInfo(
            hostname=hostname,
            platform=platform_name,
            platform_version=platform_version,
            architecture=architecture,
            cpu_count=cpu_count,
            python_version=python_version,
        )

    def _get_runtime_info(self) -> RuntimeInfo:
        current_time = datetime.now(tz=timezone.utc)
        uptime_seconds, uptime_human = self._get_uptime(APP_START_TIME)

        return RuntimeInfo(
            uptime_seconds=uptime_seconds,
            uptime_human=uptime_human,
            current_time=current_time,
            timezone="UTC",
        )

    def _get_request_info(self) -> RequestInfo:
        client_ip = self.request.client.host if self.request.client else "unknown"
        user_agent = self.request.headers.get("user-agent")
        method = self.request.method
        path = self.request.url.path

        return RequestInfo(
            client_ip=client_ip, user_agent=user_agent, method=method, path=path
        )

    def _get_endpoints(self) -> list[EndpointInfo]:
        endpoints = []
        for route in self.request.app.routes:
            if isinstance(route, APIRoute):
                for method in route.methods:
                    endpoints.append(
                        EndpointInfo(
                            path=route.path,
                            method=method,
                            description=route.description,
                        )
                    )
        return endpoints

    async def get_info(self) -> InfoResponse:
        try:
            logger.info("Starting run main func")
            endpoint_calls.labels(endpoint="/").inc()
            visits_counter.increment()

            with system_info_duration.time():
                result = InfoResponse(
                    service=self._get_service_info(),
                    system=self._get_system_info(),
                    runtime=self._get_runtime_info(),
                    request=self._get_request_info(),
                    endpoints=self._get_endpoints(),
                )
            return result
        except Exception as e:
            logger.exception(e)
            raise


SysInfoServiceDep = Annotated[SysInfoService, Depends(SysInfoService)]
