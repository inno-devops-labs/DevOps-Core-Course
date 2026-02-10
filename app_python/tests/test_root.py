import json
from app import app

def test_root_endpoint():
    client = app.test_client()
    response = client.get('/')

    assert response.status_code == 200

    data = response.get_json()
    assert isinstance(data, dict)

    assert "service" in data
    assert "system" in data
    assert "runtime" in data