from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_root_status_code():
    response = client.get("/")
    assert response.status_code == 200


def test_root_response_structure():
    response = client.get("/")
    data = response.json()

    assert "service" in data
    assert "system" in data
    assert "runtime" in data
    assert "request" in data
    assert "endpoints" in data


def test_service_metadata():
    data = client.get("/").json()["service"]

    assert data["name"] == "devops-info-service"
    assert data["framework"] == "FastAPI"
    assert isinstance(data["version"], str)


def test_runtime_fields():
    runtime = client.get("/").json()["runtime"]

    assert isinstance(runtime["uptime_seconds"], int)
    assert isinstance(runtime["uptime_human"], str)
    assert runtime["timezone"] == "UTC"
