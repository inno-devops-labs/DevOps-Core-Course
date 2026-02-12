from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_error_handler():
    response = client.get("/non-existent-endpoint")
    assert (response.json())["error"] == "Not Found"
    assert response.status_code == 404
