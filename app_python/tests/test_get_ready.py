"""
Unit tests for the GET /ready endpoint (readiness check)
"""
from datetime import datetime


class TestReadyEndpoint:
    """Test suite for the GET /ready endpoint"""

    def test_ready_endpoint_returns_200_status(self, client):
        response = client.get("/ready")
        assert response.status_code == 200

    def test_ready_endpoint_returns_expected_payload(self, client):
        response = client.get("/ready")
        data = response.json()

        assert data["status"] == "ready"
        assert data["service"] == "devops-info-service"
        assert isinstance(data["timestamp"], str)

    def test_ready_endpoint_timestamp_is_iso_format(self, client):
        response = client.get("/ready")
        timestamp = response.json()["timestamp"]

        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
