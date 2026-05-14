def test_internal_server_error(client, monkeypatch):
    def mock_failure():
        raise Exception("Simulated failure")

    monkeypatch.setattr("app.get_uptime", mock_failure)

    response = client.get("/health")

    assert response.status_code == 500

    data = response.json()

    assert "detail" in data
    assert data["detail"] == "Health check failed"

def test_404_handler(client):
    response = client.get("/non-existent-endpoint")

    assert response.status_code == 404

    data = response.json()

    assert data["error"] == "Not Found"
    assert data["message"] == "Endpoint does not exist"
    assert data["path"] == "/non-existent-endpoint"
