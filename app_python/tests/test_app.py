"""
Unit tests for the DevOps Info Service API.

Tests cover:
- GET / endpoint with all required fields and structure
- GET /health endpoint with status verification
- GET /visits endpoint and persisted counter updates
- Error cases and edge conditions
"""
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app as app_module
from app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a test client for the FastAPI app."""
    visits_file = tmp_path / "data" / "visits"
    monkeypatch.setenv("VISITS_FILE", str(visits_file))
    app_module.ensure_visits_storage()

    with TestClient(app) as test_client:
        yield test_client


class TestRootEndpoint:
    """Test suite for the main / endpoint."""

    def test_root_endpoint_returns_200(self, client):
        """Test that root endpoint returns 200 status code."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_endpoint_returns_json(self, client):
        """Test that root endpoint returns valid JSON."""
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, dict)

    def test_root_endpoint_has_required_sections(self, client):
        """Test that root endpoint has all required top-level sections."""
        response = client.get("/")
        data = response.json()
        
        required_sections = ["service", "system", "runtime", "request", "endpoints"]
        for section in required_sections:
            assert section in data, f"Missing required section: {section}"

    def test_service_section_structure(self, client):
        """Test that service section has all required fields."""
        response = client.get("/")
        service = response.json()["service"]
        
        required_fields = ["name", "version", "description", "framework"]
        for field in required_fields:
            assert field in service, f"Missing field in service: {field}"
            assert isinstance(service[field], str), f"Field {field} should be string"
            assert len(service[field]) > 0, f"Field {field} should not be empty"
        
        assert service["framework"] == "FastAPI"

    def test_system_section_structure(self, client):
        """Test that system section has all required fields with correct types."""
        response = client.get("/")
        system = response.json()["system"]
        
        required_fields = {
            "hostname": str,
            "platform": str,
            "platform_version": str,
            "architecture": str,
            "cpu_count": int,
            "python_version": str
        }
        
        for field, expected_type in required_fields.items():
            assert field in system, f"Missing field in system: {field}"
            assert isinstance(system[field], expected_type), \
                f"Field {field} should be {expected_type.__name__}"
        
        assert system["cpu_count"] > 0, "CPU count should be positive"

    def test_runtime_section_structure(self, client):
        """Test that runtime section has all required fields."""
        response = client.get("/")
        runtime = response.json()["runtime"]
        
        required_fields = {
            "uptime_seconds": int,
            "uptime_human": str,
            "current_time": str,
            "timezone": str
        }
        
        for field, expected_type in required_fields.items():
            assert field in runtime, f"Missing field in runtime: {field}"
            assert isinstance(runtime[field], expected_type), \
                f"Field {field} should be {expected_type.__name__}"
        
        assert runtime["uptime_seconds"] >= 0, "Uptime should be non-negative"
        assert runtime["timezone"] == "UTC"
        
        # Verify current_time is valid ISO format
        datetime.fromisoformat(runtime["current_time"].replace('Z', '+00:00'))

    def test_request_section_structure(self, client):
        """Test that request section captures request details."""
        response = client.get("/")
        request_info = response.json()["request"]
        
        required_fields = ["client_ip", "user_agent", "method", "path"]
        for field in required_fields:
            assert field in request_info, f"Missing field in request: {field}"
            assert isinstance(request_info[field], str), \
                f"Field {field} should be string"
        
        assert request_info["method"] == "GET"
        assert request_info["path"] == "/"
        assert request_info["client_ip"] is not None

    def test_endpoints_section_structure(self, client):
        """Test that endpoints section lists available endpoints."""
        response = client.get("/")
        endpoints = response.json()["endpoints"]
        
        assert isinstance(endpoints, list), "Endpoints should be a list"
        assert len(endpoints) >= 4, "Should have at least 4 endpoints"
        
        for endpoint in endpoints:
            assert "path" in endpoint
            assert "method" in endpoint
            assert "description" in endpoint
            assert isinstance(endpoint["path"], str)
            assert isinstance(endpoint["method"], str)
            assert isinstance(endpoint["description"], str)
        
        # Verify both main endpoints are listed
        paths = [ep["path"] for ep in endpoints]
        assert "/" in paths
        assert "/health" in paths
        assert "/visits" in paths
        assert "/metrics" in paths

    def test_root_endpoint_with_custom_user_agent(self, client):
        """Test that custom user agent is captured correctly."""
        custom_ua = "TestClient/1.0"
        response = client.get("/", headers={"User-Agent": custom_ua})
        
        assert response.status_code == 200
        request_info = response.json()["request"]
        assert custom_ua in request_info["user_agent"]


