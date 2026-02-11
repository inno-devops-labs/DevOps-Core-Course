import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestRootEndpoint:
    """Tests for the GET / endpoint"""

    def test_root_returns_200(self):
        """Test that root endpoint returns 200 OK"""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_json(self):
        """Test that root endpoint returns JSON"""
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"

    def test_root_has_service_section(self):
        """Test that response contains service information"""
        response = client.get("/")
        data = response.json()
        assert "service" in data
        assert "name" in data["service"]
        assert "version" in data["service"]
        assert "description" in data["service"]
        assert "framework" in data["service"]

    def test_root_has_system_section(self):
        """Test that response contains system information"""
        response = client.get("/")
        data = response.json()
        assert "system" in data
        assert "hostname" in data["system"]
        assert "platform" in data["system"]
        assert "architecture" in data["system"]
        assert "cpu_count" in data["system"]
        assert "python_version" in data["system"]

    def test_root_has_runtime_section(self):
        """Test that response contains runtime information"""
        response = client.get("/")
        data = response.json()
        assert "runtime" in data
        assert "uptime_seconds" in data["runtime"]
        assert "uptime_human" in data["runtime"]
        assert "current_time" in data["runtime"]
        assert "timezone" in data["runtime"]

    def test_root_has_request_section(self):
        """Test that response contains request information"""
        response = client.get("/")
        data = response.json()
        assert "request" in data
        assert "client_ip" in data["request"]
        assert "user_agent" in data["request"]
        assert "method" in data["request"]
        assert "path" in data["request"]

    def test_root_has_endpoints_section(self):
        """Test that response contains endpoints list"""
        response = client.get("/")
        data = response.json()
        assert "endpoints" in data
        assert isinstance(data["endpoints"], list)
        assert len(data["endpoints"]) > 0

    def test_root_framework_is_fastapi(self):
        """Test that framework is correctly identified as FastAPI"""
        response = client.get("/")
        data = response.json()
        assert data["service"]["framework"] == "FastAPI"

    def test_root_uptime_is_numeric(self):
        """Test that uptime_seconds is a number"""
        response = client.get("/")
        data = response.json()
        assert isinstance(data["runtime"]["uptime_seconds"], int)
        assert data["runtime"]["uptime_seconds"] >= 0

    def test_root_cpu_count_is_positive(self):
        """Test that CPU count is a positive integer"""
        response = client.get("/")
        data = response.json()
        assert isinstance(data["system"]["cpu_count"], int)
        assert data["system"]["cpu_count"] > 0

    def test_root_request_method_is_get(self):
        """Test that request method is captured correctly"""
        response = client.get("/")
        data = response.json()
        assert data["request"]["method"] == "GET"

    def test_root_request_path_is_root(self):
        """Test that request path is captured correctly"""
        response = client.get("/")
        data = response.json()
        assert data["request"]["path"] == "/"


class TestHealthEndpoint:
    """Tests for the GET /health endpoint"""

    def test_health_returns_200(self):
        """Test that health endpoint returns 200 OK"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_json(self):
        """Test that health endpoint returns JSON"""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"

    def test_health_has_status_field(self):
        """Test that health response has status field"""
        response = client.get("/health")
        data = response.json()
        assert "status" in data

    def test_health_status_is_healthy(self):
        """Test that status is 'healthy'"""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_has_timestamp(self):
        """Test that health response has timestamp"""
        response = client.get("/health")
        data = response.json()
        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)

    def test_health_has_uptime_seconds(self):
        """Test that health response has uptime_seconds"""
        response = client.get("/health")
        data = response.json()
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], int)
        assert data["uptime_seconds"] >= 0

    def test_health_timestamp_format(self):
        """Test that timestamp is in ISO 8601 format"""
        response = client.get("/health")
        data = response.json()
        # Should be ISO 8601 format (contains T and timezone info)
        assert "T" in data["timestamp"]
        assert "+" in data["timestamp"] or data["timestamp"].endswith("Z")


class TestNotFoundEndpoint:
    """Tests for non-existent endpoints"""

    def test_nonexistent_endpoint_returns_404(self):
        """Test that non-existent endpoint returns 404"""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_invalid_path_returns_404(self):
        """Test that invalid path returns 404"""
        response = client.get("/api/invalid")
        assert response.status_code == 404


class TestCustomUserAgent:
    """Tests for custom user agent handling"""

    def test_custom_user_agent_is_captured(self):
        """Test that custom user agent is captured in response"""
        custom_ua = "Mozilla/5.0 TestBot"
        response = client.get("/", headers={"User-Agent": custom_ua})
        data = response.json()
        assert data["request"]["user_agent"] == custom_ua

    def test_missing_user_agent(self):
        """Test behavior when user agent is missing"""
        response = client.get("/", headers={"User-Agent": ""})
        data = response.json()
        # Should handle empty user agent gracefully
        assert "user_agent" in data["request"]


class TestTimezone:
    """Tests for timezone handling"""

    def test_timezone_is_utc(self):
        """Test that timezone is set to UTC"""
        response = client.get("/")
        data = response.json()
        assert data["runtime"]["timezone"] == "UTC"

    def test_health_timestamp_is_utc(self):
        """Test that health check timestamp is in UTC"""
        response = client.get("/health")
        data = response.json()
        # ISO 8601 UTC timestamps end with +00:00 or Z
        assert (
            data["timestamp"].endswith("+00:00")
            or data["timestamp"].endswith("Z")
            or "+00:00" in data["timestamp"]
        )
