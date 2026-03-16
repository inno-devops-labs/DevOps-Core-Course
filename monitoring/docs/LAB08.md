# Lab 8 — Metrics & Monitoring with Prometheus

## Architecture

```
Flask App (:8000/metrics)
        |
        v
  Prometheus (:9090)  <-- scrapes every 15s
        |
        v
  Grafana (:3000)  <-- visualizes metrics
        |
        +-- also queries Loki (logs from Lab 7)

Loki (:3100/metrics)  \
Grafana (:3000/metrics) +--> Prometheus also scrapes these
Prometheus self-scrape  /
```

The app exposes Prometheus metrics at `/metrics`. Prometheus scrapes it every 15 seconds and stores the data. Grafana reads from Prometheus using PromQL to build dashboards.

---

## Application Instrumentation

Three metric types were added to `app.py` using `prometheus_client`:

### HTTP metrics (RED method)

| Metric | Type | Labels | Purpose |
|--------|------|--------|---------|
| `http_requests_total` | Counter | method, endpoint, status | Request rate and error counting |
| `http_request_duration_seconds` | Histogram | method, endpoint | Request latency distribution |
| `http_requests_in_progress` | Gauge | — | Active concurrent requests |

### App-specific metrics

| Metric | Type | Labels | Purpose |
|--------|------|--------|---------|
| `devops_info_endpoint_calls_total` | Counter | endpoint | Tracks which endpoints are used most |
| `devops_info_system_collection_seconds` | Histogram | — | Time spent collecting system info |

**Why these metrics?**
- The RED method (Rate, Errors, Duration) covers the most important signals for a request-driven service
- System info collection time shows if the app is getting slower as load increases
- Endpoint call tracking lets you see usage patterns

---

## Prometheus Configuration

**File:** `monitoring/prometheus/prometheus.yml`

- Scrape interval: 15 seconds
- Retention: 15 days / max 10 GB
- 4 scrape jobs configured:

| Job | Target | Notes |
|-----|--------|-------|
| prometheus | localhost:9090 | Self-monitoring |
| app | app-python:8000 | Flask app metrics |
| loki | loki:3100 | Loki internal metrics |
| grafana | grafana:3000 | Grafana internal metrics |

Retention is set via command-line flags:
```
--storage.tsdb.retention.time=15d
--storage.tsdb.retention.size=10GB
```

---

## Dashboard Walkthrough

Dashboard file: `monitoring/grafana/provisioning/dashboards/app-dashboard.json`

Auto-provisioned via Grafana provisioning on startup.

| Panel | Type | Query | Purpose |
|-------|------|-------|---------|
| Request Rate | Time series | `sum(rate(http_requests_total[5m])) by (endpoint)` | Requests/second per endpoint |
| Error Rate (5xx) | Time series | `sum(rate(http_requests_total{status=~"5.."}[5m]))` | How many errors per second |
| Request Duration p95 | Time series | `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))` | 95th percentile latency |
| Active Requests | Gauge | `http_requests_in_progress` | Live concurrent requests |
| App Uptime | Stat | `up{job="app"}` | Is the app up or down |
| Status Code Distribution | Pie chart | `sum by (status) (rate(http_requests_total[5m]))` | 2xx vs 4xx vs 5xx split |
| Request Duration Heatmap | Heatmap | `rate(http_request_duration_seconds_bucket[5m])` | Latency distribution over time |

---

## PromQL Examples

**1. Total requests per second (request rate):**
```promql
sum(rate(http_requests_total[5m])) by (endpoint)
```
Shows how much traffic each endpoint is getting.

**2. Error rate — only 5xx responses:**
```promql
sum(rate(http_requests_total{status=~"5.."}[5m]))
```
Zero means no errors. A spike means something broke.

**3. 95th percentile latency (duration):**
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```
95% of requests finish faster than this value. Good SLA target.

**4. Which services are up:**
```promql
up
```
Returns 1 for each healthy target, 0 for down ones.

**5. CPU usage of Prometheus process:**
```promql
rate(process_cpu_seconds_total{job="prometheus"}[5m]) * 100
```
Shows Prometheus's own CPU usage percentage.

**6. Error percentage:**
```promql
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100
```
Error rate as a percentage of all requests.

---

## Production Setup

### Health Checks

All services have health checks configured:

- **Loki**: `wget http://localhost:3100/ready`
- **Grafana**: `wget http://localhost:3000/api/health`
- **Prometheus**: `wget http://localhost:9090/-/healthy`
- **App**: `curl http://localhost:8000/health`

All checks: interval 10s, timeout 5s, retries 5.

### Resource Limits

| Service | CPU | Memory |
|---------|-----|--------|
| Loki | 1.0 | 1G |
| Promtail | 0.5 | 512M |
| Grafana | 0.5 | 512M |
| Prometheus | 1.0 | 1G |
| App | 0.5 | 256M |

### Data Retention

- **Loki**: 7 days (168h), configured in `loki/config.yml`
- **Prometheus**: 15 days or 10 GB (whichever comes first), set via CLI flags

### Volumes

Named Docker volumes used for persistence:
- `loki-data` — Loki TSDB
- `grafana-data` — Grafana dashboards and settings
- `prometheus-data` — Prometheus TSDB

Data survives `docker compose down && docker compose up -d`.

---

## Testing Results

Start the stack:
```bash
cd monitoring
docker compose up -d
docker compose ps
```

Check Prometheus targets at `http://localhost:9090/targets` — all 4 jobs should show UP.

Test the app metrics endpoint:
```bash
curl http://localhost:8000/metrics
```

Expected output includes:
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{endpoint="/",method="GET",status="200"} 5.0
...
# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
...
# HELP http_requests_in_progress HTTP requests currently being processed
# TYPE http_requests_in_progress gauge
http_requests_in_progress 0.0
```

Screenshots to add:
- `screenshots/metrics-endpoint.png` — `/metrics` output in browser/curl
- `screenshots/prometheus-targets.png` — all targets UP
- `screenshots/grafana-dashboard.png` — dashboard with live data

---

## Challenges & Solutions

**Problem:** App container had no internet access, couldn't pip install prometheus-client.
**Fix:** Used `pip download` on host, saved wheel to `pip-packages/`, installed with `--no-index --find-links`.

**Problem:** Grafana datasource needed both Loki and Prometheus.
**Fix:** Added both to `grafana/provisioning/datasources/datasources.yml`, mounted into the container.

**Problem:** Dashboard needed to survive container restarts.
**Fix:** Used Grafana provisioning — JSON file mounted into `/etc/grafana/provisioning/dashboards/`, auto-loaded on start.

---

## Metrics vs Logs — When to Use Each

| Use case | Tool |
|----------|------|
| How many requests per second? | Prometheus (metrics) |
| What exactly went wrong? | Loki (logs) |
| Is the service up? | Prometheus `up` metric |
| What did a specific error say? | Loki log search |
| Latency over time | Prometheus histogram |
| Tracing a single request | Loki structured logs |

Together, metrics (Lab 8) and logs (Lab 7) give you full observability — metrics show you **when** something is wrong, logs show you **what** happened.
