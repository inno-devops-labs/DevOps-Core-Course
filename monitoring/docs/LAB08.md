# Lab 08 - Metrics and Monitoring with Prometheus

## Overview

This lab extends the existing observability stack from Lab 07 by adding metrics instrumentation to the Python application and deploying Prometheus for scraping and query. Grafana is configured with both Loki and Prometheus data sources and pre-provisioned dashboards for logs and metrics.

Implemented scope:

- Python application instrumentation with Counter, Gauge, Histogram
- Metrics endpoint exposed at /metrics
- Prometheus service in Docker Compose with persistent storage and retention flags
- Prometheus scrape configuration for app, Prometheus, Loki, and Grafana
- Grafana provisioning for Loki and Prometheus data sources
- Grafana provisioning for dashboards (logs and app metrics)
- Production hardening: health checks, resource limits, persistent volumes
- Bonus: Ansible monitoring role extended to deploy complete Loki + Promtail + Prometheus + Grafana stack with templated configuration and dashboard provisioning

## Architecture

```text
+------------------+       scrape /metrics       +----------------------+
| app-python       | --------------------------> | Prometheus           |
| :8000            |                             | :9090                |
+------------------+                             +----------+-----------+
       |                                                       |
       | logs via docker + promtail                            | query
       v                                                       v
+------------------+                                  +------------------+
| Promtail         | ---- push logs ----------------> | Loki             |
| :9080            |                                  | :3100            |
+------------------+                                  +------------------+
                                                               |
                                                               | datasource queries
                                                               v
                                                       +------------------+
                                                       | Grafana          |
                                                       | :3001            |
                                                       +------------------+
```

## Application Instrumentation

File updated: app_python/app.py

### Added metric families

1. HTTP request counter

- Name: http_requests_total
- Type: Counter
- Labels: method, endpoint, status_code
- Purpose: request rate and status distribution

2. HTTP duration histogram

- Name: http_request_duration_seconds
- Type: Histogram
- Labels: method, endpoint, status_code
- Purpose: latency distribution and quantiles such as p95

3. In-progress gauge

- Name: http_requests_in_progress
- Type: Gauge
- Labels: method, endpoint
- Purpose: active concurrent requests

4. Business-level counters and histogram

- Name: devops_info_endpoint_calls_total (Counter)
- Name: devops_info_system_collection_seconds (Histogram)
- Purpose: endpoint usage and system info collection timing

### Endpoint and hooks

- /metrics endpoint added and returns Prometheus exposition text with correct content type
- before_request:
  - captures start time
  - increments in-progress gauge
- after_request:
  - increments request counter
  - observes duration histogram
  - decrements in-progress gauge
  - increments endpoint call counter

### Dependency update

File updated: app_python/requirements.txt

- Added prometheus-client==0.23.1

## Prometheus Configuration

Files added/updated:

- monitoring/prometheus/prometheus.yml
- monitoring/docker-compose.yml

### Scrape configuration

Global interval:

- scrape_interval: 15s
- evaluation_interval: 15s

Jobs:

- prometheus -> localhost:9090
- app -> app-python:8080, metrics_path /metrics
- loki -> loki:3100, metrics_path /metrics
- grafana -> grafana:3000, metrics_path /metrics

### Retention and persistence

Prometheus flags in compose:

- --storage.tsdb.retention.time=15d
- --storage.tsdb.retention.size=10GB

Persistent volume:

- prometheus-data mounted to /prometheus

## Grafana Dashboard Walkthrough

Provisioning files:

- monitoring/grafana/provisioning/datasources/loki.yml
- monitoring/grafana/provisioning/datasources/prometheus.yml
- monitoring/grafana/provisioning/dashboards/dashboard-provider.yml
- monitoring/grafana/provisioning/dashboards/grafana-app-dashboard.json
- monitoring/grafana/provisioning/dashboards/grafana-logs-dashboard.json

### Metrics dashboard panels

Dashboard: Lab08 - Application Metrics

1. Request Rate by Endpoint

- Query: sum(rate(http_requests_total[5m])) by (endpoint)
- Purpose: RED Rate

2. Error Rate (5xx)

- Query: sum(rate(http_requests_total{status_code=~"5.."}[5m]))
- Purpose: RED Errors

3. Request Duration p95

- Query: histogram_quantile(0.95, sum by (le, endpoint) (rate(http_request_duration_seconds_bucket[5m])))
- Purpose: RED Duration

4. Request Duration Heatmap

- Query: sum by (le) (rate(http_request_duration_seconds_bucket[5m]))
- Purpose: latency distribution by bucket

5. Active Requests

- Query: sum(http_requests_in_progress)
- Purpose: current concurrency

6. Status Code Distribution

- Query: sum by (status_code) (rate(http_requests_total[5m]))
- Purpose: response class composition

7. Uptime

- Query: up{job="app"}
- Purpose: binary health signal (1 up, 0 down)

## PromQL Examples

