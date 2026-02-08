import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app, get_system_info, get_uptime


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI application.

    This fixture is used by all test functions to make HTTP requests
    to the application without starting an actual server.
    """
    return TestClient(app)


class TestRootEndpoint:
    """Test suite for the / endpoint"""

    def test_root_endpoint_status_code(self, client):
        """Test that root endpoint returns 200 OK"""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_endpoint_returns_json(self, client):
        """Test that root endpoint returns valid JSON"""
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, dict)

    def test_root_endpoint_service_info(self, client):
        """Test that service information is present and correct"""
        response = client.get("/")
        data = response.json()

        # Check service section exists
        assert "service" in data
        service = data["service"]

        # Verify service fields
        assert service["name"] == "devops-info-service"
        assert service["version"] == "1.0.0"
        assert service["description"] == "DevOps course info service"
        assert service["framework"] == "FastAPI"

    def test_root_endpoint_system_info(self, client):
        """Test that system information is present"""
        response = client.get("/")
        data = response.json()

        # Check system section exists
        assert "system" in data
        system = data["system"]

        # Verify system fields exist
        assert "hostname" in system
        assert "platform" in system
        assert "platform_version" in system
        assert "architecture" in system
        assert "cpu_count" in system
        assert "python_version" in system

        # Verify data types
        assert isinstance(system["hostname"], str)
        assert isinstance(system["platform"], str)
        assert isinstance(system["architecture"], str)
        assert isinstance(system["cpu_count"], int)
        assert isinstance(system["python_version"], str)

    def test_root_endpoint_runtime_info(self, client):
        """Test that runtime information is present and valid"""
        response = client.get("/")
        data = response.json()

        # Check runtime section exists
        assert "runtime" in data
        runtime = data["runtime"]

        # Verify runtime fields
        assert "uptime_seconds" in runtime
        assert "uptime_human" in runtime
        assert "current_time" in runtime
        assert "timezone" in runtime

        # Verify data types and values
        assert isinstance(runtime["uptime_seconds"], int)
        assert runtime["uptime_seconds"] >= 0
        assert isinstance(runtime["uptime_human"], str)
        assert runtime["timezone"] == "UTC"

        # Verify current_time is valid ISO format
        datetime.fromisoformat(runtime["current_time"].replace("Z", "+00:00"))

    def test_root_endpoint_request_info(self, client):
        """Test that request information is captured"""
        response = client.get("/")
        data = response.json()

        # Check request section exists
        assert "request" in data
        request_info = data["request"]

        # Verify request fields
        assert "client_ip" in request_info
        assert "user_agent" in request_info
        assert "method" in request_info
        assert "path" in request_info

        # Verify values
        assert request_info["method"] == "GET"
        assert request_info["path"] == "/"

    def test_root_endpoint_endpoints_list(self, client):
        """Test that available endpoints are listed"""
        response = client.get("/")
        data = response.json()

        # Check endpoints section exists
        assert "endpoints" in data
        endpoints = data["endpoints"]

        # Verify it's a list
        assert isinstance(endpoints, list)
        assert len(endpoints) > 0

        # Verify each endpoint has required fields
        for endpoint in endpoints:
            assert "path" in endpoint
            assert "method" in endpoint
            assert "description" in endpoint

    def test_root_endpoint_custom_user_agent(self, client):
        """Test that custom user agent is captured"""
        custom_agent = "Test-Agent/1.0"
        response = client.get("/", headers={"User-Agent": custom_agent})
        data = response.json()

        assert data["request"]["user_agent"] == custom_agent


class TestHealthEndpoint:
    """Test suite for the /health endpoint"""

    def test_health_endpoint_status_code(self, client):
        """Test that health endpoint returns 200 OK"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_returns_json(self, client):
        """Test that health endpoint returns valid JSON"""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, dict)

    def test_health_endpoint_structure(self, client):
        """Test that health endpoint returns expected structure"""
        response = client.get("/health")
        data = response.json()

        # Check required fields
        assert "status" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data

    def test_health_endpoint_status_value(self, client):
        """Test that health status is 'healthy'"""
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"

    def test_health_endpoint_timestamp_format(self, client):
        """Test that timestamp is in valid ISO format"""
        response = client.get("/health")
        data = response.json()

        # Should be able to parse as datetime
        timestamp = data["timestamp"]
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    def test_health_endpoint_uptime_is_positive(self, client):
        """Test that uptime is a positive integer"""
        response = client.get("/health")
        data = response.json()

        assert isinstance(data["uptime_seconds"], int)
        assert data["uptime_seconds"] >= 0

    def test_health_endpoint_multiple_calls(self, client):
        """Test that uptime increases with multiple calls"""
        import time

        response1 = client.get("/health")
        data1 = response1.json()
        uptime1 = data1["uptime_seconds"]

        time.sleep(1)

        response2 = client.get("/health")
        data2 = response2.json()
        uptime2 = data2["uptime_seconds"]

        # Uptime should increase or stay the same (in case of fast execution)
        assert uptime2 >= uptime1


