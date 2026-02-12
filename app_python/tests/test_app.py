import app as app_module


app = app_module.app


def test_index_returns_service_system_runtime_request():
    app.config.update({"TESTING": True})
    with app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 200
    data = response.get_json()

    assert isinstance(data, dict)
    assert set(["service", "system", "runtime", "request", "endpoints"]).issubset(data.keys())

    service = data["service"]
    assert service["name"] == "devops-info-service"
    assert service["framework"] == "Flask"

    system = data["system"]
    assert system["hostname"]
    assert isinstance(system["cpu_count"], int)

    runtime = data["runtime"]
    assert isinstance(runtime["uptime_seconds"], int)
    assert runtime["timezone"] == "UTC"

    endpoints = data["endpoints"]
    assert any(endpoint["path"] == "/health" for endpoint in endpoints)


def test_health_returns_status_and_uptime():
    app.config.update({"TESTING": True})
    with app.test_client() as client:
        response = client.get("/health")

    assert response.status_code == 200
    data = response.get_json()

    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert isinstance(data["uptime_seconds"], int)


def test_not_found_returns_json():
    app.config.update({"TESTING": True})
    with app.test_client() as client:
        response = client.get("/does-not-exist")

    assert response.status_code == 404
    data = response.get_json()

    assert data["error"] == "Not Found"
    assert "message" in data


def test_internal_error_returns_json(monkeypatch):
    original_testing = app.config.get("TESTING")
    original_propagate = app.config.get("PROPAGATE_EXCEPTIONS")

    def boom():
        raise RuntimeError("boom")

    monkeypatch.setattr(app_module, "get_system_info", boom)

    app.config.update({"TESTING": False, "PROPAGATE_EXCEPTIONS": False})
    with app.test_client() as client:
        response = client.get("/")

    app.config.update({
        "TESTING": original_testing,
        "PROPAGATE_EXCEPTIONS": original_propagate
    })

    assert response.status_code == 500
    data = response.get_json()

    assert data["error"] == "Internal Server Error"
    assert "message" in data
