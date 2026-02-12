import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

client = TestClient(app)

# --------------------------------------------------
# GET / - Verify JSON structure and required fields
# --------------------------------------------------

def test_root_status_code():
    """Root endpoint returns 200 OK"""
    response = client.get("/")
    assert response.status_code == 200

def test_root_json_structure():
    """Root endpoint has all required sections"""
    response = client.get("/")
    data = response.json()
    
    # Проверяем наличие обязательных полей (ровно то, что в API)
    assert "service" in data
    assert "system" in data
    assert "runtime" in data
    assert "request" in data
    assert "endpoints" in data

def test_root_required_fields():
    """Root endpoint service section has required fields"""
    response = client.get("/")
    service = response.json()["service"]
    
    # Проверяем конкретные поля, которые есть в твоём API
    assert "name" in service
    assert "version" in service
    assert "description" in service
    
    # Проверяем, что они не пустые
    assert service["name"] != ""
    assert service["version"] != ""

# --------------------------------------------------
# GET /health - Verify health check response
# --------------------------------------------------

def test_health_status_code():
    """Health endpoint returns 200 OK"""
    response = client.get("/health")
    assert response.status_code == 200

def test_health_response():
    """Health endpoint returns correct status"""
    response = client.get("/health")
    data = response.json()
    
    assert "status" in data
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "uptime_seconds" in data

# --------------------------------------------------
# Error cases
# --------------------------------------------------

def test_404_not_found():
    """Non-existent endpoint returns 404"""
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    
    data = response.json()
    assert "error" in data
    assert "message" in data

def test_method_not_allowed():
    """POST to GET endpoint returns 405"""
    response = client.post("/")
    assert response.status_code == 405