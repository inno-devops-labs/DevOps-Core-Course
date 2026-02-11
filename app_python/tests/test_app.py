import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200

    # ✅ Проверяем что это JSON
    assert response.content_type == "application/json"

    data = response.get_json()

    # Проверяем основные блоки
    assert "service" in data
    assert "runtime" in data
    assert "request" in data
    assert "endpoints" in data

    # Проверяем конкретные значения
    assert data["service"]["framework"] == "Flask"

    # Проверяем вложенные поля
    assert "name" in data["service"]
    assert "version" in data["service"]
    assert "current_time" in data["runtime"]


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.get_json()
    assert data["status"] == "healthy"