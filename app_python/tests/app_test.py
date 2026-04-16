import pytest
from unittest.mock import patch
from datetime import datetime, timezone
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@patch("app.get_uptime")
@patch("app.get_system_info")
@patch("app.datetime")
def test_root_endpoint_success(mock_datetime, mock_system_info, mock_uptime, client):
    """Test GET /, status 200, data structures & types."""
    mock_uptime.return_value = {"seconds": 3600, "human": "1 hours, 0 minutes"}
    mock_system_info.return_value = {
        "hostname": "test-host",
        "platform": "Linux",
        "platform_version": "5.15",
        "architecture": "x86_64",
        "cpu_count": 4,
        "python_version": "3.11.0",
    }
    mock_datetime.now.return_value = datetime(2026, 2, 11, 22, 46, tzinfo=timezone.utc)

    response = client.get("/")

    assert response.status_code == 200

    data = response.get_json()
    # Check that all keys are present
    assert "service" in data
    assert "system" in data
    assert "runtime" in data
    assert "request" in data
    assert "endpoints" in data

    # And check data types
    assert isinstance(data["service"]["name"], str)
    assert isinstance(data["system"]["cpu_count"], int)
    assert isinstance(data["runtime"]["uptime_seconds"], int)
    assert isinstance(data["endpoints"], list)
    assert len(data["endpoints"]) == 2


@patch("app.get_uptime")
def test_health_endpoint_success(mock_uptime, client):
    """Test GET /health, status 200, data structures & types."""
    mock_uptime.return_value = {"seconds": 7200, "human": "2 hours, 0 minutes"}

    response = client.get("/health")

    assert response.status_code == 200

    data = response.get_json()
    assert data["status"] == "healthy"
    assert isinstance(data["timestamp"], str)
    assert isinstance(data["uptime_seconds"], int)


def test_nonexistent_endpoint_404(client):
    """Test non-existent endpoint, status 404, data structure."""
    response = client.get("/nonexistent")

    assert response.status_code == 404

    data = response.get_json()
    assert data["error"] == "Not Found"
    assert isinstance(data["message"], str)
    assert data["message"] == "Endpoint does not exist"


def test_root_wrong_method_405(client):
    """Test invalid HTTP method on / - 405."""
    response = client.post("/")

    assert response.status_code == 405


def test_health_wrong_method_405(client):
    """Test invalid HTTP method on  /health - 405."""
    response = client.post("/health")

    assert response.status_code == 405


# @patch('app.get_uptime', side_effect=Exception("Uptime calculation failed"))
# def test_internal_server_error_500(mock_uptime, client):
#     """Test for internal server error response, status 500, data structure."""
#     response = client.get('/')

#     assert response.status_code == 500

#     data = response.get_json()
#     assert data["error"] == "Internal Server Error"
#     assert isinstance(data["message"], str)
#     assert data["message"] == "An unexpected error occurred"

# @patch('app.socket.gethostname', side_effect=Exception("Hostname resolution failed"))
# def test_system_info_error_500(client):
#     """Test for get_system_info error - 500."""
#     response = client.get('/')

#     assert response.status_code == 500


def test_empty_request_data(client):
    """Edge case: base requests without any headers."""
    response = client.get("/")
    assert response.status_code == 200
    assert "client_ip" in response.get_json()["request"]


def test_with_headers(client):
    """Edge case: base reuest with User-Agent header."""
    headers = {"User-Agent": "TestAgent/1.0"}
    response = client.get("/", headers=headers)
    data = response.get_json()
    assert data["request"]["user_agent"] == "TestAgent/1.0"


def test_visits_endpoint(client):
    """Test GET /visits returns counter."""
    import os
    if os.path.exists("/data/visits"):
        os.remove("/data/visits")
    
    client.get("/")
    response = client.get("/visits")
    data = response.get_json()
    assert data["visits"] == 1
    
    client.get("/")
    response = client.get("/visits")
    data = response.get_json()
    assert data["visits"] == 2