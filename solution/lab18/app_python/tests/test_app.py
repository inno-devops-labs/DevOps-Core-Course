import json
import logging

import pytest
from fastapi.testclient import TestClient

from app import JSONFormatter, app


@pytest.fixture
def client(tmp_path, monkeypatch):
    visits_file = tmp_path / "visits"
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "applicationName": "devops-info-service",
                "environment": "test",
                "featureFlags": {
                    "visitsEndpoint": True,
                    "configFromConfigMap": True,
                },
                "settings": {
                    "greeting": "hello-from-config",
                },
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("VISITS_FILE", str(visits_file))
    monkeypatch.setenv("CONFIG_PATH", str(config_path))

    app.state.visits_file = visits_file
    app.state.config_path = config_path

    with TestClient(app) as test_client:
        yield test_client


class TestRootEndpoint:
    """Tests for GET / endpoint."""

    def test_root_status_code(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_root_response_is_json(self, client):
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"

    def test_root_has_service_section(self, client):
        data = client.get("/").json()
        assert "service" in data
        assert isinstance(data["service"], dict)

    def test_root_service_fields(self, client):
        service = client.get("/").json()["service"]
        required_fields = ["name", "version", "description", "framework"]
        for field in required_fields:
            assert field in service, f"Missing field: {field}"
            assert isinstance(service[field], str)

    def test_root_service_name(self, client):
        service = client.get("/").json()["service"]
        assert service["name"] == "devops-info-service"

    def test_root_service_framework(self, client):
        service = client.get("/").json()["service"]
        assert service["framework"] == "FastAPI"

    def test_root_has_system_section(self, client):
        data = client.get("/").json()
        assert "system" in data
        assert isinstance(data["system"], dict)

    def test_root_system_fields(self, client):
        system = client.get("/").json()["system"]
        required_fields = [
            "hostname",
            "platform",
            "platform_version",
            "architecture",
            "cpu_count",
            "python_version",
        ]
        for field in required_fields:
            assert field in system, f"Missing field: {field}"

    def test_root_system_cpu_count_is_positive(self, client):
        system = client.get("/").json()["system"]
        assert isinstance(system["cpu_count"], int)
        assert system["cpu_count"] > 0

    def test_root_has_runtime_section(self, client):
        data = client.get("/").json()
        assert "runtime" in data
        assert isinstance(data["runtime"], dict)

    def test_root_runtime_fields(self, client):
        runtime = client.get("/").json()["runtime"]
        required_fields = ["uptime_seconds", "uptime_human", "current_time", "timezone"]
        for field in required_fields:
            assert field in runtime, f"Missing field: {field}"

    def test_root_uptime_seconds_is_non_negative(self, client):
        runtime = client.get("/").json()["runtime"]
        assert isinstance(runtime["uptime_seconds"], int)
        assert runtime["uptime_seconds"] >= 0

    def test_root_has_configuration_section(self, client):
        configuration = client.get("/").json()["configuration"]
        assert configuration["file_exists"] is True
        assert configuration["content"]["environment"] == "test"

    def test_root_has_visits_section(self, client):
        visits = client.get("/").json()["visits"]
        assert "count" in visits
        assert "file_path" in visits
        assert visits["count"] >= 1

    def test_root_has_request_section(self, client):
        data = client.get("/").json()
        assert "request" in data
        assert isinstance(data["request"], dict)

    def test_root_request_fields(self, client):
        request_data = client.get("/").json()["request"]
        required_fields = ["client_ip", "user_agent", "method", "path"]
        for field in required_fields:
            assert field in request_data, f"Missing field: {field}"

    def test_root_request_method_is_get(self, client):
        request_data = client.get("/").json()["request"]
        assert request_data["method"] == "GET"

    def test_root_request_path_is_root(self, client):
        request_data = client.get("/").json()["request"]
        assert request_data["path"] == "/"

    def test_root_has_endpoints_list(self, client):
        data = client.get("/").json()
        assert "endpoints" in data
        assert isinstance(data["endpoints"], list)
        assert len(data["endpoints"]) > 0

    def test_root_endpoints_have_required_fields(self, client):
        endpoints = client.get("/").json()["endpoints"]
        for endpoint in endpoints:
            assert "path" in endpoint
            assert "method" in endpoint
            assert "description" in endpoint


class TestVisitsEndpoint:
    """Tests for GET /visits endpoint."""

    def test_visits_status_code(self, client):
        response = client.get("/visits")
        assert response.status_code == 200

    def test_visits_returns_zero_before_root_calls(self, client):
        response = client.get("/visits")
        assert response.json()["count"] == 0

    def test_visits_increments_after_root_calls(self, client):
        client.get("/")
        client.get("/")

        response = client.get("/visits")
        assert response.json()["count"] == 2

    def test_visits_persist_in_file(self, client):
        root_response = client.get("/")
        file_path = root_response.json()["visits"]["file_path"]

        response = client.get("/visits")
        assert response.json()["count"] == 1

        with open(file_path, "r", encoding="utf-8") as visits_file:
            assert visits_file.read().strip() == "1"


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_status_code(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_is_json(self, client):
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"

    def test_health_has_status_field(self, client):
        data = client.get("/health").json()
        assert "status" in data

    def test_health_status_is_healthy(self, client):
        data = client.get("/health").json()
        assert data["status"] == "healthy"

    def test_health_has_timestamp(self, client):
        data = client.get("/health").json()
        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)

    def test_health_has_uptime_seconds(self, client):
        data = client.get("/health").json()
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], int)
        assert data["uptime_seconds"] >= 0

    def test_health_required_fields(self, client):
        data = client.get("/health").json()
        required_fields = ["status", "timestamp", "uptime_seconds"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"


class TestMetricsEndpoint:
    """Tests for GET /metrics endpoint and custom metrics."""

    def test_metrics_status_code(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_content_type(self, client):
        response = client.get("/metrics")
        assert "text/plain" in response.headers["content-type"]

    def test_metrics_contains_custom_metric_names(self, client):
        client.get("/")
        client.get("/health")
        client.get("/visits")

        response = client.get("/metrics")
        body = response.text

        assert "app_http_requests_total" in body
        assert "app_http_request_duration_seconds" in body
        assert "app_http_active_requests" in body
        assert "app_root_requests_total" in body
        assert "app_system_info_duration_seconds" in body
        assert "app_uptime_seconds" in body

    def test_metrics_contains_root_endpoint_labels(self, client):
        client.get("/")

        response = client.get("/metrics")
        assert (
            'app_http_requests_total{endpoint="/",method="GET",status_code="200"}'
            in response.text
        )


class TestErrorHandling:
    """Tests for error handling."""

    def test_nonexistent_endpoint(self, client):
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_error_response_is_html(self, client):
        response = client.get("/nonexistent")
        assert response.status_code == 404


class TestMultipleRequests:
    """Tests for multiple sequential requests."""

    def test_uptime_increases(self, client):
        response1 = client.get("/health")
        uptime1 = response1.json()["uptime_seconds"]

        response2 = client.get("/health")
        uptime2 = response2.json()["uptime_seconds"]

        assert uptime2 >= uptime1

    def test_root_and_health_consistency(self, client):
        root_response = client.get("/")
        health_response = client.get("/health")

        root_uptime = root_response.json()["runtime"]["uptime_seconds"]
        health_uptime = health_response.json()["uptime_seconds"]

        assert abs(root_uptime - health_uptime) <= 1


class TestLogging:
    """Tests for JSON logging formatter."""

    def test_json_formatter_outputs_required_fields(self):
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="hello",
            args=(),
            exc_info=None,
        )
        record.method = "GET"
        record.path = "/"
        record.status_code = 200
        record.client_ip = "127.0.0.1"

        formatted = JSONFormatter().format(record)
        payload = json.loads(formatted)

        assert payload["level"] == "INFO"
        assert payload["logger"] == "test.logger"
        assert payload["message"] == "hello"
        assert payload["method"] == "GET"
        assert payload["path"] == "/"
        assert payload["status_code"] == 200
        assert payload["client_ip"] == "127.0.0.1"
        assert "timestamp" in payload
