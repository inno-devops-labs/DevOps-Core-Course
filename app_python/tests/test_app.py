"""
Unit tests for DevOps Info Service.

Testing framework: pytest
- Simple syntax and fixtures
- Widely used in Python ecosystem
- Excellent plugin support (pytest-flask)
"""

import json
import re

import pytest

import app as app_module

flask_app = app_module.app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Create a test client for the Flask application."""
    visits_file_path = tmp_path / "data" / "visits"
    config_file_path = tmp_path / "config" / "config.json"
    config_file_path.parent.mkdir(parents=True, exist_ok=True)
    config_file_path.write_text(
        json.dumps(
            {
                "application": {
                    "name": "devops-info-service",
                    "environment": "test",
                },
                "features": {
                    "visitsEndpoint": True,
                    "metricsEndpoint": True,
                },
                "settings": {
                    "logLevel": "INFO",
                    "visitsFilePath": str(visits_file_path),
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("VISITS_FILE_PATH", str(visits_file_path))
    monkeypatch.setenv("APP_CONFIG_PATH", str(config_file_path))

    flask_app.config.update({"TESTING": True})
    with flask_app.test_client() as test_client:
        yield test_client


class TestIndexEndpoint:
    """Tests for GET / endpoint."""

    def test_index_returns_200(self, client):
        """Index endpoint should return 200 OK."""
        response = client.get("/")
        assert response.status_code == 200

    def test_index_returns_json(self, client):
        """Index endpoint should return JSON content type."""
        response = client.get("/")
        assert response.content_type == "application/json"

    def test_index_has_required_sections(self, client):
        """Index response should contain all required sections."""
        response = client.get("/")
        data = response.get_json()

        assert "service" in data
        assert "system" in data
        assert "runtime" in data
        assert "request" in data
        assert "configuration" in data
        assert "visits" in data
        assert "endpoints" in data

    def test_index_service_info(self, client):
        """Service section should contain correct info."""
        response = client.get("/")
        data = response.get_json()
        service = data["service"]

        assert service["name"] == "devops-info-service"
        assert service["framework"] == "Flask"
        assert "version" in service
        assert "description" in service
        assert "environment" in service

    def test_index_system_info(self, client):
        """System section should contain all system fields."""
        response = client.get("/")
        data = response.get_json()
        system = data["system"]

        assert "hostname" in system
        assert "platform" in system
        assert "platform_version" in system
        assert "architecture" in system
        assert "cpu_count" in system
        assert "python_version" in system
        assert isinstance(system["cpu_count"], int)

    def test_index_runtime_info(self, client):
        """Runtime section should contain uptime and time info."""
        response = client.get("/")
        data = response.get_json()
        runtime = data["runtime"]

        assert isinstance(runtime["uptime_seconds"], int)
        assert isinstance(runtime["uptime_human"], str)
        assert re.match(r"\d+ hours?, \d+ minutes?", runtime["uptime_human"])
        assert "current_time" in runtime
        assert runtime["timezone"] == "UTC"

    def test_index_request_info(self, client):
        """Request section should contain client info."""
        response = client.get("/")
        data = response.get_json()
        request_info = data["request"]

        assert request_info["method"] == "GET"
        assert request_info["path"] == "/"
        assert "client_ip" in request_info
        assert "user_agent" in request_info

    def test_index_endpoints_list(self, client):
        """Endpoints list should contain the public HTTP endpoints."""
        response = client.get("/")
        data = response.get_json()
        endpoints = {ep["path"] for ep in data["endpoints"]}

        assert "/" in endpoints
        assert "/health" in endpoints
        assert "/visits" in endpoints
        assert "/metrics" in endpoints

    def test_index_includes_runtime_configuration(self, client):
        """Index response should expose env-backed and file-backed configuration."""
        response = client.get("/")
        data = response.get_json()

        assert data["configuration"]["environment"] == "local"
        assert data["configuration"]["file"]["loaded"] is True
        assert data["configuration"]["file"]["data"]["application"]["environment"] == "test"
        assert "last_modified" in data["configuration"]["file"]
        assert data["configuration"]["env"]["visits_file_path"].endswith("/data/visits")
        assert data["configuration"]["env"]["feature_flags"]["config_reload_enabled"] is True

    def test_index_increments_visits_counter(self, client):
        """Root endpoint should increment the persistent visits counter."""
        first_response = client.get("/")
        second_response = client.get("/")

        assert first_response.get_json()["visits"]["count"] == 1
        assert second_response.get_json()["visits"]["count"] == 2


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_returns_200(self, client):
        """Health endpoint should return 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_json(self, client):
        """Health endpoint should return JSON content type."""
        response = client.get("/health")
        assert response.content_type == "application/json"

    def test_health_status_healthy(self, client):
        """Health status should be 'healthy'."""
        response = client.get("/health")
        data = response.get_json()
        assert data["status"] == "healthy"

    def test_health_has_required_fields(self, client):
        """Health response should have all required fields."""
        response = client.get("/health")
        data = response.get_json()

        assert "status" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], int)


