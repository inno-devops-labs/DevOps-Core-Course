import json
import re

import pytest

from src.app import app


@pytest.fixture
def client(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "application": {
                    "name": "test-devops-info-service",
                    "environment": "test",
                    "description": "Test config for the DevOps info service",
                    "version": "1.0.0",
                },
                "featureFlags": {
                    "visitsCounter": True,
                    "metricsEndpoint": True,
                    "showRuntimeDetails": True,
                },
                "settings": {
                    "logLevel": "DEBUG",
                    "visitsFile": str(tmp_path / "visits"),
                },
            }
        ),
        encoding="utf-8",
    )

    original_values = {
        "TESTING": app.config.get("TESTING"),
        "VISITS_FILE": app.config.get("VISITS_FILE"),
        "APP_CONFIG_PATH": app.config.get("APP_CONFIG_PATH"),
        "APP_NAME": app.config.get("APP_NAME"),
        "APP_ENV": app.config.get("APP_ENV"),
        "LOG_LEVEL": app.config.get("LOG_LEVEL"),
    }

    app.config.update(
        TESTING=True,
        VISITS_FILE=str(tmp_path / "visits"),
        APP_CONFIG_PATH=str(config_path),
        APP_NAME="test-devops-info-service",
        APP_ENV="test",
        LOG_LEVEL="DEBUG",
    )

    with app.test_client() as test_client:
        yield test_client

    app.config.update(original_values)


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

    assert "service" in data
    assert "system" in data
    assert "request" in data
    assert "runtime" in data
    assert "configuration" in data
    assert "visits" in data
    assert "endpoints" in data


def test_index_service_fields(client):
    data = client.get("/").get_json()
    service = data["service"]

    assert service["name"] == "test-devops-info-service"
    assert service["version"] == "1.0.0"
    assert service["framework"] == "Flask"
    assert service["environment"] == "test"
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
    assert runtime["current_time"].endswith("Z")


def test_index_configuration_fields(client):
    configuration = client.get("/").get_json()["configuration"]

    assert configuration["environment"] == "test"
    assert configuration["log_level"] == "DEBUG"
    assert configuration["file_loaded"] is True
    assert configuration["config_path"].endswith("config.json")
    assert configuration["feature_flags"]["visitsCounter"] is True


def test_index_visits_are_incremented(client):
    first_response = client.get("/").get_json()
    second_response = client.get("/").get_json()

    assert first_response["visits"]["count"] == 1
    assert second_response["visits"]["count"] == 2
    assert second_response["visits"]["file"].endswith("visits")


def test_index_endpoints_list(client):
    data = client.get("/").get_json()
    endpoints = data["endpoints"]

    assert isinstance(endpoints, list)
    assert any(endpoint["path"] == "/" for endpoint in endpoints)
    assert any(endpoint["path"] == "/health" for endpoint in endpoints)
    assert any(endpoint["path"] == "/visits" for endpoint in endpoints)
    assert any(endpoint["path"] == "/metrics" for endpoint in endpoints)


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

    iso_regex = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    assert re.match(iso_regex, timestamp)


def test_visits_returns_current_count_without_incrementing(client):
    client.get("/")
    client.get("/")

    visits_response = client.get("/visits")

    assert visits_response.status_code == 200
    assert visits_response.get_json()["visits"] == 2


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
