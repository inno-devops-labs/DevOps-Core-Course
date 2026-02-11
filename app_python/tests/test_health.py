from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_health_status_code():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response():
    data = client.get("/health").json()

    assert data["status"] == "healthy"
    assert isinstance(data["uptime_seconds"], int)
    assert "timestamp" in data
