# LAB08 - Metrics & Monitoring with Prometheus

## 1. Architecture

```text
+---------------------+        scrape /metrics        +---------------------+
| app-python (Flask)  |------------------------------> | Prometheus 3.9.0    |
| :8080               |                                | :9090               |
| - RED HTTP metrics  |                                | TSDB retention 15d  |
| - app metrics       |                                +----------+----------+
+----------+----------+                                           |
           |                                                      | PromQL
           | logs                                                  v
           v                                           +----------+----------+
+----------+----------+                                | Grafana 12.3.1       |
| Promtail 3.0.0      |------------------------------> | dashboards + explore |
+----------+----------+           push logs            +---------------------+
           |
           v
+----------+----------+
| Loki 3.0.0          |
+---------------------+
```

## 2. Application Instrumentation

Implemented in `app_python/app.py` with `prometheus-client==0.23.1`.

### Added endpoints
- `GET /metrics` for Prometheus scrape.

### Added metrics
- `http_requests_total{method,endpoint,status_code}` (Counter): total request count.
- `http_request_duration_seconds{method,endpoint}` (Histogram): request latency distribution.
- `http_requests_in_progress` (Gauge): concurrent in-flight requests.
- `devops_info_endpoint_calls_total{endpoint}` (Counter): endpoint usage.
- `devops_info_system_collection_seconds` (Histogram): system-info build time for `/` endpoint.

### Metric design choices
- RED coverage:
  - Rate: `http_requests_total` via `rate(...)`
  - Errors: `http_requests_total{status_code=~"5.."}`
  - Duration: `http_request_duration_seconds`
- Endpoint label normalization prevents high-cardinality labels.

## 3. Prometheus Configuration

File: `monitoring/prometheus/prometheus.yml`

- `scrape_interval: 15s`
- Jobs:
  - `prometheus` -> `localhost:9090`
  - `app` -> `app-python:8080/metrics`
  - `loki` -> `loki:3100/metrics`
  - `grafana` -> `grafana:3000/metrics`

Retention is configured in compose command flags:
- `--storage.tsdb.retention.time=15d`
- `--storage.tsdb.retention.size=10GB`

## 4. Dashboard Walkthrough

Provisioned dashboard:
- `monitoring/grafana/dashboards/lab08-metrics-dashboard.json`

Panels (7 total):
1. `Request Rate`:
- `sum(rate(http_requests_total[5m])) by (endpoint)`
2. `Error Rate`:
- `sum(rate(http_requests_total{status_code=~"5.."}[5m]))`
3. `Request Duration p95`:
- `histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))`
4. `Request Duration Heatmap`:
- `sum by (le) (rate(http_request_duration_seconds_bucket[5m]))`
5. `Active Requests`:
- `http_requests_in_progress`
6. `Status Code Distribution`:
- `sum by (status_code) (rate(http_requests_total[5m]))`
7. `Uptime`:
- `up{job="app"}`

### Community dashboards
- Prometheus dashboard ID: `3662` (Prometheus Stats)
- Loki dashboard ID: `13407` (Loki Dashboard)
- Import path in Grafana: `Dashboards -> New -> Import`

## 5. PromQL Examples

1. Request throughput by endpoint:
```promql
sum(rate(http_requests_total[5m])) by (endpoint)
```

2. Total 5xx error rate:
```promql
sum(rate(http_requests_total{status_code=~"5.."}[5m]))
```

3. p95 request latency:
```promql
histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))
```

4. Current active requests:
```promql
http_requests_in_progress
```

5. Service availability check:
```promql
up{job="app"}
```

6. Endpoint call intensity (business metric):
```promql
sum(rate(devops_info_endpoint_calls_total[5m])) by (endpoint)
```

## 6. Production Setup

`monitoring/docker-compose.yml` includes:

- Health checks:
  - Prometheus `/-/healthy`
  - Loki `/ready`
  - Grafana `/api/health`
  - app `/health`
  - Promtail binary check
- Resource limits:
  - Prometheus `1G / 1.0 CPU`
  - Loki `1G / 1.0 CPU`
  - Grafana `512M / 0.50 CPU`
  - app `256M / 0.50 CPU`
- Persistence volumes:
  - `prometheus-data`
  - `loki-data`
  - `grafana-data`
  - `promtail-positions`
- Retention policy:
  - Prometheus: 15d or 10GB (whichever first)
  - Loki: `retention_period: 168h`

## 7. Testing Results

### Local checks
```bash
pytest app_python/tests monitoring/tests
cd monitoring && docker compose config
```

### Runtime verification commands
```bash
cd monitoring
docker compose up -d --build
docker compose ps
curl -fsS http://localhost:9090/-/healthy
curl -fsS http://localhost:9090/api/v1/targets
curl -fsS http://localhost:8000/metrics | head -n 40
```

### Screenshots to include in `monitoring/docs/screenshots/`
- `lab08-prometheus-targets-up.png`
- `lab08-prometheus-up-query.png`
- `lab08-grafana-6plus-panels.png`
- `lab08-compose-healthy.png`
- `lab08-persistence-proof.png`

### Metrics vs Logs (Lab07 comparison)
- Use metrics for trends/SLOs/alerts (rates, error %, latency percentiles).
- Use logs for event details and root-cause drill-down.
- Combined workflow: alert from metric spike -> inspect correlated logs in Loki.

## 8. Challenges & Solutions

1. Label mismatch between dashboard examples and task label requirement.
- Solution: standardized on `status_code` label in app and dashboard queries.

2. Grafana self-metrics scrape target reliability.
- Solution: enabled Grafana metrics with `GF_METRICS_ENABLED=true` and added Prometheus scrape job.

3. Keeping stack reproducible for grading.
- Solution: provisioned Prometheus datasource + versioned dashboard JSON in repo.
