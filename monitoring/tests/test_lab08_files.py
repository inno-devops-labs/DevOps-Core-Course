from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_compose_includes_prometheus_and_retention_flags():
    compose = _read("docker-compose.yml")
    assert "prom/prometheus:v3.9.0" in compose
    assert "--storage.tsdb.retention.time=15d" in compose
    assert "--storage.tsdb.retention.size=10GB" in compose
    assert "prometheus-data" in compose


def test_compose_has_required_resource_limits():
    compose = _read("docker-compose.yml")
    assert "loki:" in compose
    assert "grafana:" in compose
    assert "app-python:" in compose
    assert "memory: 1G" in compose
    assert "cpus: \"1.0\"" in compose
    assert "memory: 512M" in compose
    assert "cpus: \"0.50\"" in compose
    assert "memory: 256M" in compose


def test_prometheus_scrape_config_contains_all_jobs():
    config = _read("prometheus/prometheus.yml")
    assert "scrape_interval: 15s" in config
    assert "job_name: 'prometheus'" in config
    assert "job_name: 'app'" in config
    assert "job_name: 'loki'" in config
    assert "job_name: 'grafana'" in config
    assert "app-python:8080" in config


def test_prometheus_datasource_is_provisioned():
    datasource = _read("grafana/provisioning/datasources/prometheus.yml")
    assert "type: prometheus" in datasource
    assert "uid: prometheus" in datasource
    assert "url: http://prometheus:9090" in datasource


def test_lab08_dashboard_has_required_panels_and_queries():
    dashboard_path = ROOT / "grafana/dashboards/lab08-metrics-dashboard.json"
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))

    panels = dashboard["panels"]
    titles = {panel["title"] for panel in panels}
    assert titles == {
        "Request Rate",
        "Error Rate",
        "Request Duration p95",
        "Request Duration Heatmap",
        "Active Requests",
        "Status Code Distribution",
        "Uptime",
    }

    queries = {panel["title"]: panel["targets"][0]["expr"] for panel in panels}
    assert queries["Request Rate"] == "sum(rate(http_requests_total[5m])) by (endpoint)"
    assert queries["Error Rate"] == 'sum(rate(http_requests_total{status_code=~"5.."}[5m]))'
    assert queries["Request Duration p95"] == (
        "histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))"
    )
    assert queries["Request Duration Heatmap"] == (
        "sum by (le) (rate(http_request_duration_seconds_bucket[5m]))"
    )
    assert queries["Active Requests"] == "http_requests_in_progress"
    assert queries["Status Code Distribution"] == "sum by (status_code) (rate(http_requests_total[5m]))"
    assert queries["Uptime"] == 'up{job="app"}'
