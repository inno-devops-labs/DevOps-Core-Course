import pytest
import requests


def test_invalid_endpoint():
    assert requests.get("http://127.0.0.1:8000/12345").status_code == 404