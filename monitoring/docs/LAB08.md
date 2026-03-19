# LAB08 — Metrics & Monitoring with Prometheus

## 1) Architecture

```text
Browser / curl
    ↓
app-python (:5000, /metrics)
    ↓ scrape every 15s
Prometheus (:9090)
    ↓ queries (PromQL)
Grafana (:3000)
```

Flow: app exports metrics, Prometheus scrapes and stores time series, Grafana visualizes.

## 2) Application Instrumentation

Implemented in the Python app:
- `http_requests_total` (Counter) with labels: `method`, `endpoint`, `status_code`
- `http_request_duration_seconds` (Histogram) with labels: `method`, `endpoint`, `status_code`
- `http_requests_in_progress` (Gauge) with labels: `method`, `endpoint`
- `devops_info_endpoint_calls_total` (Counter, app-specific)
- `devops_info_system_collection_seconds` (Histogram, app-specific)

Why: this covers RED method (Rate, Errors, Duration) + basic app internals.

## 3) Prometheus Configuration

File: `monitoring/prometheus/prometheus.yml`

Configured scrape targets:
- `prometheus` → `localhost:9090`
- `app` → `app-python:5000` (`/metrics`)
- `loki` → `loki:3100`
- `grafana` → `grafana:3000`

Global interval:
- `scrape_interval: 15s`
- `evaluation_interval: 15s`

Retention (compose args):
- `--storage.tsdb.retention.time=15d`
- `--storage.tsdb.retention.size=10GB`

## 4) Dashboard Walkthrough

Custom Grafana dashboard includes 7 panels:
1. Request Rate by endpoint
2. Error Rate (5xx)
3. p95 Request Duration
4. Duration Heatmap
5. Active Requests
6. Status Code Distribution
7. App Uptime (`up{job="app"}`)

All panels were tested with live traffic.

## 5) PromQL Examples

1. Request rate by endpoint:
```promql
sum by (endpoint) (rate(http_requests_total[5m]))
```

2. 5xx error rate:
```promql
sum(rate(http_requests_total{status_code=~"5.."}[5m]))
```

3. p95 latency:
```promql
histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))
```

4. Active requests:
```promql
sum(http_requests_in_progress)
```

5. Status code split:
```promql
sum by (status_code) (rate(http_requests_total[5m]))
```

6. Target availability:
```promql
up
```

## 6) Production Setup

In `monitoring/docker-compose.yml`:
- Health checks enabled for all services
- Resource limits configured:
  - Prometheus: 1 CPU / 1G
  - Loki: 1 CPU / 1G
  - Grafana: 0.5 CPU / 512M
  - App: 0.5 CPU / 256M
- Persistent volumes:
  - `prometheus-data`, `loki-data`, `grafana-data`

## 7) Testing Results

Validated:
- `/metrics` endpoint returns Prometheus format
- Prometheus `/targets`: all targets are `UP`
- Query `up` returns healthy values
- Grafana panels display live data after traffic generation
- Persistence check: data remains after `docker compose down` + `up -d`

Evidence files/screenshots (attach in report):
- `targets-up.png`
- `promql-up-query.png`
- `grafana-lab08-dashboard.png`
- `grafana-lab08-panels.png`
- `metrics-endpoint.png`

## 8) Challenges & Solutions

- **Issue:** Minimal container images lacked `curl/wget` for health checks.
  - **Fix:** Replaced with command-based checks available in images.

- **Issue:** `version` field warning in Docker Compose.
  - **Fix:** Removed obsolete `version` key.

- **Issue:** Label mismatch in sample queries (`status` vs `status_code`).
  - **Fix:** Used `status_code` consistently in PromQL.

## Metrics vs Logs (Lab 7 comparison)

- **Metrics**: best for trends, SLOs, alerting, dashboards.
- **Logs**: best for detailed event context and debugging.
- Combined usage gives full observability.
