def test_health_status_code(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_json(client):
    response = client.get("/health")
    assert response.is_json


def test_health_response_content(client):
    response = client.get("/health")
    data = response.get_json()

    assert "status" in data
    assert data["status"] == "healthy"
