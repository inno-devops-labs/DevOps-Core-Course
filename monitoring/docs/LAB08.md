# Lab 8 — Metrics & Monitoring with Prometheus

**Completion Date:** February 2026  
**Tech Stack:** Prometheus 3.9 + Grafana 12.3 + prometheus_client 0.23

---

## 1. Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  app-python     │     │  Prometheus     │     │  Grafana        │
│  /metrics       │◀────│  (scrape)       │◀────│  (query)        │
│  Port 5000      │     │  Port 9090      │     │  Port 3000      │
└────────┬────────┘     └────────▲────────┘     └─────────────────┘
         │                       │
         │ pull /metrics         │ PromQL
         │                       │
         │              ┌────────┴────────┐
         │              │  Loki, Grafana  │
         │              │  (self-metrics) │
         └──────────────┴─────────────────┘

Metric flow: App exposes /metrics → Prometheus scrapes every 15s → Grafana queries via PromQL
```

---

## 2. Application Instrumentation

### Metrics Implemented (RED Method)

| Metric | Type | Labels | Purpose |
|--------|------|--------|---------|
| `http_requests_total` | Counter | method, endpoint, status | **R**ate – total requests, error counting |
| `http_request_duration_seconds` | Histogram | method, endpoint | **D**uration – latency distribution |
| `http_requests_in_progress` | Gauge | — | Active/concurrent requests |
| `devops_info_endpoint_calls` | Counter | endpoint | Endpoint usage |
| `devops_info_system_collection_seconds` | Histogram | — | System info collection time (/) |

### Endpoint Normalization

Paths are normalized for low cardinality:
- `/`, `/health`, `/metrics` → used as-is
- Other paths (e.g. 404) → `other`

### Code Snippet

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest

http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests",
    ["method", "endpoint", "status"])
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds", "HTTP request duration",
    ["method", "endpoint"], buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0))
http_requests_in_progress = Gauge("http_requests_in_progress", "Requests in progress")
```

---

## 3. Prometheus Configuration

**File:** `monitoring/prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets: ["localhost:9090"]
  - job_name: app
    static_configs:
      - targets: ["app-python:5000"]
    metrics_path: /metrics
  - job_name: loki
    static_configs:
      - targets: ["loki:3100"]
    metrics_path: /metrics
  - job_name: grafana
    static_configs:
      - targets: ["grafana:3000"]
    metrics_path: /metrics
```

**Retention:** 15 days, 10GB (via command flags in docker-compose)

---

## 4. Dashboard Walkthrough

**Dashboard:** DevOps App Metrics (provisioned)

| Panel | Type | Query | Purpose |
|-------|------|-------|---------|
| Request Rate | Time series | `sum(rate(http_requests_total{job="app"}[5m])) by (endpoint)` | Requests/sec per endpoint |
| Error Rate | Time series | `sum(rate(http_requests_total{job="app",status=~"5.."}[5m]))` | 5xx errors/sec |
| Request Duration p95 | Time series | `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job="app"}[5m])) by (le, endpoint))` | 95th percentile latency |
| Active Requests | Gauge | `http_requests_in_progress{job="app"}` | Concurrent requests |
| Status Code Distribution | Pie chart | `sum by (status) (rate(http_requests_total{job="app"}[5m]))` | 2xx vs 4xx vs 5xx |
| Service Uptime | Stat | `up{job="app"}` | 1=UP, 0=DOWN |
| Request Duration Heatmap | Heatmap | `sum(rate(http_request_duration_seconds_bucket{job="app"}[5m])) by (le)` | Latency distribution |

---

## 5. PromQL Examples

```promql
# Request rate (req/s)
rate(http_requests_total[5m])
sum(rate(http_requests_total{job="app"}[5m])) by (endpoint)

# Error rate (5xx)
sum(rate(http_requests_total{status=~"5.."}[5m]))

# p95 latency
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))

# Active requests
http_requests_in_progress

# Service health
up{job="app"}  # 1 = up, 0 = down
```

---

## 6. Production Setup

- **Health checks:** Prometheus (`/-/healthy`), app (`/health`)
- **Resource limits:** Prometheus 1G/1 CPU; Grafana 512M/0.5 CPU; app 256M/0.5 CPU
- **Retention:** 15d, 10GB
- **Volumes:** `prometheus-data`, `loki-data`, `grafana-data` for persistence

---

## 7. Testing

```bash
cd monitoring
docker compose up -d
docker compose ps  # all healthy

# App metrics
curl http://localhost:8000/metrics

# Prometheus targets
open http://localhost:9090/targets  # all UP

# Grafana
open http://localhost:3000
# Dashboards → DevOps App Metrics
```

**Generate traffic:**
```bash
for i in {1..50}; do curl -s http://localhost:8000/ > /dev/null; done
for i in {1..50}; do curl -s http://localhost:8000/health > /dev/null; done
```

---

## 8. Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| App healthcheck in slim image | Use `python -c "import urllib.request; urllib.request.urlopen(...)"` instead of curl |
| Datasource UID for provisioning | Set `uid: prometheus` in datasources.yaml so dashboards resolve |
| Prometheus 3.x storage config | Use CLI flags `--storage.tsdb.retention.time` and `--storage.tsdb.retention.size` |

---

## Metrics vs Logs (Lab 7)

- **Metrics:** Aggregated numbers (rate, latency, counts); good for dashboards and alerting
- **Logs:** Per-event records with context; good for debugging and audit
- **Together:** Metrics for trends and SLOs, logs for root cause analysis
