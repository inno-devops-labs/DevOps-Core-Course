"""Tests for visit counter persistence (Lab 12)."""


class TestVisits:
    def test_visits_increments_on_root(self, client):
        client.get("/")
        r = client.get("/visits")
        assert r.status_code == 200
        assert r.json()["visits"] == 1

    def test_visits_reflects_multiple_root_hits(self, client):
        for _ in range(3):
            client.get("/")
        r = client.get("/visits")
        assert r.json()["visits"] == 3

    def test_root_includes_visit_total(self, client):
        client.get("/")
        r = client.get("/")
        assert r.json()["visits"]["total"] >= 2
