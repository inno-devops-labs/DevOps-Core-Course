import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_health_status_code():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_status_is_healthy():
    data = client.get("/health").json()
    assert data["status"] == "healthy"


def test_health_has_all_fields():
    data = client.get("/health").json()
    assert "status" in data
    assert "timestamp" in data
    assert "uptime_seconds" in data


def test_health_uptime_is_non_negative_int():
    data = client.get("/health").json()
    assert isinstance(data["uptime_seconds"], int)
    assert data["uptime_seconds"] >= 0


def test_health_timestamp_is_iso_format():
    data = client.get("/health").json()
    assert isinstance(data["timestamp"], str)
    assert "T" in data["timestamp"]


def test_health_content_type():
    response = client.get("/health")
    assert response.headers["content-type"] == "application/json"
