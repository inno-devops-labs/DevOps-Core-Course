import pytest
import json
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from app import create_app, iso_utc_z, get_uptime

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_endpoint(client):
    response = client.get('/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['service']['name'] == 'devops-info-service'
    assert 'system' in data
    assert 'runtime' in data

def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert 'uptime_seconds' in data

def test_404_not_found(client):
    response = client.get('/nonexistent')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == 'Not Found'

def test_iso_utc_z():
    from app import iso_utc_z
    dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    result = iso_utc_z(dt)
    assert result.endswith('Z')
    assert 'T' in result
