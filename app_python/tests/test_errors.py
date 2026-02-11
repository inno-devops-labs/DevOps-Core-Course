def test_404_handler(client):
    response = client.get("/ifyoureaditthenyouaregoodta")
    assert response.status_code == 404

    data = response.get_json()

    assert "message" in data
    assert "error" in data

    assert data["error"] == "Not Found"


def test_method_not_allowed(client):
    response = client.post("/")
    assert response.status_code in (405, 500)