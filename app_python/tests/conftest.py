import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def client_no_raise():
    return TestClient(app, raise_server_exceptions=False)
