import pytest

from app import app


@pytest.fixture()
def client():
    app.config.update({"TESTING": True})
    with app.test_client() as client:
        yield client


def test_root_returns_expected_structure(client):
    res = client.get("/", headers={"User-Agent": "pytest"})
    assert res.status_code == 200

    data = res.get_json()
    assert isinstance(data, dict)

    # Top-level keys
    for key in ("service", "system", "runtime", "request", "endpoints"):
        assert key in data

    # Service keys
    for key in ("name", "version", "description", "framework"):
        assert key in data["service"]

    # System keys
    for key in ("hostname", "platform", "architecture", "cpu_count", "python_version"):
        assert key in data["system"]

    assert isinstance(data["system"]["cpu_count"], int)

    # Runtime keys
    for key in ("uptime_seconds", "uptime_human", "current_time", "timezone"):
        assert key in data["runtime"]
    assert isinstance(data["runtime"]["uptime_seconds"], int)

    # Request keys
    for key in ("client_ip", "user_agent", "method", "path"):
        assert key in data["request"]
    assert data["request"]["method"] == "GET"
    assert data["request"]["path"] == "/"


def test_health_returns_healthy(client):
    res = client.get("/health")
    assert res.status_code == 200

    data = res.get_json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert isinstance(data["uptime_seconds"], int)


def test_404_returns_json_error(client):
    res = client.get("/no-such-endpoint")
    assert res.status_code == 404

    data = res.get_json()
    assert "error" in data
