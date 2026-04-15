"""
Pytest configuration and shared fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from app import app


@pytest.fixture(autouse=True)
def isolated_visits_file(tmp_path, monkeypatch):
    """Avoid writing the visit counter to /data during tests (Lab 12)."""
    monkeypatch.setenv("VISITS_FILE", str(tmp_path / "visits"))


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)