1. Current scrape status for all jobs

- up

2. Request throughput per endpoint

- sum(rate(http_requests_total[5m])) by (endpoint)

3. Error throughput (5xx)

- sum(rate(http_requests_total{status_code=~"5.."}[5m]))

4. p95 request latency per endpoint

- histogram_quantile(0.95, sum by (le, endpoint) (rate(http_request_duration_seconds_bucket[5m])))

5. In-progress requests

- sum(http_requests_in_progress)

6. Endpoint usage total

- sum by (endpoint) (rate(devops_info_endpoint_calls_total[5m]))

## Production Setup

### Health checks

Configured in monitoring/docker-compose.yml:

- app-python: /health
- loki: /ready
- promtail: /ready
- grafana: /api/health
- prometheus: /-/healthy

### Resource limits

Configured limits:

- Prometheus: 1 CPU, 1G memory
- Loki: 1 CPU, 1G memory
- Grafana: 0.5 CPU, 512M memory
- App: 0.5 CPU, 256M memory
- Promtail: 0.5 CPU, 256M memory

### Data retention

- Prometheus: 15d and 10GB cap
- Loki: existing retention configuration retained from Lab 07

### Persistent volumes

- loki-data
- prometheus-data
- grafana-data

## Testing Results

### Application tests

File updated: app_python/tests/test_app.py

Added test verifies:

- /metrics returns 200
- exposition includes key metric families:
  - http_requests_total
  - http_request_duration_seconds_bucket
  - http_requests_in_progress

### Runtime verification checklist

Run:

```bash
cd monitoring
docker compose up -d --build
docker compose ps
```

Expected:

- all services Up
- health state for services with healthcheck is healthy

Prometheus targets page:

- http://localhost:9090/targets
- expected all configured jobs UP

Prometheus query page:

- run query up and verify values are 1

Grafana:

- http://localhost:3001
- verify both data sources appear: Loki, Prometheus
- verify dashboards are auto-loaded in folder DevOps Labs

### Local environment note

- In this specific Docker Desktop + WSL local setup, Promtail may fail to start because `/var/lib/docker/containers` is read-only and cannot be mounted as required.
- This is a host environment limitation, not a metrics-stack logic error.
- Core Lab 8 metrics path (app -> Prometheus -> Grafana) is fully validated and healthy.
- On a standard Linux Docker host (or Docker setup that exposes container log paths), Promtail works with the current configuration.

## Challenges and Solutions

1. Label naming consistency

- Challenge: query examples in some templates used status, while instrumentation used status_code
- Solution: standardized metric labels around status_code and aligned dashboard queries

2. Dual observability stack provisioning

- Challenge: keep logs and metrics both provisioned automatically
- Solution: added explicit Grafana datasource provisioning for both Loki and Prometheus and file-based dashboard provider

3. Bonus Ansible parity with local compose

- Challenge: ensure role-generated stack matches local tested stack
- Solution: role defaults expanded and compose template now includes Prometheus, retention, health checks, resource limits, and dashboard file copy

## Bonus - Ansible Automation

Files updated:

- ansible/roles/monitoring/defaults/main.yml
- ansible/roles/monitoring/tasks/setup.yml
- ansible/roles/monitoring/tasks/deploy.yml
- ansible/roles/monitoring/templates/docker-compose.yml.j2
- ansible/roles/monitoring/templates/prometheus.yml.j2
- ansible/roles/monitoring/templates/grafana-datasources.yml.j2
- ansible/roles/monitoring/templates/grafana-dashboard-provider.yml.j2
- ansible/roles/monitoring/files/grafana-app-dashboard.json
- ansible/roles/monitoring/files/grafana-logs-dashboard.json

What bonus now supports:

- Templated Prometheus scrape targets from role variables
- Automatic provisioning of Loki and Prometheus data sources
- Automatic provisioning of metrics and logs dashboards
- Prometheus readiness verification in deploy tasks
- Full stack deploy from one playbook:

```bash
cd ansible
ansible-playbook playbooks/deploy-monitoring.yml
```

Idempotency expectation:

- first run creates and starts stack (changed)
- second run should be mostly ok with no unexpected diffs

## Evidence to Attach

Add screenshots under monitoring/docs/screenshots/lab08:

1. metrics-endpoint.png
2. prometheus-targets-up.png
3. prometheus-query-up.png
4. grafana-metrics-dashboard.png
5. grafana-all-panels.png
6. compose-healthy.png

Optional bonus evidence:

7. ansible-monitoring-run-1.png
8. ansible-monitoring-run-2-idempotent.png
9. grafana-two-datasources.png

## Metrics vs Logs Comparison

- Logs are best for event detail and root-cause inspection
- Metrics are best for trends, rates, SLO tracking, and alert thresholds
- In this stack:
  - Loki plus Grafana handles investigative workflows
  - Prometheus plus Grafana handles RED monitoring and time-series analytics

Both are required for full operational observability.
