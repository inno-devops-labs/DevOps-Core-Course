"""
Unit tests for the persistent visits counter.
"""
import app as app_module


def test_visits_endpoint_returns_current_count(client, tmp_path, monkeypatch):
    visits_file = tmp_path / "visits"
    monkeypatch.setattr(app_module, "VISITS_FILE", visits_file)

    response = client.get("/visits")

    assert response.status_code == 200
    assert response.json()["visits"] == 0
    assert response.json()["file"] == str(visits_file)


def test_root_endpoint_increments_visits_file(client, tmp_path, monkeypatch):
    visits_file = tmp_path / "visits"
    monkeypatch.setattr(app_module, "VISITS_FILE", visits_file)

    client.get("/")
    client.get("/")
    response = client.get("/visits")

    assert response.json()["visits"] == 2
    assert visits_file.read_text(encoding="utf-8") == "2"