class TestHealthEndpoint:
    """Test suite for the /health endpoint."""

    def test_health_endpoint_returns_200(self, client):
        """Test that health endpoint returns 200 status code."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_returns_json(self, client):
        """Test that health endpoint returns valid JSON."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, dict)

    def test_health_endpoint_structure(self, client):
        """Test that health endpoint has all required fields."""
        response = client.get("/health")
        data = response.json()
        
        required_fields = {
            "status": str,
            "timestamp": str,
            "uptime_seconds": int
        }
        
        for field, expected_type in required_fields.items():
            assert field in data, f"Missing field in health: {field}"
            assert isinstance(data[field], expected_type), \
                f"Field {field} should be {expected_type.__name__}"

    def test_health_status_is_healthy(self, client):
        """Test that health status is 'healthy'."""
        response = client.get("/health")
        data = response.json()
        
        assert data["status"] == "healthy", "Health status should be 'healthy'"

    def test_health_timestamp_is_valid(self, client):
        """Test that health timestamp is valid ISO format."""
        response = client.get("/health")
        data = response.json()
        
        # Should be able to parse as ISO format datetime
        timestamp = data["timestamp"]
        parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert parsed is not None
        
        # Timestamp should be recent (within last minute)
        now = datetime.now(timezone.utc)
        time_diff = abs((now - parsed).total_seconds())
        assert time_diff < 60, "Timestamp should be current"

    def test_health_uptime_is_reasonable(self, client):
        """Test that uptime is a reasonable value."""
        response = client.get("/health")
        data = response.json()
        
        uptime = data["uptime_seconds"]
        assert uptime >= 0, "Uptime should be non-negative"
        # Uptime shouldn't be more than a few hours for tests
        assert uptime < 86400, "Uptime seems unreasonably high for test"

    def test_health_endpoint_multiple_calls_increase_uptime(self, client):
        """Test that multiple health checks show consistent uptime."""
        response1 = client.get("/health")
        data1 = response1.json()
        uptime1 = data1["uptime_seconds"]
        
        # Small delay to allow time to pass
        import time
        time.sleep(0.1)
        
        response2 = client.get("/health")
        data2 = response2.json()
        uptime2 = data2["uptime_seconds"]
        
        # Second uptime should be >= first (allowing for same second)
        assert uptime2 >= uptime1, "Uptime should not decrease"


class TestVisitsEndpoint:
    """Test suite for the /visits endpoint and file persistence."""

    def test_visits_endpoint_returns_zero_before_root_requests(self, client):
        """Test that visits counter starts at zero for a fresh file."""
        response = client.get("/visits")

        assert response.status_code == 200
        assert response.json() == {"visits": 0}

    def test_root_requests_increment_visits_counter(self, client):
        """Test that each GET / call increments the persisted counter."""
        client.get("/")
        client.get("/")

        response = client.get("/visits")

        assert response.status_code == 200
        assert response.json()["visits"] == 2

    def test_visits_counter_is_written_to_file(self, client):
        """Test that the counter value is stored in the configured file."""
        client.get("/")
        client.get("/")
        visits_file = Path(app_module.get_visits_file_path())

        assert visits_file.exists()
        assert visits_file.read_text(encoding="utf-8").strip() == "2"


class TestErrorHandling:
    """Test suite for error handling."""

    def test_404_for_nonexistent_endpoint(self, client):
        """Test that nonexistent endpoints return 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_404_error_structure(self, client):
        """Test that 404 errors return proper JSON structure."""
        response = client.get("/nonexistent")
        data = response.json()
        
        assert "error" in data or "message" in data or "detail" in data
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test that POST to GET-only endpoints is handled."""
        response = client.post("/")
        # FastAPI returns 405 for method not allowed
        assert response.status_code == 405

    def test_invalid_path_characters(self, client):
        """Test that paths with invalid characters are handled."""
        response = client.get("/../../etc/passwd")
        # Should either 404 or be handled safely
        assert response.status_code in [404, 400]


class TestAPIConsistency:
    """Test suite for API consistency and stability."""

    def test_multiple_root_calls_consistency(self, client):
        """Test that multiple calls return consistent structure."""
        response1 = client.get("/")
        response2 = client.get("/")
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Service info should be identical
        assert data1["service"] == data2["service"]
        
        # System info should be identical
        assert data1["system"] == data2["system"]
        
        # Endpoints list should be identical
        assert data1["endpoints"] == data2["endpoints"]

    def test_concurrent_health_checks(self, client):
        """Test that concurrent health checks all succeed."""
        import concurrent.futures
        
        def call_health():
            response = client.get("/health")
            return response.status_code
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(call_health) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All calls should return 200
        assert all(status == 200 for status in results)
        assert len(results) == 10
