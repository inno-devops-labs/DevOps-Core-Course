"""Unit tests for devops-info-service Flask application."""

import json


class TestIndexEndpoint:
    """Tests for GET / endpoint."""

    def test_index_returns_200(self, client):
        """Test that index endpoint returns HTTP 200."""
        response = client.get('/')
        assert response.status_code == 200

    def test_index_returns_json(self, client):
        """Test that index endpoint returns JSON content type."""
        response = client.get('/')
        assert response.content_type == 'application/json'

    def test_index_contains_service_info(self, client):
        """Test that response contains service information with all required fields."""
        response = client.get('/')
        data = json.loads(response.data)

        assert 'service' in data
        assert 'name' in data['service']
        assert 'version' in data['service']
        assert 'description' in data['service']
        assert 'framework' in data['service']

        assert data['service']['name'] == 'devops-info-service'
        assert data['service']['framework'] == 'Flask'

    def test_index_contains_system_info(self, client):
        """Test that response contains system information with all required fields."""
        response = client.get('/')
        data = json.loads(response.data)

        assert 'system' in data
        assert 'hostname' in data['system']
        assert 'platform' in data['system']
        assert 'platform_version' in data['system']
        assert 'architecture' in data['system']
        assert 'cpu_count' in data['system']
        assert 'python_version' in data['system']

    def test_index_contains_runtime_info(self, client):
        """Test that response contains runtime information with all required fields."""
        response = client.get('/')
        data = json.loads(response.data)

        assert 'runtime' in data
        assert 'uptime_seconds' in data['runtime']
        assert 'uptime_human' in data['runtime']
        assert 'current_time' in data['runtime']
        assert 'timezone' in data['runtime']

        assert data['runtime']['timezone'] == 'UTC'

    def test_index_contains_request_info(self, client):
        """Test that response contains request information with all required fields."""
        response = client.get('/')
        data = json.loads(response.data)

        assert 'request' in data
        assert 'client_ip' in data['request']
        assert 'user_agent' in data['request']
        assert 'method' in data['request']
        assert 'path' in data['request']

        assert data['request']['method'] == 'GET'
        assert data['request']['path'] == '/'

    def test_index_contains_endpoints(self, client):
        """Test that response contains endpoints list with at least 4 items."""
        response = client.get('/')
        data = json.loads(response.data)

        assert 'endpoints' in data
        assert isinstance(data['endpoints'], list)
        assert len(data['endpoints']) >= 4

        paths = [ep['path'] for ep in data['endpoints']]
        assert '/' in paths
        assert '/health' in paths
        assert '/visits' in paths
        assert '/metrics' in paths

    def test_index_data_types(self, client):
        """Test that response fields have correct data types."""
        response = client.get('/')
        data = json.loads(response.data)

        assert isinstance(data['runtime']['uptime_seconds'], int)
        assert isinstance(data['system']['cpu_count'], int)
        assert isinstance(data['service']['name'], str)
        assert isinstance(data['system']['hostname'], str)
        assert isinstance(data['runtime']['uptime_human'], str)


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_returns_200(self, client):
        """Test that health endpoint returns HTTP 200."""
        response = client.get('/health')
        assert response.status_code == 200

    def test_health_returns_json(self, client):
        """Test that health endpoint returns JSON content type."""
        response = client.get('/health')
        assert response.content_type == 'application/json'

    def test_health_contains_required_fields(self, client):
        """Test that health response contains all required fields."""
        response = client.get('/health')
        data = json.loads(response.data)

        assert 'status' in data
        assert 'timestamp' in data
        assert 'uptime_seconds' in data

    def test_health_status_is_healthy(self, client):
        """Test that health status is 'healthy'."""
        response = client.get('/health')
        data = json.loads(response.data)

        assert data['status'] == 'healthy'

    def test_health_uptime_is_non_negative_integer(self, client):
        """Test that uptime_seconds is a non-negative integer."""
        response = client.get('/health')
        data = json.loads(response.data)

        assert isinstance(data['uptime_seconds'], int)
        assert data['uptime_seconds'] >= 0


class TestErrorHandlers:
    """Tests for error handlers."""

    def test_404_returns_not_found(self, client):
        """Test that non-existent endpoint returns 404."""
        response = client.get('/nonexistent')
        assert response.status_code == 404

    def test_404_returns_json(self, client):
        """Test that 404 response is JSON."""
        response = client.get('/nonexistent')
        assert response.content_type == 'application/json'

    def test_404_contains_error_info(self, client):
        """Test that 404 response contains error information."""
        response = client.get('/nonexistent')
        data = json.loads(response.data)

        assert 'error' in data
        assert 'message' in data
        assert 'path' in data

        assert data['error'] == 'Not Found'

    def test_404_includes_requested_path(self, client):
        """Test that 404 response includes the requested path."""
        response = client.get('/some/invalid/path')
        data = json.loads(response.data)

        assert data['path'] == '/some/invalid/path'


class TestVisitsEndpoint:
    """Tests for GET /visits endpoint and visit counter."""

    def test_visits_returns_200(self, client):
        """Test that visits endpoint returns HTTP 200."""
        response = client.get('/visits')
        assert response.status_code == 200

    def test_visits_returns_json(self, client):
        """Test that visits endpoint returns JSON content type."""
        response = client.get('/visits')
        assert response.content_type == 'application/json'

    def test_visits_starts_at_zero(self, client):
        """Test that visits counter starts at zero."""
        response = client.get('/visits')
        data = json.loads(response.data)
        assert data['visits'] == 0

    def test_visits_increments_on_index(self, client):
        """Test that visiting / increments the counter."""
        client.get('/')
        response = client.get('/visits')
        data = json.loads(response.data)
        assert data['visits'] == 1

    def test_visits_multiple_increments(self, client):
        """Test that multiple visits increment correctly."""
        for _ in range(5):
            client.get('/')
        response = client.get('/visits')
        data = json.loads(response.data)
        assert data['visits'] == 5

    def test_index_includes_visits_count(self, client):
        """Test that index response includes visits count."""
        response = client.get('/')
        data = json.loads(response.data)
        assert 'visits' in data
        assert data['visits'] == 1


class TestMetricsEndpoint:
    """Tests for GET /metrics endpoint (Prometheus exposition)."""

    def test_metrics_returns_200(self, client):
        response = client.get('/metrics')
        assert response.status_code == 200

    def test_metrics_returns_prometheus_text(self, client):
        response = client.get('/metrics')
        assert response.content_type.startswith('text/plain')

    def test_metrics_contains_visits_counter(self, client):
        client.get('/')
        response = client.get('/metrics')
        body = response.data.decode()
        assert 'app_visits_total' in body

    def test_metrics_contains_health_counter(self, client):
        client.get('/health')
        response = client.get('/metrics')
        body = response.data.decode()
        assert 'app_health_checks_total' in body
