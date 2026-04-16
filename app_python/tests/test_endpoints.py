from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

import pytest


# Ensure we can import `app.py` regardless of where pytest is launched from.
APP_PYTHON_DIR = Path(__file__).resolve().parents[1]
if str(APP_PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(APP_PYTHON_DIR))

import app as app_module  # noqa: E402  (import after sys.path tweak)

flask_app = app_module.app


@pytest.fixture(autouse=True)
def tmp_visits_file(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "VISITS_FILE", tmp_path / "visits")


@pytest.fixture()
def client():
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as c:
        yield c


def test_get_root_returns_expected_json_structure(client):
    resp = client.get("/", headers={"User-Agent": "pytest"})
    assert resp.status_code == 200

    data = resp.get_json()
    assert isinstance(data, dict)

    # Top-level keys
    for key in ("service", "system", "runtime", "request", "visits", "endpoints"):
        assert key in data

    # Service info
    service = data["service"]
    assert service["name"] == "devops-info-service"
    assert service["framework"] == "Flask"
    assert "version" in service
    assert "description" in service

    # System info
    system = data["system"]
    for key in (
        "hostname",
        "platform",
        "platform_version",
        "architecture",
        "cpu_count",
        "python_version",
    ):
        assert key in system

    # cpu_count can be None in some environments; if present, it should be positive.
    if system["cpu_count"] is not None:
        assert isinstance(system["cpu_count"], int)
        assert system["cpu_count"] > 0

    # Runtime info
    runtime = data["runtime"]
    assert runtime["timezone"] == "UTC"
    assert isinstance(runtime["uptime_seconds"], int)
    assert runtime["uptime_seconds"] >= 0
    # Validate ISO-8601 timestamp (Python accepts "+00:00" format)
    datetime.fromisoformat(runtime["current_time"])

    # Request info
    req = data["request"]
    assert req["method"] == "GET"
    assert req["path"] == "/"
    assert req["user_agent"] == "pytest"
    assert "client_ip" in req

    visits = data["visits"]
    assert isinstance(visits["count"], int)
    assert visits["count"] >= 1
    assert "file" in visits

    # Endpoints list
    endpoints = data["endpoints"]
    assert isinstance(endpoints, list)
    paths = {e["path"] for e in endpoints}
    assert "/" in paths
    assert "/health" in paths
    assert "/visits" in paths


def test_visits_counter_persists_in_file(client):
    assert client.get("/").get_json()["visits"]["count"] == 1
    assert client.get("/").get_json()["visits"]["count"] == 2
    assert client.get("/visits").get_json()["visits"] == 2
    assert app_module.VISITS_FILE.read_text(encoding="utf-8").strip() == "2"


def test_get_health_returns_healthy_status(client):
    resp = client.get("/health")
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["status"] == "healthy"
    assert isinstance(data["uptime_seconds"], int)
    assert data["uptime_seconds"] >= 0
    datetime.fromisoformat(data["timestamp"])


def test_404_returns_json_error(client):
    resp = client.get("/does-not-exist")
    assert resp.status_code == 404

    data = resp.get_json()
    assert data == {"error": "Not Found", "message": "Endpoint does not exist"}


def test_500_returns_json_error_when_internal_exception(monkeypatch, client):
    # Force an internal error inside the "/" handler
    import app as app_module

    def boom():
        raise RuntimeError("boom")

    monkeypatch.setattr(app_module, "get_system_info", boom)

    # In Flask, TESTING=True makes exceptions propagate (error handlers won't run).
    # For this test we want to assert the JSON 500 handler response, so disable propagation.
    monkeypatch.setitem(flask_app.config, "PROPAGATE_EXCEPTIONS", False)

    resp = client.get("/")
    assert resp.status_code == 500

    data = resp.get_json()
    assert data == {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
    }


