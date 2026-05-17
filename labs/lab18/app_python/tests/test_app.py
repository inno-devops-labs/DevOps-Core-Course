"""Unit tests for Flask application."""

import json
import pytest
import sys
import os
from datetime import datetime


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app


@pytest.fixture
def client():
    """Create test client for Flask app."""
    app.config['TESTING'] = True
    app.config['DEBUG'] = False
    with app.test_client() as client:
        yield client


def test_home_endpoint(client):
    """Test GET / endpoint returns correct structure."""
    response = client.get('/')
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    
    data = json.loads(response.data)
    
    
    assert 'service' in data
    assert 'runtime' in data
    assert 'request' in data
    assert 'endpoints' in data
    
    
    assert data['service']['name'] == 'devops-info-service'
    assert 'version' in data['service']
    assert 'description' in data['service']
    assert 'framework' in data['service']
    
    
    assert isinstance(data['endpoints'], list)
    assert len(data['endpoints']) >= 2
    
    
    assert 'current_time' in data['runtime']
    assert 'uptime_seconds' in data['runtime']
    assert 'uptime_human' in data['runtime']


def test_health_endpoint(client):
    """Test GET /health endpoint returns service health."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    
    data = json.loads(response.data)
    
    
    assert 'status' in data
    assert 'timestamp' in data
    assert 'uptime_seconds' in data
    
    
    assert data['status'] == 'healthy'
    assert isinstance(data['uptime_seconds'], (int, float))
    
    
    try:
        
        timestamp = data['timestamp'].replace('Z', '+00:00')
        datetime.fromisoformat(timestamp)
    except (ValueError, AttributeError):
        pytest.fail(f"Timestamp '{data['timestamp']}' is not in ISO format")


def test_404_error(client):
    """Test non-existent endpoint returns 404."""
    response = client.get('/non-existent-path-12345')
    assert response.status_code == 404
    
    
    if response.content_type and 'application/json' in response.content_type:
        data = json.loads(response.data)
        assert 'error' in data or 'message' in data
    else:
        
        assert True


def test_method_not_allowed(client):
    """Test POST method on GET-only endpoint returns 405."""
    response = client.post('/')
    assert response.status_code == 405
    
    
    assert response.status_code == 405


def test_response_headers(client):
    """Test response headers are correct."""
    response = client.get('/')
    assert 'Content-Type' in response.headers
    assert response.headers['Content-Type'] == 'application/json'


def test_concurrent_requests(client):
    """Test multiple requests in sequence."""
    for i in range(5):
        response = client.get('/')
        assert response.status_code == 200
        
        response = client.get('/health')
        assert response.status_code == 200


def test_service_version(client):
    """Test service version is present."""
    response = client.get('/')
    data = json.loads(response.data)
    assert 'version' in data['service']
    assert isinstance(data['service']['version'], str)
    assert len(data['service']['version']) > 0


def test_endpoints_list(client):
    """Test endpoints list contains required endpoints."""
    response = client.get('/')
    data = json.loads(response.data)
    
    endpoints = data['endpoints']
    paths = [ep['path'] for ep in endpoints]
    
    assert '/' in paths
    assert '/health' in paths
    
    
    for endpoint in endpoints:
        assert 'method' in endpoint
        assert 'path' in endpoint
        assert 'description' in endpoint