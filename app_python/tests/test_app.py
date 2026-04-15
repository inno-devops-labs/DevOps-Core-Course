import pytest
import json
import sys
import os
from datetime import datetime
from unittest.mock import patch

# Add parent directory to path to import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app as app_module
from app import get_uptime


@pytest.fixture
def visits_file(monkeypatch, request):
    visits_path = os.path.join(os.getcwd(), f".{request.node.name}.visits")
    lock_path = f"{visits_path}.lock"
    if os.path.exists(visits_path):
        os.remove(visits_path)
    if os.path.exists(lock_path):
        os.remove(lock_path)
    monkeypatch.setattr(app_module, "VISITS_FILE", visits_path)
    yield visits_path
    if os.path.exists(visits_path):
        os.remove(visits_path)
    if os.path.exists(lock_path):
        os.remove(lock_path)


@pytest.fixture
def client(visits_file):
    app_module.app.config['TESTING'] = True
    with app_module.app.test_client() as client:
        yield client


# ============ TESTS FOR ENDPOINT: GET / ============

def test_home_endpoint_status_code(client):
    """Test that GET / returns 200 OK status code."""
    response = client.get('/')
    assert response.status_code == 200, "Home endpoint should return 200 OK"


def test_home_endpoint_json_content_type(client):
    """Test that GET / returns JSON content type."""
    response = client.get('/')
    assert response.content_type == 'application/json', "Response should be JSON"


def test_home_endpoint_required_fields(client):
    response = client.get('/')
    data = json.loads(response.data)
    
    # Check top-level sections exist
    assert 'service' in data, "Response missing 'service' section"
    assert 'system' in data, "Response missing 'system' section"
    assert 'runtime' in data, "Response missing 'runtime' section"
    assert 'request' in data, "Response missing 'request' section"
    assert 'endpoints' in data, "Response missing 'endpoints' section"
    
    # Check service section fields
    assert 'name' in data['service'], "Service missing 'name'"
    assert 'version' in data['service'], "Service missing 'version'"
    assert data['service']['name'] == 'devops-info-service', "Service name should be 'devops-info-service'"
    assert data['service']['version'] == '1.0.0', "Service version should be '1.0.0'"
    
    # Check runtime section fields
    assert 'uptime_seconds' in data['runtime'], "Runtime missing 'uptime_seconds'"
    assert 'uptime_human' in data['runtime'], "Runtime missing 'uptime_human'"
    assert 'current_time' in data['runtime'], "Runtime missing 'current_time'"
    assert 'timezone' in data['runtime'], "Runtime missing 'timezone'"
    assert data['runtime']['timezone'] == 'UTC', "Timezone should be UTC"
    
    # Check endpoints list
    assert isinstance(data['endpoints'], list), "Endpoints should be a list"
    assert len(data['endpoints']) >= 2, "Should have at least 2 endpoints"
    assert 'visits' in data, "Response missing 'visits' field"
    assert isinstance(data['visits'], int), "Visits count should be integer"
    
    # Verify specific endpoints exist
    endpoint_paths = [e['path'] for e in data['endpoints']]
    assert '/' in endpoint_paths, "Root endpoint (/) not documented"
    assert '/health' in endpoint_paths, "Health endpoint (/health) not documented"
    assert '/visits' in endpoint_paths, "Visits endpoint (/visits) not documented"


def test_home_endpoint_data_types(client):
    """Test that GET / returns correct data types for all fields."""
    response = client.get('/')
    data = json.loads(response.data)
    
    # String fields
    assert isinstance(data['service']['name'], str), "Service name should be string"
    assert isinstance(data['service']['version'], str), "Service version should be string"
    assert isinstance(data['system']['hostname'], str), "Hostname should be string"
    assert isinstance(data['system']['platform'], str), "Platform should be string"
    assert isinstance(data['runtime']['uptime_human'], str), "Uptime human should be string"
    assert isinstance(data['runtime']['timezone'], str), "Timezone should be string"
    assert isinstance(data['visits'], int), "Visits should be integer"
    
    # Integer fields
    assert isinstance(data['runtime']['uptime_seconds'], int), "Uptime seconds should be integer"
    if 'cpu_count' in data['system'] and data['system']['cpu_count'] is not None:
        assert isinstance(data['system']['cpu_count'], int), "CPU count should be integer"


