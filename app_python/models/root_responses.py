from pydantic import BaseModel

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
    current_time: str
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

class RootResponse(BaseModel):
    service: ServiceInfo
    system: SystemInfo
    runtime: RuntimeInfo
    request: RequestInfo
    endpoints: list[EndpointInfo]
