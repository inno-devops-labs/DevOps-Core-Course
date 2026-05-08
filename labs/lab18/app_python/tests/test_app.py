from fastapi.testclient import TestClient
import pytest

import app as app_module

from app import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_visits_file(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "VISITS_FILE", str(tmp_path / "visits"))


def test_visits_counter_persists_in_file():
    visits_file = app_module.VISITS_FILE

    first = client.get("/")
    second = client.get("/")
    visits = client.get("/visits")

    assert first.status_code == 200
    assert second.status_code == 200
    assert visits.status_code == 200
    assert visits.json()["visits"] == 2

    with open(visits_file, "r", encoding="utf-8") as fh:
        assert fh.read().strip() == "2"


def test_root_returns_expected_structure():
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["service"]["name"] == "devops-info-service"
    assert data["service"]["framework"] == "FastAPI"
    assert data["request"]["path"] == "/"
    assert isinstance(data["runtime"]["uptime_seconds"], int)

    endpoints = {item["path"] for item in data["endpoints"]}
    assert "/" in endpoints
    assert "/health" in endpoints
    assert "/visits" in endpoints


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert isinstance(data["uptime_seconds"], int)


def test_not_found_handler():
    response = client.get("/missing")
    assert response.status_code == 404

    data = response.json()
    assert data["error"] == "Not Found"
    assert data["path"] == "/missing"