def test_home_endpoint_request_info(client):
    """Test that GET / correctly captures request information."""
    custom_user_agent = "pytest-test-agent/1.0"
    headers = {'User-Agent': custom_user_agent}
    
    response = client.get('/', headers=headers)
    data = json.loads(response.data)
    
    assert data['request']['method'] == 'GET', "Should capture GET method"
    assert data['request']['path'] == '/', "Should capture root path"
    assert data['request']['user_agent'] == custom_user_agent, "Should capture User-Agent header"


def test_home_endpoint_with_different_user_agents(client):
    """Test that GET / works with various User-Agent strings."""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "curl/7.68.0",
        "python-requests/2.31.0",
        None  # No User-Agent header
    ]
    
    for ua in user_agents:
        headers = {'User-Agent': ua} if ua else {}
        response = client.get('/', headers=headers)
        assert response.status_code == 200, f"Failed with User-Agent: {ua}"


def test_visits_endpoint_starts_at_zero(client):
    response = client.get('/visits')
    data = json.loads(response.data)

    assert response.status_code == 200, "Visits endpoint should return 200 OK"
    assert data['visits'] == 0, "Visits should start at 0 for a fresh file"


def test_visits_counter_increments_and_persists(client, visits_file):
    first_response = client.get('/')
    first_data = json.loads(first_response.data)

    second_response = client.get('/')
    second_data = json.loads(second_response.data)

    visits_response = client.get('/visits')
    visits_data = json.loads(visits_response.data)

    assert first_data['visits'] == 1, "First request should increment visits to 1"
    assert second_data['visits'] == 2, "Second request should increment visits to 2"
    assert visits_data['visits'] == 2, "Visits endpoint should return the current count"
    with open(visits_file, 'r', encoding='utf-8') as file_handle:
        assert file_handle.read() == '2', "Visits file should persist the latest count"


# ============ TESTS FOR ENDPOINT: GET /health ============

def test_health_endpoint_status_code(client):
    """Test that GET /health returns 200 OK status code."""
    response = client.get('/health')
    assert response.status_code == 200, "Health endpoint should return 200 OK"


def test_health_endpoint_json_content_type(client):
    """Test that GET /health returns JSON content type."""
    response = client.get('/health')
    assert response.content_type == 'application/json', "Health response should be JSON"


def test_health_endpoint_required_fields(client):
    response = client.get('/health')
    data = json.loads(response.data)
    
    assert 'status' in data, "Health response missing 'status'"
    assert 'timestamp' in data, "Health response missing 'timestamp'"
    assert 'uptime_seconds' in data, "Health response missing 'uptime_seconds'"
    
    assert data['status'] == 'healthy', "Status should be 'healthy'"
    assert isinstance(data['uptime_seconds'], int), "Uptime seconds should be integer"
    assert data['uptime_seconds'] >= 0, "Uptime seconds should be non-negative"


def test_health_endpoint_timestamp_format(client):
    """Test that GET /health returns timestamp in valid ISO 8601 format."""
    response = client.get('/health')
    data = json.loads(response.data)
    
    timestamp = data['timestamp']
    
    # Try to parse the timestamp - should not raise exception
    try:
        # Handle both 'Z' and '+00:00' timezone formats
        if timestamp.endswith('Z'):
            timestamp = timestamp.replace('Z', '+00:00')
        datetime.fromisoformat(timestamp)
    except ValueError as e:
        pytest.fail(f"Timestamp '{timestamp}' is not in valid ISO format: {e}")


def test_health_endpoint_uptime_increases(client):
    """Test that uptime_seconds increases over time."""
    # Get first reading
    response1 = client.get('/health')
    data1 = json.loads(response1.data)
    uptime1 = data1['uptime_seconds']
    
    # Mock older start time to simulate elapsed time
    import app as app_module
    original_start_time = app_module.start_time
    
    try:
        # Set start time 10 seconds earlier
        app_module.start_time = original_start_time - 10
        
        # Get second reading
        response2 = client.get('/health')
        data2 = json.loads(response2.data)
        uptime2 = data2['uptime_seconds']
        
        assert uptime2 > uptime1, "Uptime should increase over time"
        assert uptime2 - uptime1 >= 10, "Uptime difference should be at least 10 seconds"
    finally:
        # Restore original start time
        app_module.start_time = original_start_time


# ============ TESTS FOR UPTIME HELPER FUNCTION ============

