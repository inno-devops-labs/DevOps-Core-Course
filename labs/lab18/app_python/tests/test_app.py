import pytest
from app import app


def test_health_endpoint():
    # Test health chech
    client = app.test_client()
    response = client.get('/health')

    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"


def test_default_endpoint():
    # Test default route returns expected structure
    client = app.test_client()
    response = client.get('/')

    assert response.status_code == 200
    data = response.get_json()

    assert "service" in data
    assert "system" in data
    assert "runtime" in data
    assert "request" in data
    assert "endpoints" in data

    service = data["service"]
    assert "name" in service
    assert "version" in service
    assert "description" in service
    assert "framework" in service
    assert isinstance(service["name"], str)
    assert isinstance(service["version"], str)
    assert isinstance(service["description"], str)
    assert isinstance(service["framework"], str)

    system = data["system"]
    assert "hostname" in system
    assert "platform" in system
    assert "platform_version" in system
    assert "architecture" in system
    assert "cpu_count" in system
    assert "python_version" in system

    runtime = data["runtime"]
    assert "uptime_seconds" in runtime
    assert "uptime_human" in runtime
    assert "current_time" in runtime
    assert "timezone" in runtime
    assert isinstance(runtime["timezone"], str)

    request = data["request"]
    assert "client_ip" in request
    assert "user_agent" in request
    assert "method" in request
    assert "path" in request

    endpoints = data["endpoints"]
    assert isinstance(endpoints, list)
    assert len(endpoints) == 3
    for i in range(3):
        assert "path" in endpoints[i]
        assert "method" in endpoints[i]
        assert "description" in endpoints[i]
        assert isinstance(endpoints[i]["path"], str)
        assert isinstance(endpoints[i]["method"], str)
        assert isinstance(endpoints[i]["description"], str)


def test_error_404():
    # Test error 404 response
    client = app.test_client()
    response = client.get('/nonexistingpath')

    assert response.status_code == 404
    
    data = response.get_json()
    assert "error" in data
    assert "message" in data
    assert isinstance(data["error"], str)
    assert isinstance(data["message"], str)