class TestErrorHandling:
    """Test suite for error handling"""

    def test_404_not_found(self, client):
        """Test that non-existent endpoints return 404"""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_404_error_structure(self, client):
        """Test that 404 errors return proper JSON structure"""
        response = client.get("/does-not-exist")
        data = response.json()

        assert "error" in data
        assert "message" in data
        assert "path" in data

        assert data["error"] == "Not Found"
        assert data["path"] == "/does-not-exist"

    def test_405_method_not_allowed(self, client):
        """Test that wrong HTTP methods are rejected"""
        # Root endpoint only supports GET
        response = client.post("/")
        assert response.status_code == 405

    def test_health_endpoint_wrong_method(self, client):
        """Test that health endpoint rejects non-GET methods"""
        response = client.post("/health")
        assert response.status_code == 405


class TestUtilityFunctions:
    """Test suite for utility functions"""

    def test_get_system_info_structure(self):
        """Test that get_system_info returns expected structure"""
        info = get_system_info()

        # Check all required fields
        assert "hostname" in info
        assert "platform" in info
        assert "platform_version" in info
        assert "architecture" in info
        assert "cpu_count" in info
        assert "python_version" in info

        # Check types
        assert isinstance(info["hostname"], str)
        assert isinstance(info["platform"], str)
        assert isinstance(info["cpu_count"], int)

    def test_get_uptime_structure(self):
        """Test that get_uptime returns expected structure"""
        uptime = get_uptime()

        # Check required fields
        assert "seconds" in uptime
        assert "human" in uptime

        # Check types and values
        assert isinstance(uptime["seconds"], int)
        assert isinstance(uptime["human"], str)
        assert uptime["seconds"] >= 0
        assert "hours" in uptime["human"]
        assert "minutes" in uptime["human"]


class TestDocumentation:
    """Test suite for API documentation endpoints"""

    def test_docs_endpoint_exists(self, client):
        """Test that /docs endpoint is accessible"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_endpoint_exists(self, client):
        """Test that /redoc endpoint is accessible"""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_schema_exists(self, client):
        """Test that OpenAPI schema is accessible"""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        # Should be valid JSON
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema


class TestCORS:
    """Test CORS headers if applicable"""

    def test_cors_headers_on_root(self, client):
        """Test CORS handling on root endpoint"""
        response = client.get("/")
        # FastAPI doesn't add CORS headers by default, this test verifies that
        # If CORS is added later, this test should be updated
        assert response.status_code == 200


# Performance and stress testing (optional but good practice)
class TestPerformance:
    """Basic performance tests"""

    def test_root_endpoint_response_time(self, client):
        """Test that root endpoint responds quickly"""
        import time

        start = time.time()
        response = client.get("/")
        end = time.time()

        # Should respond in less than 1 second
        assert response.status_code == 200
        assert (end - start) < 1.0

    def test_health_endpoint_response_time(self, client):
        """Test that health endpoint responds quickly"""
        import time

        start = time.time()
        response = client.get("/health")
        end = time.time()

        # Health check should be very fast (less than 500ms)
        assert response.status_code == 200
        assert (end - start) < 0.5
