import pytest
from fastapi.testclient import TestClient

import app as app_module
from app import app


@pytest.fixture(autouse=True)
def tmp_visits_file(tmp_path, monkeypatch):
    """Redirect VISITS_FILE to a writable temp path for all tests."""
    visits_file = str(tmp_path / "visits")
    monkeypatch.setattr(app_module, "VISITS_FILE", visits_file)
    yield visits_file


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def client_no_raise():
    return TestClient(app, raise_server_exceptions=False)
