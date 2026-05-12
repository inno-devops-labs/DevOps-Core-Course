import re


def test_metrics_endpoint_ok(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert b"http_requests_total" in r.data


def _http_requests_in_progress_value(data: bytes) -> float:
    m = re.search(rb"^http_requests_in_progress\s+(\S+)\s*$", data, re.MULTILINE)
    assert m is not None
    return float(m.group(1))


def test_metrics_scrape_does_not_inflate_in_progress_gauge(client):
    """Regression: /metrics must not increment http_requests_in_progress without a dec."""
    baseline = _http_requests_in_progress_value(client.get("/metrics").data)
    for _ in range(10):
        client.get("/metrics")
    after = _http_requests_in_progress_value(client.get("/metrics").data)
    assert after == baseline
