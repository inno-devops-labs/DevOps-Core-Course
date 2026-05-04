import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_root_ok_and_structure(client):
    r = client.get("/")
    assert r.status_code == 200

    data = r.get_json()
    assert isinstance(data, dict)

    # service
    assert "service" in data
    assert data["service"]["framework"] == "Flask"

    # system
    assert "system" in data
    assert "hostname" in data["system"]
    assert "python_version" in data["system"]

    # runtime
    assert "runtime" in data
    assert "uptime_seconds" in data["runtime"]
    assert "current_time" in data["runtime"]

    # endpoints
    assert "endpoints" in data
    assert isinstance(data["endpoints"], list)


def test_health_ok_and_structure(client):
    r = client.get("/health")
    assert r.status_code == 200

    data = r.get_json()
    assert isinstance(data, dict)
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "uptime_seconds" in data


def test_404_json(client):
    r = client.get("/nope")
    assert r.status_code == 404
    data = r.get_json()
    assert data["error"] == "Not Found"