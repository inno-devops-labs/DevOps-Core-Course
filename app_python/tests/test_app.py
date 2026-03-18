"""
Unit tests for DevOps Info Service.
Tests all endpoints, response structure, and error handling.
"""
import pytest
from fastapi.testclient import TestClient

from app import app, START_TIME, SERVICE_INFO, ENDPOINTS, get_uptime, get_system_info


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET / — Main endpoint tests
# ---------------------------------------------------------------------------

class TestMainEndpoint:
    """Tests for the main endpoint GET /."""

    def test_status_code(self, client):
        """GET / should return 200 OK."""
        response = client.get("/")
        assert response.status_code == 200

    def test_response_is_json(self, client):
        """GET / should return valid JSON."""
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, dict)

    def test_top_level_keys(self, client):
        """Response must contain all required top-level keys."""
        data = client.get("/").json()
        required_keys = {"service", "system", "runtime", "request", "endpoints"}
        assert required_keys.issubset(data.keys())

    # -- service section ---------------------------------------------------

    def test_service_fields(self, client):
        """Service section must contain name, version, description, framework."""
        service = client.get("/").json()["service"]
        for field in ("name", "version", "description", "framework"):
            assert field in service
            assert isinstance(service[field], str)
            assert len(service[field]) > 0

    def test_service_values(self, client):
        """Service section values must match constants."""
        service = client.get("/").json()["service"]
        assert service["name"] == SERVICE_INFO["name"]
        assert service["version"] == SERVICE_INFO["version"]
        assert service["framework"] == "FastAPI"

    # -- system section ----------------------------------------------------

    def test_system_fields(self, client):
        """System section must contain all required fields."""
        system = client.get("/").json()["system"]
        required = {
            "hostname", "platform", "platform_version",
            "architecture", "cpu_count", "python_version",
        }
        assert required.issubset(system.keys())

    def test_system_types(self, client):
        """System field types must be correct."""
        system = client.get("/").json()["system"]
        assert isinstance(system["hostname"], str)
        assert isinstance(system["platform"], str)
        assert isinstance(system["cpu_count"], int)
        assert system["cpu_count"] > 0

    # -- runtime section ---------------------------------------------------

    def test_runtime_fields(self, client):
        """Runtime section must contain uptime and time info."""
        runtime = client.get("/").json()["runtime"]
        for field in ("uptime_seconds", "uptime_human", "current_time", "timezone"):
            assert field in runtime

    def test_runtime_uptime_nonnegative(self, client):
        """Uptime must be a non-negative integer."""
        uptime = client.get("/").json()["runtime"]["uptime_seconds"]
        assert isinstance(uptime, int)
        assert uptime >= 0

    def test_runtime_timezone_utc(self, client):
        """Timezone must be UTC."""
        assert client.get("/").json()["runtime"]["timezone"] == "UTC"

    # -- request section ---------------------------------------------------

    def test_request_fields(self, client):
        """Request section must contain ip, user-agent, method, path."""
        req = client.get("/").json()["request"]
        for field in ("client_ip", "user_agent", "method", "path"):
            assert field in req

    def test_request_method_is_get(self, client):
        """Request method must be GET."""
        assert client.get("/").json()["request"]["method"] == "GET"

    def test_request_path_is_root(self, client):
        """Request path must be /."""
        assert client.get("/").json()["request"]["path"] == "/"

    # -- endpoints section -------------------------------------------------

    def test_endpoints_list(self, client):
        """Endpoints must be a non-empty list."""
        eps = client.get("/").json()["endpoints"]
        assert isinstance(eps, list)
        assert len(eps) >= 2

    def test_endpoints_structure(self, client):
        """Each endpoint entry must have path, method, description."""
        for ep in client.get("/").json()["endpoints"]:
            assert "path" in ep
            assert "method" in ep
            assert "description" in ep


# ---------------------------------------------------------------------------
# GET /health — Health check tests
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    """Tests for the health check endpoint GET /health."""

    def test_status_code(self, client):
        """GET /health should return 200 OK."""
        assert client.get("/health").status_code == 200

    def test_healthy_status(self, client):
        """Health status must be 'healthy'."""
        assert client.get("/health").json()["status"] == "healthy"

    def test_required_fields(self, client):
        """Health response must contain status, timestamp, uptime_seconds."""
        data = client.get("/health").json()
        for field in ("status", "timestamp", "uptime_seconds"):
            assert field in data

    def test_uptime_nonnegative(self, client):
        """Uptime seconds must be non-negative."""
        uptime = client.get("/health").json()["uptime_seconds"]
        assert isinstance(uptime, int)
        assert uptime >= 0

    def test_timestamp_format(self, client):
        """Timestamp must be a valid ISO 8601 string."""
        from datetime import datetime
        ts = client.get("/health").json()["timestamp"]
        # Should not raise
        datetime.fromisoformat(ts)


class TestMetricsEndpoint:
    """Tests for the Prometheus metrics endpoint GET /metrics."""

    def test_status_code(self, client):
        """GET /metrics should return 200 OK."""
        assert client.get("/metrics").status_code == 200

    def test_response_is_prometheus_text(self, client):
        """GET /metrics should return Prometheus text exposition format."""
        response = client.get("/metrics")
        assert response.headers["content-type"].startswith("text/plain")

    def test_expected_metric_series_exist(self, client):
        """Metrics output must include HTTP and app-specific metrics."""
        client.get("/")
        client.get("/health")
        client.get("/missing")

        metrics_text = client.get("/metrics").text
        assert "http_requests_total" in metrics_text
        assert "http_request_duration_seconds" in metrics_text
        assert "http_requests_in_progress" in metrics_text
        assert "devops_info_endpoint_calls_total" in metrics_text
        assert "devops_info_system_info_collection_seconds" in metrics_text

    def test_metrics_include_expected_labels(self, client):
        """Metrics should expose normalized labels for successful and 404 requests."""
        client.get("/")
        client.get("/health")
        client.get("/missing")

        metrics_text = client.get("/metrics").text
        assert 'http_requests_total{method="GET",endpoint="/",status_code="200"}' in metrics_text
        assert 'http_requests_total{method="GET",endpoint="/health",status_code="200"}' in metrics_text
        assert 'http_requests_total{method="GET",endpoint="/unknown",status_code="404"}' in metrics_text
        assert 'devops_info_endpoint_calls_total{endpoint="/"}' in metrics_text
        assert 'devops_info_endpoint_calls_total{endpoint="/health"}' in metrics_text


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """Tests for error handling (404)."""

    def test_404_status_code(self, client):
        """Non-existent route should return 404."""
        assert client.get("/nonexistent").status_code == 404

    def test_404_json_body(self, client):
        """404 response must contain error and message fields."""
        data = client.get("/nonexistent").json()
        assert "error" in data
        assert "message" in data

    def test_404_includes_path(self, client):
        """404 response must include the requested path."""
        data = client.get("/some/bad/path").json()
        assert data["path"] == "/some/bad/path"


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------

class TestHelpers:
    """Tests for helper / utility functions."""

    def test_get_uptime_structure(self):
        """get_uptime must return dict with seconds and human keys."""
        result = get_uptime()
        assert "seconds" in result
        assert "human" in result
        assert isinstance(result["seconds"], int)
        assert isinstance(result["human"], str)

    def test_get_system_info_keys(self):
        """get_system_info must return all expected keys."""
        info = get_system_info()
        expected = {
            "hostname", "platform", "platform_version",
            "architecture", "cpu_count", "python_version",
        }
        assert expected.issubset(info.keys())

    def test_start_time_exists(self):
        """START_TIME must be set."""
        assert START_TIME is not None
