


import pytest

import app as app_module


@pytest.fixture()
def client():
    """Create a Flask test client."""
    flask_app = app_module.app
    flask_app.testing = True  # Enable testing mode
    return flask_app.test_client()


def test_root_returns_expected_json_structure(client):
    """GET / should return a JSON payload with required sections and endpoint list."""
    resp = client.get("/", headers={"User-Agent": "pytest"})
    assert resp.status_code == 200

    data = resp.get_json()
    assert isinstance(data, dict)

    # Top-level keys
    for key in ("service", "system", "runtime", "request", "endpoints"):
        assert key in data, f"Missing key: {key}"

    # Service metadata
    assert data["service"]["name"], "service.name must be non-empty"
    assert data["service"]["version"], "service.version must be non-empty"

    # Endpoints list should contain at least / and /health
    endpoints = data["endpoints"]
    assert isinstance(endpoints, list)
    paths = {e.get("path") for e in endpoints if isinstance(e, dict)}
    assert "/" in paths
    assert "/health" in paths


def test_healthcheck_is_healthy(client):
    """GET /health should return healthy + timestamp + uptime_seconds."""
    resp = client.get("/health")
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "uptime_seconds" in data
    assert isinstance(data["uptime_seconds"], int)
    assert data["uptime_seconds"] >= 0


def test_404_returns_json_error(client):
    """Unknown endpoints should return JSON 404 (not HTML)."""
    resp = client.get("/does-not-exist")
    assert resp.status_code == 404

    data = resp.get_json()
    assert isinstance(data, dict)
    assert "error" in data
    assert "message" in data
