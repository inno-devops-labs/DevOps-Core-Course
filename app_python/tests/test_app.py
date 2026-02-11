import pytest
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestIndexEndpoint:
    def test_status_code(self, client):
        response = client.get('/')
        assert response.status_code == 200

    def test_content_type(self, client):
        response = client.get('/')
        assert response.content_type == 'application/json'

    def test_required_fields_present(self, client):
        response = client.get('/')
        data = response.get_json()
        assert 'service' in data
        assert 'system' in data
        assert 'runtime' in data
        assert 'request' in data
        assert 'endpoints' in data

    def test_service_structure(self, client):
        response = client.get('/')
        data = response.get_json()
        service = data['service']
        assert service['name'] == 'devops-info-service'
        assert 'version' in service
        assert 'description' in service
        assert 'framework' in service
        assert service['framework'] == 'Flask'

    def test_system_structure(self, client):
        response = client.get('/')
        data = response.get_json()
        system = data['system']
        assert 'hostname' in system
        assert 'platform' in system
        assert 'platform_version' in system
        assert 'architecture' in system
        assert 'cpu_count' in system
        assert 'python_version' in system

    def test_runtime_structure(self, client):
        response = client.get('/')
        data = response.get_json()
        runtime = data['runtime']
        assert 'uptime_seconds' in runtime
        assert isinstance(runtime['uptime_seconds'], int)
        assert 'uptime_human' in runtime
        assert isinstance(runtime['uptime_human'], str)
        assert 'current_time' in runtime
        assert 'timezone' in runtime

    def test_request_structure(self, client):
        response = client.get('/')
        data = response.get_json()
        request_data = data['request']
        assert 'client_ip' in request_data
        assert 'user_agent' in request_data
        assert 'method' in request_data
        assert request_data['method'] == 'GET'
        assert 'path' in request_data
        assert request_data['path'] == '/'

    def test_endpoints_list(self, client):
        response = client.get('/')
        data = response.get_json()
        endpoints = data['endpoints']
        assert isinstance(endpoints, list)
        assert len(endpoints) >= 2
        paths = [e['path'] for e in endpoints]
        assert '/' in paths
        assert '/health' in paths


class TestHealthEndpoint:
    def test_status_code(self, client):
        response = client.get('/health')
        assert response.status_code == 200

    def test_content_type(self, client):
        response = client.get('/health')
        assert response.content_type == 'application/json'

    def test_status_healthy(self, client):
        response = client.get('/health')
        data = response.get_json()
        assert data['status'] == 'healthy'

    def test_required_fields(self, client):
        response = client.get('/health')
        data = response.get_json()
        assert 'timestamp' in data
        assert 'uptime_seconds' in data
        assert isinstance(data['uptime_seconds'], int)


class TestErrorHandling:
    def test_404_not_found(self, client):
        response = client.get('/nonexistent')
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == 'Not Found'
