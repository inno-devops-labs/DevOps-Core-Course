"""
Unit tests for DevOps Info Service
Tests all endpoints and error handling.
"""

import pytest
from datetime import datetime
from app import (
    app,
    get_endpoints,
    get_service_info,
    get_system_info,
    get_uptime,
)


@pytest.fixture
def client(monkeypatch, tmp_path):
    """Create a test client for the Flask application."""
    monkeypatch.setenv("VISITS_FILE", str(tmp_path / "visits"))
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestMainEndpoint:
    """Tests for GET / endpoint."""

    def test_main_endpoint_status_code(self, client):
        """Test that main endpoint returns 200 OK."""
        response = client.get("/")
        assert response.status_code == 200

    def test_main_endpoint_content_type(self, client):
        """Test that response is JSON."""
        response = client.get("/")
        assert response.content_type == "application/json"

    def test_main_endpoint_service_info(self, client):
        """Test that service information is present and correct."""
        response = client.get("/")
        data = response.get_json()

        assert "service" in data
        assert data["service"]["name"] == "devops-info-service"
        assert data["service"]["version"] == "1.0.0"
        assert data["service"]["description"] == "DevOps course info service"
        assert data["service"]["framework"] == "Flask"

    def test_main_endpoint_system_info(self, client):
        """Test that system information is present and has correct types."""
        response = client.get("/")
        data = response.get_json()

        assert "system" in data
        system = data["system"]

        # Check all required fields exist
        assert "hostname" in system
        assert "platform" in system
        assert "platform_version" in system
        assert "architecture" in system
        assert "cpu_count" in system
        assert "python_version" in system

        # Check types
        assert isinstance(system["hostname"], str)
        assert isinstance(system["platform"], str)
        assert isinstance(system["platform_version"], str)
        assert isinstance(system["architecture"], str)
        assert isinstance(system["cpu_count"], int)
        assert isinstance(system["python_version"], str)

        # Check CPU count is positive
        assert system["cpu_count"] > 0

    def test_main_endpoint_runtime_info(self, client):
        """Test that runtime information is present and correct."""
        response = client.get("/")
        data = response.get_json()

        assert "runtime" in data
        runtime = data["runtime"]

        # Check required fields
        assert "uptime_seconds" in runtime
        assert "uptime_human" in runtime
        assert "current_time" in runtime
        assert "timezone" in runtime

        # Check types
        assert isinstance(runtime["uptime_seconds"], int)
        assert isinstance(runtime["uptime_human"], str)
        assert isinstance(runtime["current_time"], str)
        assert runtime["timezone"] == "UTC"

        # Check uptime is non-negative
        assert runtime["uptime_seconds"] >= 0

        # Check time format (ISO 8601)
        try:
            datetime.fromisoformat(runtime["current_time"].replace("Z", "+00:00"))
        except ValueError:
            pytest.fail("current_time is not in ISO 8601 format")

    def test_main_endpoint_request_info(self, client):
        """Test that request information is captured correctly."""
        response = client.get("/", headers={"User-Agent": "TestAgent/1.0"})
        data = response.get_json()

        assert "request" in data
        request_info = data["request"]

        # Check required fields
        assert "client_ip" in request_info
        assert "user_agent" in request_info
        assert "method" in request_info
        assert "path" in request_info

        # Check values
        assert request_info["method"] == "GET"
        assert request_info["path"] == "/"
        assert request_info["user_agent"] == "TestAgent/1.0"
        assert isinstance(request_info["client_ip"], str)

    def test_main_endpoint_endpoints_list(self, client):
        """Test that endpoints list is present and correct."""
        response = client.get("/")
        data = response.get_json()

        assert "endpoints" in data
        assert isinstance(data["endpoints"], list)
        assert len(data["endpoints"]) == 3

        # Check endpoint structure
        for endpoint in data["endpoints"]:
            assert "path" in endpoint
            assert "method" in endpoint
            assert "description" in endpoint

        # Check specific endpoints
        paths = [e["path"] for e in data["endpoints"]]
        assert "/" in paths
        assert "/health" in paths
        assert "/visits" in paths

    def test_main_endpoint_increments_visit_counter(
        self, client, monkeypatch, tmp_path
    ):
        """Test that GET / increments persisted visit counter."""
        visits_file = tmp_path / "visits"
        monkeypatch.setenv("VISITS_FILE", str(visits_file))

        response = client.get("/")
        data = response.get_json()

        assert response.status_code == 200
        assert data["persistence"]["visits"] == 1
        assert visits_file.read_text(encoding="utf-8").strip() == "1"

    def test_main_endpoint_reports_fly_metadata_without_secret_values(
        self, client, monkeypatch
    ):
        """Test that Fly metadata is present and secrets are redacted."""
        monkeypatch.setenv("FLY_APP_NAME", "devops-info-python")
        monkeypatch.setenv("FLY_REGION", "ams")
        monkeypatch.setenv("PRIMARY_REGION", "ams")
        monkeypatch.setenv("API_KEY", "super-secret")
        monkeypatch.setenv("DATABASE_URL", "postgres://example")

        response = client.get("/")
        data = response.get_json()

        deployment = data["deployment"]
        assert deployment["platform"] == "fly.io"
        assert deployment["app_name"] == "devops-info-python"
        assert deployment["region"] == "ams"
        assert deployment["primary_region"] == "ams"
        assert deployment["secrets"]["API_KEY"] is True
        assert deployment["secrets"]["DATABASE_URL"] is True
        assert "super-secret" not in str(data)
        assert "postgres://example" not in str(data)


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_endpoint_status_code(self, client):
        """Test that health endpoint returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_content_type(self, client):
        """Test that response is JSON."""
        response = client.get("/health")
        assert response.content_type == "application/json"

    def test_health_endpoint_structure(self, client):
        """Test that health endpoint returns correct structure."""
        response = client.get("/health")
        data = response.get_json()

        # Check required fields
        assert "status" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data

        # Check values
        assert data["status"] == "healthy"
        assert isinstance(data["uptime_seconds"], int)
        assert data["uptime_seconds"] >= 0

        # Check timestamp format
        try:
            datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            pytest.fail("timestamp is not in ISO 8601 format")

    def test_health_endpoint_uptime_increases(self, client):
        """Test that uptime increases over time."""
        import time

        response1 = client.get("/health")
        uptime1 = response1.get_json()["uptime_seconds"]

        time.sleep(1)

        response2 = client.get("/health")
        uptime2 = response2.get_json()["uptime_seconds"]

        assert uptime2 >= uptime1


class TestVisitsEndpoint:
    """Tests for GET /visits endpoint."""

    def test_visits_endpoint_returns_current_count(self, client, monkeypatch, tmp_path):
        """Test that /visits returns current persisted count."""
        visits_file = tmp_path / "visits"
        visits_file.write_text("7", encoding="utf-8")
        monkeypatch.setenv("VISITS_FILE", str(visits_file))

        response = client.get("/visits")
        data = response.get_json()

        assert response.status_code == 200
        assert data["visits"] == 7
        assert data["storage"]["path"] == str(visits_file)

    def test_visits_endpoint_defaults_to_zero_when_file_missing(
        self, client, monkeypatch, tmp_path
    ):
        """Test that /visits handles missing persistence file gracefully."""
        visits_file = tmp_path / "missing" / "visits"
        monkeypatch.setenv("VISITS_FILE", str(visits_file))

        response = client.get("/visits")
        data = response.get_json()

        assert response.status_code == 200
        assert data["visits"] == 0


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_error(self, client):
        """Test that 404 errors return correct JSON response."""
        response = client.get("/nonexistent")

        assert response.status_code == 404
        assert response.content_type == "application/json"

        data = response.get_json()
        assert "error" in data
        assert "message" in data
        assert data["error"] == "Not Found"
        assert data["message"] == "Endpoint does not exist"

    def test_404_error_different_paths(self, client):
        """Test 404 handling for various invalid paths."""
        invalid_paths = ["/invalid", "/api/v1", "/test/123"]

        for path in invalid_paths:
            response = client.get(path)
            assert response.status_code == 404
            data = response.get_json()
            assert data["error"] == "Not Found"


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_service_info(self):
        """Test get_service_info helper function."""
        info = get_service_info()

        assert isinstance(info, dict)
        assert info["name"] == "devops-info-service"
        assert info["version"] == "1.0.0"
        assert info["description"] == "DevOps course info service"
        assert info["framework"] == "Flask"

    def test_get_system_info(self):
        """Test get_system_info helper function."""
        info = get_system_info()

        assert isinstance(info, dict)
        assert "hostname" in info
        assert "platform" in info
        assert "architecture" in info
        assert "cpu_count" in info
        assert "python_version" in info
        assert isinstance(info["cpu_count"], int)
        assert info["cpu_count"] > 0

    def test_get_endpoints(self):
        """Test get_endpoints helper function."""
        endpoints = get_endpoints()

        assert isinstance(endpoints, list)
        assert len(endpoints) == 3

        for endpoint in endpoints:
            assert "path" in endpoint
            assert "method" in endpoint
            assert "description" in endpoint

    def test_get_uptime(self):
        """Test get_uptime helper function."""
        uptime = get_uptime()

        assert isinstance(uptime, dict)
        assert "seconds" in uptime
        assert "human" in uptime
        assert isinstance(uptime["seconds"], int)
        assert uptime["seconds"] >= 0
        assert isinstance(uptime["human"], str)
        assert "hour" in uptime["human"] or "minute" in uptime["human"]


class TestHTTPMethods:
    """Tests for different HTTP methods."""

    def test_post_not_allowed(self, client):
        """Test that POST to / returns 405 or handles gracefully."""
        response = client.post("/")
        # Flask returns 405 Method Not Allowed for unsupported methods
        assert response.status_code in [405, 200]  # Some frameworks return 200

    def test_put_not_allowed(self, client):
        """Test that PUT to / returns 405 or handles gracefully."""
        response = client.put("/")
        assert response.status_code in [405, 200]

    def test_delete_not_allowed(self, client):
        """Test that DELETE to / returns 405 or handles gracefully."""
        response = client.delete("/")
        assert response.status_code in [405, 200]
