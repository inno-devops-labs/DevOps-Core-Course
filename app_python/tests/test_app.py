"""Unit tests for DevOps Info Service."""
import json
import pytest
import app as app_module
from app import app, get_system_info, get_uptime


@pytest.fixture(autouse=True)
def isolate_visits(tmp_path):
    """Redirect visits file to a temp directory for every test."""
    tmp_file = str(tmp_path / "visits")
    original = app_module.VISITS_FILE
    app_module.VISITS_FILE = tmp_file
    yield
    app_module.VISITS_FILE = original


@pytest.fixture
def client():
    """Create test client for Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# --- GET / endpoint tests ---

class TestMainEndpoint:
    """Tests for GET / endpoint."""

    def test_status_code(self, client):
        """GET / returns 200 OK."""
        response = client.get('/')
        assert response.status_code == 200

    def test_content_type(self, client):
        """GET / returns JSON content type."""
        response = client.get('/')
        assert response.content_type == 'application/json'

    def test_service_fields(self, client):
        """GET / response contains all required service fields."""
        response = client.get('/')
        data = json.loads(response.data)

        assert 'service' in data
        service = data['service']
        assert service['name'] == 'devops-info-service'
        assert service['version'] == '1.0.0'
        assert service['description'] == 'DevOps course info service'
        assert service['framework'] == 'Flask'

    def test_system_fields(self, client):
        """GET / response contains all required system fields."""
        response = client.get('/')
        data = json.loads(response.data)

        assert 'system' in data
        system = data['system']
        assert 'hostname' in system
        assert 'platform' in system
        assert 'platform_version' in system
        assert 'architecture' in system
        assert 'cpu_count' in system
        assert 'python_version' in system

    def test_system_field_types(self, client):
        """System fields have correct types."""
        response = client.get('/')
        data = json.loads(response.data)
        system = data['system']

        assert isinstance(system['hostname'], str)
        assert isinstance(system['platform'], str)
        assert isinstance(system['cpu_count'], int)
        assert system['cpu_count'] > 0

    def test_runtime_fields(self, client):
        """GET / response contains all required runtime fields."""
        response = client.get('/')
        data = json.loads(response.data)

        assert 'runtime' in data
        runtime = data['runtime']
        assert 'uptime_seconds' in runtime
        assert 'uptime_human' in runtime
        assert 'current_time' in runtime
        assert runtime['timezone'] == 'UTC'

    def test_runtime_field_types(self, client):
        """Runtime fields have correct types."""
        response = client.get('/')
        data = json.loads(response.data)
        runtime = data['runtime']

        assert isinstance(runtime['uptime_seconds'], int)
        assert runtime['uptime_seconds'] >= 0
        assert isinstance(runtime['uptime_human'], str)
        assert isinstance(runtime['current_time'], str)

    def test_request_fields(self, client):
        """GET / response contains request metadata."""
        response = client.get('/')
        data = json.loads(response.data)

        assert 'request' in data
        req = data['request']
        assert req['method'] == 'GET'
        assert req['path'] == '/'
        assert 'client_ip' in req
        assert 'user_agent' in req

    def test_endpoints_list(self, client):
        """GET / response contains endpoints list."""
        response = client.get('/')
        data = json.loads(response.data)

        assert 'endpoints' in data
        endpoints = data['endpoints']
        assert isinstance(endpoints, list)
        assert len(endpoints) == 4

        paths = [e['path'] for e in endpoints]
        assert '/' in paths
        assert '/health' in paths
        assert '/visits' in paths
        assert '/metrics' in paths

    def test_all_top_level_keys(self, client):
        """GET / response has exactly the expected top-level keys."""
        response = client.get('/')
        data = json.loads(response.data)

        expected_keys = {'service', 'system', 'runtime', 'request', 'endpoints', 'visits'}
        assert set(data.keys()) == expected_keys

    def test_custom_user_agent(self, client):
        """GET / captures custom user agent."""
        response = client.get('/', headers={'User-Agent': 'TestBot/1.0'})
        data = json.loads(response.data)
        assert data['request']['user_agent'] == 'TestBot/1.0'


# --- GET /health endpoint tests ---

class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_status_code(self, client):
        """GET /health returns 200 OK."""
        response = client.get('/health')
        assert response.status_code == 200

    def test_content_type(self, client):
        """GET /health returns JSON content type."""
        response = client.get('/health')
        assert response.content_type == 'application/json'

    def test_health_status(self, client):
        """GET /health returns 'healthy' status."""
        response = client.get('/health')
        data = json.loads(response.data)
        assert data['status'] == 'healthy'

    def test_health_fields(self, client):
        """GET /health contains all required fields."""
        response = client.get('/health')
        data = json.loads(response.data)

        assert 'status' in data
        assert 'timestamp' in data
        assert 'uptime_seconds' in data

    def test_health_field_types(self, client):
        """Health fields have correct types."""
        response = client.get('/health')
        data = json.loads(response.data)

        assert isinstance(data['status'], str)
        assert isinstance(data['timestamp'], str)
        assert isinstance(data['uptime_seconds'], int)
        assert data['uptime_seconds'] >= 0

    def test_health_all_keys(self, client):
        """GET /health has exactly the expected keys."""
        response = client.get('/health')
        data = json.loads(response.data)

        expected_keys = {'status', 'timestamp', 'uptime_seconds'}
        assert set(data.keys()) == expected_keys


# --- Error handling tests ---

class TestErrorHandling:
    """Tests for error handling."""

    def test_404_unknown_endpoint(self, client):
        """Unknown endpoints return 404."""
        response = client.get('/nonexistent')
        assert response.status_code == 404

    def test_404_json_response(self, client):
        """404 response is JSON with error fields."""
        response = client.get('/nonexistent')
        data = json.loads(response.data)

        assert 'error' in data
        assert data['error'] == 'Not Found'
        assert 'message' in data

    def test_404_content_type(self, client):
        """404 response has JSON content type."""
        response = client.get('/nonexistent')
        assert response.content_type == 'application/json'

    def test_post_method_not_allowed(self, client):
        """POST to / returns 405 Method Not Allowed."""
        response = client.post('/')
        assert response.status_code == 405

    def test_put_method_not_allowed(self, client):
        """PUT to / returns 405 Method Not Allowed."""
        response = client.put('/')
        assert response.status_code == 405


# --- Helper function tests ---

class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_system_info_returns_dict(self):
        """get_system_info returns a dictionary."""
        info = get_system_info()
        assert isinstance(info, dict)

    def test_get_system_info_keys(self):
        """get_system_info has all required keys."""
        info = get_system_info()
        required_keys = {'hostname', 'platform', 'platform_version',
                         'architecture', 'cpu_count', 'python_version'}
        assert required_keys.issubset(set(info.keys()))

    def test_get_uptime_returns_dict(self):
        """get_uptime returns a dictionary."""
        uptime = get_uptime()
        assert isinstance(uptime, dict)
        assert 'seconds' in uptime
        assert 'human' in uptime

    def test_get_uptime_non_negative(self):
        """Uptime seconds is non-negative."""
        uptime = get_uptime()
        assert uptime['seconds'] >= 0

    def test_get_uptime_human_readable(self):
        """Uptime human string contains 'minute'."""
        uptime = get_uptime()
        assert 'minute' in uptime['human']


class TestMetricsEndpoint:
    """Tests for GET /metrics endpoint."""

    def test_metrics_status_code(self, client):
        """GET /metrics returns 200."""
        response = client.get('/metrics')
        assert response.status_code == 200

    def test_metrics_content_type(self, client):
        """GET /metrics returns Prometheus text format."""
        response = client.get('/metrics')
        assert 'text/plain' in response.content_type or 'text/plain' in response.content_type

    def test_metrics_contains_http_requests_total(self, client):
        """Metrics output includes http_requests_total counter."""
        client.get('/')
        response = client.get('/metrics')
        assert b'http_requests_total' in response.data

    def test_metrics_contains_histogram(self, client):
        """Metrics output includes http_request_duration_seconds histogram."""
        client.get('/')
        response = client.get('/metrics')
        assert b'http_request_duration_seconds' in response.data

    def test_metrics_contains_gauge(self, client):
        """Metrics output includes http_requests_in_progress gauge."""
        response = client.get('/metrics')
        assert b'http_requests_in_progress' in response.data

    def test_metrics_contains_business_counter(self, client):
        """Metrics output includes business-level endpoint call counter."""
        client.get('/')
        response = client.get('/metrics')
        assert b'devops_info_endpoint_calls_total' in response.data
