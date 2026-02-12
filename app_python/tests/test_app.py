"""
Unit tests for DevOps Info Service FastAPI application.
"""
import pytest
from fastapi.testclient import TestClient
from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


class TestMainEndpoint:
    """Tests for the main GET / endpoint."""

    def test_main_endpoint_success(self, client):
        """Test that GET / returns correct JSON structure with all required fields."""
        response = client.get('/')

        assert response.status_code == 200
        data = response.json()

        # Verify service metadata
        assert 'service' in data
        assert data['service']['name'] == 'devops-info-service'
        assert 'version' in data['service']
        assert 'description' in data['service']
        assert data['service']['framework'] == 'FastAPI'

        # Verify system information
        assert 'system' in data
        assert 'hostname' in data['system']
        assert 'platform' in data['system']
        assert 'architecture' in data['system']
        assert 'cpu_count' in data['system']
        assert isinstance(data['system']['cpu_count'], int)
        assert 'python_version' in data['system']

        # Verify runtime information
        assert 'runtime' in data
        assert 'uptime_seconds' in data['runtime']
        assert isinstance(data['runtime']['uptime_seconds'], int)
        assert 'uptime_human' in data['runtime']
        assert 'current_time' in data['runtime']
        assert 'timezone' in data['runtime']

        # Verify request information
        assert 'request' in data
        assert 'client_ip' in data['request']
        assert 'user_agent' in data['request']
        assert data['request']['method'] == 'GET'
        assert data['request']['path'] == '/'

        # Verify endpoints list
        assert 'endpoints' in data
        assert isinstance(data['endpoints'], list)
        assert len(data['endpoints']) >= 2

    def test_main_endpoint_data_types(self, client):
        """Test that response data has correct types."""
        response = client.get('/')
        data = response.json()

        assert isinstance(data['service'], dict)
        assert isinstance(data['system'], dict)
        assert isinstance(data['runtime'], dict)
        assert isinstance(data['request'], dict)
        assert isinstance(data['endpoints'], list)

    def test_main_endpoint_required_fields_present(self, client):
        """Test that all fields from the spec are present."""
        response = client.get('/')
        data = response.json()

        # Top-level fields
        required_fields = ['service', 'system', 'runtime', 'request', 'endpoints']
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Service fields
        service_fields = ['name', 'version', 'description', 'framework']
        for field in service_fields:
            assert field in data['service'], f"Missing service field: {field}"

        # System fields
        system_fields = ['hostname', 'platform', 'platform_version', 'architecture', 'cpu_count', 'python_version']
        for field in system_fields:
            assert field in data['system'], f"Missing system field: {field}"

        # Runtime fields
        runtime_fields = ['uptime_seconds', 'uptime_human', 'current_time', 'timezone']
        for field in runtime_fields:
            assert field in data['runtime'], f"Missing runtime field: {field}"

        # Request fields
        request_fields = ['client_ip', 'user_agent', 'method', 'path']
        for field in request_fields:
            assert field in data['request'], f"Missing request field: {field}"


class TestHealthEndpoint:
    """Tests for the GET /health endpoint."""

    def test_health_endpoint_success(self, client):
        """Test that GET /health returns correct health status."""
        response = client.get('/health')

        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'uptime_seconds' in data
        assert isinstance(data['uptime_seconds'], int)

    def test_health_endpoint_json_structure(self, client):
        """Test that health endpoint returns correct JSON structure."""
        response = client.get('/health')
        data = response.json()

        required_fields = ['status', 'timestamp', 'uptime_seconds']
        for field in required_fields:
            assert field in data, f"Missing health field: {field}"

    def test_health_endpoint_data_types(self, client):
        """Test that health endpoint data has correct types."""
        response = client.get('/health')
        data = response.json()

        assert isinstance(data['status'], str)
        assert isinstance(data['timestamp'], str)
        assert isinstance(data['uptime_seconds'], int)
        assert data['uptime_seconds'] >= 0


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_not_found(self, client):
        """Test that non-existent endpoints return 404."""
        response = client.get('/nonexistent')
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data or 'detail' in data

    def test_post_not_allowed(self, client):
        """Test that POST to unsupported endpoints returns appropriate error."""
        # POST to main endpoint (should fail as it's GET only)
        response = client.post('/')
        assert response.status_code == 405  # Method Not Allowed
