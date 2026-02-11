from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_root_endpoint_structure():
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()

    assert "service" in data
    assert "system" in data
    assert "runtime" in data
    assert "request" in data
    assert "endpoints" in data


def test_root_service_fields():
    response = client.get("/")
    data = response.json()

    assert data["service"]["name"] == "devops-info-service"
    assert data["service"]["framework"] == "FastAPI"


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "uptime_seconds" in data


def test_404_handler():
    response = client.get("/nonexistent")
    assert response.status_code == 404

    data = response.json()
    assert data["error"] == "Not Found"
    assert data["message"] == "Endpoint does not exist"
