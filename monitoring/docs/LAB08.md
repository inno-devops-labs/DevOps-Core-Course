# LAB08 Report - Metrics & Monitoring with Prometheus

## 1. Architecture

Lab 8 extends the Lab 7 logging stack with application metrics and Prometheus scraping.

```text
+-------------------+          scrape /metrics          +----------------------+
| app-python        | --------------------------------> | Prometheus 3.9.0     |
| Flask + metrics   |                                   | retention: 15d/10GB  |
+---------+---------+                                   +----------+-----------+
          |                                                         |
          | logs via stdout                                          | PromQL
          v                                                         v
+---------+---------+    push logs    +----------------------+   +----------------------+
| Promtail 3.0      | --------------> | Loki 3.0             |   | Grafana 12.3.1       |
| docker_sd + labels|                 | log storage + query  |   | dashboards + alerts  |
+-------------------+                 +----------------------+   +----------------------+
```

Main flow for Lab 8:

- `app-python` exposes Prometheus metrics on `/metrics`
- `prometheus` scrapes `app`, `prometheus`, `loki`, and `grafana` every `15s`
- `grafana` has two provisioned data sources: Loki and Prometheus
- Grafana provides both the Lab 7 logs dashboard and the new Lab 8 metrics dashboard

## 2. Application Instrumentation

Files updated:

- `app_python/src/app.py`
- `app_python/requirements.txt`
- `app_python/pyproject.toml`
- `app_python/tests/test_app.py`

### Metrics added

HTTP RED metrics:

- `http_requests_total{method, endpoint, status_code}` - request counter
- `http_request_duration_seconds{method, endpoint, status_code}` - latency histogram
- `http_requests_in_progress{method, endpoint}` - active request gauge

Application-specific metrics:

- `devops_info_endpoint_calls_total{endpoint}` - endpoint usage counter
- `devops_info_system_info_collection_seconds` - system info collection histogram

Implementation details:

- Added `@app.before_request`, `@app.after_request`, and `@app.teardown_request`
- Added endpoint normalization so 404s are grouped as `unmatched`
- Excluded `/metrics` from the RED HTTP counter to avoid scrape noise
- Kept `/metrics` available in the root endpoint listing and exposed raw Prometheus output

### Example local metric output

Observed from `curl http://localhost:8000/metrics` after traffic generation:

```text
http_requests_total{endpoint="/health",method="GET",status_code="200"} 57.0
http_requests_total{endpoint="/",method="GET",status_code="200"} 15.0
http_requests_total{endpoint="unmatched",method="GET",status_code="404"} 3.0
devops_info_endpoint_calls_total{endpoint="/"} 15.0
devops_info_system_info_collection_seconds_count 15.0
```

## 3. Prometheus Configuration

Prometheus config lives in `monitoring/prometheus/prometheus.yml`.

Scrape setup:

- global scrape interval: `15s`
- `prometheus` -> `localhost:9090`
- `app` -> `app-python:5000/metrics`
- `loki` -> `loki:3100/metrics`
- `grafana` -> `grafana:3000/metrics`

Retention and persistence are configured in Compose:

- `--storage.tsdb.retention.time=15d`
- `--storage.tsdb.retention.size=10GB`
- persistent volume: `prometheus-data`

### Validation results

Prometheus `up` query:

```json
{
  "grafana:3000": "1",
  "localhost:9090": "1",
  "loki:3100": "1",
  "app-python:5000": "1"
}
```

Prometheus `/api/v1/targets` showed all four targets with `"health":"up"` and empty `lastError`.

## 4. Dashboard Walkthrough

### Metrics dashboard

File: `monitoring/grafana/dashboards/devops-info-service-metrics.json`

Panels:

1. `Request Rate by Endpoint`
   Query: `sum by (endpoint) (rate(http_requests_total[5m]))`
2. `Error Rate`
   Query: `sum(rate(http_requests_total{status_code=~"5.."}[5m]))`
3. `Request Duration p95`
   Query: `histogram_quantile(0.95, sum by (le, endpoint) (rate(http_request_duration_seconds_bucket[5m])))`
4. `Request Duration Heatmap`
   Query: `sum by (le) (rate(http_request_duration_seconds_bucket[5m]))`
5. `Active Requests`
   Query: `sum(http_requests_in_progress)`
6. `Status Code Distribution`
   Query: `sum by (status_code) (rate(http_requests_total[5m]))`
7. `Application Uptime`
   Query: `up{job="app"}`

### Logs dashboard

File: `monitoring/grafana/dashboards/devops-info-service-logs.json`

Panels:

1. `Application Logs`
   Query: `{app=~"devops-.*"}`
2. `Log Rate by App`
   Query: `sum by (app) (rate({app=~"devops-.*"}[1m]))`
3. `Log Level Distribution`
   Query: `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))`
4. `Error Logs (5m)`
   Query: `sum(count_over_time({app=~"devops-.*"} | json | level="ERROR" [5m]))`

