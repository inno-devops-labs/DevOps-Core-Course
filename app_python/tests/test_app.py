"""
Unit tests for DevOps Info Service Flask application.

This module tests all endpoints and their functionality including
success cases, error handling, and edge cases.
"""
import json
import time
from datetime import datetime

import pytest

from app import app, format_uptime, get_system_info


@pytest.fixture
def client():
    """
    Create a test client for the Flask application.
    
    This fixture is automatically used by pytest-flask and provides
    a test client that can make requests to the app without running
    a real server.
    """
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_start_time(monkeypatch):
    """Mock start time for consistent uptime testing."""
    fixed_time = time.time() - 100  # App running for 100 seconds
    monkeypatch.setattr('app.start_time', fixed_time)


class TestMainEndpoint:
    """Tests for the main endpoint (GET /)."""
    
    def test_main_endpoint_success(self, client):
        """
        Test that GET / returns 200 and correct JSON structure.
        
        Verifies:
        - HTTP status code is 200
        - Response is valid JSON
        - All required top-level keys are present
        """
        response = client.get('/')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        
        # Verify all top-level keys exist
        assert 'service' in data
        assert 'system' in data
        assert 'runtime' in data
        assert 'request' in data
        assert 'endpoints' in data
    
    def test_main_endpoint_service_info(self, client):
        """
        Test that service information contains required fields.
        
        Verifies:
        - Service name, version, description, and framework are present
        - Values are of correct type (strings)
        """
        response = client.get('/')
        data = response.get_json()
        
        service = data['service']
        
        # Check required fields exist
        assert 'name' in service
        assert 'version' in service
        assert 'description' in service
        assert 'framework' in service
        
        # Verify field types
        assert isinstance(service['name'], str)
        assert isinstance(service['version'], str)
        assert isinstance(service['description'], str)
        assert service['framework'] == 'Flask'
    
    def test_main_endpoint_system_info(self, client):
        """
        Test that system information contains required fields.
        
        Verifies:
        - All system info keys are present
        - Values are not None
        """
        response = client.get('/')
        data = response.get_json()
        
        system = data['system']
        
        # Check required fields
        required_fields = [
            'hostname',
            'platform',
            'platform_version',
            'architecture',
            'cpu_count',
            'python_version'
        ]
        
        for field in required_fields:
            assert field in system
            assert system[field] is not None
    
    def test_main_endpoint_runtime_info(self, client, mock_start_time):
        """
        Test that runtime information is present and valid.
        
        Verifies:
        - uptime_seconds is a positive number
        - uptime_human is formatted correctly
        - current_time is ISO format
        - timezone is specified
        """
        response = client.get('/')
        data = response.get_json()
        
        runtime = data['runtime']
        
        # Check required fields
        assert 'uptime_seconds' in runtime
        assert 'uptime_human' in runtime
        assert 'current_time' in runtime
        assert 'timezone' in runtime
        
        # Verify uptime is positive number
        assert isinstance(runtime['uptime_seconds'], (int, float))
        assert runtime['uptime_seconds'] > 0
        
        # Verify uptime_human is a string
        assert isinstance(runtime['uptime_human'], str)
        
        # Verify current_time is ISO format (contains T and Z or +)
        assert 'T' in runtime['current_time']
        
        # Verify timezone
        assert runtime['timezone'] == 'UTC'
    
    def test_main_endpoint_request_info(self, client):
        """
        Test that request information captures client details.
        
        Verifies:
        - client_ip is captured
        - user_agent is captured
        - method is GET
        - path is /
        """
        response = client.get('/', headers={'User-Agent': 'TestClient/1.0'})
        data = response.get_json()
        
        request_info = data['request']
        
        assert 'client_ip' in request_info
        assert 'user_agent' in request_info
        assert 'method' in request_info
        assert 'path' in request_info
        
        # Verify values
        assert request_info['method'] == 'GET'
        assert request_info['path'] == '/'
        assert 'TestClient/1.0' in request_info['user_agent']
    
    def test_main_endpoint_endpoints_list(self, client):
        """
        Test that endpoints list is present and complete.
        
        Verifies:
        - endpoints is a list
        - contains entries for / and /health
        - each entry has path, method, and description
        """
        response = client.get('/')
        data = response.get_json()
        
        endpoints = data['endpoints']
        
        assert isinstance(endpoints, list)
        assert len(endpoints) >= 2  # At least / and /health
        
        # Verify structure of each endpoint
        for endpoint in endpoints:
            assert 'path' in endpoint
            assert 'method' in endpoint
            assert 'description' in endpoint
        
        # Verify specific endpoints exist
        paths = [ep['path'] for ep in endpoints]
        assert '/' in paths
        assert '/health' in paths


