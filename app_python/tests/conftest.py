"""
Test fixtures for DevOps Info Service
"""

import pytest
from fastapi.testclient import TestClient
from app import app


@pytest.fixture
def client():
    """Create test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_request_headers():
    """Sample request headers for testing."""
    return {
        "User-Agent": "Test-Agent/1.0",
        "X-Forwarded-For": "192.168.1.1",
    }


@pytest.fixture(scope="session")
def expected_service_info():
    """Expected service information structure."""
    return {
        "name": "devops-info-service",
        "version": "1.0.0",
        "description": "DevOps course info service",
        "framework": "FastAPI",
    }