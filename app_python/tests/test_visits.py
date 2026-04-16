import pytest

def test_visits_endpoint(client):
    response = client.get("/visits")
    assert response.status_code == 200
    data = response.get_json()
    assert "visits" in data
    assert isinstance(data["visits"], int)