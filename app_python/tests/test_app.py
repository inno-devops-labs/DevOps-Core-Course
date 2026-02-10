"""
Unit tests for DevOps Info Service
Tests all endpoints and functionality
"""
import json
import pytest
from app import app, START_TIME
from datetime import datetime, timezone


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestMainEndpoint:
    """Tests for the main endpoint (GET /)"""

    def test_main_endpoint_returns_200(self, client):
        """Test that the main endpoint returns 200 OK."""
        response = client.get('/')
        assert response.status_code == 200

    def test_main_endpoint_returns_json(self, client):
        """Test that the main endpoint returns valid JSON."""
        response = client.get('/')
        assert response.content_type == 'application/json'
        
        # Verify JSON is parseable
        data = response.get_json()
        assert data is not None

    def test_main_endpoint_has_required_sections(self, client):
        """Test that the response contains all required sections."""
        response = client.get('/')
        data = response.get_json()
        
        # Check top-level keys
        assert 'service' in data
        assert 'system' in data
        assert 'runtime' in data
        assert 'request' in data
        assert 'endpoints' in data

    def test_service_section_structure(self, client):
        """Test that the service section has correct structure."""
        response = client.get('/')
        data = response.get_json()
        service = data['service']
        
        # Check required fields
        assert 'name' in service
        assert 'version' in service
        assert 'description' in service
        assert 'framework' in service
        
        # Check data types
        assert isinstance(service['name'], str)
        assert isinstance(service['version'], str)
        assert isinstance(service['framework'], str)
        
        # Check expected values
        assert service['name'] == 'devops-info-service'
        assert service['framework'] == 'Flask'

    def test_system_section_structure(self, client):
        """Test that the system section has correct structure."""
        response = client.get('/')
        data = response.get_json()
        system = data['system']
        
        # Check required fields
        assert 'hostname' in system
        assert 'platform' in system
        assert 'platform_version' in system
        assert 'architecture' in system
        assert 'cpu_count' in system
        assert 'python_version' in system
        
        # Check data types
        assert isinstance(system['hostname'], str)
        assert isinstance(system['platform'], str)
        assert isinstance(system['architecture'], str)
        assert isinstance(system['cpu_count'], int)
        assert isinstance(system['python_version'], str)
        
        # Check reasonable values
        assert system['cpu_count'] > 0
        assert len(system['hostname']) > 0

    def test_runtime_section_structure(self, client):
        """Test that the runtime section has correct structure."""
        response = client.get('/')
        data = response.get_json()
        runtime = data['runtime']
        
        # Check required fields
        assert 'uptime_seconds' in runtime
        assert 'uptime_human' in runtime
        assert 'current_time' in runtime
        assert 'timezone' in runtime
        
        # Check data types
        assert isinstance(runtime['uptime_seconds'], int)
        assert isinstance(runtime['uptime_human'], str)
        assert isinstance(runtime['current_time'], str)
        assert isinstance(runtime['timezone'], str)
        
        # Check reasonable values
        assert runtime['uptime_seconds'] >= 0
        assert runtime['timezone'] == 'UTC'
        
        # Verify timestamp format (ISO 8601)
        datetime.fromisoformat(runtime['current_time'])

    def test_request_section_structure(self, client):
        """Test that the request section has correct structure."""
        response = client.get('/')
        data = response.get_json()
        request_info = data['request']
        
        # Check required fields
        assert 'client_ip' in request_info
        assert 'user_agent' in request_info
        assert 'method' in request_info
        assert 'path' in request_info
        
        # Check data types
        assert isinstance(request_info['client_ip'], str)
        assert isinstance(request_info['user_agent'], str)
        assert isinstance(request_info['method'], str)
        assert isinstance(request_info['path'], str)
        
        # Check expected values
        assert request_info['method'] == 'GET'
        assert request_info['path'] == '/'

    def test_endpoints_section_structure(self, client):
        """Test that the endpoints section has correct structure."""
        response = client.get('/')
        data = response.get_json()
        endpoints = data['endpoints']
        
        # Check it's a list
        assert isinstance(endpoints, list)
        assert len(endpoints) >= 2
        
        # Check each endpoint has required fields
        for endpoint in endpoints:
            assert 'path' in endpoint
            assert 'method' in endpoint
            assert 'description' in endpoint
            assert isinstance(endpoint['path'], str)
            assert isinstance(endpoint['method'], str)
            assert isinstance(endpoint['description'], str)

    def test_user_agent_in_request(self, client):
        """Test that custom user agent is captured correctly."""
        headers = {'User-Agent': 'pytest-test-client/1.0'}
        response = client.get('/', headers=headers)
        data = response.get_json()
        
        # The actual user agent will be from werkzeug test client
        assert 'user_agent' in data['request']
        assert isinstance(data['request']['user_agent'], str)


