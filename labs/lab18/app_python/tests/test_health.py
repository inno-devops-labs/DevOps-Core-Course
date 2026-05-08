from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_health_status_code():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_structure():
    response = client.get("/health")
    data = response.json()

    required_fields = ["status", "timestamp", "uptime_seconds"]

    for field in required_fields:
        assert field in data

    assert data["status"] == "healthy"
    assert isinstance(data["uptime_seconds"], int)
    assert data["uptime_seconds"] >= 0


def test_health_method_not_allowed():
    response = client.post("/health")
    assert response.status_code == 405


def test_unknown_endpoint():
    response = client.get("/non-existent")
    assert response.status_code == 404
