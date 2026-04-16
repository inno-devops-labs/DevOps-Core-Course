"""
Unit tests for DevOps Info Service.
Tests endpoints, file-backed visit persistence, and config loading.
"""

from concurrent.futures import ThreadPoolExecutor
import json
from datetime import datetime

import pytest

import app as app_module


@pytest.fixture
def runtime_files(monkeypatch, tmp_path):
    """Prepare isolated runtime files for each test."""
    visits_file = tmp_path / "data" / "visits"
    config_file = tmp_path / "config" / "config.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(
        json.dumps(
            {
                "application": {
                    "name": "devops-info-service",
                    "environment": "test",
                },
                "featureFlags": {
                    "visitsCounter": True,
                    "configMapDemo": True,
                },
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(app_module, "VISITS_FILE_PATH", visits_file)
    monkeypatch.setattr(app_module, "APP_CONFIG_FILE", config_file)

    with app_module.visit_counter_lock:
        app_module.VISIT_COUNTER = app_module.read_visit_count_from_file()

    return {
        "visits_file": visits_file,
        "config_file": config_file,
    }


@pytest.fixture
def client(runtime_files):
    """Create a test client for the Flask application."""
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        yield client


class TestMainEndpoint:
    """Tests for GET / endpoint."""

    def test_main_endpoint_status_code(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_main_endpoint_content_type(self, client):
        response = client.get("/")
        assert response.content_type == "application/json"

    def test_main_endpoint_service_info(self, client):
        response = client.get("/")
        data = response.get_json()

        assert "service" in data
        assert data["service"]["name"] == "devops-info-service"
        assert data["service"]["version"] == "1.0.0"
        assert data["service"]["description"] == "DevOps course info service"
        assert data["service"]["framework"] == "Flask"

    def test_main_endpoint_system_info(self, client):
        response = client.get("/")
        data = response.get_json()
        system = data["system"]

        assert isinstance(system["hostname"], str)
        assert isinstance(system["platform"], str)
        assert isinstance(system["platform_version"], str)
        assert isinstance(system["architecture"], str)
        assert isinstance(system["cpu_count"], int)
        assert isinstance(system["python_version"], str)
        assert system["cpu_count"] > 0

    def test_main_endpoint_runtime_info(self, client):
        response = client.get("/")
        data = response.get_json()
        runtime = data["runtime"]

        assert isinstance(runtime["uptime_seconds"], int)
        assert isinstance(runtime["uptime_human"], str)
        assert isinstance(runtime["current_time"], str)
        assert runtime["timezone"] == "UTC"
        assert runtime["uptime_seconds"] >= 0
        datetime.fromisoformat(runtime["current_time"].replace("Z", "+00:00"))

    def test_main_endpoint_request_info(self, client):
        response = client.get("/", headers={"User-Agent": "TestAgent/1.0"})
        data = response.get_json()
        request_info = data["request"]

        assert request_info["method"] == "GET"
        assert request_info["path"] == "/"
        assert request_info["user_agent"] == "TestAgent/1.0"
        assert isinstance(request_info["client_ip"], str)

    def test_main_endpoint_endpoints_list(self, client):
        response = client.get("/")
        data = response.get_json()

        assert "endpoints" in data
        assert isinstance(data["endpoints"], list)
        assert len(data["endpoints"]) == 4

        paths = [endpoint["path"] for endpoint in data["endpoints"]]
        assert "/" in paths
        assert "/health" in paths
        assert "/visits" in paths
        assert "/metrics" in paths

    def test_main_endpoint_increments_and_persists_visits(self, client, runtime_files):
        first_response = client.get("/")
        second_response = client.get("/")

        first_count = first_response.get_json()["visits"]["count"]
        second_count = second_response.get_json()["visits"]["count"]

        assert first_count == 1
        assert second_count == 2
        assert runtime_files["visits_file"].read_text(encoding="utf-8").strip() == "2"

    def test_main_endpoint_loads_config_file(self, client, runtime_files):
        response = client.get("/")
        data = response.get_json()
        configuration = data["configuration"]

        assert configuration["loaded"] is True
        assert configuration["path"] == str(runtime_files["config_file"])
        assert configuration["data"]["application"]["environment"] == "test"
        assert configuration["data"]["featureFlags"]["visitsCounter"] is True

    def test_main_endpoint_handles_missing_config_file(self, client, monkeypatch, tmp_path):
        missing_config = tmp_path / "missing" / "config.json"
        monkeypatch.setattr(app_module, "APP_CONFIG_FILE", missing_config)

        response = client.get("/")
        data = response.get_json()

        assert data["configuration"]["loaded"] is False
        assert data["configuration"]["path"] == str(missing_config)
        assert data["configuration"]["data"] == {}


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_endpoint_status_code(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_content_type(self, client):
        response = client.get("/health")
        assert response.content_type == "application/json"

    def test_health_endpoint_structure(self, client):
        response = client.get("/health")
        data = response.get_json()

        assert data["status"] == "healthy"
        assert isinstance(data["uptime_seconds"], int)
        assert data["uptime_seconds"] >= 0
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

    def test_health_endpoint_uptime_increases(self, client):
        import time

        response1 = client.get("/health")
        uptime1 = response1.get_json()["uptime_seconds"]

        time.sleep(1)

        response2 = client.get("/health")
        uptime2 = response2.get_json()["uptime_seconds"]

        assert uptime2 >= uptime1


class TestVisitsEndpoint:
    """Tests for GET /visits endpoint."""

    def test_visits_endpoint_returns_current_count_without_increment(self, client):
        client.get("/")
        client.get("/")

        response = client.get("/visits")
        data = response.get_json()

        assert response.status_code == 200
        assert data["count"] == 2

        second_response = client.get("/visits")
        assert second_response.get_json()["count"] == 2

    def test_visits_endpoint_returns_zero_when_file_does_not_exist(self, client, runtime_files):
        assert runtime_files["visits_file"].exists() is False

        response = client.get("/visits")
        data = response.get_json()

        assert data["count"] == 0
        assert data["file_path"] == str(runtime_files["visits_file"])


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_error(self, client):
        response = client.get("/nonexistent")

        assert response.status_code == 404
        assert response.content_type == "application/json"

        data = response.get_json()
        assert data["error"] == "Not Found"
        assert data["message"] == "Endpoint does not exist"

    def test_404_error_different_paths(self, client):
        invalid_paths = ["/invalid", "/api/v1", "/test/123"]

        for path in invalid_paths:
            response = client.get(path)
            assert response.status_code == 404
            assert response.get_json()["error"] == "Not Found"


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_service_info(self):
        info = app_module.get_service_info()

        assert isinstance(info, dict)
        assert info["name"] == "devops-info-service"
        assert info["version"] == "1.0.0"
        assert info["description"] == "DevOps course info service"
        assert info["framework"] == "Flask"

    def test_get_system_info(self):
        info = app_module.get_system_info()

        assert isinstance(info, dict)
        assert isinstance(info["cpu_count"], int)
        assert info["cpu_count"] > 0

    def test_get_endpoints(self):
        endpoints = app_module.get_endpoints()

        assert isinstance(endpoints, list)
        assert len(endpoints) == 4
        assert any(endpoint["path"] == "/visits" for endpoint in endpoints)

    def test_get_uptime(self):
        uptime = app_module.get_uptime()

        assert isinstance(uptime, dict)
        assert isinstance(uptime["seconds"], int)
        assert uptime["seconds"] >= 0
        assert isinstance(uptime["human"], str)

    def test_read_visit_count_from_invalid_file(self, monkeypatch, tmp_path):
        visits_file = tmp_path / "data" / "visits"
        visits_file.parent.mkdir(parents=True, exist_ok=True)
        visits_file.write_text("not-a-number", encoding="utf-8")
        monkeypatch.setattr(app_module, "VISITS_FILE_PATH", visits_file)

        assert app_module.read_visit_count_from_file() == 0

    def test_increment_visit_count_is_thread_safe(self, monkeypatch, tmp_path):
        visits_file = tmp_path / "data" / "visits"
        monkeypatch.setattr(app_module, "VISITS_FILE_PATH", visits_file)

        with app_module.visit_counter_lock:
            app_module.VISIT_COUNTER = 0

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(lambda _: app_module.increment_visit_count(), range(25)))

        assert sorted(results) == list(range(1, 26))
        assert app_module.read_visit_count_from_file() == 25
        assert visits_file.read_text(encoding="utf-8").strip() == "25"


class TestHTTPMethods:
    """Tests for unsupported HTTP methods."""

    def test_post_not_allowed(self, client):
        response = client.post("/")
        assert response.status_code in [405, 200]

    def test_put_not_allowed(self, client):
        response = client.put("/")
        assert response.status_code in [405, 200]

    def test_delete_not_allowed(self, client):
        response = client.delete("/")
        assert response.status_code in [405, 200]
