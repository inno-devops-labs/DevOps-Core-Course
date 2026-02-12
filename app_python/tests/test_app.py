from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_root_endpoint_status_code():
    response = client.get("/")
    assert response.status_code == 200


def test_root_endpoint_structure():
    response = client.get("/")
    data = response.json()

    assert "service" in data
    assert "system" in data
    assert "runtime" in data
    assert "request" in data
    assert "endpoints" in data


def test_service_info():
    response = client.get("/")
    service = response.json()["service"]

    assert service["name"] == "devops-info-service"
    assert service["framework"] == "FastAPI"


def test_health_endpoint_status_code():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_endpoint_payload():
    response = client.get("/health")
    data = response.json()

    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "uptime_seconds" in data
    assert isinstance(data["uptime_seconds"], int)


def test_runtime_fields():
    data = client.get("/").json()["runtime"]

    assert isinstance(data["uptime_seconds"], int)
    assert isinstance(data["uptime_human"], str)
    assert isinstance(data["current_time"], str)
    assert data["timezone"] == "UTC"


def test_system_info_fields():
    system = client.get("/").json()["system"]

    assert "hostname" in system
    assert "platform" in system
    assert "architecture" in system
    assert "cpu_count" in system
    assert "python_version" in system

    assert isinstance(system["cpu_count"], int)


def test_not_found_endpoint():
    response = client.get("/does-not-exist")
    assert response.status_code == 404
