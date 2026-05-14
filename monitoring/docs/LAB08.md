# Lab 08 - Metrics and Monitoring with Prometheus

## 1. Architecture

```text
+------------------------------+
|      Grafana 12.3.1          |
|  - Loki + Prometheus DS      |
|  - Lab07 + Lab08 dashboards  |
+---------------+--------------+
                |
                | PromQL / LogQL
                v
+---------------+--------------+
|     Prometheus 3.9.0         |
|  - 15s scrape interval       |
|  - 15d / 10GB retention      |
+-------+-----------+----------+
        |           |
        | scrape    | scrape
        v           v
  app-python    Loki / Grafana metrics
```

## 2. Application Metrics

`app_python/app.py` now exposes `/metrics` and `/app1/metrics` using `prometheus_client==0.23.1`.

Implemented metric families:
- `http_requests_total{method,endpoint,status_code}` for request rate and status distribution.
- `http_request_duration_seconds{method,endpoint}` for latency histograms and p95.
- `http_requests_in_progress{method,endpoint}` for concurrency.
- `devops_info_endpoint_calls_total{endpoint}` for business-level endpoint usage.
- `devops_info_system_collection_seconds` for internal system info collection cost.

Design choices:
- Endpoint labels are normalized from the matched FastAPI route path to keep cardinality low.
- `/metrics` is excluded from request counters and latency histograms so Prometheus scrapes do not distort application traffic charts.
- The in-progress gauge still includes `/metrics`, which is useful to confirm the scrape path is active.

## 3. Prometheus

Config file: `monitoring/prometheus/prometheus.yml`

Scrape jobs:
- `prometheus` -> `localhost:9090`
- `app` -> `app-python:8000/metrics`
- `loki` -> `loki:3100/metrics`
- `grafana` -> `grafana:3000/metrics`

Global settings:
- `scrape_interval: 15s`
- `evaluation_interval: 15s`

Runtime retention is set in Compose:
- `--storage.tsdb.retention.time=15d`
- `--storage.tsdb.retention.size=10GB`

## 4. Grafana

Provisioned datasources:
- `Loki` (`uid=loki`)
- `Prometheus` (`uid=prometheus`)

Provisioned dashboard:
- `monitoring/grafana/dashboards/lab08-metrics-dashboard.json`

Panels included:
1. Request Rate
2. Error Rate
3. Request Duration p95
4. Request Duration Heatmap
5. Active Requests
6. Status Code Distribution
7. Uptime

## 5. Production Hardening

`monitoring/docker-compose.yml` now includes:
- health checks for Loki, Promtail, Grafana, Prometheus, app-python, and app-go
- persistent volumes for Loki, Grafana, and Prometheus
- resource limits aligned with the lab requirements
- Grafana metrics enabled via `GF_METRICS_ENABLED=true`

## 6. Verification Commands

Install deps and run tests:

```bash
cd app_python
pip install -r requirements.txt
pytest
```

Validate Compose:

```bash
docker compose -f monitoring/docker-compose.yml config
docker compose -f monitoring/docker-compose.yml up -d --build
docker compose -f monitoring/docker-compose.yml ps
```

Generate traffic and inspect metrics:

```bash
curl http://localhost:8000/
curl http://localhost:8000/health
curl http://localhost:8000/metrics
curl http://localhost:9090/api/v1/query --data-urlencode 'query=up'
```

## 7. Evidence

### 7.1 Docker Compose Status

Validated with:

```bash
docker compose -f monitoring/docker-compose.yml ps
```

Observed result:

```text
NAME            IMAGE                    COMMAND                  SERVICE      STATUS                    PORTS
devops-go       monitoring-app-go        "./main"                 app-go       Up (healthy)              0.0.0.0:8001->8080/tcp
devops-python   monitoring-app-python    "python app.py"          app-python   Up (healthy)              0.0.0.0:8000->8000/tcp
grafana         grafana/grafana:12.3.1   "/run.sh"                grafana      Up (healthy)              0.0.0.0:3000->3000/tcp
loki            grafana/loki:3.0.0       "/usr/bin/loki ..."      loki         Up (healthy)              0.0.0.0:3100->3100/tcp
prometheus      prom/prometheus:v3.9.0   "/bin/prometheus ..."    prometheus   Up (healthy)              0.0.0.0:9090->9090/tcp
promtail        grafana/promtail:3.0.0   "/usr/bin/promtail ..."  promtail     Up (healthy)
```

This confirms the monitoring stack, both sample apps, and log shipping are running successfully.

### 7.2 Prometheus Target Verification

Validated with:

```bash
docker exec prometheus wget -qO- 'http://localhost:9090/api/v1/query?query=up'
```

Observed result:

```json
{
  "status": "success",
  "data": {
    "resultType": "vector",
    "result": [
      {"metric": {"instance": "loki:3100", "job": "loki"}, "value": [1774894567.653, "1"]},
      {"metric": {"instance": "grafana:3000", "job": "grafana"}, "value": [1774894567.653, "1"]},
      {"metric": {"instance": "localhost:9090", "job": "prometheus"}, "value": [1774894567.653, "1"]},
      {"metric": {"instance": "app-python:8000", "job": "app"}, "value": [1774894567.653, "1"]}
    ]
  }
}
```

Interpretation:
- All four configured scrape jobs are present.
- Every target returned `up = 1`, so Prometheus scraping is working.

### 7.3 Application Metrics Endpoint

Validated with:

```bash
docker exec devops-python python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/metrics').read().decode()[:1500])"
```

Observed excerpt:

```text
# HELP python_gc_objects_collected_total Objects collected during gc
# TYPE python_gc_objects_collected_total counter
python_gc_objects_collected_total{generation="0"} 3891.0
...
# HELP python_info Python platform information
# TYPE python_info gauge
python_info{implementation="CPython",major="3",minor="12",patchlevel="13",version="3.12.13"} 1.0
# HELP process_virtual_memory_bytes Virtual memory size in bytes.
# TYPE process_virtual_memory_bytes gauge
process_virtual_memory_bytes 2.42081792e+08
```

Additionally verified during runtime:
- `http_requests_total`
- `http_request_duration_seconds`
- `http_requests_in_progress`
- `devops_info_endpoint_calls_total`
- `devops_info_system_collection_seconds`

This confirms the application exposes Prometheus-format metrics and includes both default process metrics and custom lab metrics.

### 7.4 Grafana Provisioning Evidence

Provisioned automatically via:
- `monitoring/grafana/provisioning/datasources/loki.yml`
- `monitoring/grafana/provisioning/dashboards/dashboard.yml`
- `monitoring/grafana/dashboards/lab08-metrics-dashboard.json`

Runtime evidence from Grafana startup logs showed:
- insertion of datasource `Prometheus`
- successful dashboard provisioning completion

### 7.5 WSL Access Note

In this environment, browser access may require opening the published ports from Windows rather than from inside the restricted WSL shell:

- `http://127.0.0.1:3000`
- `http://127.0.0.1:9090`
- `http://127.0.0.1:8000/metrics`

If localhost forwarding is disabled on the host, use the Windows-reachable WSL IP instead.

## 8. Ansible Alignment

The monitoring Ansible role now templates:
- Prometheus config
- Prometheus datasource
- Lab 08 dashboard
- Updated Compose stack with Prometheus and health checks
