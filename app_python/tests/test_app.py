from datetime import datetime

from fastapi.testclient import TestClient

import app

client = TestClient(app.app)


def is_iso8601(s: str) -> bool:
    """Простая проверка, что строка парсится datetime.fromisoformat."""
    try:
        datetime.fromisoformat(s)
        return True
    except Exception:
        return False


def test_root_success_structure_and_types():
    resp = client.get("/")
    assert resp.status_code == 200

    data = resp.json()
    for key in ("service", "system", "runtime", "request", "endpoints"):
        assert key in data

    # service
    svc = data["service"]
    for k in ("name", "version", "description", "framework"):
        assert k in svc and isinstance(svc[k], str)

    # system
    system = data["system"]
    assert "hostname" in system and isinstance(system["hostname"], str)
    assert "platform" in system and isinstance(system["platform"], str)
    assert "cpu_count" in system and isinstance(system["cpu_count"], int)

    # runtime
    runtime = data["runtime"]
    assert "uptime_seconds" in runtime and \
        isinstance(runtime["uptime_seconds"], int)
    assert "uptime_human" in runtime and \
        isinstance(runtime["uptime_human"], str)
    assert "current_time" in runtime and \
        is_iso8601(runtime["current_time"])

    # request
    req = data["request"]
    assert "client_ip" in req
    assert "user_agent" in req
    assert req.get("method") == "GET"
    assert req.get("path") == "/"

    # endpoints
    endpoints = data["endpoints"]
    paths = {e.get("path") for e in endpoints if isinstance(e, dict)}
    assert "/" in paths
    assert "/health" in paths


def test_health_success_and_types():
    resp = client.get("/health")
    assert resp.status_code == 200

    data = resp.json()
    assert data.get("status") == "healthy"
    assert "timestamp" in data and is_iso8601(data["timestamp"])
    assert "uptime_seconds" in data and \
        isinstance(data["uptime_seconds"], int)


def test_404_not_found_handler():
    resp = client.get("/endpoint-does-not-exist")
    assert resp.status_code == 404

    data = resp.json()
    assert data.get("error") == "Not Found"
    assert "message" in data
    assert "timestamp" in data and is_iso8601(data["timestamp"])


def test_internal_server_error_handler(monkeypatch):
    def raise_exc():
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(app, "get_service_info", raise_exc)

    client_no_raise = TestClient(app.app, raise_server_exceptions=False)
    resp = client_no_raise.get("/")

    assert resp.status_code == 500

    data = resp.json()
    assert data.get("error") == "Internal Server Error"
    assert data.get("message") == "An unexpected error occurred"
    assert "timestamp" in data and is_iso8601(data["timestamp"])
