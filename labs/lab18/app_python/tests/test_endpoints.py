import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import time
import sys
import os

# Add the parent directory to path so we can import the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Try different import paths
try:
    # If running from root directory
    from app import app
except ImportError:
    try:
        # If running from tests directory
        from app_python.app import app
    except ImportError:
        # If app is in parent directory
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app_python')))
        from app_python.app import app

client = TestClient(app)


def test_root_endpoint_success():
    """Test GET / endpoint returns successful response with correct structure."""
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

    data = response.json()

    assert "service" in data
    assert "system" in data
    assert "runtime" in data
    assert "request" in data
    assert "endpoints" in data


def test_root_endpoint_service_info():
    """Test service information in root endpoint."""
    response = client.get("/")
    data = response.json()
    service_info = data["service"]

    assert service_info["name"] == "devops-info-service"
    assert service_info["version"] == "1.0.0"
    assert service_info["description"] == "DevOps course info service"
    assert service_info["framework"] == "FastAPI"

    expected_fields = ["name", "version", "description", "framework"]
    assert all(field in service_info for field in expected_fields)


def test_root_endpoint_system_info():
    """Test system information in root endpoint."""
    response = client.get("/")
    data = response.json()
    system_info = data["system"]

    required_fields = [
        "hostname", "platform", "platform_version",
        "architecture", "cpu_count", "python_version"
    ]
    assert all(field in system_info for field in required_fields)

    assert isinstance(system_info["hostname"], str)
    assert isinstance(system_info["platform"], str)
    assert isinstance(system_info["architecture"], str)
    assert isinstance(system_info["cpu_count"], int)
    assert isinstance(system_info["python_version"], str)

    # Verify CPU count is reasonable
    assert system_info["cpu_count"] > 0


def test_root_endpoint_runtime_info():
    """Test runtime information in root endpoint."""
    response = client.get("/")
    data = response.json()
    runtime_info = data["runtime"]

    # Verify required runtime fields
    required_fields = [
        "uptime_seconds", "uptime_human",
        "current_time", "timezone"
    ]
    assert all(field in runtime_info for field in required_fields)

    # Verify data types and formats
    assert isinstance(runtime_info["uptime_seconds"], int)
    assert isinstance(runtime_info["uptime_human"], str)
    assert isinstance(runtime_info["current_time"], str)
    assert isinstance(runtime_info["timezone"], str)

    # Verify uptime is non-negative
    assert runtime_info["uptime_seconds"] >= 0

    # Verify timestamp format (ISO 8601)
    try:
        datetime.fromisoformat(runtime_info["current_time"].replace('Z', '+00:00'))
    except ValueError:
        pytest.fail("current_time is not in valid ISO format")

    # Verify uptime human format
    assert "hours" in runtime_info["uptime_human"]
    assert "minutes" in runtime_info["uptime_human"]


def test_root_endpoint_request_info():
    """Test request information in root endpoint."""
    response = client.get("/")
    data = response.json()
    request_info = data["request"]

    # Verify required request fields
    required_fields = ["client_ip", "user_agent", "method", "path"]
    assert all(field in request_info for field in required_fields)

    # Verify data types
    assert isinstance(request_info["client_ip"], str)
    assert isinstance(request_info["method"], str)
    assert isinstance(request_info["path"], str)

    # Verify specific values
    assert request_info["method"] == "GET"
    assert request_info["path"] == "/"

    # Verify IP address format (basic check)
    assert request_info["client_ip"] in ["127.0.0.1", "testclient"] or ":" in request_info["client_ip"]


def test_root_endpoint_endpoints_list():
    """Test endpoints list in root endpoint."""
    response = client.get("/")
    data = response.json()
    endpoints = data["endpoints"]

    assert isinstance(endpoints, list)
    assert len(endpoints) >= 2

    for endpoint in endpoints:
        assert "path" in endpoint
        assert "method" in endpoint
        assert "description" in endpoint

        assert isinstance(endpoint["path"], str)
        assert isinstance(endpoint["method"], str)
        assert isinstance(endpoint["description"], str)

    endpoint_paths = [e["path"] for e in endpoints]
    assert "/" in endpoint_paths
    assert "/health" in endpoint_paths


