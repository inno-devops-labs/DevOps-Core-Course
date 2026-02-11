import re

import pytest

from app import app as flask_app


@pytest.fixture()
def client():
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as c:
        yield c


def test_root_ok_json_shape(client):
    resp = client.get("/")
    assert resp.status_code == 200

    data = resp.get_json()
    assert isinstance(data, dict)

    # top-level keys
    for key in ("service", "system", "runtime", "request", "endpoints"):
        assert key in data

    # service
    assert isinstance(data["service"]["name"], str)
    assert isinstance(data["service"]["version"], str)
    assert isinstance(data["service"]["description"], str)
    assert data["service"]["framework"] == "Flask"

    # runtime
    assert isinstance(data["runtime"]["uptime_seconds"], int)
    assert isinstance(data["runtime"]["uptime_human"], str)
    assert isinstance(data["runtime"]["current_time"], str)
    assert data["runtime"]["timezone"] == "UTC"

    # endpoints list
    assert isinstance(data["endpoints"], list)
    paths = {e["path"] for e in data["endpoints"]}
    assert "/" in paths
    assert "/health" in paths


def test_root_respects_x_forwarded_for(client):
    resp = client.get("/", headers={"X-Forwarded-For": "203.0.113.10"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["request"]["client_ip"] == "203.0.113.10"


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["status"] == "healthy"
    assert isinstance(data["uptime_seconds"], int)
    assert isinstance(data["timestamp"], str)

    # basic ISO-ish sanity check: ends with Z
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
