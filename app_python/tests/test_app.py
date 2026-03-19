from datetime import datetime

import pytest

import app as info_service


@pytest.fixture()
def client():
    info_service.app.config.update(TESTING=True, PROPAGATE_EXCEPTIONS=False)

    with info_service.app.test_client() as test_client:
        yield test_client


def test_index_returns_expected_payload(client):
    response = client.get("/", headers={"User-Agent": "pytest-client"})

    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert set(data.keys()) == {"service", "system", "runtime", "request", "endpoints"}

    service = data["service"]
    assert service["name"] == "devops-info-service"
    assert service["version"] == "1.0.0"
    assert service["description"] == "DevOps course info service"
    assert service["framework"] == "Flask"

    system = data["system"]
    assert isinstance(system["hostname"], str)
    assert isinstance(system["platform"], str)
    assert isinstance(system["platform_version"], str)
    assert isinstance(system["architecture"], str)
    assert isinstance(system["python_version"], str)
    assert isinstance(system["cpu_count"], int) or system["cpu_count"] is None

    runtime = data["runtime"]
    assert isinstance(runtime["uptime_seconds"], int)
    assert runtime["uptime_seconds"] >= 0
    assert isinstance(runtime["uptime_human"], str)
    assert runtime["timezone"] == "UTC"
    parsed_current_time = datetime.fromisoformat(runtime["current_time"])
    assert parsed_current_time.tzinfo is not None

    request_info = data["request"]
    assert request_info["method"] == "GET"
    assert request_info["path"] == "/"
    assert request_info["user_agent"] == "pytest-client"

    endpoints = {(item["method"], item["path"]) for item in data["endpoints"]}
    assert endpoints == {("GET", "/"), ("GET", "/health"), ("GET", "/metrics")}


def test_health_returns_expected_payload(client):
    response = client.get("/health")

    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert data["status"] == "healthy"
    assert isinstance(data["uptime_seconds"], int)
    assert data["uptime_seconds"] >= 0
    parsed_timestamp = datetime.fromisoformat(data["timestamp"])
    assert parsed_timestamp.tzinfo is not None


def test_missing_route_returns_json_404(client):
    response = client.get("/missing")

    assert response.status_code == 404
    data = response.get_json()
    assert data == {"error": "Not Found", "message": "Endpoint does not exist"}


def test_unhandled_exception_returns_json_500(client, monkeypatch):
    def broken_service_info():
        raise RuntimeError("forced failure")

    monkeypatch.setattr(info_service, "get_service_info", broken_service_info)

    response = client.get("/")

    assert response.status_code == 500
    data = response.get_json()
    assert data == {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
    }


def test_metrics_endpoint_exposes_prometheus_metrics(client):
    client.get("/", headers={"User-Agent": "pytest-client"})
    client.get("/health")
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.content_type.startswith("text/plain")

    metrics_output = response.get_data(as_text=True)

    assert "# HELP http_requests_total Total HTTP requests" in metrics_output
    assert '# TYPE http_requests_total counter' in metrics_output
    assert 'http_requests_total{endpoint="/",method="GET",status_code="200"}' in metrics_output
    assert 'http_requests_total{endpoint="/health",method="GET",status_code="200"}' in metrics_output

    assert "# HELP http_request_duration_seconds HTTP request duration in seconds" in metrics_output
    assert 'http_request_duration_seconds_bucket{endpoint="/",le=' in metrics_output
    assert 'method="GET",status_code="200"}' in metrics_output
    assert 'http_request_duration_seconds_bucket{endpoint="/health",le=' in metrics_output

    assert "# HELP http_requests_in_progress HTTP requests currently being processed" in metrics_output
    assert 'http_requests_in_progress{endpoint="/metrics",method="GET"}' in metrics_output

    assert "# HELP devops_info_endpoint_calls_total Total calls to application endpoints" in metrics_output
    assert 'devops_info_endpoint_calls_total{endpoint="/"}' in metrics_output
    assert 'devops_info_endpoint_calls_total{endpoint="/health"}' in metrics_output
    assert 'devops_info_endpoint_calls_total{endpoint="/metrics"}' in metrics_output

    assert "# HELP devops_info_system_collection_seconds Time spent collecting system information" in metrics_output
    assert 'devops_info_system_collection_seconds_bucket{le=' in metrics_output
