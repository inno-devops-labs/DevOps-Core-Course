from pydantic import BaseModel
from datetime import datetime


class ServiceInfo(BaseModel):
    name: str
    version: str
    description: str
    framework: str


class SystemInfo(BaseModel):
    hostname: str
    platform: str
    platform_version: str
    architecture: str
    cpu_count: int
    python_version: str


class RuntimeInfo(BaseModel):
    uptime_seconds: int
    uptime_human: str
    current_time: datetime
    timezone: str


class RequestInfo(BaseModel):
    client_ip: str
    user_agent: str
    method: str
    path: str


class EndpointInfo(BaseModel):
    path: str
    method: str
    description: str


class InfoResponse(BaseModel):
    service: ServiceInfo
    system: SystemInfo
    runtime: RuntimeInfo
    request: RequestInfo
    endpoints: list[EndpointInfo]


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    uptime_seconds: int
