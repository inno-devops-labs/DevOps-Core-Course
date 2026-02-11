import pytest
from app import app

@pytest.fixture
def client():
    """Make Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_endpoint(client):
    """Test GET / — check structure JSON."""
    response = client.get('/')
    assert response.status_code == 200
    json_data = response.json
    
    assert 'service' in json_data
    assert json_data['service']['name'] == 'devops-info-service'
    assert 'system' in json_data
    assert 'hostname' in json_data['system']
    assert 'runtime' in json_data
    assert 'request' in json_data

def test_health_endpoint(client):
    """Test GET /health."""
    response = client.get('/health')
    assert response.status_code == 200
    json_data = response.json
    
    assert json_data['status'] == 'healthy'
    assert 'timestamp' in json_data
    assert 'uptime_seconds' in json_data
    assert isinstance(json_data['uptime_seconds'], int)

def test_404_not_found(client):
    """Test error handler 404."""
    response = client.get('/nonexistent')
    assert response.status_code == 404
    json_data = response.json
    assert json_data['error'] == 'Not Found'
