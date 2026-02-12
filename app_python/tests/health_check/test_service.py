import pytest
from datetime import datetime, timezone, timedelta

from pytest_mock import MockerFixture
from routes.health_check.service import HealthCheckService
from utils import APP_START_TIME
from routes.health_check.schemas import HealthResponse


@pytest.mark.asyncio
async def test_health_check_returns_healthy():
    service = HealthCheckService()
    result: HealthResponse = await service.health_check()

    assert result.status == "healthy"

    assert isinstance(result.timestamp, datetime)
    assert result.timestamp <= datetime.now(tz=timezone.utc)

    uptime_seconds, _ = service.get_uptime(APP_START_TIME)
    assert result.uptime_seconds == uptime_seconds


@pytest.mark.asyncio
async def test_get_uptime_returns_correct_tuple(mocker: MockerFixture):
    fixed_start = datetime(2026, 2, 12, 12, 0, tzinfo=timezone.utc)
    mocker.patch("routes.health_check.service.APP_START_TIME", fixed_start)

    service_instance = HealthCheckService()
    result: HealthResponse = await service_instance.health_check()

    assert result.status == "healthy"
    expected_seconds, _ = service_instance.get_uptime(fixed_start)
    assert result.uptime_seconds == expected_seconds
