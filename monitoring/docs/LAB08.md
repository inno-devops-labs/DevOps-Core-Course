# Lab 8: Metrics & Monitoring with Prometheus

## 1. Architecture

```
┌────────────────────────┐
│ app-python (FastAPI)   │
│ /, /health, /metrics   │
└───────────┬────────────┘
            │ scrape /metrics (15s)
┌───────────▼────────────┐
│ Prometheus (9090)      │
│ TSDB + PromQL          │
└───────────┬────────────┘
            │ query
┌───────────▼────────────┐
│ Grafana (3000)         │
│ Dashboards + Panels    │
└────────────────────────┘

Also scraped by Prometheus:
- Loki (`loki:3100/metrics`)
- Grafana (`grafana:3000/metrics`)
- Prometheus self-scrape (`localhost:9090`)
```

## 2. Application Instrumentation

Application instrumentation was added in `app_python/app.py` using `prometheus-client`.

### Implemented HTTP metrics (RED)

- `http_requests_total{method, endpoint, status_code}` (Counter)
  - Tracks request rate and status distribution (including 5xx error rate).
- `http_request_duration_seconds{method, endpoint}` (Histogram)
  - Tracks latency distribution for p50/p95/p99 style queries.
- `http_requests_in_progress{method, endpoint}` (Gauge)
  - Tracks current in-flight requests.

### App-specific metrics

- `devops_info_endpoint_calls_total{endpoint}` (Counter)
  - Tracks endpoint usage for business-level visibility.
- `devops_info_system_collection_seconds` (Histogram)
  - Tracks duration of system information collection.

### Endpoint and middleware behavior

- Added `/metrics` endpoint returning Prometheus exposition format.
- Added global HTTP middleware to record:
  - start time
  - response status code
  - duration
  - in-progress increments/decrements
- Added path normalization helper to reduce high-cardinality labels for dynamic paths.

## 3. Prometheus Configuration

File: `monitoring/prometheus/prometheus.yml`

- `scrape_interval`: `15s`
- `evaluation_interval`: `15s`
- Jobs:
  - `prometheus` -> `localhost:9090`
  - `app` -> `app-python:5000` (`/metrics`)
  - `loki` -> `loki:3100` (`/metrics`)
  - `grafana` -> `grafana:3000` (`/metrics`)

Prometheus service was added to `monitoring/docker-compose.yml` with:

- Image: `prom/prometheus:v3.9.0`
- Port: `9090:9090`
- Config mount: `./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml`
- Data volume: `prometheus-data:/prometheus`
- Retention:
  - `--storage.tsdb.retention.time=15d`
  - `--storage.tsdb.retention.size=10GB`

## 4. Grafana Dashboard Walkthrough (Target Layout)

Create a dashboard with at least these panels:

1. Request Rate
   - `sum(rate(http_requests_total[5m])) by (endpoint)`
2. Error Rate (5xx)
   - `sum(rate(http_requests_total{status_code=~"5.."}[5m]))`
3. Request Duration p95
   - `histogram_quantile(0.95, sum by (le, endpoint) (rate(http_request_duration_seconds_bucket[5m])))`
4. Request Duration Heatmap
   - `sum by (le, endpoint) (rate(http_request_duration_seconds_bucket[5m]))`
5. Active Requests
   - `sum(http_requests_in_progress) by (endpoint)`
6. Status Code Distribution
   - `sum by (status_code) (rate(http_requests_total[5m]))`
7. Uptime
   - `up{job="app"}`

## 5. PromQL Examples

1. Total request rate:
   - `sum(rate(http_requests_total[5m]))`
2. Request rate per endpoint:
   - `sum by (endpoint) (rate(http_requests_total[5m]))`
3. 5xx error rate:
   - `sum(rate(http_requests_total{status_code=~"5.."}[5m]))`
4. p95 latency:
   - `histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))`
5. Active requests:
   - `sum(http_requests_in_progress)`
6. Endpoint business usage:
   - `sum by (endpoint) (increase(devops_info_endpoint_calls_total[15m]))`

## 6. Production Setup

Production hardening in `monitoring/docker-compose.yml`:

- Health checks:
  - Prometheus: `/-/healthy`
  - Loki: `/ready`
  - Grafana: `/api/health`
  - app-python: `/health`
- Resource limits:
  - Prometheus: `1 CPU`, `1G`
  - Loki: `1 CPU`, `1G`
  - Grafana: `0.5 CPU`, `512M`
  - app-python: `0.5 CPU`, `256M`
- Persistent volumes:
  - `prometheus-data`, `loki-data`, `grafana-data`
- Retention:
  - Prometheus: `15d` and `10GB`
  - Loki: configured in `monitoring/loki/config.yml` (7 days)

## 7. Testing Results (Command-Based)

Run from repo root:

```bash
pip install -r requirements.txt
pytest app_python/tests -v
```

Run monitoring stack:

```bash
cd monitoring
docker compose up -d
docker compose ps
curl -s http://localhost:9090/-/healthy
curl -s http://localhost:5000/metrics | sed -n '1,80p'
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
```

Expected:
- `/metrics` returns Prometheus text format and custom metrics.
- Prometheus targets show `up` for jobs: `prometheus`, `app`, `loki`, `grafana`.

## 8. Challenges & Solutions

1. Port mismatch in lab text (`8000`) vs current service (`5000`):
   - Fixed by targeting `app-python:5000` in Prometheus and compose health checks.
2. Low-cardinality labels:
   - Added endpoint normalization for dynamic path segments.
3. Existing Lab 7 stack compatibility:
   - Reused `logging` network and existing Loki/Grafana services; only extended with Prometheus.

