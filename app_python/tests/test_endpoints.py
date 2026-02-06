import pytest
from app import app


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "service" in data
    assert data["service"]["name"] == "devops-info-service"
    
    assert "system" in data
    assert "hostname" in data["system"]
    assert "platform" in data["system"]
    
    assert "endpoints" in data
    assert any(e["path"] == "/" for e in data["endpoints"])
    assert any(e["path"] == "/health" for e in data["endpoints"])


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "uptime_seconds" in data


def test_404(client):
    resp = client.get("/notfound")
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["error"] == "Not Found"
