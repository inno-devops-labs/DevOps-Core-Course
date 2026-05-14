import pytest
from routes.healthcheck.service import HealthCheckService
from routes.healthcheck.schemas import HealthCheckResponse
from core.runtime import set_start_time


@pytest.fixture
def healthcheck_service():
    set_start_time()
    return HealthCheckService()


def test_healthcheck_service_health_check_success(healthcheck_service):
    result = healthcheck_service.health_check()
    
    HealthCheckResponse(**result.model_dump())


def test_healthcheck_service_health_check_structure(healthcheck_service):
    result = healthcheck_service.health_check()
    
    validated = HealthCheckResponse(**result.model_dump())
    
    assert validated.status == "healthy"
    assert isinstance(validated.timestamp, str)
    assert isinstance(validated.uptime_seconds, int)


def test_healthcheck_service_health_check_uptime(healthcheck_service):
    result = healthcheck_service.health_check()
    
    validated = HealthCheckResponse(**result.model_dump())
    
    assert validated.uptime_seconds >= 0
