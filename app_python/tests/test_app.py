import os
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolate_visits_file(tmp_path, monkeypatch):
    visits_file = tmp_path / "visits"
    monkeypatch.setenv("VISITS_FILE", str(visits_file))
    yield


class TestRootEndpoint:
    """Comprehensive tests for GET / endpoint."""

    def test_success_response_code(self):
        """Verify endpoint returns 200 OK for valid request."""

        response = client.get("/")
        assert response.status_code == 200

    def test_response_content_type(self):
        """Verify response has correct Content-Type header."""

        response = client.get("/")
        assert response.headers["content-type"] == "application/json"

    def test_response_structure_validation(self):
        """Verify all required top-level keys exist."""

        response = client.get("/")
        data = response.json()

        required_keys = ["service", "system", "runtime", "request", "visits", "endpoints"]
        for key in required_keys:
            assert key in data, f"Missing required key: {key}"

        # No extra top-level keys
        extra_keys = set(data.keys()) - set(required_keys)
        assert len(extra_keys) == 0, f"Unexpected top-level keys: {extra_keys}"

    def test_service_section_validation(self):
        """Verify service section contains correct data."""

        response = client.get("/")
        data = response.json()["service"]

        assert data["name"] == "devops-info-service"
        assert data["version"] == "1.0.0"
        assert data["description"] == "DevOps course info service"
        assert data["framework"] == "FastAPI"

    def test_system_section_validation(self):
        """Verify system section contains valid system information."""

        response = client.get("/")
        data = response.json()["system"]

        # Required fields
        required_fields = ["hostname", "platform", "platform_version", 
                          "architecture", "cpu_count", "python_version"]
        for field in required_fields:
            assert field in data, f"Missing system field: {field}"

        # Type validation
        assert isinstance(data["hostname"], str)
        assert isinstance(data["platform"], str)
        assert isinstance(data["platform_version"], str)
        assert isinstance(data["architecture"], str)
        assert isinstance(data["cpu_count"], int)
        assert isinstance(data["python_version"], str)

        # Value validation (where possible)
        assert data["cpu_count"] > 0
        assert data["python_version"].startswith("3.")

    def test_runtime_section_validation(self):
        """Verify runtime section contains valid runtime data."""

        response = client.get("/")
        data = response.json()["runtime"]

        required_fields = ["uptime_seconds", "uptime_human", "current_time", "timezone"]
        for field in required_fields:
            assert field in data, f"Missing runtime field: {field}"

        # Type validation
        assert isinstance(data["uptime_seconds"], int)
        assert isinstance(data["uptime_human"], str)
        assert isinstance(data["current_time"], str)
        assert isinstance(data["timezone"], str)

        # Value validation
        assert data["uptime_seconds"] >= 0
        assert data["timezone"] == "UTC"
        
        # Uptime format validation (should contain "hour" and "minute")
        assert "hour" in data["uptime_human"].lower()
        assert "minute" in data["uptime_human"].lower()

        # Timestamp format validation
        assert "Z" in data["current_time"]
        assert "T" in data["current_time"]

        # Verify timestamp is recent (within last minute)
        timestamp_str = data["current_time"]
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        time_diff = (now - timestamp).total_seconds()
        assert time_diff >= 0 and time_diff < 60, "Timestamp should be recent"

    def test_request_section_validation(self):
        """Verify request section captures request metadata correctly."""

        response = client.get("/")
        data = response.json()["request"]

        required_fields = ["client_ip", "user_agent", "method", "path"]
        for field in required_fields:
            assert field in data, f"Missing request field: {field}"

        # Type validation
        assert isinstance(data["client_ip"], str)
        assert isinstance(data["user_agent"], str)
        assert isinstance(data["method"], str)
        assert isinstance(data["path"], str)

        # Value validation
        assert data["method"] == "GET"
        assert data["path"] == "/"

        # Client IP should be valid (not empty)
        assert data["client_ip"] != ""

    def test_endpoints_section_validation(self):
        """Verify endpoints section lists all available endpoints."""

        response = client.get("/")
        data = response.json()["endpoints"]

        # Should be a list
        assert isinstance(data, list)
        assert len(data) >= 3

        # Each endpoint should have required fields
        for endpoint in data:
            assert "path" in endpoint
            assert "method" in endpoint
            assert "description" in endpoint

            assert isinstance(endpoint["path"], str)
            assert isinstance(endpoint["method"], str)
            assert isinstance(endpoint["description"], str)

        # Should contain our main endpoints
        endpoint_paths = [e["path"] for e in data]
        assert "/" in endpoint_paths
        assert "/health" in endpoint_paths
        assert "/visits" in endpoint_paths

        # Verify specific endpoint details
        root_endpoint = next(e for e in data if e["path"] == "/")
        assert root_endpoint["method"] == "GET"
        assert "Service information" in root_endpoint["description"]

        health_endpoint = next(e for e in data if e["path"] == "/health")
        assert health_endpoint["method"] == "GET"
        assert "Health check" in health_endpoint["description"]

        visits_endpoint = next(e for e in data if e["path"] == "/visits")
        assert visits_endpoint["method"] == "GET"
        assert "Visits counter" in visits_endpoint["description"]

    def test_visits_section_validation(self):
        """Verify root endpoint includes visits counter section."""

        response = client.get("/")
        data = response.json()["visits"]

        assert "count" in data
        assert isinstance(data["count"], int)
        assert data["count"] >= 1

    def test_x_forwarded_for_header_handling(self):
        """Verify X-Forwarded-For header is correctly processed."""

        test_ip = "192.168.1.100"
        headers = {"X-Forwarded-For": f"{test_ip}, 10.0.0.1"}
        
        response = client.get("/", headers=headers)
        data = response.json()["request"]
        
        assert data["client_ip"] == test_ip

    def test_uptime_increases_over_time(self):
        """Verify uptime increases between consecutive requests."""

        response1 = client.get("/")
        uptime1 = response1.json()["runtime"]["uptime_seconds"]

        import time
        time.sleep(0.1)  # Small delay
        
        response2 = client.get("/")
        uptime2 = response2.json()["runtime"]["uptime_seconds"]

        assert uptime2 >= uptime1, "Uptime should not decrease"


