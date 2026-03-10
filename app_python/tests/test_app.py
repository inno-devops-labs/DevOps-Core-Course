"""Unit tests for DevOps Info Service Flask application."""

import pytest

from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestIndexEndpoint:
    """Tests for GET / endpoint."""

    def test_index_status_code(self, client):
        """GET / should return 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_index_content_type(self, client):
        """GET / should return JSON."""
        response = client.get("/")
        assert response.content_type == "application/json"

    def test_index_has_service_section(self, client):
        """Response should contain service section with required fields."""
        data = client.get("/").get_json()
        assert "service" in data
        assert data["service"]["name"] == "DevOps Info Service"
        assert "version" in data["service"]
        assert "description" in data["service"]

    def test_index_has_system_section(self, client):
        """Response should contain system section with required fields."""
        data = client.get("/").get_json()
        assert "system" in data
        system = data["system"]
        assert "hostname" in system
        assert "platform" in system
        assert "platform_version" in system
        assert "architecture" in system
        assert "cpu_count" in system
        assert isinstance(system["cpu_count"], int)

    def test_index_has_runtime_section(self, client):
        """Response should contain runtime section with required fields."""
        data = client.get("/").get_json()
        assert "runtime" in data
        runtime = data["runtime"]
        assert "python_version" in runtime
        assert "uptime_seconds" in runtime
        assert "current_time" in runtime
        assert runtime["timezone"] == "UTC"
        assert isinstance(runtime["uptime_seconds"], (int, float))

    def test_index_has_request_section(self, client):
        """Response should contain request metadata."""
        data = client.get("/").get_json()
        assert "request" in data
        req = data["request"]
        assert "client_ip" in req
        assert "user_agent" in req
        assert req["method"] == "GET"
        assert req["path"] == "/"

    def test_index_has_endpoints_section(self, client):
        """Response should list available endpoints."""
        data = client.get("/").get_json()
        assert "endpoints" in data
        assert isinstance(data["endpoints"], list)
        assert len(data["endpoints"]) >= 2
        paths = [ep["path"] for ep in data["endpoints"]]
        assert "/" in paths
        assert "/health" in paths

    def test_index_user_agent_forwarded(self, client):
        """Custom User-Agent header should appear in response."""
        response = client.get("/", headers={"User-Agent": "TestAgent/1.0"})
        data = response.get_json()
        assert data["request"]["user_agent"] == "TestAgent/1.0"


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_status_code(self, client):
        """GET /health should return 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_content_type(self, client):
        """GET /health should return JSON."""
        response = client.get("/health")
        assert response.content_type == "application/json"

    def test_health_status_field(self, client):
        """Health response should indicate healthy status."""
        data = client.get("/health").get_json()
        assert data["status"] == "healthy"

    def test_health_has_timestamp(self, client):
        """Health response should include a timestamp."""
        data = client.get("/health").get_json()
        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)
        assert len(data["timestamp"]) > 0

    def test_health_has_uptime(self, client):
        """Health response should include uptime in seconds."""
        data = client.get("/health").get_json()
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["uptime_seconds"] >= 0


class TestErrorHandlers:
    """Tests for error handling."""

    def test_404_for_unknown_route(self, client):
        """Unknown routes should return 404 with JSON error."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data
        assert data["path"] == "/nonexistent"

    def test_404_json_content_type(self, client):
        """404 responses should be JSON."""
        response = client.get("/nonexistent")
        assert response.content_type == "application/json"

    def test_404_different_paths(self, client):
        """404 should reflect the requested path."""
        for path in ["/foo", "/bar/baz", "/api/v1/missing"]:
            response = client.get(path)
            assert response.status_code == 404
            data = response.get_json()
            assert data["path"] == path
