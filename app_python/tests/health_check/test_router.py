from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from app import app
from routes.health_check.schemas import HealthResponse
from routes.health_check.service import HealthCheckService


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_get_health_success(client: TestClient, mocker: MockerFixture):
    mock_service = mocker.AsyncMock()
    mock_service.health_check.return_value = HealthResponse(
        status="healthy",
        timestamp=datetime(2026, 2, 12, 11, 37, 1, 912380, tzinfo=timezone.utc),
        uptime_seconds=1020
    )

    # Override зависимости
    app.dependency_overrides[HealthCheckService] = lambda: mock_service

    r = client.get("/health")
    print(r.json())

    assert r.status_code == 200
    assert r.json()["uptime_seconds"] == 1020
    assert r.json()["status"] == "healthy"

    mock_service.health_check.assert_awaited_once()
    app.dependency_overrides.clear()

