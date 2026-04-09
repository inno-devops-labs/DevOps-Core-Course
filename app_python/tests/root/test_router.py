import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from datetime import datetime, timezone

from app import app
from routes.root.service import SysInfoService
from routes.root.schemas import (
    InfoResponse,
    ServiceInfo,
    SystemInfo,
    RuntimeInfo,
    RequestInfo,
    EndpointInfo,
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_get_info_router(client: TestClient, mocker: MockerFixture) -> None:
    mock_service = mocker.AsyncMock()
    mock_service.get_info.return_value = InfoResponse(
        service=ServiceInfo(
            name="test-service", version="1.0", description="desc", framework="FastAPI"
        ),
        system=SystemInfo(
            hostname="localhost",
            platform="Linux",
            platform_version="5.0",
            architecture="x86_64",
            cpu_count=4,
            python_version="3.11",
        ),
        runtime=RuntimeInfo(
            uptime_seconds=1000,
            uptime_human="0 hours, 16 minutes",
            current_time=datetime.now(tz=timezone.utc),
            timezone="UTC",
        ),
        request=RequestInfo(
            client_ip="127.0.0.1", user_agent="pytest", method="GET", path="/"
        ),
        endpoints=[
            EndpointInfo(path="/", method="GET", description="Service information")
        ],
    )

    app.dependency_overrides[SysInfoService] = lambda: mock_service

    response = client.get("/")

    assert response.status_code == 200
    json_data = response.json()
    print(json_data)
    assert json_data["service"]["name"] == "test-service"
    assert json_data["system"]["hostname"] == "localhost"
    assert json_data["runtime"]["uptime_seconds"] == 1000
    assert json_data["request"]["method"] == "GET"
    assert len(json_data["endpoints"]) == 1

    mock_service.get_info.assert_awaited_once()
    app.dependency_overrides.clear()
