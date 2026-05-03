def test_unknown_route_returns_404(client):
    response = client.get("/aboba")
    assert response.status_code == 404
