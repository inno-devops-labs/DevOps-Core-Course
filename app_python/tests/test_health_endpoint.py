from datetime import datetime

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_status_code():
    response = client.get("/health")
    assert response.status_code == 200


def test_response_structure():
    data = client.get("/health").json()

    assert data["status"] == "healthy"
    assert isinstance(data["uptime_seconds"], int)
    assert "timestamp" in data

    timestamp = data["timestamp"]
    try:
        parsed_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert parsed_time.tzinfo is not None
    except (ValueError, AttributeError):
        assert False
