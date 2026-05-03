def test_visits_starts_at_zero(client):
    response = client.get("/visits")
    assert response.status_code == 200
    assert response.get_json()["visits"] == 0


def test_root_increments_visits_counter(client):
    client.get("/")
    client.get("/")

    visits_response = client.get("/visits")
    assert visits_response.status_code == 200
    assert visits_response.get_json()["visits"] == 2
