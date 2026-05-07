from src.app import app
import pytest
import re
from pathlib import Path


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("VISITS_FILE", str(tmp_path / "visits"))
    monkeypatch.delenv("DEVOPS_SERVICE_VERSION", raising=False)
    monkeypatch.delenv("DEVOPS_RELEASE_TRACK", raising=False)
    monkeypatch.delenv("DEVOPS_RELEASE_COLOR", raising=False)
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
    assert "visits" in data
    assert "endpoints" in data


def test_index_service_fields(client):
    data = client.get("/").get_json()
    service = data["service"]

    assert service["name"] == "devops-info-service"
    assert service["version"] == "1.0.0"
    assert service["framework"] == "Flask"
    assert isinstance(service["description"], str)


def test_index_service_release_metadata_overrides(client, monkeypatch):
    monkeypatch.setenv("DEVOPS_SERVICE_VERSION", "2.0.0-canary")
    monkeypatch.setenv("DEVOPS_RELEASE_TRACK", "canary")
    monkeypatch.setenv("DEVOPS_RELEASE_COLOR", "green")

    service = client.get("/").get_json()["service"]

    assert service["version"] == "2.0.0-canary"
    assert service["release_track"] == "canary"
    assert service["release_color"] == "green"


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
    assert any(e["path"] == "/visits" for e in endpoints)
    assert any(e["path"] == "/metrics" for e in endpoints)


def test_visits_starts_at_zero_when_file_is_missing(client):
    response = client.get("/visits")

    assert response.status_code == 200
    assert response.get_json()["visits"] == 0


def test_index_increments_persisted_visits_count(client):
    first_response = client.get("/").get_json()
    second_response = client.get("/").get_json()

    assert first_response["visits"]["count"] == 1
    assert second_response["visits"]["count"] == 2
    assert second_response["visits"]["file"].endswith("visits")


def test_visits_does_not_increment_counter(client):
    client.get("/")
    client.get("/")

    response = client.get("/visits")

    assert response.status_code == 200
    assert response.get_json()["visits"] == 2


def test_invalid_visits_file_contents_are_handled(client, monkeypatch, tmp_path):
    visits_file = tmp_path / "invalid-visits"
    visits_file.write_text("not-a-number", encoding="utf-8")
    monkeypatch.setenv("VISITS_FILE", str(visits_file))

    visits_response = client.get("/visits")
    index_response = client.get("/")

    assert visits_response.get_json()["visits"] == 0
    assert index_response.get_json()["visits"]["count"] == 1


def test_index_creates_visits_parent_directory(client, monkeypatch, tmp_path):
    visits_file = tmp_path / "nested" / "directory" / "visits"
    monkeypatch.setenv("VISITS_FILE", str(visits_file))

    client.get("/")

    assert Path(visits_file).exists()


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


def test_metrics_success(client):
    client.get("/")
    client.get("/health")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.mimetype.startswith("text/plain")


def test_metrics_contains_http_and_app_specific_metrics(client):
    client.get("/")
    client.get("/health")
    client.get("/visits")
    client.get("/non-existent")

    metrics_output = client.get("/metrics").get_data(as_text=True)

    assert "http_requests_total" in metrics_output
    assert "http_request_duration_seconds" in metrics_output
    assert "http_requests_in_progress" in metrics_output
    assert "devops_info_endpoint_calls_total" in metrics_output
    assert "devops_info_system_info_collection_seconds" in metrics_output
    assert 'endpoint="/"' in metrics_output
    assert 'endpoint="/health"' in metrics_output
    assert 'endpoint="/visits"' in metrics_output


# ----------------------------
# Error Handling Tests
# ----------------------------


def test_404_error(client):
    response = client.get("/non-existent")
    assert response.status_code == 404

    data = response.get_json()
    assert data["error"] == "Not Found"
    assert data["message"] == "Endpoint does not exist"
