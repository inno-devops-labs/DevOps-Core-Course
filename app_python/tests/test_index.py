def test_index_status_code(client):
    response = client.get("/")
    assert response.status_code == 200


def test_index_response_structure(client):
    response = client.get("/")
    data = response.get_json()

    assert "endpoints" in data
    assert "request" in data
    assert "runtime" in data
    assert "service" in data
    assert "system" in data

    assert data["service"]["name"] == "devops-info-service"
    assert data["service"]["framework"] == "Flask"

    assert "hostname" in data["system"]
    assert "python_version" in data["system"]

    assert isinstance(data["runtime"]["uptime_seconds"], int)

    assert data["request"]["method"] == "GET"
    assert data["request"]["path"] == "/"

    assert "visits" in data
    assert isinstance(data["visits"], int)
