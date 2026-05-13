from app import app
import pytest


def test_health_endpoint():
    client = app.test_client()
    response = client.get("/health")

    assert (
        response.status_code == 200
        or response.status_code == 404
        or response.status_code == 500
    )

    resp = response.get_json()

    if response.status_code == 200:

        status = resp.get("status")
        assert status
        assert isinstance(status, str)

        timestamp = resp.get("timestamp")
        assert timestamp
        assert isinstance(timestamp, str)

        uptime_seconds = resp.get("uptime_seconds")
        assert uptime_seconds >= 0
        assert isinstance(uptime_seconds, int)

    elif response.status_code == 404 or response.status_code == 500:
        assert isinstance(resp, dict)

        error = resp.get("error")
        assert error
        assert isinstance(error, str)

        message = resp.get("message")
        assert message
        assert isinstance(message, str)
