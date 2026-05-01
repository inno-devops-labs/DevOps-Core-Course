import pytest
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import app as app_module

app = app_module.app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Fixture for test client Flask"""
    visits_file = tmp_path / "visits"
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "application_name": "test-devops-service",
                "environment": "test",
                "settings": {
                    "featureGreeting": True,
                    "maxVisitsDisplay": 10,
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(app_module, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(app_module, "VISITS_FILE", str(visits_file))
    monkeypatch.setattr(app_module, "CONFIG_FILE", str(config_file))
    with app.test_client() as client:
        yield client


def test_get_system_info():
    """Test of get_system_info()"""
    from app import get_system_info

    info = get_system_info()

    assert isinstance(info, dict)
    assert "hostname" in info
    assert "platform" in info
    assert "python_version" in info
    assert isinstance(info["cpu_count"], int)


def test_get_uptime():
    """Test of get_uptime()"""
    from app import get_uptime

    uptime = get_uptime()

    assert isinstance(uptime, dict)
    assert "seconds" in uptime
    assert "human" in uptime
    assert isinstance(uptime["seconds"], int)
    assert isinstance(uptime["human"], str)


def test_main_endpoint(client):
    """Test of main endpoint GET /"""
    response = client.get("/")

    # Status check
    assert response.status_code == 200

    # Json structure test
    data = response.get_json()

    # Service structure test
    assert "service" in data
    assert data["service"]["name"] == "devops-info-service"
    assert data["service"]["version"] == "2.0.0"
    assert data["service"]["framework"] == "Flask"

    # System structure test
    assert "system" in data
    assert all(
        key in data["system"]
        for key in [
            "hostname",
            "platform",
            "platform_version",
            "architecture",
            "cpu_count",
            "python_version",
        ]
    )

    # Time structure test
    assert "runtime" in data
    assert "uptime_seconds" in data["runtime"]
    assert "current_time" in data["runtime"]
    assert data["runtime"]["timezone"] == "UTC"
    assert data["runtime"]["visits_count"] == 1

    # Request structure test
    assert "request" in data
    assert "client_ip" in data["request"]
    assert "method" in data["request"]
    assert data["request"]["method"] == "GET"

    assert "configuration" in data
    assert data["configuration"]["file"]["application_name"] == "test-devops-service"
    assert data["configuration"]["environment"]["CONFIG_FILE"].endswith("config.json")

    # Endpoints structure test
    assert "endpoints" in data
    assert isinstance(data["endpoints"], list)
    assert len(data["endpoints"]) >= 3


def test_health_endpoint(client):
    """Test of health endpoint GET /health"""
    response = client.get("/health")

    # Status check
    assert response.status_code == 200

    # Json structure test
    data = response.get_json()

    assert "status" in data
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "uptime_seconds" in data
    assert isinstance(data["uptime_seconds"], int)


def test_404_error(client):
    """404 error handling test"""
    response = client.get("/nonexistent")

    assert response.status_code == 404

    data = response.get_json()
    assert "error" in data
    assert "message" in data
    assert data["error"] == "Not Found"


def test_different_user_agent(client):
    """Test with different User-Agent headers."""
    headers = {"User-Agent": "Test-Agent/1.0"}
    response = client.get("/", headers=headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data["request"]["user_agent"] == "Test-Agent/1.0"


def test_json_structure_types(client):
    """Checking the data types in the JSON response"""
    response = client.get("/")
    data = response.get_json()

    # Type check in service
    assert isinstance(data["service"]["name"], str)
    assert isinstance(data["service"]["version"], str)
    assert isinstance(data["service"]["description"], str)

    # Type check in system
    assert isinstance(data["system"]["hostname"], str)
    assert isinstance(data["system"]["cpu_count"], int)
    assert isinstance(data["system"]["python_version"], str)

    # Type check in runtime
    assert isinstance(data["runtime"]["uptime_seconds"], int)
    assert isinstance(data["runtime"]["current_time"], str)


def test_health_response_structure(client):
    """Detailed verification of the health endpoint structure"""
    response = client.get("/health")
    data = response.get_json()

    # Checking all required fields
    required_fields = ["status", "timestamp", "uptime_seconds"]
    for field in required_fields:
        assert field in data

    # Checking the status value
    assert data["status"] == "healthy"

    # Checking the timestamp format
    from datetime import datetime

    try:
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        timestamp_valid = True
    except ValueError:
        timestamp_valid = False
    assert timestamp_valid


def test_metrics_endpoint(client):
    """Metrics endpoint exposes Prometheus metrics in text format."""
    client.get("/")
    client.get("/health")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.mimetype == "text/plain"

    metrics_output = response.get_data(as_text=True)
    metric_lines = metrics_output.splitlines()

    assert "http_requests_total" in metrics_output
    assert any(
        line.startswith("http_requests_total{")
        and 'endpoint="/"' in line
        and 'method="GET"' in line
        and 'status_code="200"' in line
        for line in metric_lines
    )
    assert any(
        line.startswith("http_requests_total{")
        and 'endpoint="/health"' in line
        and 'method="GET"' in line
        and 'status_code="200"' in line
        for line in metric_lines
    )
    assert "http_request_duration_seconds_bucket" in metrics_output
    assert any(
        line.startswith("http_requests_in_progress{")
        and 'endpoint="/metrics"' in line
        and 'method="GET"' in line
        for line in metric_lines
    )
    assert "devops_info_endpoint_calls_total" in metrics_output
    assert "devops_info_system_info_collection_seconds_bucket" in metrics_output


def test_visits_endpoint_and_persistence(client):
    """The root endpoint increments visits and /visits returns the stored counter."""
    first_response = client.get("/")
    second_response = client.get("/")
    visits_response = client.get("/visits")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert visits_response.status_code == 200

    assert first_response.get_json()["runtime"]["visits_count"] == 1
    assert second_response.get_json()["runtime"]["visits_count"] == 2
    assert visits_response.get_json()["visits"] == 2
    assert os.path.exists(app_module.VISITS_FILE)

    with open(app_module.VISITS_FILE, "r", encoding="utf-8") as visits_file:
        assert visits_file.read().strip() == "2"
