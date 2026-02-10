import pytest
import requests


def test_get_root():
    response = requests.get("http://127.0.0.1:8000/")
    check_field = response.json()["service"]["name"] == "devops-info-service"
    assert response.status_code == 200 and check_field
    

def test_get_health():
    response = requests.get("http://127.0.0.1:8000/health")
    check_field = response.json()["status"] == "healthy"
    assert response.status_code == 200 and check_field
    
