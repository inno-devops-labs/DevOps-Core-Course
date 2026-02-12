import pytest

from app import app as flask_app


@pytest.fixture()
def client():
    flask_app.config.update({"TESTING": True})
    with flask_app.test_client() as client:
        yield client


def test_index_ok(client):
    headers = {"User-Agent": "pytest", "X-Forwarded-For": "1.2.3.4"}
    resp = client.get("/", headers=headers)

    assert resp.status_code == 200
    data = resp.get_json()

    assert set(data.keys()) == {"service", "system", "runtime", "request", "endpoints"}
    assert data["service"]["name"] == "devops-info-service"
    assert data["service"]["framework"] == "Flask"

    assert isinstance(data["system"]["cpu_count"], int)
    assert isinstance(data["runtime"]["uptime_seconds"], int)
    assert data["runtime"]["timezone"] == "UTC"

    assert data["request"]["method"] == "GET"
    assert data["request"]["path"] == "/"
    assert data["request"]["user_agent"] == "pytest"
    assert data["request"]["client_ip"] == "1.2.3.4"

    endpoints = {(e["path"], e["method"]) for e in data["endpoints"]}
    assert ("/", "GET") in endpoints
    assert ("/health", "GET") in endpoints


def test_health_ok(client):
    resp = client.get("/health")

    assert resp.status_code == 200
    data = resp.get_json()

    assert data["status"] == "healthy"
    assert isinstance(data["uptime_seconds"], int)
    assert isinstance(data["timestamp"], str)
    assert data["timestamp"].endswith("Z")


def test_404(client):
    resp = client.get("/no-such-endpoint")

    assert resp.status_code == 404
    data = resp.get_json()

    assert data["error"] == "Not Found"
    assert "message" in data


def test_500_error_handler(monkeypatch):
    flask_app.config.update({"TESTING": False, "PROPAGATE_EXCEPTIONS": False})

    import app as app_module

    def boom():
        raise RuntimeError("boom")

    monkeypatch.setattr(app_module, "get_uptime_seconds", boom)

    with flask_app.test_client() as client:
        resp = client.get("/health")

    assert resp.status_code == 500
    data = resp.get_json()
    assert data["error"] == "Internal Server Error"