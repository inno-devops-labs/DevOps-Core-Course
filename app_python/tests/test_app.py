import json
from datetime import datetime

import pytest

import app as app_module
from app import app


@pytest.fixture()
def client():
    app.testing = True
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def isolate_visits_file(tmp_path, monkeypatch):
    visits_file = tmp_path / "visits"
    monkeypatch.setattr(app_module, "VISITS_FILE", str(visits_file))
    monkeypatch.setattr(app_module, "VISITS_LOCK_FILE", f"{visits_file}.lock")


def assert_iso8601(timestamp: str) -> None:
    """Basic check that a string looks like ISO 8601."""
    # Will raise ValueError if format is invalid
    datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


def test_index_success_response_structure(client):
    response = client.get(
        "/",
        headers={"User-Agent": "pytest-client"},
        environ_overrides={"REMOTE_ADDR": "127.0.0.1"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)

    # Top-level keys
    for key in (
        "service",
        "system",
        "runtime",
        "request",
        "visits",
        "endpoints",
    ):
        assert key in data

    # Service info
    service = data["service"]
    for key in ("name", "version", "description", "framework"):
        assert key in service
        assert isinstance(service[key], str)

    # System info
    system = data["system"]
    for key in (
        "hostname",
        "platform",
        "platform_version",
        "architecture",
        "cpu_count",
        "python_version",
    ):
        assert key in system

    assert isinstance(system["cpu_count"], int)

    # Runtime info
    runtime = data["runtime"]
    for key in ("uptime_seconds", "uptime_human", "current_time", "timezone"):
        assert key in runtime

    assert isinstance(runtime["uptime_seconds"], int)
    assert isinstance(runtime["uptime_human"], str)
    assert_iso8601(runtime["current_time"])
    assert runtime["timezone"] == "UTC"

    # Request info
    request_info = data["request"]
    assert request_info["client_ip"] == "127.0.0.1"
    assert request_info["user_agent"] == "pytest-client"
    assert request_info["method"] == "GET"
    assert request_info["path"] == "/"

    # Visits info
    visits = data["visits"]
    assert isinstance(visits["count"], int)
    assert visits["count"] == 1

    # Endpoints list
    endpoints = data["endpoints"]
    assert isinstance(endpoints, list)
    assert any(ep["path"] == "/" for ep in endpoints)
    assert any(ep["path"] == "/health" for ep in endpoints)
    assert any(ep["path"] == "/metrics" for ep in endpoints)
    assert any(ep["path"] == "/visits" for ep in endpoints)


def test_index_error_method_not_allowed(client):
    # POST is not defined and should return 405
    response = client.post("/")
    assert response.status_code == 405


def test_health_success_response_structure(client):
    response = client.get("/health")

    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)

    assert data["status"] == "healthy"
    assert isinstance(data["uptime_seconds"], int)
    assert_iso8601(data["timestamp"])


def test_visits_counter_endpoint_returns_current_count(client):
    client.get("/")
    client.get("/")
    response = client.get("/visits")

    assert response.status_code == 200
    data = response.get_json()
    assert data["visits"] == 2


def test_metrics_endpoint_exposes_prometheus_metrics(client):
    # Generate a little traffic first so counters have values
    client.get("/")
    client.get("/health")

    response = client.get("/metrics")
    assert response.status_code == 200

    payload = response.data.decode()
    assert "# HELP http_requests_total" in payload
    assert "# TYPE http_requests_total counter" in payload
    assert "# HELP http_request_duration_seconds" in payload
    assert "# TYPE http_request_duration_seconds histogram" in payload
    assert "# HELP http_requests_in_progress" in payload
    assert "# TYPE http_requests_in_progress gauge" in payload
    assert (
        "http_requests_total{endpoint=\"/\",method=\"GET\","
        "status_code=\"200\"}"
        in payload
    )


def test_not_found_error_handler_returns_json(client):
    response = client.get("/does-not-exist")

    assert response.status_code == 404
    data = response.get_json()
    assert isinstance(data, dict)
    assert data["error"] == "Not Found"
    assert "message" in data


def test_internal_error_handler_returns_json(client, monkeypatch):
    # Force an exception inside the index handler to trigger 500
    def boom():
        raise RuntimeError("boom")

    monkeypatch.setattr("app.get_service_info", lambda: boom())

    # For this test we want the Flask error handler to run,
    # not to propagate the exception to pytest.
    from app import app as flask_app  # local import to avoid circular issues

    flask_app.testing = False
    flask_app.config["PROPAGATE_EXCEPTIONS"] = False

    response = client.get("/")
    assert response.status_code == 500

    data = json.loads(response.data.decode())
    assert data["error"] == "Internal Server Error"
    assert "message" in data
