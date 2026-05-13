"""
Unit tests for the GET /metrics endpoint and Prometheus instrumentation.
"""


class TestMetricsEndpoint:
    def test_metrics_endpoint_returns_200_status(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_endpoint_returns_prometheus_text_format(self, client):
        response = client.get("/metrics")
        assert response.headers["content-type"].startswith("text/plain")

    def test_metrics_endpoint_exposes_required_metric_families(self, client):
        client.get("/")
        client.get("/health")
        response = client.get("/metrics")
        body = response.text

        assert "http_requests_total" in body
        assert "http_request_duration_seconds" in body
        assert "http_requests_in_progress" in body
        assert "devops_info_endpoint_calls_total" in body
        assert "devops_info_system_collection_seconds" in body

    def test_metrics_endpoint_tracks_normalized_labels(self, client):
        client.get("/")
        client.get("/health")
        response = client.get("/metrics")
        body = response.text

        assert 'http_requests_total{endpoint="/",method="GET",status_code="200"}' in body
        assert (
            'http_requests_total{endpoint="/health",method="GET",status_code="200"}' in body
        )
        assert 'devops_info_endpoint_calls_total{endpoint="/"}' in body

    def test_metrics_endpoint_tracks_in_progress_gauge_for_scrape_endpoint(self, client):
        response = client.get("/metrics")
        assert 'http_requests_in_progress{endpoint="/metrics",method="GET"}' in response.text
