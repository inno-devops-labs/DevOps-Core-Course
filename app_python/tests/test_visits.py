import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_visits_starts_at_zero():
    assert client.get("/visits").json() == {"visits": 0}


def test_root_increments_visits():
    client.get("/")
    assert client.get("/visits").json() == {"visits": 1}
    client.get("/")
    assert client.get("/visits").json() == {"visits": 2}


def test_visits_endpoint_does_not_increment():
    client.get("/visits")
    client.get("/visits")
    assert client.get("/visits").json() == {"visits": 0}
