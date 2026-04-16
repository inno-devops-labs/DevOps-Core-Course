from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import app as app_module  # noqa: E402


client = TestClient(app_module.app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def isolated_visits_file(tmp_path, monkeypatch):
    visits_path = tmp_path / "visits"
    monkeypatch.setattr(app_module, "VISITS_FILE", str(visits_path))
    yield


def test_root_returns_expected_structure():
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()

    required_top = {"service", "system", "runtime", "request", "endpoints", "visits"}
    assert required_top.issubset(payload.keys())
    assert isinstance(payload["visits"], int)

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
    assert {"/", "/health", "/visits"}.issubset(endpoint_paths)


def test_visits_endpoint_tracks_root_calls_and_is_persistent_in_file():
    response = client.get("/visits")
    assert response.status_code == 200
    assert response.json() == {"visits": 0}

    first = client.get("/")
    second = client.get("/")
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["visits"] == 1
    assert second.json()["visits"] == 2

    visits = client.get("/visits")
    assert visits.status_code == 200
    assert visits.json() == {"visits": 2}

    visits_file = Path(app_module.VISITS_FILE)
    assert visits_file.exists()
    assert visits_file.read_text(encoding="utf-8").strip() == "2"


def test_visits_endpoint_does_not_increment_counter():
    client.get("/")
    response_one = client.get("/visits")
    response_two = client.get("/visits")

    assert response_one.status_code == 200
    assert response_two.status_code == 200
    assert response_one.json() == {"visits": 1}
    assert response_two.json() == {"visits": 1}


def test_visits_endpoint_returns_zero_for_invalid_file_content():
    Path(app_module.VISITS_FILE).write_text("invalid-counter", encoding="utf-8")
    response = client.get("/visits")
    assert response.status_code == 200
    assert response.json() == {"visits": 0}


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
