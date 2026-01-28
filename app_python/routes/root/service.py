import platform
import socket
import os
from fastapi import Depends, HTTPException, Request
from typing import Annotated
from datetime import datetime
from core.runtime import get_uptime
from routes.root.schemas import (
    SystemInfoResponse,
    ServiceSchema,
    SystemSchema,
    RuntimeSchema,
    RequestSchema,
    EndpointSchema,
)
import logging


class RootService:
    def system_info(self, request: Request) -> SystemInfoResponse:
        logging.info(f"Collecting system information")
        try:
            return SystemInfoResponse(
                service=ServiceSchema(
                    name="devops-info-service",
                    version="1.0.0",
                    description="DevOps course info service",
                    framework="FastAPI"
                ),
                system=SystemSchema(
                    hostname=socket.gethostname(),
                    platform=platform.system(),
                    platform_version=platform.version(),
                    architecture=platform.machine(),
                    cpu_count=os.cpu_count(),
                    python_version=platform.python_version()
                ),
                runtime=RuntimeSchema(
                    uptime_seconds=get_uptime()['seconds'],
                    uptime_human=get_uptime()['human'],
                    current_time=datetime.now().isoformat(),
                    timezone=str(datetime.now().astimezone().tzinfo)
                ),
                request=RequestSchema(
                    client_ip=request.client.host,
                    user_agent=request.headers.get('user-agent'),
                    method=request.method,
                    path=request.url.path,
                ),
                endpoints=[
                    EndpointSchema(
                        path="/",
                        method="GET",
                        description="Service information"
                    ),
                    EndpointSchema(
                        path='/health',
                        method='GET',
                        description="Health check"
                    ),
                ]
            )
        except Exception as e:
            logging.error(f"System information retrieval failed: {e}")
            raise HTTPException(status_code=500, detail="System information retrieval failed")


RootServiceDep = Annotated[RootService, Depends()]
