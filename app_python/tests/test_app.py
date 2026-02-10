import os
import platform
import socket
import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["PROPAGATE_EXCEPTIONS"] = False
    with app.test_client() as client:
        yield client


def test_index():
    client = app.test_client()
    response = client.get(
        '/',
        headers={"User-Agent": "pytest-agent"}
    )

    assert response.status_code == 200

    data = response.get_json()
    assert "service" in data
    assert "system" in data
    assert "runtime" in data
    assert "request" in data
    assert "endpoints" in data

    service_data = data["service"]
    assert service_data["name"] == "devops-info-service"
    assert service_data["version"] == "1.0.0"
    assert service_data["description"] == "DevOps course info service"
    assert service_data["framework"] == "Flask"

    system_data = data["system"]
    assert system_data["hostname"] == socket.gethostname()
    assert system_data["platform"] == platform.system()
    assert system_data["platform_version"] == platform.version()
    assert system_data["architecture"] == platform.machine()
    assert system_data["cpu_count"] == os.cpu_count()
    assert system_data["python_version"] == platform.python_version()

    runtime_data = data["runtime"]
    assert "uptime_seconds" in runtime_data
    assert "uptime_human" in runtime_data
    assert "current_time" in runtime_data
    assert "timezone" in runtime_data
    assert runtime_data["timezone"] == "UTC"

    request_data = data["request"]
    assert request_data["client_ip"] == "127.0.0.1"
    assert request_data["user_agent"] == "pytest-agent"
    assert request_data["method"] == "GET"
    assert request_data["path"] == "/"

    endpoints_data = data["endpoints"]
    assert endpoints_data == [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"}
    ]


def test_health():
    client = app.test_client()
    response = client.get(
        '/health',
        headers={"User-Agent": "pytest-agent"}
    )

    assert response.status_code == 200

    data = response.get_json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "uptime_seconds" in data


def test_not_found():
    client = app.test_client()
    response = client.get(
        '/nope',
        headers={"User-Agent": "pytest-agent"}
    )

    assert response.status_code == 404

    data = response.get_json()
    data == {"error": "Not Found", "message": "Endpoint does not exist"}


def test_internal_server_error(client):
    def error_raise():
        raise RuntimeError("error_raise")

    app.view_functions["index"] = error_raise
    response = client.get("/")

    assert response.status_code == 500
    data = response.get_json()
    assert data == {"error": "Internal Server Error", "message": "Unexpected error"}
