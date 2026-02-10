import time
from fastapi.testclient import TestClient
from jsonschema import validate
from app import app

client = TestClient(app)


def test_read_health():
    response = client.get("/health")
    schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string"},
            "timestamp": {"type": "string"},
            "uptime_seconds": {"type": "integer"},
        },
        "required": ["status", "timestamp", "uptime_seconds"]
    }
    assert response.status_code == 200

    validate(instance=response.json(), schema=schema)


def test_read_root():
    response = client.get("/")

    schema = {
        "type": "object",
        "properties": {
            "service": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "version": {"type": "string"},
                    "description": {"type": "string"},
                    "framework": {"type": "string"}
                },
                "required": ["name", "version", "description", "framework"]
            },
            "system": {
                "type": "object",
                "properties": {
                    "hostname": {"type": "string"},
                    "platform": {"type": "string"},
                    "platform_version": {"type": "string"},
                    "architecture": {"type": "string"},
                    "cpu_count": {"type": "integer"},
                    "python_version": {"type": "string"}
                },
                "required": [
                    "hostname", "platform", "platform_version",
                    "architecture", "cpu_count", "python_version"
                ]
            },
            "runtime": {
                "type": "object",
                "properties": {
                    "uptime_seconds": {"type": "integer"},
                    "uptime_human": {"type": "string"},
                    "current_time": {"type": "string"},
                    "timezone": {"type": "string"}
                },
                "required": [
                    "uptime_seconds", "uptime_human",
                    "current_time", "timezone"
                ]
            },
            "request": {
                "type": "object",
                "properties": {
                    "client_ip": {"type": "string"},
                    "user_agent": {"type": "string"},
                    "method": {"type": "string"},
                    "path": {"type": "string"}
                },
                "required": ["client_ip", "user_agent", "method", "path"]
            },
            "endpoints": {"type": "array"}
        },
        "required": ["service", "system", "runtime", "request", "endpoints"]
    }

    assert response.status_code == 200

    validate(instance=response.json(), schema=schema)


def test_404_handler():
    response = client.get("/this-route-does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"] == "Not Found"


def test_uptime_increments():
    res1 = client.get("/health").json()["uptime_seconds"]
    time.sleep(1)
    res2 = client.get("/health").json()["uptime_seconds"]
    assert res2 > res1
