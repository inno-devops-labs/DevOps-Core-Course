from pathlib import Path
import sys

from fastapi.testclient import TestClient

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import app as app_module  # noqa: E402


client = TestClient(app_module.app, raise_server_exceptions=False)


def test_root_returns_expected_structure():
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()

    required_top = {"service", "system", "runtime", "request", "endpoints"}
    assert required_top.issubset(payload.keys())

    service = payload["service"]
    for key in ("name", "version", "description", "framework"):
        assert key in service

    system = payload["system"]
    for key in ("hostname", "platform", "platform_version", "architecture", "cpu_count", "python_version"):
        assert key in system
    assert isinstance(system["cpu_count"], int)

    runtime = payload["runtime"]
    for key in ("uptime_seconds", "uptime_human", "current_time", "timezone"):
        assert key in runtime
    assert isinstance(runtime["uptime_seconds"], int)

    request_info = payload["request"]
    for key in ("client_ip", "user_agent", "method", "path"):
        assert key in request_info

    endpoints = payload["endpoints"]
    assert isinstance(endpoints, list)
    endpoint_paths = {item["path"] for item in endpoints}
    assert {"/", "/health"}.issubset(endpoint_paths)


def test_root_request_metadata_uses_forwarded_for_header():
    response = client.get(
        "/",
        headers={
            "X-Forwarded-For": "203.0.113.7, 10.0.0.2",
            "User-Agent": "pytest-client",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    request_info = payload["request"]

    assert request_info["client_ip"] == "203.0.113.7"
    assert request_info["user_agent"] == "pytest-client"
    assert request_info["method"] == "GET"
    assert request_info["path"] == "/"


def test_health_endpoint_returns_status():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "healthy"
    assert "timestamp" in payload
    assert isinstance(payload["uptime_seconds"], int)


def test_health_returns_500_when_runtime_fails(monkeypatch):
    def _boom():
        raise RuntimeError("uptime failed")

    monkeypatch.setattr(app_module, "get_uptime", _boom)
    response = client.get("/health")
    assert response.status_code == 500
    payload = response.json()

    assert payload["error"] == "Internal Server Error"
    assert payload["message"] == "An unexpected error occurred"


def test_404_returns_expected_payload():
    response = client.get("/missing-endpoint")
    assert response.status_code == 404
    payload = response.json()

    assert payload["error"] == "Not Found"
    assert payload["path"] == "/missing-endpoint"


def test_500_handler_returns_json(monkeypatch):
    def _boom():
        raise RuntimeError("boom")

    monkeypatch.setattr(app_module, "get_system_info", _boom)
    response = client.get("/")
    assert response.status_code == 500
    payload = response.json()

    assert payload["error"] == "Internal Server Error"
    assert payload["message"] == "An unexpected error occurred"
