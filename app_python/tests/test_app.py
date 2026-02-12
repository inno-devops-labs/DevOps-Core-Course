from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_root_returns_required_structure():
    response = client.get("/", headers={"User-Agent": "pytest"})
    assert response.status_code == 200

    data = response.json()

    assert "service" in data
    assert "system" in data
    assert "runtime" in data
    assert "request" in data
    assert "endpoints" in data

    service = data["service"]
    assert service["name"] == "devops-info-service"
    assert service["version"] == "1.0.0"
    assert service["framework"] == "FastAPI"

    system = data["system"]
    for key in ["hostname", "platform", "platform_version", "architecture", "cpu_count", "python_version"]:
        assert key in system

    runtime = data["runtime"]
    assert isinstance(runtime["uptime_seconds"], int)
    assert runtime["uptime_seconds"] >= 0
    assert isinstance(runtime["uptime_human"], str)
    assert isinstance(runtime["current_time"], str)
    assert runtime["timezone"] == "UTC"

    req = data["request"]
    assert req["method"] == "GET"
    assert req["path"] == "/"
    assert isinstance(req["user_agent"], (str, type(None)))


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert isinstance(data["timestamp"], str)
    assert isinstance(data["uptime_seconds"], int)
    assert data["uptime_seconds"] >= 0


def test_404_returns_json():
    response = client.get("/does-not-exist")
    assert response.status_code == 404

    data = response.json()
    assert data["error"] == "Not Found"
    assert "message" in data

