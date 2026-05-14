def test_root_status_code(client):
    response = client.get("/")
    assert response.status_code == 200


def test_root_json_structure(client):
    response = client.get("/")
    data = response.json()

    # Top-level keys
    assert "service" in data
    assert "system" in data
    assert "runtime" in data
    assert "request" in data
    assert "endpoints" in data


def test_root_service_fields(client):
    data = client.get("/").json()

    service = data["service"]

    assert service["name"] == "devops-info-service"
    assert service["version"] == "1.0.0"
    assert service["framework"] == "FastAPI"
    assert isinstance(service["description"], str)


def test_root_system_fields(client):
    data = client.get("/").json()

    system = data["system"]

    assert isinstance(system["hostname"], str)
    assert isinstance(system["platform"], str)
    assert isinstance(system["platform_version"], str)
    assert isinstance(system["architecture"], str)
    assert isinstance(system["cpu_count"], int)
    assert isinstance(system["python_version"], str)


def test_root_runtime_fields(client):
    data = client.get("/").json()

    runtime = data["runtime"]

    assert isinstance(runtime["uptime_seconds"], int)
    assert isinstance(runtime["uptime_human"], str)
    assert runtime["timezone"] == "UTC"
    assert runtime["current_time"].endswith("Z")


def test_root_request_metadata(client):
    headers = {"User-Agent": "pytest-agent"}
    response = client.get("/", headers=headers)

    data = response.json()
    request_data = data["request"]

    assert request_data["method"] == "GET"
    assert request_data["path"] == "/"
    assert request_data["user_agent"] == "pytest-agent"
    assert isinstance(request_data["client_ip"], str)


def test_root_endpoints_list(client):
    data = client.get("/").json()

    endpoints = data["endpoints"]

    assert isinstance(endpoints, list)
    assert any(e["path"] == "/health" for e in endpoints)