class TestVisitsEndpoint:
    """Tests for GET /visits endpoint."""

    def test_startup_initialization_creates_counter_file_with_zero(
        self,
        tmp_path,
        monkeypatch,
    ):
        """Startup initialization should create the counter file and load a default zero."""
        visits_file_path = tmp_path / "data" / "visits"
        monkeypatch.setenv("VISITS_FILE_PATH", str(visits_file_path))

        initial_count = app_module.initialize_visits_storage()

        assert initial_count == 0
        assert visits_file_path.read_text(encoding="utf-8") == "0\n"

    def test_visits_returns_200(self, client):
        """Visits endpoint should return 200 OK."""
        response = client.get("/visits")
        assert response.status_code == 200

    def test_visits_starts_at_zero_before_root_requests(self, client):
        """Visits endpoint should default to zero before the first root request."""
        response = client.get("/visits")
        assert response.get_json()["count"] == 0

    def test_visits_persists_across_requests(self, client):
        """Visits endpoint should reflect persisted increments from the root endpoint."""
        client.get("/")
        client.get("/")

        response = client.get("/visits")
        payload = response.get_json()

        assert payload["count"] == 2
        assert payload["path"].endswith("/data/visits")
        assert "timestamp" in payload

    def test_config_file_changes_are_reloaded_on_next_request(
        self,
        client,
        tmp_path,
        monkeypatch,
    ):
        """Config file changes should be visible without restarting the process."""
        config_file_path = tmp_path / "config" / "config.json"
        config_file_path.write_text(
            json.dumps(
                {
                    "application": {
                        "name": "devops-info-service",
                        "environment": "reloaded",
                    },
                    "features": {
                        "configReload": True,
                    },
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setenv("APP_CONFIG_PATH", str(config_file_path))

        response = client.get("/")
        payload = response.get_json()

        assert payload["configuration"]["file"]["loaded"] is True
        assert (
            payload["configuration"]["file"]["data"]["application"]["environment"]
            == "reloaded"
        )


class TestErrorHandling:
    """Tests for error handlers."""

    def test_404_not_found(self, client):
        """Non-existent endpoint should return 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_404_returns_json(self, client):
        """404 error should return JSON."""
        response = client.get("/nonexistent")
        assert response.content_type == "application/json"

    def test_404_error_structure(self, client):
        """404 response should have proper structure."""
        response = client.get("/nonexistent")
        data = response.get_json()

        assert data["error"] == "Not Found"
        assert data["status_code"] == 404
        assert "message" in data

    def test_405_method_not_allowed(self, client):
        """Unsupported methods should return JSON 405 responses."""
        response = client.post("/")
        data = response.get_json()

        assert response.status_code == 405
        assert response.content_type == "application/json"
        assert data["error"] == "Method Not Allowed"
        assert data["status_code"] == 405
        assert "message" in data
        assert "allowed_methods" in data
        assert "GET" in data["allowed_methods"]


class TestMetricsEndpoint:
    """Tests for GET /metrics endpoint and Prometheus instrumentation."""

    def test_metrics_returns_200(self, client):
        """Metrics endpoint should return 200 OK."""
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_returns_prometheus_content_type(self, client):
        """Metrics endpoint should return Prometheus text exposition format."""
        response = client.get("/metrics")
        assert response.content_type.startswith("text/plain")

    def test_metrics_expose_expected_metric_names(self, client):
        """Metrics output should include the custom application metrics."""
        response = client.get("/metrics")
        payload = response.get_data(as_text=True)

        assert "http_requests_total" in payload
        assert "http_request_duration_seconds" in payload
        assert "http_requests_in_progress" in payload
        assert "devops_info_endpoint_calls_total" in payload
        assert "devops_info_system_collection_seconds" in payload

    def test_metrics_capture_application_requests(self, client):
        """Request metrics should include normalized endpoint labels."""
        client.get("/")
        client.get("/health")
        client.get("/nonexistent")

        response = client.get("/metrics")
        payload = response.get_data(as_text=True)

        assert re.search(
            r'http_requests_total\{endpoint="/",method="GET",status_code="200"\} \d+\.?\d*',
            payload
        )
        assert re.search(
            r'http_requests_total\{endpoint="/health",method="GET",status_code="200"\} \d+\.?\d*',
            payload
        )
        assert re.search(
            r'http_requests_total\{endpoint="unmatched",method="GET",status_code="404"\} \d+\.?\d*',
            payload
        )
        assert 'endpoint="/metrics"' not in payload
