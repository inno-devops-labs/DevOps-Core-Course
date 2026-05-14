import json
import logging

from fastapi.testclient import TestClient

from app import JSONFormatter, app, logger


client = TestClient(app)


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


def test_request_logging_emits_json_log():
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


def test_root_endpoint_structure():
    response = client.get("/", headers={"User-Agent": "pytest"})
    assert response.status_code == 200

    data = response.json()
    assert data["service"]["name"] == "devops-info-service"
    assert data["service"]["framework"] == "FastAPI"

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


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert isinstance(data["uptime_seconds"], int)
    assert isinstance(data["timestamp"], str)


def test_unknown_endpoint_returns_404():
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert response.json()["detail"] == "Not Found"
