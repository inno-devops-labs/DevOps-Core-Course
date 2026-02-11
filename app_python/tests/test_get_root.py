"""
Unit tests for the GET / endpoint (service information)
"""
import pytest


class TestGetRootEndpoint:
    """Test suite for the GET / endpoint"""

    def test_root_endpoint_returns_200_status(self, client):
        """Test that GET / returns HTTP 200 status code"""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_endpoint_returns_json(self, client):
        """Test that GET / returns valid JSON response"""
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"
        # Verify we can parse JSON without errors
        data = response.json()
        assert isinstance(data, dict)

    def test_root_endpoint_response_structure(self, client):
        """Test that response has required top-level sections"""
        response = client.get("/")
        data = response.json()
        
        required_sections = ["service", "system", "runtime", "request"]
        for section in required_sections:
            assert section in data, f"Missing required section: {section}"

    def test_root_endpoint_service_section(self, client):
        """Test that service section has all required fields"""
        response = client.get("/")
        service = response.json()["service"]
        
        required_fields = ["name", "version", "description", "framework"]
        for field in required_fields:
            assert field in service, f"Missing field in service: {field}"
        
        # Verify data types and values
        assert isinstance(service["name"], str)
        assert service["name"] == "devops-info-service"
        assert isinstance(service["version"], str)
        assert service["version"] == "1.0.0"
        assert isinstance(service["framework"], str)
        assert service["framework"] == "FastAPI"

    def test_root_endpoint_system_section(self, client):
        """Test that system section has all required fields"""
        response = client.get("/")
        system = response.json()["system"]
        
        required_fields = ["hostname", "platform", "platform_version", "architecture", "cpu_count", "python_version"]
        for field in required_fields:
            assert field in system, f"Missing field in system: {field}"
        
        # Verify data types
        assert isinstance(system["hostname"], str)
        assert len(system["hostname"]) > 0
        assert isinstance(system["platform"], str)
        assert isinstance(system["platform_version"], str)
        assert isinstance(system["architecture"], str)
        assert isinstance(system["cpu_count"], int)
        assert system["cpu_count"] > 0
        assert isinstance(system["python_version"], str)

    def test_root_endpoint_runtime_section(self, client):
        """Test that runtime section has all required fields"""
        response = client.get("/")
        runtime = response.json()["runtime"]
        
        required_fields = ["uptime_seconds", "uptime_human", "current_time", "timezone"]
        for field in required_fields:
            assert field in runtime, f"Missing field in runtime: {field}"
        
        # Verify data types
        assert isinstance(runtime["uptime_seconds"], int)
        assert runtime["uptime_seconds"] >= 0
        assert isinstance(runtime["uptime_human"], str)
        assert isinstance(runtime["current_time"], str)
        assert isinstance(runtime["timezone"], str)
        # Verify uptime_human format
        assert "hours" in runtime["uptime_human"]
        assert "minutes" in runtime["uptime_human"]

    def test_root_endpoint_request_section(self, client):
        """Test that request section has all required fields"""
        response = client.get("/")
        request_data = response.json()["request"]
        
        required_fields = ["client_ip", "user_agent", "method", "path"]
        for field in required_fields:
            assert field in request_data, f"Missing field in request: {field}"
        
        # Verify data types and values
        assert isinstance(request_data["client_ip"], str)
        assert isinstance(request_data["user_agent"], str)
        assert request_data["method"] == "GET"
        assert request_data["path"] == "/"

    def test_root_endpoint_with_custom_user_agent(self, client):
        """Test that custom user agent is captured in request section"""
        custom_user_agent = "CustomTestClient/1.0"
        response = client.get("/", headers={"User-Agent": custom_user_agent})
        request_data = response.json()["request"]
        
        assert request_data["user_agent"] == custom_user_agent

    def test_root_endpoint_multiple_calls_increase_uptime(self, client):
        """Test that uptime increases with multiple calls"""
        import time
        
        response1 = client.get("/")
        uptime1 = response1.json()["runtime"]["uptime_seconds"]
        
        time.sleep(0.1)  # Small delay to ensure uptime increases
        
        response2 = client.get("/")
        uptime2 = response2.json()["runtime"]["uptime_seconds"]
        
        # Uptime should be equal or greater (allowing for clock variations)
        assert uptime2 >= uptime1

    def test_root_endpoint_timestamp_format_is_iso(self, client):
        """Test that timestamp is in ISO format"""
        response = client.get("/")
        current_time = response.json()["runtime"]["current_time"]
        
        # Should be ISO format (can parse with datetime)
        from datetime import datetime
        try:
            datetime.fromisoformat(current_time.replace('Z', '+00:00'))
            is_valid = True
        except ValueError:
            is_valid = False
        
        assert is_valid, f"Timestamp is not in ISO format: {current_time}"

    def test_root_endpoint_consistent_hostname(self, client):
        """Test that multiple calls return the same hostname"""
        response1 = client.get("/")
        hostname1 = response1.json()["system"]["hostname"]
        
        response2 = client.get("/")
        hostname2 = response2.json()["system"]["hostname"]
        
        assert hostname1 == hostname2, "Hostname should be consistent across requests"