class TestHealthEndpoint:
    """Comprehensive tests for GET /health endpoint."""

    def test_success_response_code(self):
        """Verify health endpoint returns 200 OK."""

        response = client.get("/health")
        assert response.status_code == 200

    def test_response_structure(self):
        """Verify health response has correct structure."""

        response = client.get("/health")
        data = response.json()

        required_fields = ["status", "timestamp", "uptime_seconds"]
        for field in required_fields:
            assert field in data, f"Missing health field: {field}"

        # No extra fields
        extra_fields = set(data.keys()) - set(required_fields)
        assert len(extra_fields) == 0, f"Unexpected health fields: {extra_fields}"

    def test_status_field(self):
        """Verify status is always 'healthy'."""

        response = client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"
        assert isinstance(data["status"], str)
    
    def test_uptime_field(self):
        """Verify uptime_seconds is valid."""

        response = client.get("/health")
        data = response.json()

        assert isinstance(data["uptime_seconds"], int)
        assert data["uptime_seconds"] >= 0

    def test_timestamp_field(self):
        """Verify timestamp is valid ISO8601 format."""

        response = client.get("/health")
        data = response.json()

        timestamp = data["timestamp"]
        assert isinstance(timestamp, str)
        assert "Z" in timestamp
        assert "T" in timestamp

        # Verify it can be parsed
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            assert dt.tzinfo == timezone.utc
        except ValueError:
            pytest.fail(f"Invalid timestamp format: {timestamp}")

    def test_uptime_consistency_with_root(self):
        """Verify uptime is consistent between / and /health endpoints."""

        root_response = client.get("/")
        health_response = client.get("/health")

        root_uptime = root_response.json()["runtime"]["uptime_seconds"]
        health_uptime = health_response.json()["uptime_seconds"]

        assert abs(root_uptime - health_uptime) <= 1


class TestVisitsEndpoint:
    """Tests for GET /visits endpoint and persistence behavior."""

    def test_visits_endpoint_success(self):
        response = client.get("/visits")
        assert response.status_code == 200

        data = response.json()
        assert "visits" in data
        assert "file_path" in data
        assert "timestamp" in data
        assert isinstance(data["visits"], int)
        assert data["visits"] >= 0

    def test_visits_increases_after_root_request(self):
        before = client.get("/visits").json()["visits"]
        client.get("/")
        after = client.get("/visits").json()["visits"]
        assert after == before + 1

    def test_visits_persisted_to_file(self):
        client.get("/")
        client.get("/")

        visits_data = client.get("/visits").json()
        file_path = visits_data["file_path"]
        assert os.path.exists(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            stored_value = int(f.read().strip())
        assert stored_value == visits_data["visits"]


class TestErrorHandling:
    """Tests for error scenarios and edge cases."""

    def test_404_not_found(self):
        """Verify 404 response for non-existent endpoints."""

        response = client.get("/non-existent-endpoint")
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert data["error"] == "Not Found"
        assert isinstance(data["error"], str)

    def test_method_not_allowed(self):
        """Verify 405 for unsupported HTTP methods."""

        unsupported_methods = ["POST", "PUT", "DELETE", "PATCH"]

        for method in unsupported_methods:
            response = client.request(method, "/")
            assert response.status_code == 405, f"Should 405 for {method} /"

            data = response.json()
            assert "error" in data

    def test_method_not_allowed_health(self):
        """Verify 405 for unsupported methods on health endpoint."""

        unsupported_methods = ["POST", "PUT", "DELETE", "PATCH"]

        for method in unsupported_methods:
            response = client.request(method, "/health")
            assert response.status_code == 405, f"Should 405 for {method} /"

            data = response.json()
            assert "error" in data
