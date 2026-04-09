# app_python/tests/test_app.py
import re
import pytest
import app as app_module
from app import app


def _crash():
    """Test-only endpoint to trigger 500."""
    1 / 0


if "__test_crash__" not in app.view_functions:
    app.add_url_rule(
        "/__test__/crash",
        endpoint="__test_crash__",
        view_func=_crash,
        methods=["GET"],
    )


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """
    Flask test client (no real server).
    Important: disable exception propagation so errorhandler(500)
    returns JSON instead of raising.
    """

    monkeypatch.setattr(app_module, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(
        app_module,
        "VISITS_FILE",
        str(tmp_path / "visits"),
    )

    app.config["TESTING"] = True
    app.config["PROPAGATE_EXCEPTIONS"] = False

    with app.test_client() as c:
        yield c


def test_index_payload_structure(client):
    """GET / returns service + system + runtime + request + endpoints."""
    resp = client.get("/")
    assert resp.status_code == 200

    data = resp.get_json()
    assert isinstance(data, dict)

    # Root keys
    for key in ("service", "system", "runtime", "request", "endpoints"):
        assert key in data

    # Service section
    assert data["service"]["name"] == "devops-info-service"
    assert "version" in data["service"]
    assert isinstance(data["service"]["version"], str)

    # System section
    assert isinstance(data["system"]["hostname"], str)
    assert isinstance(data["system"]["python_version"], str)

    # Runtime section
    # values change over time => check type/range, not equality)
    assert isinstance(data["runtime"]["uptime_seconds"], int)
    assert data["runtime"]["uptime_seconds"] >= 0
    assert isinstance(data["runtime"]["current_time"], str)
    assert data["runtime"]["timezone"] == "UTC"

    # Endpoints list contains / and /health
    endpoints = data["endpoints"]
    assert isinstance(endpoints, list)
    paths = {e["path"] for e in endpoints}
    assert "/" in paths
    assert "/health" in paths


def test_health_payload(client):
    """GET /health returns healthy + timestamp + uptime."""
    resp = client.get("/health")
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["status"] == "healthy"

    assert isinstance(data["uptime_seconds"], int)
    assert data["uptime_seconds"] >= 0

    assert isinstance(data["timestamp"], str)
    # ISO-like UTC format: 2026-02-10T12:34:56Z
    assert re.match(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", data["timestamp"]
    )


def test_unknown_route_returns_404_json(client):
    """GET unknown path returns JSON error via 404 handler."""
    resp = client.get("/no-such-endpoint")
    assert resp.status_code == 404

    data = resp.get_json()
    assert data == {
        "error": "Not Found",
        "message": "Endpoint does not exist",
    }


def test_x_forwarded_for_sets_client_ip(client):
    """X-Forwarded-For first IP should be used as client_ip."""
    resp = client.get(
        "/",
        headers={"X-Forwarded-For": "203.0.113.10, 10.0.0.1"})
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["request"]["client_ip"] == "203.0.113.10"


def test_method_not_allowed_returns_405(client):
    """POST /health should be rejected (only GET is allowed)."""
    resp = client.post("/health")
    assert resp.status_code == 405


def test_500_handler_returns_json(client):
    """
    Internal error returns JSON via 500 handler
    (triggered by test-only endpoint).
    """
    resp = client.get("/__test__/crash")
    assert resp.status_code == 500

    data = resp.get_json()
    assert data == {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
    }
