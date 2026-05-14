from pydantic import BaseModel


class HealthCheckResponse(BaseModel):
    status: str
    timestamp: str
    uptime_seconds: int
