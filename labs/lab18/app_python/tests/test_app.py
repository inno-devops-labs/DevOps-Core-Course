from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_root_ok_structure():
    r = client.get("/", headers={"user-agent": "pytest"})
    assert r.status_code == 200
    data = r.json()

    # top-level keys
    for key in ("service", "system", "runtime", "request", "endpoints"):
        assert key in data

    # service section
    assert "name" in data["service"]
    assert "version" in data["service"]
    assert "framework" in data["service"]

    # system section (values depend on runner, so only validate presence/types)
    assert "hostname" in data["system"]
    assert "cpu_count" in data["system"]
    assert isinstance(data["system"]["cpu_count"], int)

    # runtime section
    assert "uptime_seconds" in data["runtime"]
    assert isinstance(data["runtime"]["uptime_seconds"], int)
    assert "current_time" in data["runtime"]
    assert data["runtime"]["timezone"] == "UTC"

    # request section
    assert data["request"]["path"] == "/"
    assert data["request"]["method"] == "GET"


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "uptime_seconds" in data
    assert isinstance(data["uptime_seconds"], int)


def test_404_returns_json_message():
    r = client.get("/no-such-endpoint")
    assert r.status_code == 404
    data = r.json()
    assert "message" in data
