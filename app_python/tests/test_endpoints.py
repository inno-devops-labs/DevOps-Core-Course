import re
import tempfile
from pathlib import Path

import pytest

import app as app_module


@pytest.fixture()
def client():
    with tempfile.TemporaryDirectory() as temp_dir:
        app_module.VISITS_FILE = str(Path(temp_dir) / "visits")
        app_module.app.config.update(TESTING=True)
        with app_module.app.test_client() as c:
            yield c


def test_root_ok_json_shape(client):
    resp = client.get("/")
    assert resp.status_code == 200

    data = resp.get_json()
    assert isinstance(data, dict)

    for key in ("service", "system", "runtime", "request", "endpoints", "visits"):
        assert key in data

    assert isinstance(data["service"]["name"], str)
    assert isinstance(data["service"]["version"], str)
    assert isinstance(data["service"]["description"], str)
    assert data["service"]["framework"] == "Flask"

    assert isinstance(data["runtime"]["uptime_seconds"], int)
    assert isinstance(data["runtime"]["uptime_human"], str)
    assert isinstance(data["runtime"]["current_time"], str)
    assert data["runtime"]["timezone"] == "UTC"

    assert isinstance(data["endpoints"], list)
    paths = {e["path"] for e in data["endpoints"]}
    assert "/" in paths
    assert "/health" in paths
    assert "/visits" in paths


def test_root_respects_x_forwarded_for(client):
    resp = client.get("/", headers={"X-Forwarded-For": "203.0.113.10"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["request"]["client_ip"] == "203.0.113.10"


def test_visits_counter_increments_and_reads(client):
    first = client.get("/")
    assert first.status_code == 200
    assert first.get_json()["visits"]["count"] == 1

    second = client.get("/")
    assert second.status_code == 200
    assert second.get_json()["visits"]["count"] == 2

    visits_resp = client.get("/visits")
    assert visits_resp.status_code == 200
    assert visits_resp.get_json()["visits"] == 2


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["status"] == "healthy"
    assert isinstance(data["uptime_seconds"], int)
    assert isinstance(data["timestamp"], str)

    assert data["timestamp"].endswith("Z")
    assert re.match(r".+T.+\.\d{3}Z$", data["timestamp"])


def test_not_found_has_json_body(client):
    resp = client.get("/no-such-endpoint")
    assert resp.status_code == 404

    data = resp.get_json()
    assert data["error"] == "Not Found"
    assert isinstance(data["message"], str)


def test_method_not_allowed(client):
    resp = client.post("/health")
    assert resp.status_code == 405
