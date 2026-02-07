from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_root_success_structure():
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert set(data.keys()) >= {"service", "system", "runtime", "request", "endpoints"}

    service = data["service"]
    assert service["name"] == "devops-info-service"
    assert service["framework"] == "FastAPI"

    request = data["request"]
    assert request["path"] == "/"
    assert request["method"] == "GET"

    runtime = data["runtime"]
    assert isinstance(runtime["uptime_seconds"], int)
    assert runtime["uptime_seconds"] >= 0
    assert runtime["timezone"] == "UTC"

    endpoints = data["endpoints"]
    assert any(endpoint["path"] == "/" for endpoint in endpoints)
    assert any(endpoint["path"] == "/health" for endpoint in endpoints)


def test_health_success():
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert isinstance(data["uptime_seconds"], int)


def test_not_found_error_response():
    response = client.get("/does-not-exist")
    assert response.status_code == 404

    data = response.json()
    assert data["error"] == "Not Found"
    assert "message" in data


def test_method_not_allowed_error_response():
    response = client.post("/health")
    assert response.status_code == 405
