"""
Unit tests for GET / endpoint.
Tests cover JSON structure, required fields, and data validation.
"""


class TestRootEndpoint:
    """Test suite for GET / endpoint."""

    def test_root_endpoint_status_code(self, client):
        """Test that root endpoint returns 200 OK."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_endpoint_json_structure(self, client):
        """Test that root endpoint returns valid JSON with required fields."""
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        
        # Verify top-level structure
        assert "service" in data
        assert "system" in data
        assert "runtime" in data
        assert "visits" in data
        assert "request" in data
        assert "endpoints" in data

    def test_root_endpoint_service_info(self, client):
        """Test service information structure and values."""
        response = client.get("/")
        data = response.json()
        
        service = data["service"]
        assert service["name"] == "devops-info-service"
        assert service["version"] == "1.0.0"
        assert service["description"] == "DevOps course info service"
        assert service["framework"] == "FastAPI"
        assert service.get("environment") == "development"

    def test_root_endpoint_system_info(self, client):
        """Test system information structure and types."""
        response = client.get("/")
        data = response.json()
        
        system = data["system"]
        assert isinstance(system["hostname"], str)
        assert isinstance(system["platform"], str)
        assert isinstance(system["platform_version"], str)
        assert isinstance(system["architecture"], str)
        assert isinstance(system["python_version"], str)
        # cpu_count can be int or "unknown"
        assert isinstance(system["cpu_count"], (int, str))

    def test_root_endpoint_runtime_info(self, client):
        """Test runtime information structure and types."""
        response = client.get("/")
        data = response.json()
        
        runtime = data["runtime"]
        assert isinstance(runtime["uptime_seconds"], int)
        assert runtime["uptime_seconds"] >= 0
        assert isinstance(runtime["uptime_human"], str)
        assert "hours" in runtime["uptime_human"] or "minutes" in runtime["uptime_human"]
        assert isinstance(runtime["current_time"], str)
        assert runtime["timezone"] == "UTC"

    def test_root_endpoint_request_info(self, client):
        """Test request information structure."""
        response = client.get("/")
        data = response.json()
        
        request_info = data["request"]
        assert isinstance(request_info["client_ip"], str)
        assert isinstance(request_info["method"], str)
        assert request_info["method"] == "GET"
        assert isinstance(request_info["path"], str)
        assert request_info["path"] == "/"
        # user_agent might be None for test client
        assert request_info["user_agent"] is None or isinstance(request_info["user_agent"], str)

    def test_root_endpoint_endpoints_list(self, client):
        """Test that endpoints list contains expected entries."""
        response = client.get("/")
        data = response.json()
        
        endpoints = data["endpoints"]
        assert isinstance(endpoints, list)
        assert len(endpoints) >= 2
        
        # Check that root and health endpoints are listed
        endpoint_paths = [ep["path"] for ep in endpoints]
        assert "/" in endpoint_paths
        assert "/visits" in endpoint_paths
        assert "/health" in endpoint_paths
        
        # Verify endpoint structure
        for endpoint in endpoints:
            assert "path" in endpoint
            assert "method" in endpoint
            assert "description" in endpoint
            assert isinstance(endpoint["path"], str)
            assert isinstance(endpoint["method"], str)
            assert isinstance(endpoint["description"], str)
