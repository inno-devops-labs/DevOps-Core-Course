from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_compose_has_required_services_and_images():
    compose = _read("docker-compose.yml")
    assert "grafana/loki:3.0.0" in compose
    assert "grafana/promtail:3.0.0" in compose
    assert "grafana/grafana:12.3.1" in compose
    assert "app-python:" in compose


def test_compose_has_production_settings():
    compose = _read("docker-compose.yml")
    assert "GF_AUTH_ANONYMOUS_ENABLED: \"false\"" in compose
    assert "GF_SECURITY_ADMIN_PASSWORD" in compose
    assert "healthcheck:" in compose
    assert "deploy:" in compose
    assert "resources:" in compose


def test_promtail_filters_promtail_label_and_extracts_app_label():
    config = _read("promtail/config.yml")
    assert "logging=promtail" in config
    assert "__meta_docker_container_name" in config
    assert "__meta_docker_container_label_app" in config
    assert "target_label: \"app\"" in config


def test_loki_uses_tsdb_v13_and_retention():
    config = _read("loki/config.yml")
    assert "store: tsdb" in config
    assert "schema: v13" in config
    assert "retention_period: 168h" in config


def test_dashboard_has_required_panels_and_queries():
    dashboard_path = ROOT / "grafana/dashboards/lab07-logs-dashboard.json"
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))

    panels = dashboard["panels"]
    titles = {panel["title"] for panel in panels}
    assert titles == {
        "Logs Table",
        "Request Rate",
        "Error Logs",
        "Log Level Distribution",
    }

    queries = {panel["title"]: panel["targets"][0]["expr"] for panel in panels}
    assert queries["Logs Table"] == '{app=~"devops-.*"}'
    assert queries["Request Rate"] == 'sum by (app) (rate({app=~"devops-.*"}[1m]))'
    assert queries["Error Logs"] == '{app=~"devops-.*"} | json | level="ERROR"'
    assert queries["Log Level Distribution"] == (
        'sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))'
    )
