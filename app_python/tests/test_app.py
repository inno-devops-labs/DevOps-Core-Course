import app as app_module
import pytest


app = app_module.app


@pytest.fixture(autouse=True)
def use_temp_visits_file(tmp_path, monkeypatch):
    visits_file = tmp_path / "visits"
    monkeypatch.setattr(app_module, "VISITS_FILE", str(visits_file))


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
    assert any(endpoint["path"] == "/visits" for endpoint in endpoints)


def test_visits_counter_persists_to_file(tmp_path, monkeypatch):
    visits_file = tmp_path / "visits"
    monkeypatch.setattr(app_module, "VISITS_FILE", str(visits_file))

    app.config.update({"TESTING": True})
    with app.test_client() as client:
        response = client.get("/visits")
        assert response.status_code == 200
        assert response.get_json()["visits"] == 0

        client.get("/")
        client.get("/")

        response = client.get("/visits")
        assert response.status_code == 200
        assert response.get_json()["visits"] == 2

    assert visits_file.exists()
    assert visits_file.read_text(encoding="utf-8").strip() == "2"


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


def test_metrics_endpoint_exposes_prometheus_text_format():
    app.config.update({"TESTING": True})
    with app.test_client() as client:
        client.get("/")
        client.get("/health")
        response = client.get("/metrics")

    assert response.status_code == 200
    body = response.data.decode("utf-8")
    assert "# HELP http_requests_total" in body
    assert "# TYPE http_requests_total counter" in body
    assert "http_requests_total{" in body
    assert "http_request_duration_seconds_bucket{" in body
    assert "http_requests_in_progress{" in body
