from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
import sys

import pytest
import app

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture()
def client(tmp_path):
    app.VISITS_FILE = tmp_path / "visits"
    app.initialize_visits_storage()
    app.app.config.update({"TESTING": True})
    with app.app.test_client() as client:
        yield client


def test_index_success_structure(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.get_json()

    assert set(data.keys()) == {"service", "visits", "system", "runtime", "request", "endpoints"}
    assert isinstance(data["visits"], int)
    assert data["visits"] >= 1

    service = data["service"]
    assert service["name"] == app.APP_NAME
    assert service["version"] == app.APP_VERSION
    assert service["description"] == app.APP_DESCRIPTION
    assert service["framework"] == app.FRAMEWORK

    system = data["system"]
    assert "hostname" in system
    assert "platform" in system
    assert "platform_version" in system
    assert "architecture" in system
    assert isinstance(system.get("cpu_count"), int)
    assert "python_version" in system

    runtime = data["runtime"]
    assert isinstance(runtime.get("uptime_seconds"), int)
    assert "uptime_human" in runtime
    assert "current_time" in runtime
    assert "timezone" in runtime
    # Validate current_time is ISO-like
    datetime.fromisoformat(runtime["current_time"].replace("Z", "+00:00"))

    request_info = data["request"]
    assert request_info["method"] == "GET"
    assert request_info["path"] == "/"
    assert "client_ip" in request_info
    assert "user_agent" in request_info

    endpoints = data["endpoints"]
    assert isinstance(endpoints, list)
    paths_methods = {(item.get("path"), item.get("method")) for item in endpoints}
    assert ("/", "GET") in paths_methods
    assert ("/visits", "GET") in paths_methods
    assert ("/health", "GET") in paths_methods
    assert ("/metrics", "GET") in paths_methods


def test_visits_counter_increments_and_reads_current_value(client):
    first = client.get("/")
    second = client.get("/")
    third = client.get("/visits")

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 200

    first_count = first.get_json()["visits"]
    second_count = second.get_json()["visits"]
    current_count = third.get_json()["visits"]

    assert second_count == first_count + 1
    assert current_count == second_count


def test_health_success(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()

    assert data["status"] == "healthy"
    assert isinstance(data.get("uptime_seconds"), int)
    datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))


def test_metrics_endpoint_exposes_prometheus_metrics(client):
    client.get("/")
    client.get("/health")

    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    assert "http_requests_total" in body
    assert "http_request_duration_seconds" in body
    assert "http_requests_in_progress" in body
    assert "devops_info_endpoint_calls_total" in body
    assert "devops_info_system_collection_seconds" in body


def test_not_found(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    data = response.get_json()
    assert data == {"error": "Not Found", "message": "Endpoint does not exist"}


def test_internal_server_error(monkeypatch):
    def boom():
        raise RuntimeError("boom")

    monkeypatch.setattr(app, "get_system_info", boom)
    original_testing = app.app.config.get("TESTING")
    original_propagate = app.app.config.get("PROPAGATE_EXCEPTIONS")
    app.app.config.update({"TESTING": False, "PROPAGATE_EXCEPTIONS": False})

    try:
        with app.app.test_client() as client:
            response = client.get("/")
    finally:
        app.app.config.update(
            {"TESTING": original_testing, "PROPAGATE_EXCEPTIONS": original_propagate}
        )

    assert response.status_code == 500
    data = response.get_json()
    assert data == {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
    }


def test_json_formatter_outputs_valid_json():
    formatter = app.JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    record.method = "GET"
    record.path = "/health"
    record.status_code = 200
    record.client_ip = "127.0.0.1"

    payload = json.loads(formatter.format(record))
    assert payload["level"] == "INFO"
    assert payload["message"] == "hello"
    assert payload["method"] == "GET"
    assert payload["path"] == "/health"
    assert payload["status_code"] == 200
    assert payload["client_ip"] == "127.0.0.1"
    datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))


def test_setup_logging_emits_startup_event(capsys):
    app.setup_logging()
    captured = capsys.readouterr()
    lines = [line for line in captured.err.splitlines() if line.strip()]
    assert lines

    payload = json.loads(lines[-1])
    assert payload["message"] == "application_startup"
    assert payload["event"] == "startup"
    assert payload["app"] == app.APP_NAME
    assert payload["version"] == app.APP_VERSION


def test_request_completion_log_contains_status_and_path(client, capsys):
    app.setup_logging()
    response = client.get("/health")
    assert response.status_code == 200

    captured = capsys.readouterr()
    lines = [line for line in captured.err.splitlines() if line.strip()]
    assert lines
    parsed = [json.loads(line) for line in lines]
    completion_logs = [line for line in parsed if line.get("event") == "request_completed"]
    assert completion_logs

    last = completion_logs[-1]
    assert last["method"] == "GET"
    assert last["path"] == "/health"
    assert last["status_code"] == 200
    assert "client_ip" in last
