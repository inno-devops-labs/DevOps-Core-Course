import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_root_status_code():
    response = client.get("/")
    assert response.status_code == 200


def test_root_has_all_top_level_keys():
    response = client.get("/")
    data = response.json()
    assert "service" in data
    assert "system" in data
    assert "runtime" in data
    assert "request" in data
    assert "endpoints" in data


def test_root_service_fields():
    data = client.get("/").json()["service"]
    assert data["name"] == "devops-info-service"
    assert data["version"] == "1.0.0"
    assert data["description"] == "DevOps course info service"
    assert data["framework"] == "FastAPI"


def test_root_system_fields():
    data = client.get("/").json()["system"]
    assert isinstance(data["hostname"], str)
    assert len(data["hostname"]) > 0
    assert isinstance(data["platform"], str)
    assert isinstance(data["platform_version"], str)
    assert isinstance(data["architecture"], str)
    assert isinstance(data["cpu_count"], int)
    assert data["cpu_count"] > 0
    assert isinstance(data["python_version"], str)


def test_root_runtime_fields():
    data = client.get("/").json()["runtime"]
    assert isinstance(data["uptime_seconds"], int)
    assert data["uptime_seconds"] >= 0
    assert isinstance(data["uptime_human"], str)
    assert isinstance(data["current_time"], str)
    assert data["timezone"] == "UTC"


def test_root_request_fields():
    data = client.get("/").json()["request"]
    assert isinstance(data["client_ip"], str)
    assert isinstance(data["user_agent"], str)
    assert data["method"] == "GET"
    assert data["path"] == "/"


def test_root_endpoints_list():
    data = client.get("/").json()["endpoints"]
    assert isinstance(data, list)
    assert len(data) >= 3
    paths = [e["path"] for e in data]
    assert "/" in paths
    assert "/health" in paths
    assert "/visits" in paths


def test_root_endpoint_entries_have_required_fields():
    data = client.get("/").json()["endpoints"]
    for endpoint in data:
        assert "path" in endpoint
        assert "method" in endpoint
        assert "description" in endpoint


def test_root_content_type():
    response = client.get("/")
    assert response.headers["content-type"] == "application/json"