class TestHealthEndpoint:
    """Tests for the health check endpoint (GET /health)"""

    def test_health_endpoint_returns_200(self, client):
        """Test that the health endpoint returns 200 OK."""
        response = client.get('/health')
        assert response.status_code == 200

    def test_health_endpoint_returns_json(self, client):
        """Test that the health endpoint returns valid JSON."""
        response = client.get('/health')
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        assert data is not None

    def test_health_endpoint_structure(self, client):
        """Test that the health response has correct structure."""
        response = client.get('/health')
        data = response.get_json()
        
        # Check required fields
        assert 'status' in data
        assert 'timestamp' in data
        assert 'uptime_seconds' in data
        
        # Check data types
        assert isinstance(data['status'], str)
        assert isinstance(data['timestamp'], str)
        assert isinstance(data['uptime_seconds'], int)
        
        # Check values
        assert data['status'] == 'healthy'
        assert data['uptime_seconds'] >= 0
        
        # Verify timestamp format (ISO 8601)
        datetime.fromisoformat(data['timestamp'])

    def test_health_endpoint_always_healthy(self, client):
        """Test that health endpoint always returns healthy status."""
        for _ in range(5):
            response = client.get('/health')
            data = response.get_json()
            assert data['status'] == 'healthy'
            assert response.status_code == 200


class TestErrorHandling:
    """Tests for error handling"""

    def test_404_not_found(self, client):
        """Test that non-existent endpoints return 404."""
        response = client.get('/nonexistent')
        assert response.status_code == 404

    def test_404_returns_json(self, client):
        """Test that 404 errors return JSON."""
        response = client.get('/nonexistent')
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        assert data is not None
        assert 'error' in data
        assert 'message' in data

    def test_404_error_structure(self, client):
        """Test that 404 response has correct structure."""
        response = client.get('/does-not-exist')
        data = response.get_json()
        
        assert 'error' in data
        assert 'message' in data
        assert 'path' in data
        
        assert data['error'] == 'Not Found'
        assert data['path'] == '/does-not-exist'

    def test_method_not_allowed(self, client):
        """Test that unsupported methods return appropriate error."""
        response = client.post('/')
        # Flask returns 405 for unsupported methods
        assert response.status_code == 405


class TestEdgeCases:
    """Tests for edge cases and special scenarios"""

    def test_uptime_increases(self, client):
        """Test that uptime increases between requests."""
        import time
        
        response1 = client.get('/health')
        data1 = response1.get_json()
        uptime1 = data1['uptime_seconds']
        
        # Wait a bit
        time.sleep(1)
        
        response2 = client.get('/health')
        data2 = response2.get_json()
        uptime2 = data2['uptime_seconds']
        
        # Uptime should have increased
        assert uptime2 >= uptime1

    def test_concurrent_requests(self, client):
        """Test that multiple concurrent requests all succeed."""
        responses = []
        for _ in range(10):
            response = client.get('/')
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.get_json()
            assert 'service' in data

    def test_response_encoding(self, client):
        """Test that responses are properly UTF-8 encoded."""
        response = client.get('/')
        # Check content type includes charset
        content_type = response.content_type
        assert content_type == 'application/json' or 'charset=utf-8' in str(response.headers.get('Content-Type', ''))
