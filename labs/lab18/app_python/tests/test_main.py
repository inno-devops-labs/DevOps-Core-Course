def test_main_endpoint_status(client):
    response = client.get("/")
    assert response.status_code == 200


def test_main_endpoint_structure(client):
    response = client.get("/")
    data = response.get_json()

    assert "service" in data
    assert "system" in data
    assert "runtime" in data
    assert "request" in data
    assert "endpoints" in data

    assert data["service"]["name"] == "devops-info-service"
    assert data["service"]["framework"] == "Flask"
