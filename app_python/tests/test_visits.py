from fastapi.testclient import TestClient
import app as app_module


def test_visits_counter_increments(tmp_path, monkeypatch):
    visits_file = tmp_path / "visits"
    monkeypatch.setattr(app_module, "visit_counter", app_module.VisitCounter(str(visits_file)))
    monkeypatch.setattr(app_module, "VISITS_FILE", str(visits_file))

    client = TestClient(app_module.app)

    first = client.get("/").json()["runtime"]["visits"]
    second = client.get("/").json()["runtime"]["visits"]
    current = client.get("/visits").json()["visits"]

    assert first == 1
    assert second == 2
    assert current == 2