def test_get_uptime_function_structure():
    """Test that get_uptime() returns correct dictionary structure."""
    uptime = get_uptime()
    
    assert isinstance(uptime, dict), "get_uptime should return a dictionary"
    assert 'uptime_seconds' in uptime, "Uptime dict missing 'uptime_seconds'"
    assert 'uptime_human' in uptime, "Uptime dict missing 'uptime_human'"
    assert isinstance(uptime['uptime_seconds'], int), "uptime_seconds should be integer"
    assert isinstance(uptime['uptime_human'], str), "uptime_human should be string"


def test_get_uptime_human_format():
    """Test that get_uptime() returns human-readable format correctly."""
    uptime = get_uptime()
    human = uptime['uptime_human']
    
    # Should contain "hour" and "minutes"
    assert 'hour' in human, "Human readable uptime should contain 'hour'"
    assert 'minutes' in human, "Human readable uptime should contain 'minutes'"
    
    # Should be formatted as "X hour, Y minutes"
    parts = human.split(',')
    assert len(parts) == 2, "Should be formatted as 'X hour, Y minutes'"


# ============ TESTS FOR ERROR CASES ============

def test_404_not_found_handler(client):
    """Test that accessing non-existent endpoint returns 404."""
    response = client.get('/non-existent-route-12345')
    assert response.status_code == 404, "Non-existent route should return 404"
    
    # Flask default returns HTML for 404, but we just verify status code
    # This tests that the application handles invalid routes gracefully


def test_method_not_allowed(client):
    """Test that POST to GET-only endpoint returns 405."""
    response = client.post('/')
    assert response.status_code == 405, "POST to root should return 405 Method Not Allowed"
    
    response = client.post('/health')
    assert response.status_code == 405, "POST to health should return 405 Method Not Allowed"


def test_invalid_methods(client):
    """Test various HTTP methods on endpoints."""
    methods = ['put', 'delete', 'patch']
    
    for method in methods:
        # Test on root endpoint
        response = getattr(client, method)('/')
        assert response.status_code in [405, 404], f"{method.upper()} to / returned wrong status"
        
        # Test on health endpoint
        response = getattr(client, method)('/health')
        assert response.status_code in [405, 404], f"{method.upper()} to / returned wrong status"


def test_malformed_url(client):
    """Test that malformed URLs are handled gracefully."""
    # URLs with special characters
    response = client.get('/%')
    assert response.status_code in [404, 400], "Malformed URL should return 4xx error"


# ============ TESTS FOR ENVIRONMENT CONFIGURATION ============

@patch.dict('os.environ', {'PORT': '8080', 'HOST': '127.0.0.1'})
def test_environment_variables_loaded():
    """Test that environment variables are correctly loaded."""
    # Reload app module with new environment
    import importlib
    import app as app_module
    importlib.reload(app_module)
    
    assert app_module.PORT == 8080, "PORT environment variable not loaded correctly"
    assert app_module.HOST == '127.0.0.1', "HOST environment variable not loaded correctly"


def test_default_configuration():
    """Test that default configuration works without environment variables."""
    import app as app_module
    
    # Should have defaults
    assert hasattr(app_module, 'PORT'), "PORT should be defined"
    assert hasattr(app_module, 'HOST'), "HOST should be defined"
    assert hasattr(app_module, 'VISITS_FILE'), "VISITS_FILE should be defined"


# ============ TESTS FOR DATA CONSISTENCY ============

def test_uptime_consistency_across_endpoints(client):
    """Test that uptime values are consistent between / and /health."""
    response_home = client.get('/')
    data_home = json.loads(response_home.data)
    
    response_health = client.get('/health')
    data_health = json.loads(response_health.data)
    
    # Uptime should be roughly the same (allow small difference due to timing)
    uptime_diff = abs(data_home['runtime']['uptime_seconds'] - data_health['uptime_seconds'])
    assert uptime_diff < 2, f"Uptime differs by {uptime_diff} seconds between endpoints"


def test_timestamp_consistency(client):
    """Test that timestamps are in UTC timezone."""
    response = client.get('/')
    data = json.loads(response.data)
    
    # Timestamp should end with Z (Zulu/UTC) or +00:00
    timestamp = data['runtime']['current_time']
    assert timestamp.endswith('+00:00') or timestamp.endswith('Z'), \
        f"Timestamp '{timestamp}' should be in UTC timezone"
