from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_root_status_code():
    response = client.get("/")
    assert response.status_code == 200


def test_root_structure():
    response = client.get("/")
    data = response.json()

    # Top-level keys
    assert "service" in data
    assert "system" in data
    assert "runtime" in data
    assert "request" in data
    assert "endpoints" in data


def test_service_info_fields():
    response = client.get("/")
    service = response.json()["service"]

    required_fields = ["name", "version", "description", "framework"]
    for field in required_fields:
        assert field in service
        assert isinstance(service[field], str)


def test_system_info_fields():
    response = client.get("/")
    system = response.json()["system"]

    required_fields = [
        "hostname",
        "platform",
        "platform_version",
        "architecture",
        "cpu_count",
        "python_version",
    ]

    for field in required_fields:
        assert field in system

    assert isinstance(system["cpu_count"], (int, type(None)))


def test_runtime_info_fields():
    response = client.get("/")
    runtime = response.json()["runtime"]

    required_fields = [
        "uptime_seconds",
        "uptime_human",
        "current_time",
        "timezone",
    ]

    for field in required_fields:
        assert field in runtime

    assert isinstance(runtime["uptime_seconds"], int)
    assert runtime["uptime_seconds"] >= 0


def test_request_info_fields():
    response = client.get("/")
    request_info = response.json()["request"]

    required_fields = ["client_ip", "user_agent", "method", "path"]
    for field in required_fields:
        assert field in request_info

    assert request_info["method"] == "GET"
    assert request_info["path"] == "/"


def test_endpoints_info():
    response = client.get("/")
    endpoints = response.json()["endpoints"]

    assert isinstance(endpoints, list)
    assert len(endpoints) >= 2

    paths = [endpoint["path"] for endpoint in endpoints]
    assert "/" in paths
    assert "/health" in paths
