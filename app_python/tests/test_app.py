from fastapi.testclient import TestClient
import app as app_module

client = TestClient(app_module.app)


def test_root_endpoint_structure(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "VISITS_FILE", tmp_path / "visits")

    response = client.get("/")
    assert response.status_code == 200

    data = response.json()

    assert "service" in data
    assert "system" in data
    assert "runtime" in data
    assert "request" in data
    assert "endpoints" in data
    assert "visits" in data
    assert "configuration" in data


def test_root_service_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "VISITS_FILE", tmp_path / "visits")

    response = client.get("/")
    data = response.json()

    assert data["service"]["name"] == "devops-info-service"
    assert data["service"]["framework"] == "FastAPI"


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "uptime_seconds" in data


def test_visits_endpoint_counts_requests(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "VISITS_FILE", tmp_path / "visits")

    client.get("/")
    client.get("/")

    response = client.get("/visits")
    assert response.status_code == 200

    data = response.json()
    assert data["visits"] == 2


def test_404_handler():
    response = client.get("/nonexistent")
    assert response.status_code == 404

    data = response.json()
    assert data["error"] == "Not Found"
    assert data["message"] == "Endpoint does not exist"