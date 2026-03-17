def test_metrics_endpoint_returns_prometheus_format(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.mimetype.startswith("text/plain")

    body = response.get_data(as_text=True)
    assert "http_requests_total" in body
    assert "http_request_duration_seconds" in body
    assert "http_requests_in_progress" in body


def test_metrics_endpoint_records_http_traffic(client):
    client.get("/health")
    response = client.get("/metrics")
    body = response.get_data(as_text=True)

    assert 'endpoint="/health"' in body
    assert 'status="200"' in body
