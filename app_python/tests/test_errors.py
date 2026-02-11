from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_404_handler():
    response = client.get("/non-existent-endpoint")
    assert response.status_code == 404

    data = response.json()
    assert data["error"] == "Not Found"
