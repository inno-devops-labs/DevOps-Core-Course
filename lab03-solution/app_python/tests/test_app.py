"""
Test suite for DevOps Info Service

This module contains comprehensive unit tests for all endpoints of the DevOps Info Service.
Tests use pytest and FastAPI's TestClient to verify endpoint behavior.
"""

import pytest
from fastapi.testclient import TestClient
from app import app


@pytest.fixture
def client():
    """Provide a test client for the FastAPI application."""
    return TestClient(app)


class TestRootEndpoint:
    """Test cases for the root (/) endpoint."""

    def test_root_endpoint_returns_200(self, client):
        """Test that GET / returns HTTP 200 status code."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_endpoint_returns_json(self, client):
        """Test that GET / returns JSON response."""
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"

    def test_root_response_has_service_info(self, client):
        """Test that root endpoint returns service information."""
        response = client.get("/")
        data = response.json()

        assert "service" in data
        assert "name" in data["service"]
        assert "version" in data["service"]
        assert "description" in data["service"]
        assert "framework" in data["service"]

    def test_root_response_service_fields_are_strings(self, client):
        """Test that service fields are strings."""
        response = client.get("/")
        data = response.json()

        assert isinstance(data["service"]["name"], str)
        assert isinstance(data["service"]["version"], str)
        assert isinstance(data["service"]["framework"], str)

    def test_root_response_has_system_info(self, client):
        """Test that root endpoint returns system information."""
        response = client.get("/")
        data = response.json()

        assert "system" in data
        assert "hostname" in data["system"]
        assert "platform" in data["system"]
        assert "platform_version" in data["system"]
        assert "architecture" in data["system"]
        assert "cpu_count" in data["system"]
        assert "python_version" in data["system"]

    def test_root_response_system_fields_types(self, client):
        """Test that system fields have correct types."""
        response = client.get("/")
        data = response.json()

        assert isinstance(data["system"]["hostname"], str)
        assert isinstance(data["system"]["platform"], str)
        assert isinstance(data["system"]["cpu_count"], int)
        assert data["system"]["cpu_count"] > 0

    def test_root_response_has_runtime_info(self, client):
        """Test that root endpoint returns runtime information."""
        response = client.get("/")
        data = response.json()

        assert "runtime" in data
        assert "uptime_seconds" in data["runtime"]
        assert "uptime_human" in data["runtime"]
        assert "current_time" in data["runtime"]
        assert "timezone" in data["runtime"]

    def test_root_response_runtime_uptime_is_non_negative(self, client):
        """Test that uptime is non-negative."""
        response = client.get("/")
        data = response.json()

        assert data["runtime"]["uptime_seconds"] >= 0
        assert isinstance(data["runtime"]["uptime_seconds"], int)

    def test_root_response_runtime_timezone_is_utc(self, client):
        """Test that timezone is UTC."""
        response = client.get("/")
        data = response.json()

        assert data["runtime"]["timezone"] == "UTC"

    def test_root_response_has_request_info(self, client):
        """Test that root endpoint returns request information."""
        response = client.get("/")
        data = response.json()

        assert "request" in data
        assert "client_ip" in data["request"]
        assert "method" in data["request"]
        assert "path" in data["request"]
        assert "user_agent" in data["request"]

    def test_root_response_request_info_correctness(self, client):
        """Test that request information is correct."""
        response = client.get("/")
        data = response.json()

        assert data["request"]["method"] == "GET"
        assert data["request"]["path"] == "/"

    def test_root_response_has_endpoints_list(self, client):
        """Test that root endpoint returns list of available endpoints."""
        response = client.get("/")
        data = response.json()

        assert "endpoints" in data
        assert isinstance(data["endpoints"], list)
        assert len(data["endpoints"]) > 0

    def test_root_response_endpoints_have_required_fields(self, client):
        """Test that each endpoint in list has required fields."""
        response = client.get("/")
        data = response.json()

        for endpoint in data["endpoints"]:
            assert "path" in endpoint
            assert "method" in endpoint
            assert "description" in endpoint
            assert isinstance(endpoint["path"], str)
            assert isinstance(endpoint["method"], str)
            assert isinstance(endpoint["description"], str)

    def test_root_response_includes_root_endpoint(self, client):
        """Test that endpoints list includes the root endpoint."""
        response = client.get("/")
        data = response.json()

        paths = [ep["path"] for ep in data["endpoints"]]
        assert "/" in paths

    def test_root_response_includes_health_endpoint(self, client):
        """Test that endpoints list includes the health endpoint."""
        response = client.get("/")
        data = response.json()

        paths = [ep["path"] for ep in data["endpoints"]]
        assert "/health" in paths

    def test_root_multiple_requests_increase_uptime(self, client):
        """Test that multiple requests show increasing uptime."""
        import time

        response1 = client.get("/")
        time.sleep(0.1)  # Small delay
        response2 = client.get("/")

        uptime1 = response1.json()["runtime"]["uptime_seconds"]
        uptime2 = response2.json()["runtime"]["uptime_seconds"]

        assert uptime2 >= uptime1


class TestHealthEndpoint:
    """Test cases for the health check (/health) endpoint."""

    def test_health_endpoint_returns_200(self, client):
        """Test that GET /health returns HTTP 200 status code."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_returns_json(self, client):
        """Test that GET /health returns JSON response."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"

    def test_health_response_has_status_field(self, client):
        """Test that health endpoint returns status field."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_response_has_timestamp(self, client):
        """Test that health endpoint returns timestamp."""
        response = client.get("/health")
        data = response.json()

        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)
        assert data["timestamp"].endswith("Z")  # ISO format with Z suffix

    def test_health_response_has_uptime(self, client):
        """Test that health endpoint returns uptime."""
        response = client.get("/health")
        data = response.json()

        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], int)
        assert data["uptime_seconds"] >= 0

    def test_health_response_is_healthy(self, client):
        """Test that health status is 'healthy'."""
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"

    def test_health_multiple_requests_successful(self, client):
        """Test that multiple health checks succeed."""
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"


