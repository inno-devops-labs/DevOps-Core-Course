def test_health_status_code(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_structure(client):
    data = client.get("/health").json()

    assert data["status"] == "healthy"
    assert data["service"] == "devops-info-service"
    assert data["version"] == "1.0.0"

    assert isinstance(data["timestamp"], str)
    assert data["timestamp"].endswith("Z")
    assert isinstance(data["uptime_seconds"], int)