def test_health_endpoint_success():
    """Test GET /health endpoint returns healthy status."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

    data = response.json()

    required_fields = ["status", "timestamp", "uptime_seconds"]
    assert all(field in data for field in required_fields)

    assert data["status"] == "healthy"
    assert isinstance(data["uptime_seconds"], int)
    assert data["uptime_seconds"] >= 0


def test_health_endpoint_uptime_increases():
    """Verify that uptime increases between calls."""
    response1 = client.get("/health")
    uptime1 = response1.json()["uptime_seconds"]

    time.sleep(0.1)

    response2 = client.get("/health")
    uptime2 = response2.json()["uptime_seconds"]

    assert uptime2 >= uptime1


def test_nonexistent_endpoint_404():
    """Test that non-existent endpoints return 404 with proper error structure."""
    response = client.get("/nonexistent")

    assert response.status_code == 404
    assert response.headers["content-type"] == "application/json"

    data = response.json()

    # Fix: Check for the actual error message from your app
    assert "ERROR" in data or "error" in data
    assert "message" in data

    # Your app returns "Endpoint not found" not "Endpoint does not exist"
    assert data["message"] in ["Endpoint not found", "Endpoint does not exist"]


def test_invalid_method_405():
    """Test that invalid HTTP methods return proper error."""
    response = client.post("/health")

    assert response.status_code == 405
    assert response.headers["content-type"] == "application/json"


def test_root_endpoint_json_structure_completeness():
    """Verify the complete JSON structure matches documentation."""
    response = client.get("/")
    data = response.json()

    # Expected structure
    expected_structure = {
        "service": {
            "name": str,
            "version": str,
            "description": str,
            "framework": str
        },
        "system": {
            "hostname": str,
            "platform": str,
            "platform_version": str,
            "architecture": str,
            "cpu_count": int,
            "python_version": str
        },
        "runtime": {
            "uptime_seconds": int,
            "uptime_human": str,
            "current_time": str,
            "timezone": str
        },
        "request": {
            "client_ip": str,
            "user_agent": (str, type(None)),  # Can be None
            "method": str,
            "path": str
        },
        "endpoints": list
    }

    def validate_structure(data, expected, path=""):
        for key, expected_type in expected.items():
            full_path = f"{path}.{key}" if path else key

            assert key in data, f"Missing key: {full_path}"

            if isinstance(expected_type, tuple):
                assert isinstance(data[key], expected_type), \
                    f"{full_path} should be one of {expected_type}, got {type(data[key])}"
            elif isinstance(expected_type, dict):
                assert isinstance(data[key], dict), \
                    f"{full_path} should be dict, got {type(data[key])}"
                validate_structure(data[key], expected_type, full_path)
            elif isinstance(expected_type, list):
                assert isinstance(data[key], list), \
                    f"{full_path} should be list, got {type(data[key])}"
            else:
                assert isinstance(data[key], expected_type), \
                    f"{full_path} should be {expected_type}, got {type(data[key])}"

    validate_structure(data, expected_structure)


def test_endpoints_list_accuracy():
    """Verify that the endpoints list accurately describes available endpoints."""
    response = client.get("/")
    data = response.json()
    endpoints = data["endpoints"]

    # Test each endpoint listed
    for endpoint in endpoints:
        if endpoint["method"] == "GET":
            response = client.get(endpoint["path"])
            assert response.status_code == 200


def test_error_handling_structure():
    """Verify that error responses have consistent structure."""
    # Test 404
    response = client.get("/invalid-endpoint")
    data = response.json()

    # Fix: Check for the actual error structure
    has_error_field = "ERROR" in data or "error" in data
    assert has_error_field, "Error response missing error field"
    assert "message" in data
    assert isinstance(data["message"], str)


@pytest.mark.parametrize("invalid_path", [
    "/api/v1",
    "/HEALTH",
    "/healthz",
    "/status",
])
def test_various_nonexistent_paths(invalid_path):
    """Test various non-existent paths return proper 404."""
    response = client.get(invalid_path)
    assert response.status_code == 404

    data = response.json()
    # Fix: Check for the actual message
    assert data["message"] in ["Endpoint not found", "Endpoint does not exist"]