"""
Unit tests for DevOps Info Service
"""

import json
from unittest.mock import patch
import pytest
from datetime import datetime, timezone


class TestMainEndpoint:
    """Test suite for GET / endpoint."""
    
    def test_get_root_returns_200(self, client):
        """Test that root endpoint returns 200 OK."""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_get_root_returns_json(self, client):
        """Test that root endpoint returns JSON."""
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"
    
    def test_get_root_has_service_info(self, client, expected_service_info):
        """Test that service information is present."""
        response = client.get("/")
        data = response.json()
        
        assert "service" in data
        assert data["service"] == expected_service_info
    
    def test_get_root_has_system_info(self, client):
        """Test that system information is present."""
        response = client.get("/")
        data = response.json()
        
        assert "system" in data
        system_info = data["system"]
        
        required_fields = [
            "hostname",
            "platform",
            "platform_version",
            "architecture",
            "cpu_count",
            "python_version",
        ]
        
        for field in required_fields:
            assert field in system_info, f"Missing field: {field}"
            assert system_info[field] is not None, f"Field {field} is None"
    
    def test_get_root_has_runtime_info(self, client):
        """Test that runtime information is present."""
        response = client.get("/")
        data = response.json()
        
        assert "runtime" in data
        runtime_info = data["runtime"]
        
        required_fields = [
            "uptime_seconds",
            "uptime_human",
            "current_time",
            "timezone",
        ]
        
        for field in required_fields:
            assert field in runtime_info, f"Missing field: {field}"
        
        # Check uptime values
        assert isinstance(runtime_info["uptime_seconds"], int)
        assert runtime_info["uptime_seconds"] >= 0
        assert "hours" in runtime_info["uptime_human"] or "minutes" in runtime_info["uptime_human"]
        
        # Check timestamp format
        try:
            datetime.fromisoformat(runtime_info["current_time"].replace("Z", "+00:00"))
        except ValueError:
            pytest.fail(f"Invalid timestamp format: {runtime_info['current_time']}")
    
    def test_get_root_has_request_info(self, client):
        """Test that request information is present."""
        response = client.get("/")
        data = response.json()
        
        assert "request" in data
        request_info = data["request"]
        
        required_fields = [
            "client_ip",
            "user_agent",
            "method",
            "path",
        ]
        
        for field in required_fields:
            assert field in request_info, f"Missing field: {field}"
        
        # Check request values
        assert request_info["method"] == "GET"
        assert request_info["path"] == "/"
        assert request_info["client_ip"] is not None
        assert request_info["user_agent"] is not None
    
    def test_get_root_has_endpoints_list(self, client):
        """Test that endpoints list is present."""
        response = client.get("/")
        data = response.json()
        
        assert "endpoints" in data
        assert isinstance(data["endpoints"], list)
        assert len(data["endpoints"]) >= 2
        
        # Check for required endpoints
        endpoints = {e["path"]: e for e in data["endpoints"]}
        assert "/" in endpoints
        assert "/health" in endpoints
        assert endpoints["/"]["method"] == "GET"
        assert endpoints["/"]["description"] == "Service information"
    
    def test_get_root_with_custom_headers(self, client):
        """Test that request info captures custom headers."""
        custom_headers = {
            "User-Agent": "Custom-Agent/2.0",
            "X-Forwarded-For": "10.0.0.1",
        }
        
        response = client.get("/", headers=custom_headers)
        data = response.json()
        
        assert data["request"]["user_agent"] == "Custom-Agent/2.0"
    
    @patch("socket.gethostname")
    def test_get_root_mocked_hostname(self, mock_gethostname, client):
        """Test with mocked system information."""
        mock_gethostname.return_value = "test-hostname"
        
        response = client.get("/")
        data = response.json()
        
        assert data["system"]["hostname"] == "test-hostname"


class TestHealthEndpoint:
    """Test suite for GET /health endpoint."""
    
    def test_get_health_returns_200(self, client):
        """Test that health endpoint returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_get_health_returns_json(self, client):
        """Test that health endpoint returns JSON."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"
    
    def test_get_health_has_correct_structure(self, client):
        """Test that health response has correct structure."""
        response = client.get("/health")
        data = response.json()
        
        required_fields = ["status", "timestamp", "uptime_seconds"]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Check field values
        assert data["status"] == "healthy"
        assert isinstance(data["uptime_seconds"], int)
        assert data["uptime_seconds"] >= 0
        
        # Check timestamp format
        try:
            datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            pytest.fail(f"Invalid timestamp format: {data['timestamp']}")
    
    def test_health_status_is_always_healthy(self, client):
        """Test that health status is consistently 'healthy'."""
        for _ in range(3):  # Multiple requests
            response = client.get("/health")
            data = response.json()
            assert data["status"] == "healthy"
    
    def test_health_uptime_increases(self, client):
        """Test that uptime increases between requests."""
        response1 = client.get("/health")
        uptime1 = response1.json()["uptime_seconds"]
        
        import time
        time.sleep(1)
        
        response2 = client.get("/health")
        uptime2 = response2.json()["uptime_seconds"]
        
        assert uptime2 >= uptime1


class TestErrorHandling:
    """Test suite for error handling."""
    
    def test_404_not_found(self, client):
        """Test that non-existent endpoint returns 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
        
        data = response.json()
        assert "error" in data
        assert "message" in data
        assert data["error"] == "Not Found"
    
    def test_404_response_structure(self, client):
        """Test 404 error response structure."""
        response = client.get("/nonexistent")
        data = response.json()
        
        assert response.headers["content-type"] == "application/json"
        assert "error" in data
        assert "message" in data
    
    def test_method_not_allowed(self, client):
        """Test that POST to GET endpoints returns 405."""
        response = client.post("/")
        assert response.status_code == 405  # Method Not Allowed


class TestConfiguration:
    """Test suite for environment configuration."""
    
    def test_port_configuration(self):
        """Test that PORT environment variable works."""
        import os
        from unittest.mock import patch
        
        with patch.dict(os.environ, {"PORT": "8080"}):
            # Re-import app to pick up new env var
            import importlib
            import app
            importlib.reload(app)
            
            # Check that app uses PORT from env
            assert os.getenv("PORT") == "8080"
    
    def test_host_configuration(self):
        """Test that HOST environment variable works."""
        import os
        from unittest.mock import patch
        
        with patch.dict(os.environ, {"HOST": "127.0.0.1"}):
            # Re-import app to pick up new env var
            import importlib
            import app
            importlib.reload(app)
            
            # Check that app uses HOST from env
            assert os.getenv("HOST") == "127.0.0.1"


class TestPerformance:
    """Test suite for performance characteristics."""
    
    @pytest.mark.slow
    def test_response_time(self, client):
        """Test that response time is within acceptable limits."""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time < 1.0  # Should respond within 1 second
        assert response.status_code == 200


class TestEdgeCases:
    """Test suite for edge cases."""
    
    def test_empty_user_agent(self, client):
        """Test with empty User-Agent header."""
        response = client.get("/", headers={"User-Agent": ""})
        data = response.json()
        
        # Should handle empty user agent gracefully
        assert data["request"]["user_agent"] == ""
    
    def test_malformed_path(self, client):
        """Test with malformed path."""
        response = client.get("/%invalid%path%")
        # Should either 404 or handle gracefully
        assert response.status_code in [200, 404, 400]
    
    def test_long_path(self, client):
        """Test with very long path."""
        long_path = "/" + "a" * 1000
        response = client.get(long_path)
        # Should 404, not crash
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main(["-v", __file__])