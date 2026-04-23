# Lab 8 — Metrics & Monitoring with Prometheus

**Name:** Makar  
**Date:** 2026-03-19  
**Lab Points:** 10 + 0 bonus

---

## 1. Architecture

### Metrics flow

```text
app-python FastAPI (:5000, /metrics)
    └── scraped every 15s by ──> Prometheus (:9090)

Loki (:3100, /metrics)
    └── scraped every 15s by ──> Prometheus (:9090)

Grafana (:3000, /metrics)
    └── scraped every 15s by ──> Prometheus (:9090)

Prometheus (:9090)
    └── queried via PromQL by ──> Grafana Dashboards
```

### Components
- **app-python** exposes Prometheus metrics on `/metrics`.
- **Prometheus 3.9.0** scrapes app, Loki, Grafana, and itself every 15s.
- **Grafana 12.3.1** visualizes Prometheus metrics via dashboard panels.
- **Loki 3.0.0** continues log aggregation from Lab 7 (logs + metrics together).

---

## 2. Application Instrumentation

Implemented in `app_python/app.py` using `prometheus_client==0.23.1`.

### Added metric families

1. **Counter**: `http_requests_total{method,endpoint,status_code}`  
   Tracks request rate and error counts (RED: Rate + Errors).

2. **Histogram**: `http_request_duration_seconds{method,endpoint,status_code}`  
   Tracks request latency distribution (RED: Duration).

3. **Gauge**: `http_requests_in_progress{method,endpoint}`  
   Tracks current in-flight requests.

4. **Business metrics**:
   - `devops_info_endpoint_calls_total{endpoint}`
   - `devops_info_system_collection_seconds`

### Instrumentation approach
- `@app.middleware("http")` captures start time, status code, duration, and in-progress requests.
- `/metrics` endpoint returns `generate_latest()` with Prometheus content type.
- Root endpoint now advertises `/metrics` in `endpoints` list.

---

## 3. Prometheus Configuration

### Compose changes (`monitoring/docker-compose.yml`)
- Added `prometheus` service:
  - Image: `prom/prometheus:v3.9.0`
  - Port: `9090:9090`
  - Config mount: `./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro`
  - Persistent volume: `prometheus-data:/prometheus`
  - Retention flags:
    - `--storage.tsdb.retention.time=15d`
    - `--storage.tsdb.retention.size=10GB`
- Added health checks and production resource limits.

### Scrape config (`monitoring/prometheus/prometheus.yml`)
- `scrape_interval: 15s`
- Jobs:
  - `prometheus` → `localhost:9090`
  - `app` → `app-python:5000` (`/metrics`)
  - `loki` → `loki:3100` (`/metrics`)
  - `grafana` → `grafana:3000` (`/metrics`)

---

## 4. Dashboard Walkthrough

Provisioned dashboard JSON:  
`monitoring/grafana/dashboards/app-metrics-dashboard.json`

Provisioning files:
- `monitoring/grafana/provisioning/datasources/datasources.yml`
- `monitoring/grafana/provisioning/dashboards/dashboards.yml`

### Panels (7 total)
1. **Request Rate by Endpoint**  
   `sum(rate(http_requests_total[5m])) by (endpoint)`

2. **Error Rate (5xx)**  
   `sum(rate(http_requests_total{status_code=~"5.."}[5m]))`

3. **Request Duration p95**  
   `histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))`

4. **Request Duration Heatmap**  
   `sum by (le) (rate(http_request_duration_seconds_bucket[5m]))`

5. **Active Requests**  
   `sum(http_requests_in_progress)`

6. **Status Code Distribution**  
   `sum by (status_code) (rate(http_requests_total[5m]))`

7. **App Uptime**  
   `up{job="app"}`

---

## 5. PromQL Examples

1. **Overall request rate**  
   `sum(rate(http_requests_total[5m]))`

2. **Request rate by endpoint**  
   `sum by (endpoint) (rate(http_requests_total[5m]))`

3. **5xx error rate**  
   `sum(rate(http_requests_total{status_code=~"5.."}[5m]))`

4. **Error percentage (5xx / all)**  
   `100 * sum(rate(http_requests_total{status_code=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))`

5. **p95 latency**  
   `histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))`

6. **Service up/down**  
   `up`

7. **In-flight requests**  
   `sum(http_requests_in_progress)`

---

## 6. Production Setup

### Health checks
- Prometheus: `http://localhost:9090/-/healthy`
- Loki: `http://localhost:3100/ready`
- Grafana: `http://localhost:3000/api/health`
- app-python: Python-based HTTP check to `http://localhost:5000/health`

### Resource limits
- Prometheus: **1 CPU, 1G RAM**
- Loki: **1 CPU, 1G RAM**
- Grafana: **0.5 CPU, 512M RAM**
- app-python: **0.5 CPU, 256M RAM**

### Retention
- Prometheus retention: **15d** or **10GB** (whichever limit is reached first).
- Loki retention from Lab 7 remains configured at 7 days.

### Persistence
Persistent volumes:
- `prometheus-data`
- `loki-data`
- `grafana-data`

---

## 7. Testing Results (with console proof)

### 7.1 Python venv setup

```bash
/bin/python -m venv .venv
.venv/bin/python -m pip install -r app_python/requirements.txt -r app_python/requirements-dev.txt
```

Installed package proof (excerpt):

```text
Collecting prometheus-client==0.23.1
Successfully installed prometheus-client-0.23.1
```

### 7.2 Unit tests

```bash
.venv/bin/python -m pytest -q app_python/tests
```

Output:

```text
....                                                                     [100%]
4 passed, 13 warnings in 0.67s
```

### 7.3 Runtime endpoint proof

```bash
curl -s http://localhost:5000/health
curl -s http://localhost:5000/
curl -s http://localhost:5000/metrics | grep -E 'http_requests_total|http_request_duration_seconds_bucket|http_requests_in_progress|devops_info_endpoint_calls_total|devops_info_system_collection_seconds' | head -n 15
```

Output excerpts:

```text
{"status":"healthy","timestamp":"2026-03-19T08:54:23.162Z","uptime_seconds":46}

# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{endpoint="/health",method="GET",status_code="200"} 1.0
http_requests_total{endpoint="/",method="GET",status_code="200"} 1.0
http_request_duration_seconds_bucket{endpoint="/health",le="0.005",method="GET",status_code="200"} 1.0
...
```

### 7.4 Compose config validation

```bash
cd monitoring
docker compose config
```

Output excerpt:

```text
volumes:
  grafana-data:
    name: monitoring_grafana-data
  loki-data:
    name: monitoring_loki-data
  prometheus-data:
    name: monitoring_prometheus-data
```

## 8. Challenges & Solutions

1. **Duplicate Prometheus timeseries at app startup**  
   Cause: `uvicorn.run("app:app", ...)` re-imported module when launching from `app.py`, re-registering metrics.  
   Fix: run with object directly: `uvicorn.run(app, host=..., port=..., reload=DEBUG)`.

2. **App healthcheck in container**  
   `curl`/`wget` may be unavailable in slim Python image.  
   Fix: Python-based healthcheck command using `urllib.request`.

3. **Grafana metrics scraping**  
   Grafana `/metrics` may be disabled by default.  
   Fix: enabled `GF_METRICS_ENABLED=true` in compose.

4. **Metrics + logs comparison (Lab 7 vs Lab 8)**  
   - Use **metrics** for trend/alerting: RPS, latency, error rate, uptime.
   - Use **logs** for deep debugging and request-specific context.
   - Combined workflow: detect anomaly via metrics → investigate root cause in logs.

