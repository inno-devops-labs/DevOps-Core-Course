def test_health_status_code(client):
    r = client.get("/health")
    assert r.status_code == 200


def test_health_response_structure(client):
    r = client.get("/health")
    data = r.json()

    for key in ["status", "timestamp", "uptime_seconds"]:
        assert key in data, f"Missing health field: {key}"

    assert data["status"] == "healthy"
    assert isinstance(data["uptime_seconds"], int)
    assert data["uptime_seconds"] >= 0

    assert isinstance(data["timestamp"], str)
    assert "T" in data["timestamp"]