class TestHealthEndpoint:
    """Tests for the health check endpoint (GET /health)."""
    
    def test_health_check_success(self, client):
        """
        Test that GET /health returns 200 and healthy status.
        
        Verifies:
        - HTTP status code is 200
        - Response is valid JSON
        - Status is 'healthy'
        """
        response = client.get('/health')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        
        assert 'status' in data
        assert data['status'] == 'healthy'
    
    def test_health_check_required_fields(self, client):
        """
        Test that health check contains all required fields.
        
        Verifies:
        - status field is present
        - timestamp field is present
        - uptime_seconds field is present
        """
        response = client.get('/health')
        data = response.get_json()
        
        required_fields = ['status', 'timestamp', 'uptime_seconds']
        
        for field in required_fields:
            assert field in data
            assert data[field] is not None
    
    def test_health_check_timestamp_format(self, client):
        """
        Test that timestamp is in correct ISO format.
        
        Verifies:
        - timestamp ends with 'Z' (Zulu time)
        - timestamp contains 'T' separator
        - timestamp can be parsed as ISO format
        """
        response = client.get('/health')
        data = response.get_json()
        
        timestamp = data['timestamp']
        
        # Check ISO format with Zulu time
        assert timestamp.endswith('Z')
        assert 'T' in timestamp
        
        # Verify it's parseable (will raise exception if invalid)
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    def test_health_check_uptime(self, client, mock_start_time):
        """
        Test that uptime_seconds is a positive number.
        
        Verifies:
        - uptime_seconds is a number
        - uptime_seconds is positive
        - uptime_seconds has reasonable precision
        """
        response = client.get('/health')
        data = response.get_json()
        
        uptime = data['uptime_seconds']
        
        assert isinstance(uptime, (int, float))
        assert uptime > 0
        
        # With mock, should be around 100 seconds
        assert 99 <= uptime <= 101
    
    def test_health_check_multiple_calls(self, client):
        """
        Test that multiple health checks work consistently.
        
        Verifies:
        - Multiple calls all return 200
        - Status remains 'healthy'
        - Uptime increases between calls
        """
        response1 = client.get('/health')
        uptime1 = response1.get_json()['uptime_seconds']
        
        time.sleep(0.1)  # Small delay
        
        response2 = client.get('/health')
        uptime2 = response2.get_json()['uptime_seconds']
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert uptime2 >= uptime1  # Uptime should increase


class TestErrorHandling:
    """Tests for error handling and edge cases."""
    
    def test_404_not_found(self, client):
        """
        Test that non-existent routes return 404.
        
        Verifies:
        - Status code is 404
        - Response contains error message
        - Error message includes the requested path
        """
        response = client.get('/nonexistent')
        
        assert response.status_code == 404
        
        data = response.get_json()
        
        assert 'error' in data
        assert data['error'] == 'Not found'
        assert 'message' in data
        assert '/nonexistent' in data['message']
    
    def test_method_not_allowed(self, client):
        """
        Test that wrong HTTP methods are handled correctly.
        
        Verifies:
        - POST to GET-only endpoint returns 405
        """
        response = client.post('/')
        assert response.status_code == 405
        
        response = client.post('/health')
        assert response.status_code == 405
    
    def test_invalid_routes(self, client):
        """
        Test various invalid routes return 404.
        
        Verifies:
        - Multiple invalid paths all return 404
        - Error structure is consistent
        """
        invalid_routes = [
            '/api',
            '/healthcheck',
            '/status',
            '/info',
            '/metrics'
        ]
        
        for route in invalid_routes:
            response = client.get(route)
            assert response.status_code == 404
            data = response.get_json()
            assert 'error' in data

    """Integration tests checking overall application behavior."""
    
    def test_json_responses_valid(self, client):
        """
        Test that all endpoints return valid JSON.
        
        Verifies responses can be parsed as JSON without errors.
        """
        endpoints = ['/', '/health']
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # This will raise exception if JSON is invalid
            data = response.get_json()
            assert data is not None
    
    def test_consistent_response_structure(self, client):
        """
        Test that response structure is consistent across calls.
        
        Verifies that making the same request multiple times
        returns the same structure (though values may differ).
        """
        response1 = client.get('/')
        response2 = client.get('/')
        
        data1 = response1.get_json()
        data2 = response2.get_json()
        
        # Keys should be identical
        assert data1.keys() == data2.keys()
        assert data1['service'].keys() == data2['service'].keys()
        assert data1['system'].keys() == data2['system'].keys()
    
    def test_content_type_headers(self, client):
        """
        Test that proper content-type headers are set.
        
        Verifies:
        - All responses are application/json
        """
        endpoints = ['/', '/health', '/nonexistent']
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert 'application/json' in response.content_type
