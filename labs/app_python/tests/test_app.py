"""Unit tests for DevOps Info Service."""
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


# --- GET / endpoint ---

def test_root_status_code():
    response = client.get("/")
    assert response.status_code == 200


def test_root_has_service_section():
    response = client.get("/")
    data = response.json()
    assert "service" in data
    assert data["service"]["name"] == "devops-info-service"
    assert data["service"]["version"] == "1.0.0"
    assert data["service"]["framework"] == "FastAPI"


def test_root_has_system_section():
    response = client.get("/")
    data = response.json()
    assert "system" in data
    system = data["system"]
    assert "hostname" in system
    assert "platform" in system
    assert "python_version" in system
    assert isinstance(system["cpu_count"], int)


def test_root_has_runtime_section():
    response = client.get("/")
    data = response.json()
    assert "runtime" in data
    runtime = data["runtime"]
    assert "uptime_seconds" in runtime
    assert "uptime_human" in runtime
    assert "current_time" in runtime
    assert runtime["timezone"] == "UTC"


def test_root_has_request_section():
    response = client.get("/")
    data = response.json()
    assert "request" in data
    req = data["request"]
    assert "client_ip" in req
    assert "user_agent" in req
    assert req["method"] == "GET"
    assert req["path"] == "/"


def test_root_has_endpoints_list():
    response = client.get("/")
    data = response.json()
    assert "endpoints" in data
    assert isinstance(data["endpoints"], list)
    assert len(data["endpoints"]) >= 2


def test_root_returns_json():
    response = client.get("/")
    assert response.headers["content-type"] == "application/json"


# --- GET /health endpoint ---

def test_health_status_code():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_status_healthy():
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "healthy"


def test_health_has_timestamp():
    response = client.get("/health")
    data = response.json()
    assert "timestamp" in data
    assert data["timestamp"].endswith("Z")


def test_health_has_uptime():
    response = client.get("/health")
    data = response.json()
    assert "uptime_seconds" in data
    assert isinstance(data["uptime_seconds"], int)
    assert data["uptime_seconds"] >= 0


# --- Error handling ---

def test_not_found_returns_404():
    response = client.get("/nonexistent")
    assert response.status_code == 404


def test_not_found_returns_error_json():
    response = client.get("/nonexistent")
    data = response.json()
    assert "detail" in data or "error" in data
