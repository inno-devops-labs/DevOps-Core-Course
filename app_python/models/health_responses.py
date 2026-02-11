from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    uptime_seconds: int
