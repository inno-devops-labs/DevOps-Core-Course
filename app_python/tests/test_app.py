"""
Unit tests for the DevOps Info Service FastAPI application.
Tests both successful responses and error cases for all endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


class TestIndexEndpoint:
    """Test cases for the main index endpoint (GET /)."""

    def test_index_returns_200_status_code(self, client):
        """Test that the index endpoint returns a successful status code."""
        response = client.get("/")
        assert response.status_code == 200

    def test_index_returns_json_content_type(self, client):
        """Test that the index endpoint returns JSON content."""
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"

    def test_index_response_structure(self, client):
        """Test that the index response has the expected structure and fields."""
        response = client.get("/")
        data = response.json()

        # Check top-level structure
        assert "service" in data
        assert "system" in data
        assert "runtime" in data
        assert "request" in data
        assert "endpoints" in data

    def test_index_service_info(self, client):
        """Test that service information is correct."""
        response = client.get("/")
        data = response.json()

        service = data["service"]
        assert service["name"] == "devops-info-service"
        assert service["version"] == "1.0.0"
        assert service["description"] == "DevOps course info service"
        assert service["framework"] == "FastAPI"

    def test_index_system_info(self, client):
        """Test that system information fields are present."""
        response = client.get("/")
        data = response.json()

        system = data["system"]
        required_fields = ["hostname", "platform", "platform_version",
                          "architecture", "cpu_count", "python_version"]

        for field in required_fields:
            assert field in system
            assert system[field] is not None

    def test_index_runtime_info(self, client):
        """Test that runtime information is present and valid."""
        response = client.get("/")
        data = response.json()

        runtime = data["runtime"]
        required_fields = ["uptime_seconds", "uptime_human",
                          "current_time", "timezone"]

        for field in required_fields:
            assert field in runtime

        # Uptime should be non-negative
        assert runtime["uptime_seconds"] >= 0
        assert runtime["timezone"] == "UTC"

    def test_index_request_info(self, client):
        """Test that request information is captured."""
        response = client.get("/")
        data = response.json()

        request_info = data["request"]
        required_fields = ["client_ip", "user_agent", "method", "path"]

        for field in required_fields:
            assert field in request_info

        assert request_info["method"] == "GET"
        assert request_info["path"] == "/"

    def test_index_endpoints_list(self, client):
        """Test that endpoints list is correct."""
        response = client.get("/")
        data = response.json()

        endpoints = data["endpoints"]
        assert isinstance(endpoints, list)
        assert len(endpoints) == 3

        # Check that expected endpoints are listed
        endpoint_paths = [ep["path"] for ep in endpoints]
        assert "/" in endpoint_paths
        assert "/health" in endpoint_paths
        assert "/visits" in endpoint_paths

        # Verify endpoint structure
        for endpoint in endpoints:
            assert "path" in endpoint
            assert "method" in endpoint
            assert "description" in endpoint


class TestVisitsEndpoint:
    """Tests for GET /visits and visit counter persistence behavior."""

    def test_visits_starts_at_zero(self, client):
        response = client.get("/visits")
        assert response.status_code == 200
        assert response.json()["visits"] == 0

    def test_root_increments_visits(self, client):
        client.get("/")
        client.get("/")
        response = client.get("/visits")
        assert response.status_code == 200
        assert response.json()["visits"] == 2

    def test_visits_does_not_increment_counter(self, client):
        client.get("/visits")
        client.get("/visits")
        response = client.get("/visits")
        assert response.json()["visits"] == 0


class TestHealthEndpoint:
    """Test cases for the health check endpoint (GET /health)."""

    def test_health_returns_200_status_code(self, client):
        """Test that the health endpoint returns a successful status code."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_json_content_type(self, client):
        """Test that the health endpoint returns JSON content."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"

    def test_health_response_structure(self, client):
        """Test that the health response has the expected structure."""
        response = client.get("/health")
        data = response.json()

        required_fields = ["status", "timestamp", "uptime_seconds"]
        for field in required_fields:
            assert field in data

    def test_health_status_is_healthy(self, client):
        """Test that the health status is 'healthy'."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_timestamp_format(self, client):
        """Test that the timestamp is in ISO format."""
        response = client.get("/health")
        data = response.json()

        # Should be able to parse as ISO format (basic check)
        timestamp = data["timestamp"]
        assert "T" in timestamp  # ISO format has 'T' separator
        assert "+" in timestamp or "Z" in timestamp  # Has timezone

    def test_health_uptime_is_valid(self, client):
        """Test that uptime_seconds is a non-negative integer."""
        response = client.get("/health")
        data = response.json()

        uptime = data["uptime_seconds"]
        assert isinstance(uptime, int)
        assert uptime >= 0


class TestErrorHandling:
    """Test cases for error handling and edge cases."""

    def test_404_not_found_returns_json_error(self, client):
        """Test that 404 errors return proper JSON error response."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "message" in data
        assert data["error"] == "Not Found"
        assert data["message"] == "Endpoint does not exist"

    def test_405_method_not_allowed(self, client):
        """Test that unsupported methods return proper error."""
        response = client.post("/")
        assert response.status_code == 405

        data = response.json()
        assert "error" in data
        assert data["error"] == "HTTP Error"

    def test_health_endpoint_does_not_support_post(self, client):
        """Test that health endpoint properly rejects POST requests."""
        response = client.post("/health")
        assert response.status_code == 405