import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_404_returns_json_error():
    response = client.get("/bebra")
    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "Not Found"
    assert data["message"] == "Endpoint does not exist"


def test_404_content_type():
    response = client.get("/bebra")
    assert response.headers["content-type"] == "application/json"
