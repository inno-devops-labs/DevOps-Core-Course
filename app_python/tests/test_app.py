from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

import pytest
import app

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture()
def client():
    app.app.config.update({"TESTING": True})
    with app.app.test_client() as client:
        yield client


def test_index_success_structure(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.get_json()

    assert set(data.keys()) == {"service", "system", "runtime", "request", "endpoints"}

    service = data["service"]
    assert service["name"] == app.APP_NAME
    assert service["version"] == app.APP_VERSION
    assert service["description"] == app.APP_DESCRIPTION
    assert service["framework"] == app.FRAMEWORK

    system = data["system"]
    assert "hostname" in system
    assert "platform" in system
    assert "platform_version" in system
    assert "architecture" in system
    assert isinstance(system.get("cpu_count"), int)
    assert "python_version" in system

    runtime = data["runtime"]
    assert isinstance(runtime.get("uptime_seconds"), int)
    assert "uptime_human" in runtime
    assert "current_time" in runtime
    assert "timezone" in runtime
    # Validate current_time is ISO-like
    datetime.fromisoformat(runtime["current_time"].replace("Z", "+00:00"))

    request_info = data["request"]
    assert request_info["method"] == "GET"
    assert request_info["path"] == "/"
    assert "client_ip" in request_info
    assert "user_agent" in request_info

    endpoints = data["endpoints"]
    assert isinstance(endpoints, list)
    paths_methods = {(item.get("path"), item.get("method")) for item in endpoints}
    assert ("/", "GET") in paths_methods
    assert ("/health", "GET") in paths_methods


def test_health_success(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()

    assert data["status"] == "healthy"
    assert isinstance(data.get("uptime_seconds"), int)
    datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))


def test_not_found(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    data = response.get_json()
    assert data == {"error": "Not Found", "message": "Endpoint does not exist"}


def test_internal_server_error(monkeypatch):
    def boom():
        raise RuntimeError("boom")

    monkeypatch.setattr(app, "get_system_info", boom)
    original_testing = app.app.config.get("TESTING")
    original_propagate = app.app.config.get("PROPAGATE_EXCEPTIONS")
    app.app.config.update({"TESTING": False, "PROPAGATE_EXCEPTIONS": False})

    try:
        with app.app.test_client() as client:
            response = client.get("/")
    finally:
        app.app.config.update(
            {"TESTING": original_testing, "PROPAGATE_EXCEPTIONS": original_propagate}
        )

    assert response.status_code == 500
    data = response.get_json()
    assert data == {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
    }
