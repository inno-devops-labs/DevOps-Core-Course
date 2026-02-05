import pytest
from datetime import datetime, timezone
from unittest.mock import patch
import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app, get_system_info, get_uptime, get_request_info


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_get_system_info():
    """Test that system info returns expected keys and types."""
    info = get_system_info()
    assert isinstance(info, dict)
    assert "hostname" in info
    assert "platform" in info
    assert "platform_version" in info
    assert "architecture" in info
    assert "cpu_count" in info
    assert "python_version" in info

    assert isinstance(info["hostname"], str)
    assert isinstance(info["platform"], str)
    assert isinstance(info["cpu_count"], int)
    assert info["cpu_count"] >= 1


def test_get_uptime():
    """Test uptime calculation logic."""
    uptime = get_uptime()
    assert "seconds" in uptime
    assert "human" in uptime
    assert isinstance(uptime["seconds"], int)
    assert uptime["seconds"] >= 0
    assert isinstance(uptime["human"], str)
    assert "hours" in uptime["human"]
    assert "minutes" in uptime["human"]


def test_get_request_info_with_context():
    """Test get_request_info inside a request context."""
    # Test with X-Forwarded-For
    with app.test_request_context(
        "/test-path",
        headers={"User-Agent": "pytest-agent", "X-Forwarded-For": "192.0.2.1"},
        environ_base={"REMOTE_ADDR": "10.0.0.1"}
    ):
        info = get_request_info()
        assert info["client_ip"] == "192.0.2.1"
        assert info["user_agent"] == "pytest-agent"
        assert info["method"] == "GET"
        assert info["path"] == "/test-path"

    # Test without X-Forwarded-For (use remote_addr)
    with app.test_request_context(
        "/",
        environ_base={"REMOTE_ADDR": "192.168.1.100"}
    ):
        info = get_request_info()
        assert info["client_ip"] == "192.168.1.100"


def test_index_endpoint(client):
    """Test the main '/' endpoint returns correct structure and data."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.get_json()

    assert "service" in data
    assert "system" in data
    assert "runtime" in data
    assert "request" in data
    assert "endpoints" in data

    service = data["service"]
    assert service["name"] == "devops-info-service"
    assert service["version"] == "1.0.0"
    assert "description" in service

    system = data["system"]
    assert "hostname" in system
    assert "platform" in system

    runtime = data["runtime"]
    assert "uptime_seconds" in runtime
    assert "uptime_human" in runtime
    assert "current-time" in runtime
    assert runtime["timezone"] == "UTC"

    current_time = datetime.fromisoformat(runtime["current-time"].replace("Z", "+00:00"))
    assert current_time.tzinfo == timezone.utc

    req_info = data["request"]
    assert "client_ip" in req_info
    assert "user_agent" in req_info
    assert req_info["method"] == "GET"
    assert req_info["path"] == "/"

    endpoints = data["endpoints"]
    assert len(endpoints) == 2
    paths = {e["path"] for e in endpoints}
    assert "/" in paths
    assert "/health" in paths


def test_health_endpoint(client):
    """Test the /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()

    assert "status" in data
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "uptime_seconds" in data

    ts = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    assert ts.tzinfo == timezone.utc

    assert isinstance(data["uptime_seconds"], int)
    assert data["uptime_seconds"] >= 0


def test_404_error_handler(client):
    """Test that invalid routes return 404 with proper JSON."""
    response = client.get("/nonexistent")
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Not Found"
    assert "message" in data


def test_uptime_consistency_between_endpoints(client):
    """Ensure uptime is consistent between / and /health at roughly same time."""
    resp1 = client.get("/")
    resp2 = client.get("/health")

    data1 = resp1.get_json()
    data2 = resp2.get_json()

    uptime1 = data1["runtime"]["uptime_seconds"]
    uptime2 = data2["uptime_seconds"]

    assert abs(uptime1 - uptime2) <= 2


def test_timezone_is_utc(client):
    """Ensure all timestamps are in UTC."""
    resp = client.get("/")
    data = resp.get_json()
    current_time_str = data["runtime"]["current-time"]
    
    assert current_time_str.endswith("Z") or "+00:00" in current_time_str

    dt = datetime.fromisoformat(current_time_str.replace("Z", "+00:00"))
    assert dt.utcoffset().total_seconds() == 0