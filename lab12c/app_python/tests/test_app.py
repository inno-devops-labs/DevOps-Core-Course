from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app import _format_uptime, app, get_system_info, get_uptime, isoformat_utc


@pytest.fixture
def client(tmp_path, monkeypatch):
    vf = tmp_path / "visits"
    monkeypatch.setenv("VISITS_FILE", str(vf))
    # Reload app module so VISITS_FILE is picked up
    import importlib

    import app as app_module

    importlib.reload(app_module)
    from app import app as reloaded

    with TestClient(reloaded) as c:
        yield c


def test_root_increments_visits(client):
    r1 = client.get("/")
    assert r1.status_code == 200
    assert r1.json()["visits"]["total"] == 1

    r2 = client.get("/")
    assert r2.json()["visits"]["total"] == 2


def test_visits_read_only(client):
    client.get("/")
    client.get("/")
    r = client.get("/visits")
    assert r.status_code == 200
    assert r.json()["visits"] == 2


def test_root_endpoint_structure(client):
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "service" in data
    assert "system" in data
    assert "runtime" in data
    assert "request" in data
    assert "endpoints" in data
    assert "visits" in data
    assert data["visits"]["total"] >= 1

    service = data["service"]
    assert service["name"] == "devops-info-service"
    assert service["framework"] == "FastAPI"

    system = data["system"]
    for key in [
        "hostname",
        "platform",
        "platform_version",
        "architecture",
        "cpu_count",
        "python_version",
    ]:
        assert key in system

    runtime = data["runtime"]
    assert isinstance(runtime["uptime_seconds"], int)
    assert isinstance(runtime["uptime_human"], str)
    assert runtime["timezone"] == "UTC"


def test_health_endpoint_structure(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert isinstance(data["uptime_seconds"], int)
    assert "timestamp" in data


def test_not_found_returns_json(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "Not Found"


def test_helpers_are_consistent():
    system = get_system_info()
    assert system["hostname"]
    assert system["platform"]
    assert system["python_version"]

    uptime = get_uptime()
    assert uptime["seconds"] >= 0
    assert "hours" in uptime["human"] or "hour" in uptime["human"]


def test_format_and_iso_helpers():
    assert _format_uptime(3660) == "1 hour, 1 minute"
    test_dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert isoformat_utc(test_dt) == "2024-01-01T00:00:00Z"
