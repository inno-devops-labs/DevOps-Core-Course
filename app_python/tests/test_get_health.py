"""
Unit tests for the GET /health endpoint (health check)
"""
import pytest
from datetime import datetime


class TestHealthEndpoint:
    """Test suite for the GET /health endpoint"""

    def test_health_endpoint_returns_200_status(self, client):
        """Test that GET /health returns HTTP 200 status code"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_returns_json(self, client):
        """Test that GET /health returns valid JSON response"""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"
        # Verify we can parse JSON without errors
        data = response.json()
        assert isinstance(data, dict)

    def test_health_endpoint_has_required_fields(self, client):
        """Test that health response has all required fields"""
        response = client.get("/health")
        data = response.json()
        
        required_fields = ["status", "timestamp", "uptime_seconds"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_health_endpoint_status_is_healthy(self, client):
        """Test that health status returns 'healthy'"""
        response = client.get("/health")
        data = response.json()
        
        assert isinstance(data["status"], str)
        assert data["status"] == "healthy"

    def test_health_endpoint_timestamp_is_iso_format(self, client):
        """Test that timestamp is in ISO format"""
        response = client.get("/health")
        timestamp = response.json()["timestamp"]
        
        assert isinstance(timestamp, str)
        # Should be ISO format
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            is_valid = True
        except ValueError:
            is_valid = False
        
        assert is_valid, f"Timestamp is not in ISO format: {timestamp}"

    def test_health_endpoint_timestamp_is_recent(self, client):
        """Test that timestamp is recent (within last 5 seconds)"""
        response = client.get("/health")
        timestamp_str = response.json()["timestamp"]
        
        # Parse timestamp
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now(timestamp.tzinfo)
        
        # Check that timestamp is within 5 seconds of now
        time_diff = abs((now - timestamp).total_seconds())
        assert time_diff < 5, f"Timestamp is not recent: {time_diff} seconds old"

    def test_health_endpoint_uptime_is_integer(self, client):
        """Test that uptime_seconds is an integer"""
        response = client.get("/health")
        uptime = response.json()["uptime_seconds"]
        
        assert isinstance(uptime, int)
        assert uptime >= 0

    def test_health_endpoint_uptime_non_negative(self, client):
        """Test that uptime is non-negative"""
        response = client.get("/health")
        uptime = response.json()["uptime_seconds"]
        
        assert uptime >= 0, "Uptime should never be negative"

    def test_health_endpoint_response_size(self, client):
        """Test that response size is reasonable (not excessively large)"""
        response = client.get("/health")
        content_length = len(response.content)
        
        # Health check response should be small (typically < 500 bytes)
        assert content_length < 1000, f"Response is too large: {content_length} bytes"

    def test_health_endpoint_multiple_calls_increase_uptime(self, client):
        """Test that uptime increases with multiple calls"""
        import time
        
        response1 = client.get("/health")
        uptime1 = response1.json()["uptime_seconds"]
        
        time.sleep(0.1)  # Small delay
        
        response2 = client.get("/health")
        uptime2 = response2.json()["uptime_seconds"]
        
        # Uptime should be equal or greater
        assert uptime2 >= uptime1

    def test_health_endpoint_consistency_across_calls(self, client):
        """Test that status remains 'healthy' across multiple calls"""
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"

    def test_health_endpoint_response_structure_integrity(self, client):
        """Test that response maintains consistent structure"""
        response = client.get("/health")
        data = response.json()
        
        # Verify all fields exist and have correct types
        assert isinstance(data["status"], str)
        assert isinstance(data["timestamp"], str)
        assert isinstance(data["uptime_seconds"], int)
        
        # Verify no extra or unexpected fields (should only have these 3)
        assert len(data) == 3, f"Unexpected fields in response: {data.keys()}"


class TestHealthEndpointEdgeCases:
    """Test edge cases for health endpoint"""

    def test_health_endpoint_is_deterministic(self, client):
        """Test that repeated calls return consistent structure"""
        responses = [client.get("/health").json() for _ in range(3)]
        
        # All should have same keys
        for response in responses:
            assert set(response.keys()) == {"status", "timestamp", "uptime_seconds"}
            assert response["status"] == "healthy"

    def test_health_endpoint_no_authentication_required(self, client):
        """Test that health endpoint doesn't require authentication"""
        # Should work without any special headers
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
