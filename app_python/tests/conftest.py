import pytest

from app import create_app


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("VISITS_FILE", str(tmp_path / "visits"))
    app = create_app()
    app.config.update(TESTING=True, PROPAGATE_EXCEPTIONS=False)
    return app.test_client()