### Grafana provisioning validation

Verified through Grafana HTTP API:

- data sources:
  - `Loki`
  - `Prometheus`
- dashboards:
  - `DevOps Info Service Metrics`
  - `DevOps Logs Overview`

## 5. PromQL Examples

1. Availability of all scraped services:

```promql
up
```

2. Request rate per endpoint:

```promql
sum by (endpoint) (rate(http_requests_total[5m]))
```

3. 5xx error rate:

```promql
sum(rate(http_requests_total{status_code=~"5.."}[5m]))
```

4. 95th percentile latency by endpoint:

```promql
histogram_quantile(0.95, sum by (le, endpoint) (rate(http_request_duration_seconds_bucket[5m])))
```

5. Concurrent requests:

```promql
sum(http_requests_in_progress)
```

6. Status-code distribution:

```promql
sum by (status_code) (rate(http_requests_total[5m]))
```

7. Raw business metric for system info collection:

```promql
rate(devops_info_system_info_collection_seconds_sum[5m])
/
rate(devops_info_system_info_collection_seconds_count[5m])
```

## 6. Production Setup

Implemented production-oriented baseline:

- health checks on `loki`, `prometheus`, `promtail`, `grafana`, `app-python`, and optional `app-bonus`
- resource limits and reservations for all services
- persistent volumes:
  - `prometheus-data`
  - `loki-data`
  - `grafana-data`
  - `promtail-positions`
- Grafana anonymous access disabled
- Prometheus retention set to `15d` and `10GB`

Resource profile used:

- Prometheus: `1 CPU`, `1G`
- Loki: `1 CPU`, `1G`
- Grafana: `0.5 CPU`, `512M`
- Apps: `0.5 CPU`, `256M`
- Promtail: `0.5 CPU`, `256M`

### Persistence proof

After `docker compose restart grafana`, the Grafana API still returned both provisioned dashboards:

- `DevOps Info Service Metrics`
- `DevOps Logs Overview`

This confirms dashboard persistence across restart with the mounted volume and provisioning files.

## 7. Testing Results

### Python tests

```text
.venv/bin/pytest app_python/tests
13 passed in 1.95s
```

### Compose validation

```text
docker compose -f monitoring/docker-compose.yml config
CONFIG_OK
```

### Healthy core services

Observed after final restart:

```text
app-python   Up (healthy)
grafana      Up (healthy)
loki         Up (healthy)
prometheus   Up (healthy)
promtail     Up (healthy)
```

### Prometheus evidence

- `curl http://localhost:9090/api/v1/query?query=up` returned `1` for all four jobs
- `curl http://localhost:9090/api/v1/targets` showed all targets `up`
- `curl http://localhost:8000/metrics` exposed counters, histograms, and gauges correctly

### Grafana evidence

- `GET /api/datasources` returned both `Loki` and `Prometheus`
- `GET /api/search?query=DevOps` returned both provisioned dashboards

### Ansible bonus validation

The monitoring role was extended with Prometheus config, dashboard provisioning, and dual data-source provisioning.

Syntax check passed:

```text
playbook: playbooks/deploy-monitoring.yml
```

Note: the repo `.vault_pass` helper uses CRLF line endings in this environment, so validation was executed with a temporary LF-normalized copy of the same script content.

### Screenshots

Screenshots are provided in `monitoring/docs/screenshots`

## 8. Metrics vs Logs

Metrics and logs answer different questions:

- Metrics are best for trends, rates, latency, uptime, and alert conditions
- Logs are best for event details, request context, stack traces, and debugging specific failures

Examples from this lab:

- Use Prometheus for request rate, p95 latency, and uptime
- Use Loki for request details, log levels, and structured error investigation

Together they give a more complete observability picture than either one alone.

## 9. Challenges & Solutions

1. Grafana upgrade compatibility from Lab 7
   - Problem: the persisted Grafana DB already contained a manually created Loki data source with a generated UID, and fixed UIDs in provisioning caused Grafana startup failure.
   - Solution: switched datasource provisioning to name-based configuration instead of hard-coded UIDs.

2. Promtail healthcheck failure
   - Problem: the `grafana/promtail:3.0.0` image does not include `wget`, so the original healthcheck always failed.
   - Solution: replaced it with a `bash` `/dev/tcp` readiness probe that works with the shipped image.

3. Ansible vault helper on WSL/Windows filesystem
   - Problem: `.vault_pass` has CRLF line endings, which breaks `/usr/bin/env bash`.
   - Solution: used a temporary LF-normalized copy for syntax validation without changing the repo helper.

## 10. Summary

Lab 8 is implemented end to end:

- Python app instrumented with Prometheus metrics
- Prometheus added to the monitoring stack and scraping all required targets
- Grafana provisioned with Prometheus and Loki data sources
- Custom metrics and logs dashboards provisioned automatically
- Health checks, limits, retention, and persistence configured
- Ansible monitoring role extended for the bonus path
