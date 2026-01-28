from pydantic import BaseModel


class ServiceSchema(BaseModel):
    name: str
    version: str
    description: str
    framework: str


class SystemSchema(BaseModel):
    hostname: str
    platform: str
    platform_version: str
    architecture: str
    cpu_count: int
    python_version: str


class RuntimeSchema(BaseModel):
    uptime_seconds: int
    uptime_human: str
    current_time: str
    timezone: str


class RequestSchema(BaseModel):
    client_ip: str
    user_agent: str
    method: str
    path: str


class EndpointSchema(BaseModel):
    path: str
    method: str
    description: str


class SystemInfoResponse(BaseModel):
    service: ServiceSchema
    system: SystemSchema
    runtime: RuntimeSchema
    request: RequestSchema
    endpoints: list[EndpointSchema]
