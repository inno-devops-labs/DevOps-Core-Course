import pytest


@pytest.fixture(autouse=True)
def isolated_visits_file(tmp_path, monkeypatch):
    """Each test gets its own visits file so order does not affect counts."""
    monkeypatch.setenv("VISITS_FILE_PATH", str(tmp_path / "visits"))
