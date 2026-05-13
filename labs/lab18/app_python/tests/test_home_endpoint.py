from app import app
import pytest


def test_home_endpoint():
    client = app.test_client()
    response = client.get("/")

    assert (
        response.status_code == 200
        or response.status_code == 404
        or response.status_code == 500
    )
    resp = response.get_json()

    if response.status_code == 200:
        message = resp.get("message")
        assert message
        assert isinstance(message, dict)

        service = message.get("service")
        assert service
        assert isinstance(service, dict)
        assert service.get("name")
        assert service.get("version")
        assert service.get("description")
        assert service.get("framework")
        assert service.get("debug status")

        system = message.get("system")
        assert system
        assert isinstance(system, dict)
        assert system.get("hostname")
        assert system.get("platform")
        assert system.get("platform_version")
        assert system.get("architecture")
        assert system.get("cpu_count")
        assert system.get("python_version")

        runtime = message.get("runtime")
        assert runtime
        assert isinstance(runtime, dict)
        assert runtime.get("uptime_seconds")
        assert runtime.get("uptime_human")
        assert runtime.get("current_time")
        assert runtime.get("timezone")

        request = message.get("request")
        assert request
        assert isinstance(request, dict)
        assert request.get("client_ip")
        assert request.get("port")
        assert request.get("user_agent")
        assert request.get("method")
        assert request.get("path")

        endpoints = message.get("endpoints")
        assert endpoints
        assert isinstance(endpoints, list)
        assert endpoints[0]
        assert endpoints[0].get("path")
        assert endpoints[1]
        assert endpoints[1].get("path")

    elif response.status_code == 404 or response.status_code == 500:
        assert isinstance(resp, dict)

        error = resp.get("error")
        assert error
        assert isinstance(error, str)

        message = resp.get("message")
        assert message
        assert isinstance(message, str)
