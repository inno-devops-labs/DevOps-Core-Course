def test_docker_endpoint(client):
    response = client.get("/docker")
    assert response.status_code == 200

    data = response.get_json()

    assert "is_docker" in data
    assert "container_id" in data
    assert "message" in data
