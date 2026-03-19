from __future__ import annotations

import app as app_module
import pytest


@pytest.fixture()
def client():
    app_module.app.config.update(TESTING=True, PROPAGATE_EXCEPTIONS=False)
    with app_module.app.test_client() as test_client:
        yield test_client


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
    assert {"service", "system", "runtime", "request", "endpoints"}.issubset(payload.keys())

    assert payload["service"]["name"] == "devops-info-service"
    assert payload["request"]["client_ip"] == "203.0.113.10"
    assert payload["request"]["user_agent"] == "pytest-client"
    assert payload["request"]["method"] == "GET"
    assert payload["request"]["path"] == "/"
    assert isinstance(payload["endpoints"], list)


def test_health_returns_healthy_status(client):
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.get_json()

    assert payload["status"] == "healthy"
    assert isinstance(payload["timestamp"], str)
    assert payload["timestamp"].endswith("Z")
    assert isinstance(payload["uptime_seconds"], int)
    assert payload["uptime_seconds"] >= 0


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


def test_metrics_endpoint_exposes_prometheus_metrics(client):
    # Generate some traffic to populate metric series.
    client.get("/")
    client.get("/health")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.content_type.startswith("text/plain")

    body = response.get_data(as_text=True)
    assert "http_requests_total" in body
    assert "http_request_duration_seconds_bucket" in body
    assert "http_requests_in_progress" in body
    assert "devops_info_endpoint_calls_total" in body
    assert "devops_info_system_collection_seconds_bucket" in body
