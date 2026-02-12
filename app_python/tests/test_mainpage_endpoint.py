import re

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_status_code():
    response = client.get("/")
    assert response.status_code == 200


def test_response_structure():
    response = client.get("/")
    assert all(key in response.json() for key in ["service", "system", "runtime", "request", "endpoints"])


def test_service_structure():
    data = client.get("/").json()["service"]
    assert isinstance(data["version"], str)
    assert data["name"] == "devops-info-service"
    assert data["framework"] == "FastAPI"


def test_system_structure():
    response = client.get("/")
    data = response.json()
    system = data["system"]
    expected_fields = {"hostname", "platform_name", "architecture", "python_version"}
    assert expected_fields.issubset(system.keys())

    assert isinstance(system["hostname"], str)
    assert isinstance(system["platform_name"], str)
    assert isinstance(system["architecture"], str)
    assert isinstance(system["python_version"], str)

    assert re.match(r'^\d+\.\d+\.\d+', system["python_version"])


def test_runtime_structure():
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()

    assert "runtime" in data

    runtime = data["runtime"]

    assert "seconds" in runtime
    assert "human" in runtime

    assert isinstance(runtime["seconds"], int)
    assert isinstance(runtime["human"], str)

    assert runtime["seconds"] >= 0

    human = runtime["human"]
    assert "h" in human or "m" in human or "s" in human
    assert any(char.isdigit() for char in human)


def test_request_info_structure():
    response = client.get("/")
    data = response.json()
    request_info = data["request"]
    expected_fields = {"client_ip", "user_agent", "method", "path"}

    assert expected_fields.issubset(request_info.keys())

    assert request_info["method"] == "GET"
    assert request_info["path"] == "/"
    assert isinstance(request_info["client_ip"], str)
    assert request_info["user_agent"] is None or isinstance(request_info["user_agent"], str)


def test_endpoints_list():
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

    endpoint_paths = {(e["path"], e["method"]) for e in endpoints}
    assert ("/", "GET") in endpoint_paths
    assert ("/health", "GET") in endpoint_paths
