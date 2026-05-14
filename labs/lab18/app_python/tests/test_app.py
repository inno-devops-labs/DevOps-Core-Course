from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_root_status():
    response = client.get("/")
    assert response.status_code == 200


def test_root_structure():
    response = client.get("/")
    data = response.json()

    assert "service" in data
    assert "system" in data
    assert "runtime" in data
    assert "request" in data
    assert "endpoints" in data


def test_health_status():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_structure():
    response = client.get("/health")
    data = response.json()

    assert "status" in data
    assert "timestamp" in data
    assert "uptime_seconds" in data
