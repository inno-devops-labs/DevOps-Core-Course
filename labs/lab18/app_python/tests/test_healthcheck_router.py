import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from core.runtime import set_start_time
from routes.router import api_router
from routes.healthcheck.schemas import HealthCheckResponse


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(api_router)
    set_start_time()
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_health_endpoint_structure(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

    data = response.json()

    HealthCheckResponse(**data)
