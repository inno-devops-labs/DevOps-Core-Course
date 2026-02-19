"""Unit tests for API endpoints."""
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


class TestRootEndpoint:
    """Tests for GET / endpoint."""

    def test_status_code(self):
        """Verify root endpoint returns 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_response_structure(self):
        """Verify JSON contains required top-level fields."""
        response = client.get("/")
        data = response.json()
        assert "service" in data
        assert "system" in data
        assert "runtime" in data
        assert "request" in data
        assert "endpoints" in data

    def test_service_fields(self):
        """Verify service object has required fields and types."""
        response = client.get("/")
        service = response.json()["service"]
        assert "name" in service
        assert "version" in service
        assert "description" in service
        assert "framework" in service
        assert isinstance(service["name"], str)
        assert isinstance(service["framework"], str)

    def test_system_fields(self):
        """Verify system object has required fields."""
        response = client.get("/")
        system = response.json()["system"]
        assert "hostname" in system
        assert "platform" in system
        assert "architecture" in system
        assert "python_version" in system
        assert isinstance(system["hostname"], str)

    def test_runtime_fields(self):
        """Verify runtime object has required fields."""
        response = client.get("/")
        runtime = response.json()["runtime"]
        assert "uptime_seconds" in runtime
        assert "uptime_human" in runtime
        assert isinstance(runtime["uptime_seconds"], int)
        assert runtime["uptime_seconds"] >= 0

    def test_request_fields(self):
        """Verify request info is present."""
        response = client.get("/")
        request_info = response.json()["request"]
        assert "client_ip" in request_info
        assert "method" in request_info
        assert "path" in request_info
        assert request_info["method"] == "GET"
        assert request_info["path"] == "/"

    def test_endpoints_is_list(self):
        """Verify endpoints is a non-empty list."""
        response = client.get("/")
        endpoints = response.json()["endpoints"]
        assert isinstance(endpoints, list)
        assert len(endpoints) >= 2
        assert any(ep["path"] == "/" for ep in endpoints)
        assert any(ep["path"] == "/health" for ep in endpoints)


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_status_code(self):
        """Verify health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_status_healthy(self):
        """Verify health check returns healthy status."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_required_fields(self):
        """Verify health response has required fields."""
        response = client.get("/health")
        data = response.json()
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], int)
        assert data["uptime_seconds"] >= 0


class TestErrorCases:
    """Tests for error handling."""

    def test_404_nonexistent_endpoint(self):
        """Verify 404 for non-existent endpoint."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_404_response_structure(self):
        """Verify 404 response has expected structure."""
        response = client.get("/nonexistent")
        data = response.json()
        assert "error" in data
        assert "message" in data
        assert "Not Found" in data["error"] or "Not Found" in data["message"]
