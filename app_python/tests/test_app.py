import re
import pytest
import app as app_module  # app.py
from app import app as flask_app


@pytest.fixture
def isolated_counter(tmp_path, monkeypatch):
    visits_file = tmp_path / "visits"
    monkeypatch.setattr(app_module, "VISITS_FILE", visits_file)
    monkeypatch.setattr(app_module, "visit_counter", app_module.VisitCounter(visits_file))
    return visits_file


@pytest.fixture
def client(isolated_counter):
    # Standard test client setup
    flask_app.config.update(
        TESTING=True,
    )
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def client_no_propagate(isolated_counter):
    """
    Flask in TESTING mode often propagates exceptions instead of invoking error handlers.
    This fixture ensures our 500 handler is actually returned as JSON.
    """
    flask_app.config.update(
        TESTING=True,
        PROPAGATE_EXCEPTIONS=False,
    )
    with flask_app.test_client() as client:
        yield client


ISO_8601_UTC_REGEX = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?\+00:00$"
)


def test_get_root_returns_expected_json_structure(client):
    resp = client.get("/", headers={"User-Agent": "pytest-agent"})
    assert resp.status_code == 200
    assert resp.is_json

    data = resp.get_json()

    # Top-level keys
    for key in ("service", "system", "runtime", "request", "endpoints"):
        assert key in data
    assert data["visits"] == 1

    # service block
    service = data["service"]
    assert service["name"] == "devops-info-service"
    assert service["framework"] == "Flask"
    assert isinstance(service["version"], str)
    assert isinstance(service["description"], str)
    assert isinstance(service["visits_file"], str) and service["visits_file"]

    # system block (types + presence)
    system = data["system"]
    assert isinstance(system["hostname"], str) and system["hostname"]
    assert isinstance(system["platform"], str) and system["platform"]
    assert isinstance(system["platform_version"], str)
    assert isinstance(system["architecture"], str) and system["architecture"]
    assert isinstance(system["cpu_count"], int) and system["cpu_count"] >= 1
    assert isinstance(system["python_version"], str) and system["python_version"]

    # runtime block
    runtime = data["runtime"]
    assert isinstance(runtime["uptime_seconds"], int) and runtime["uptime_seconds"] >= 0
    assert isinstance(runtime["uptime_human"], str) and runtime["uptime_human"]
    assert isinstance(runtime["current_time"], str)
    assert ISO_8601_UTC_REGEX.match(runtime["current_time"])
    assert runtime["timezone"] == "UTC"

    # request block
    req = data["request"]
    assert req["method"] == "GET"
    assert req["path"] == "/"
    assert isinstance(req["client_ip"], str) and req["client_ip"]
    assert req["user_agent"] == "pytest-agent"

    # endpoints list contains both entries
    endpoints = data["endpoints"]
    assert isinstance(endpoints, list)
    paths = {(e["path"], e["method"]) for e in endpoints}
    assert ("/", "GET") in paths
    assert ("/health", "GET") in paths
    assert ("/visits", "GET") in paths


def test_root_uses_x_forwarded_for_as_client_ip(client):
    resp = client.get(
        "/",
        headers={
            "X-Forwarded-For": "203.0.113.10",
            "User-Agent": "pytest-agent",
        },
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["request"]["client_ip"] == "203.0.113.10"


def test_get_health_returns_expected_payload(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.is_json

    data = resp.get_json()
    assert data["status"] == "healthy"
    assert isinstance(data["uptime_seconds"], int) and data["uptime_seconds"] >= 0
    assert isinstance(data["timestamp"], str)
    assert ISO_8601_UTC_REGEX.match(data["timestamp"])


def test_visits_endpoint_returns_current_counter(client):
    client.get("/")
    client.get("/")

    resp = client.get("/visits")
    assert resp.status_code == 200
    assert resp.is_json

    data = resp.get_json()
    assert data["visits"] >= 2
    assert isinstance(data["visits_file"], str) and data["visits_file"]


def test_visits_counter_persists_to_file(tmp_path, client, monkeypatch):
    visits_file = tmp_path / "visits"
    monkeypatch.setattr(app_module, "VISITS_FILE", visits_file)
    monkeypatch.setattr(app_module, "visit_counter", app_module.VisitCounter(visits_file))

    client.get("/")
    client.get("/")

    assert visits_file.read_text(encoding="utf-8").strip() == "2"
    assert app_module.visit_counter.get() == 2


def test_404_returns_json_error_payload(client):
    resp = client.get("/does-not-exist")
    assert resp.status_code == 404
    assert resp.is_json

    data = resp.get_json()
    assert data["error"] == "Not Found"
    assert data["message"] == "Endpoint does not exist"


def test_500_returns_json_error_payload_when_exception_occurs(client_no_propagate, monkeypatch):
    # Force an exception during GET / by breaking get_system_info
    monkeypatch.setattr(app_module, "get_system_info", lambda: 1 / 0)

    resp = client_no_propagate.get("/")
    assert resp.status_code == 500
    assert resp.is_json

    data = resp.get_json()
    assert data["error"] == "Internal Server Error"
    assert data["message"] == "An unexpected error occurred"
