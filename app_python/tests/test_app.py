"""
Unit tests for DevOps Info Service - Flask application

Tests cover:
- Main endpoint (/) responses
- Health check endpoint (/health) responses
- Error handling (404)
- Response structure validation
- Data type validation
"""

from datetime import datetime

import pytest
from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestMainEndpoint:
    """Tests for the main / endpoint."""

    def test_main_endpoint_returns_200(self, client):
        """Test that main endpoint returns HTTP 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_main_endpoint_returns_json(self, client):
        """Test that main endpoint returns JSON content type."""
        response = client.get("/")
        assert response.content_type == "application/json"

    def test_main_endpoint_response_structure(self, client):
        """Test that main endpoint response has correct structure."""
        response = client.get("/")
        data = response.get_json()

        # Verify all top-level keys exist
        assert "service" in data
        assert "system" in data
        assert "runtime" in data
        assert "request" in data
        assert "endpoints" in data

    def test_main_endpoint_service_info(self, client):
        """Test that service information is correct."""
        response = client.get("/")
        data = response.get_json()

        service = data["service"]
        assert service["name"] == "devops-info-service"
        assert service["version"] == "1.0.0"
        assert service["description"] == "DevOps course info service"
        assert service["framework"] == "Flask"

    def test_main_endpoint_system_info(self, client):
        """Test that system information is present and valid."""
        response = client.get("/")
        data = response.get_json()

        system = data["system"]
        assert "hostname" in system
        assert isinstance(system["hostname"], str)
        assert len(system["hostname"]) > 0

        assert "platform" in system
        assert isinstance(system["platform"], str)

        assert "architecture" in system
        assert isinstance(system["architecture"], str)

        assert "cpu_count" in system
        assert isinstance(system["cpu_count"], int)
        assert system["cpu_count"] > 0

        assert "python_version" in system
        assert isinstance(system["python_version"], str)

    def test_main_endpoint_runtime_info(self, client):
        """Test that runtime information is present and valid."""
        response = client.get("/")
        data = response.get_json()

        runtime = data["runtime"]
        assert "uptime_seconds" in runtime
        assert isinstance(runtime["uptime_seconds"], int)
        assert runtime["uptime_seconds"] >= 0

        assert "uptime_human" in runtime
        assert isinstance(runtime["uptime_human"], str)

        assert "current_time" in runtime
        # Verify ISO format timestamp
        datetime.fromisoformat(runtime["current_time"].replace("Z", "+00:00"))

        assert "timezone" in runtime
        assert runtime["timezone"] == "UTC"

    def test_main_endpoint_request_info(self, client):
        """Test that request information is captured."""
        response = client.get("/")
        data = response.get_json()

        request_info = data["request"]
        assert "client_ip" in request_info
        assert "user_agent" in request_info
        assert request_info["method"] == "GET"
        assert request_info["path"] == "/"

    def test_main_endpoint_endpoints_list(self, client):
        """Test that endpoints list is correct."""
        response = client.get("/")
        data = response.get_json()

        endpoints = data["endpoints"]
        assert isinstance(endpoints, list)
        assert len(endpoints) >= 2

        # Check for / endpoint
        root_endpoint = next((e for e in endpoints if e["path"] == "/"), None)
        assert root_endpoint is not None
        assert root_endpoint["method"] == "GET"

        # Check for /health endpoint
        health_endpoint = next((e for e in endpoints if e["path"] == "/health"), None)
        assert health_endpoint is not None
        assert health_endpoint["method"] == "GET"


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_endpoint_returns_200(self, client):
        """Test that health endpoint returns HTTP 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_returns_json(self, client):
        """Test that health endpoint returns JSON content type."""
        response = client.get("/health")
        assert response.content_type == "application/json"

    def test_health_endpoint_response_structure(self, client):
        """Test that health endpoint response has correct structure."""
        response = client.get("/health")
        data = response.get_json()

        assert "status" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data

    def test_health_endpoint_status(self, client):
        """Test that health endpoint shows healthy status."""
        response = client.get("/health")
        data = response.get_json()

        assert data["status"] == "healthy"

    def test_health_endpoint_timestamp(self, client):
        """Test that health endpoint timestamp is valid ISO format."""
        response = client.get("/health")
        data = response.get_json()

        # Verify ISO format timestamp
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

    def test_health_endpoint_uptime(self, client):
        """Test that health endpoint uptime is valid."""
        response = client.get("/health")
        data = response.get_json()

        assert isinstance(data["uptime_seconds"], int)
        assert data["uptime_seconds"] >= 0


class TestMetricsEndpoint:
    """Tests for the /metrics endpoint and instrumentation."""

    def test_metrics_endpoint_returns_200(self, client):
        """Test that metrics endpoint returns HTTP 200."""
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_endpoint_returns_prometheus_format(self, client):
        """Test that metrics endpoint uses Prometheus text format."""
        response = client.get("/metrics")
        assert response.content_type.startswith("text/plain")
        body = response.get_data(as_text=True)
        assert "# HELP http_requests_total" in body
        assert "# TYPE http_request_duration_seconds histogram" in body
        assert "# TYPE http_requests_in_progress gauge" in body

    def test_metrics_count_application_requests(self, client):
        """Test that application requests are exported in metrics."""
        client.get("/")
        client.get("/health")

        response = client.get("/metrics")
        body = response.get_data(as_text=True)

        assert 'http_requests_total{endpoint="/",method="GET",status_code="200"}' in body
        assert 'http_requests_total{endpoint="/health",method="GET",status_code="200"}' in body
        assert 'devops_info_endpoint_calls_total{endpoint="/"}' in body
        assert 'devops_info_endpoint_calls_total{endpoint="/health"}' in body


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_error_handler(self, client):
        """Test that 404 errors return JSON error response."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

        data = response.get_json()
        assert "error" in data
        assert data["error"] == "Not Found"
        assert "message" in data


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_post_to_main_endpoint(self, client):
        """Test that POST to main endpoint returns 405 Method Not Allowed."""
        response = client.post("/")
        # Flask routes only accept GET by default unless specified
        assert response.status_code == 405

    def test_main_endpoint_with_query_params(self, client):
        """Test main endpoint with query parameters."""
        response = client.get("/?test=param&foo=bar")
        assert response.status_code == 200
        data = response.get_json()
        assert "service" in data

    def test_multiple_requests_increasing_uptime(self, client):
        """Test that uptime increases between requests."""
        import time

        response1 = client.get("/")
        data1 = response1.get_json()
        uptime1 = data1["runtime"]["uptime_seconds"]

        time.sleep(1)

        response2 = client.get("/")
        data2 = response2.get_json()
        uptime2 = data2["runtime"]["uptime_seconds"]

        # Second request should have higher uptime
        assert uptime2 >= uptime1
