"""Unit tests for DevOps Info Service endpoints."""


def test_index_returns_200(client):
    """GET / returns 200 OK."""
    response = client.get("/")
    assert response.status_code == 200


def test_index_returns_json(client):
    """GET / returns valid JSON."""
    response = client.get("/")
    assert response.content_type == "application/json"
    data = response.get_json()
    assert data is not None


def test_index_service_structure(client):
    """GET / includes required service metadata."""
    response = client.get("/")
    data = response.get_json()
    assert "service" in data
    service = data["service"]
    assert service["name"] == "devops-info-service"
    assert service["version"] == "1.0.0"
    assert service["description"] == "DevOps course info service"
    assert service["framework"] == "Flask"


def test_index_system_structure(client):
    """GET / includes system info with required fields."""
    response = client.get("/")
    data = response.get_json()
    assert "system" in data
    system = data["system"]
    assert "hostname" in system
    assert "platform" in system
    assert "platform_version" in system
    assert "architecture" in system
    assert "cpu_count" in system
    assert "python_version" in system
    assert isinstance(system["cpu_count"], (int, type(None)))


def test_index_runtime_structure(client):
    """GET / includes runtime info with required fields."""
    response = client.get("/")
    data = response.get_json()
    assert "runtime" in data
    runtime = data["runtime"]
    assert "uptime_seconds" in runtime
    assert "uptime_human" in runtime
    assert "current_time" in runtime
    assert runtime["timezone"] == "UTC"
    assert isinstance(runtime["uptime_seconds"], int)


def test_index_request_structure(client):
    """GET / includes request info from the client."""
    response = client.get("/", headers={"User-Agent": "test-agent/1.0"})
    data = response.get_json()
    assert "request" in data
    req = data["request"]
    assert "client_ip" in req
    assert "user_agent" in req
    assert req["user_agent"] == "test-agent/1.0"
    assert req["method"] == "GET"
    assert req["path"] == "/"


def test_index_endpoints_list(client):
    """GET / includes list of available endpoints."""
    response = client.get("/")
    data = response.get_json()
    assert "endpoints" in data
    endpoints = data["endpoints"]
    assert len(endpoints) >= 2
    paths = [e["path"] for e in endpoints]
    assert "/" in paths
    assert "/health" in paths
    assert "/visits" in paths


def test_visits_returns_200(client):
    """GET /visits returns 200 OK."""
    response = client.get("/visits")
    assert response.status_code == 200


def test_visits_increments_on_index(client):
    """GET / increments persisted visit counter; GET /visits reflects it."""
    c1 = client.get("/visits").get_json()["visits_total"]
    client.get("/")
    c2 = client.get("/visits").get_json()["visits_total"]
    assert c2 == c1 + 1


def test_health_returns_200(client):
    """GET /health returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_json(client):
    """GET /health returns valid JSON."""
    response = client.get("/health")
    assert response.content_type == "application/json"
    data = response.get_json()
    assert data is not None


def test_health_structure(client):
    """GET /health includes status, timestamp, uptime_seconds."""
    response = client.get("/health")
    data = response.get_json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "uptime_seconds" in data
    assert isinstance(data["uptime_seconds"], int)


def test_404_nonexistent_endpoint(client):
    """GET /nonexistent returns 404 with error structure."""
    response = client.get("/nonexistent")
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Not Found"
    assert "path" in data
    assert data["path"] == "/nonexistent"


def test_404_wrong_method(client):
    """POST / returns 405 or 404 (method not allowed or not found)."""
    response = client.post("/")
    assert response.status_code in (404, 405)


def test_index_request_has_client_ip(client):
    """Request info includes client_ip field."""
    response = client.get("/")
    data = response.get_json()
    assert "request" in data
    assert "client_ip" in data["request"]