class TestErrorHandling:
    """Test cases for error handling."""

    def test_nonexistent_endpoint_returns_404(self, client):
        """Test that accessing non-existent endpoint returns 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_404_response_is_json(self, client):
        """Test that 404 error response is JSON."""
        response = client.get("/nonexistent")
        assert response.headers["content-type"] == "application/json"

    def test_404_response_has_error_info(self, client):
        """Test that 404 response contains error information."""
        response = client.get("/nonexistent")
        data = response.json()

        assert "error" in data
        assert "message" in data
        assert "path" in data

    def test_invalid_http_method(self, client):
        """Test that invalid HTTP method on valid endpoint returns error."""
        response = client.post("/")
        # POST is not allowed on root endpoint
        assert response.status_code != 200


class TestTypeValidation:
    """Test cases for response type validation."""

    def test_root_response_complete_structure(self, client):
        """Test that root response has all expected top-level keys."""
        response = client.get("/")
        data = response.json()

        expected_keys = {"service", "system", "runtime", "request", "endpoints"}
        assert set(data.keys()) == expected_keys

    def test_json_serializable(self, client):
        """Test that responses are properly serializable to JSON."""
        response = client.get("/")
        data = response.json()

        # If we can convert to JSON string and back, it's valid
        import json

        json_str = json.dumps(data)
        parsed = json.loads(json_str)

        assert parsed == data

    def test_health_response_minimal_structure(self, client):
        """Test that health response has minimal required structure."""
        response = client.get("/health")
        data = response.json()

        expected_keys = {"status", "timestamp", "uptime_seconds"}
        assert set(data.keys()) == expected_keys


class TestConcurrency:
    """Test cases for concurrent request handling."""

    def test_multiple_root_requests(self, client):
        """Test that multiple concurrent-like requests to root work."""
        for _ in range(10):
            response = client.get("/")
            assert response.status_code == 200

    def test_multiple_health_requests(self, client):
        """Test that multiple concurrent-like requests to health work."""
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200

    def test_interleaved_requests(self, client):
        """Test that interleaved requests to different endpoints work."""
        for _ in range(5):
            response1 = client.get("/")
            assert response1.status_code == 200

            response2 = client.get("/health")
            assert response2.status_code == 200
