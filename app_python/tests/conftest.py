"""
Test configuration and fixtures for the DevOps Info Service
"""
import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture
def client():
    """
    Fixture that provides a TestClient for making requests to the FastAPI application.
    This allows testing endpoints without starting an actual server.
    """
    return TestClient(app)
