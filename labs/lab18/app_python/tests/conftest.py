import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture
def client():
    """
    Creates a TestClient instance for the FastAPI app.
    This allows testing without starting the server.
    """
    return TestClient(app)
