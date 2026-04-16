import pytest

import app as app_module
from app import app as flask_app


@pytest.fixture(autouse=True)
def patch_visits(tmp_path, monkeypatch):
    visits_file = str(tmp_path / "visits")
    monkeypatch.setattr(app_module, "VISITS_FILE", visits_file)


@pytest.fixture
def client():
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        yield client


def test_index_structure(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.get_json()
    # top-level keys
    assert "service" in data
    assert "system" in data
    assert "runtime" in data
    assert "request" in data
    assert "endpoints" in data

    # service fields
    svc = data["service"]
    assert isinstance(svc.get("name"), str)
    assert isinstance(svc.get("version"), str)

    # system fields
    sys = data["system"]
    assert "hostname" in sys
    assert "platform" in sys

    # runtime fields
    rt = data["runtime"]
    assert "uptime_seconds" in rt
    assert "current_time" in rt


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("status") == "healthy"
    assert "timestamp" in data
    assert isinstance(data.get("uptime_seconds"), int)


def test_404_error(client):
    resp = client.get("/does/not/exist")
    assert resp.status_code == 404
    data = resp.get_json()
    assert data.get("error") == "Not Found"


def test_visits_endpoint(client):
    resp = client.get("/visits")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "visits" in data
    assert isinstance(data["visits"], int)


def test_visits_increments(client):
    before = client.get("/visits").get_json()["visits"]
    client.get("/")
    after = client.get("/visits").get_json()["visits"]
    assert after == before + 1
