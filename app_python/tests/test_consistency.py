"""
Unit tests for endpoint consistency.
Tests verify that data is consistent across different endpoints.
"""


class TestEndpointConsistency:
    """Test consistency between endpoints."""

    def test_uptime_consistency(self, client):
        """Test that uptime values are consistent between root and health endpoints."""
        root_response = client.get("/")
        health_response = client.get("/health")
        
        root_uptime = root_response.json()["runtime"]["uptime_seconds"]
        health_uptime = health_response.json()["uptime_seconds"]
        
        # Uptime should be very close (within 1 second) since requests are sequential
        assert abs(root_uptime - health_uptime) <= 1

    def test_timestamp_consistency(self, client):
        """Test that timestamps are in consistent format across endpoints."""
        root_response = client.get("/")
        health_response = client.get("/health")
        
        root_time = root_response.json()["runtime"]["current_time"]
        health_timestamp = health_response.json()["timestamp"]
        
        # Both should be ISO 8601 format strings
        assert isinstance(root_time, str)
        assert isinstance(health_timestamp, str)
        # Both should contain 'T' separator (ISO 8601 format)
        assert "T" in root_time or root_time.endswith("Z")
        assert "T" in health_timestamp or health_timestamp.endswith("Z")
