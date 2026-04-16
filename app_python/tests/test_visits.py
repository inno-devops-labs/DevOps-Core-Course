"""
Unit tests for file-backed visit persistence.
"""


class TestVisitsEndpoint:
    def test_root_endpoint_increments_visits_counter(self, client):
        first = client.get("/").json()
        second = client.get("/").json()

        assert first["visits"]["count"] == 1
        assert second["visits"]["count"] == 2

    def test_visits_endpoint_returns_current_counter(self, client):
        client.get("/")
        client.get("/")

        response = client.get("/visits")
        assert response.status_code == 200
        assert response.json()["visits"] == 2

    def test_root_endpoint_exposes_loaded_configuration(self, client):
        response = client.get("/")
        data = response.json()

        assert data["configuration"]["environment"]["APP_ENV"] == "test"
        assert data["configuration"]["file"]["applicationName"] == "devops-info-service"
        assert data["configuration"]["file"]["features"]["configHotReload"] is True
