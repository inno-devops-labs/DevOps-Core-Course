def test_root_status_code(client):
    response = client.get("/")
    assert response.status_code == 200


def test_root_returns_json(client):
    response = client.get("/")
    assert response.is_json


def test_root_json_structure(client):
    response = client.get("/")
    data = response.get_json()

    assert isinstance(data, dict)

    # Required fields (adjust to match your app)
    assert "service" in data
    assert "system" in data
    assert "runtime" in data
    assert "request" in data
    assert "visits" in data
    assert "endpoints" in data
