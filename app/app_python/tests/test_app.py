from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import app as app_module
import pytest


@pytest.fixture()
def client():
    fixture_dir = Path(__file__).resolve().parent / f".testdata-{uuid.uuid4().hex}"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    visits_file = fixture_dir / "visits"
    config_file = fixture_dir / "config.json"
    config_file.write_text(
        (
            '{"applicationName":"devops-info-service","environment":"test",'
            '"featureFlags":{"visitsCounter":true},"settings":{"logLevel":"debug"}}'
        ),
        encoding="utf-8",
    )

    app_module.app.config.update(TESTING=True, PROPAGATE_EXCEPTIONS=False)
    app_module.app.config["VISITS_FILE_PATH"] = str(visits_file)
    app_module.app.config["APP_CONFIG_PATH"] = str(config_file)
    app_module.initialize_visit_counter()

    with app_module.app.test_client() as test_client:
        yield test_client

    app_module.app.config.pop("VISITS_FILE_PATH", None)
    app_module.app.config.pop("APP_CONFIG_PATH", None)
    shutil.rmtree(fixture_dir, ignore_errors=True)


def test_index_returns_required_json_structure(client):
    response = client.get(
        "/",
        headers={
            "User-Agent": "pytest-client",
            "X-Forwarded-For": "203.0.113.10, 10.0.0.1",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()

    assert isinstance(payload, dict)
    assert {"service", "system", "runtime", "request", "endpoints", "visits", "configuration"}.issubset(payload.keys())

    assert payload["service"]["name"] == "devops-info-service"
    assert payload["service"]["environment"] == "test"
    assert payload["request"]["client_ip"] == "203.0.113.10"
    assert payload["request"]["user_agent"] == "pytest-client"
    assert payload["request"]["method"] == "GET"
    assert payload["request"]["path"] == "/"
    assert isinstance(payload["endpoints"], list)
    assert payload["visits"]["count"] == 1
    assert payload["configuration"]["environment"] == "test"


def test_health_returns_healthy_status(client):
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.get_json()

    assert payload["status"] == "healthy"
    assert isinstance(payload["timestamp"], str)
    assert payload["timestamp"].endswith("Z")
    assert isinstance(payload["uptime_seconds"], int)
    assert payload["uptime_seconds"] >= 0


def test_visits_counter_persists_in_file(client):
    client.get("/")
    client.get("/")
    visits_response = client.get("/visits")

    assert visits_response.status_code == 200
    assert visits_response.get_json()["count"] == 2


def test_metrics_endpoint_exposes_prometheus_metrics(client):
    client.get("/")
    response = client.get("/metrics")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "devops_info_http_requests_total" in body
    assert "devops_info_visits_total" in body
    assert "devops_info_uptime_seconds" in body


def test_not_found_returns_404_json(client):
    response = client.get("/missing")

    assert response.status_code == 404
    payload = response.get_json()
    assert payload == {
        "error": "Not Found",
        "message": "Endpoint does not exist",
    }


def test_internal_server_error_returns_500_json(client, monkeypatch):
    def boom():
        raise RuntimeError("forced failure")

    monkeypatch.setattr(app_module, "get_service_info", boom)

    response = client.get("/")

    assert response.status_code == 500
    payload = response.get_json()
    assert payload == {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
    }
