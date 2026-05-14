def test_404_handler(client):
    response = client.get("/unknown-endpoint")
    assert response.status_code == 404

    data = response.get_json()

    assert data["error"] == "Not Found"
    assert "available_endpoints" in data
