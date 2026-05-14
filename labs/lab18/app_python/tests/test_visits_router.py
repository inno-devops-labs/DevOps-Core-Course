import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from routes.visits.router import visits_router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(visits_router)
    return TestClient(app)


def test_visits_endpoint_returns_zero(client):
    response = client.get("/visits")
    assert response.status_code == 200
    assert response.json() == {"visits": 0}
