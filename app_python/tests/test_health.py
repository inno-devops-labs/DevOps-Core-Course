"""
Unit tests for GET /health endpoint.
Tests cover health check response structure and validation.
"""


class TestHealthEndpoint:
    """Test suite for GET /health endpoint."""

    def test_health_endpoint_status_code(self, client):
        """Test that health endpoint returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_json_structure(self, client):
        """Test that health endpoint returns valid JSON with required fields."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        
        assert "status" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data

    def test_health_endpoint_status_value(self, client):
        """Test that health status is 'healthy'."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_endpoint_timestamp_format(self, client):
        """Test that timestamp is in ISO 8601 format."""
        response = client.get("/health")
        data = response.json()
        
        timestamp = data["timestamp"]
        assert isinstance(timestamp, str)
        # ISO 8601 format should contain 'T' or end with 'Z'
        assert "T" in timestamp or timestamp.endswith("Z")

    def test_health_endpoint_uptime(self, client):
        """Test that uptime_seconds is a non-negative integer."""
        response = client.get("/health")
        data = response.json()
        
        uptime = data["uptime_seconds"]
        assert isinstance(uptime, int)
        assert uptime >= 0
