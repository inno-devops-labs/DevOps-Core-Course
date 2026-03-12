from src.app import app
import pytest
import re


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ----------------------------
# GET / Tests
# ----------------------------


def test_index_success_status_code(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.is_json


def test_index_json_structure(client):
    response = client.get("/")
    data = response.get_json()

    # Top-level keys
    assert "service" in data
    assert "system" in data
    assert "request" in data
    assert "runtime" in data
    assert "endpoints" in data


def test_index_service_fields(client):
    data = client.get("/").get_json()
    service = data["service"]

    assert service["name"] == "devops-info-service"
    assert service["version"] == "1.0.0"
    assert service["framework"] == "Flask"
    assert isinstance(service["description"], str)


def test_index_system_fields(client):
    data = client.get("/").get_json()
    system = data["system"]

    assert "hostname" in system
    assert "platform" in system
    assert "architecture" in system
    assert "python_version" in system

    assert isinstance(system["hostname"], str)
    assert isinstance(system["platform"], str)
    assert isinstance(system["architecture"], str)
    assert isinstance(system["python_version"], str)


def test_index_request_fields(client):
    response = client.get("/", headers={"User-Agent": "pytest-agent"})
    data = response.get_json()
    request_info = data["request"]

    assert request_info["method"] == "GET"
    assert request_info["path"] == "/"
    assert request_info["user_agent"] == "pytest-agent"
    assert request_info["client_ip"] is not None


def test_index_runtime_fields(client):
    data = client.get("/").get_json()
    runtime = data["runtime"]

    assert "seconds" in runtime
    assert "human" in runtime
    assert "current_time" in runtime
    assert runtime["timezone"] == "UTC"

    assert isinstance(runtime["seconds"], int)
    assert runtime["seconds"] >= 0

    # Validate Zulu timestamp format
    assert runtime["current_time"].endswith("Z")


def test_index_endpoints_list(client):
    data = client.get("/").get_json()
    endpoints = data["endpoints"]

    assert isinstance(endpoints, list)
    assert any(e["path"] == "/" for e in endpoints)
    assert any(e["path"] == "/health" for e in endpoints)


# ----------------------------
# GET /health Tests
# ----------------------------


def test_health_success(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.is_json


def test_health_response_structure(client):
    data = client.get("/health").get_json()

    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "uptime_seconds" in data

    assert isinstance(data["uptime_seconds"], int)
    assert data["uptime_seconds"] >= 0


def test_health_timestamp_format(client):
    data = client.get("/health").get_json()
    timestamp = data["timestamp"]

    # ISO 8601 basic validation
    iso_regex = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    assert re.match(iso_regex, timestamp)


# ----------------------------
# Error Handling Tests
# ----------------------------


def test_404_error(client):
    response = client.get("/non-existent")
    assert response.status_code == 404

    data = response.get_json()
    assert data["error"] == "Not Found"
    assert data["message"] == "Endpoint does not exist"
