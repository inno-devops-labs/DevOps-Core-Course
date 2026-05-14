import json
import logging

import pytest
from fastapi.testclient import TestClient

import app as app_module
from app import JSONFormatter, logger


client = TestClient(app_module.app)


@pytest.fixture()
def isolated_visit_counter(monkeypatch, tmp_path):
    counter = app_module.VisitCounter(tmp_path / "visits")
    monkeypatch.setattr(app_module, "visit_counter", counter)
    return counter


def test_json_formatter_returns_json_object():
    record = logging.LogRecord(
        name="app",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request_completed",
        args=(),
        exc_info=None,
    )
    record.method = "GET"
    record.path = "/"
    record.status_code = 200

    payload = json.loads(JSONFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["message"] == "request_completed"
    assert payload["method"] == "GET"
    assert payload["path"] == "/"
    assert payload["status_code"] == 200


def test_request_logging_emits_json_log(isolated_visit_counter):
    records = []

    class ListHandler(logging.Handler):
        def emit(self, record):
            records.append(json.loads(JSONFormatter().format(record)))

    handler = ListHandler()
    logger.addHandler(handler)
    try:
        response = client.get("/", headers={"User-Agent": "pytest"})
    finally:
        logger.removeHandler(handler)

    assert response.status_code == 200
    matching = [item for item in records if item.get("message") == "request_completed"]
    assert matching, "expected request_completed log entry"

    log_entry = matching[-1]
    assert log_entry["method"] == "GET"
    assert log_entry["path"] == "/"
    assert log_entry["status_code"] == 200
    assert log_entry["client_ip"] in {"testclient", "127.0.0.1", "unknown"}


def test_root_endpoint_structure(isolated_visit_counter):
    response = client.get("/", headers={"User-Agent": "pytest"})
    assert response.status_code == 200

    data = response.json()
    assert data["service"]["name"] == "devops-info-service"
    assert data["service"]["framework"] == "FastAPI"
    assert data["visits"] == 1

    assert "hostname" in data["system"]
    assert "platform" in data["system"]
    assert isinstance(data["system"]["cpu_count"], int)

    assert isinstance(data["runtime"]["uptime_seconds"], int)
    assert "current_time" in data["runtime"]

    assert data["request"]["method"] == "GET"
    assert data["request"]["path"] == "/"

    endpoints = {item["path"] for item in data["endpoints"]}
    assert "/" in endpoints
    assert "/health" in endpoints
    assert "/visits" in endpoints


def test_visit_counter_persists(isolated_visit_counter):
    client.get("/")
    client.get("/")

    visits_response = client.get("/visits")
    assert visits_response.status_code == 200
    assert visits_response.json()["visits"] == 2

    visits_file = isolated_visit_counter.file_path
    assert visits_file.read_text(encoding="utf-8").strip() == "2"

    reloaded_counter = app_module.VisitCounter(visits_file)
    assert reloaded_counter.get() == 2


def test_health_endpoint(isolated_visit_counter):
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert isinstance(data["uptime_seconds"], int)
    assert isinstance(data["timestamp"], str)


def test_unknown_endpoint_returns_404(isolated_visit_counter):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert response.json()["detail"] == "Not Found"
