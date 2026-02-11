def test_health_status_code(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_structure(client):
    response = client.get("/health")
    data = response.get_json()

    assert "status" in data
    assert "timestamp" in data
    assert "uptime_seconds" in data

    assert data["status"] == "healthy"
