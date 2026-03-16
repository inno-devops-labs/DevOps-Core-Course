# Lab 08 — Metrics & Monitoring with Prometheus

## 1. Architecture

```
┌──────────────┐     ┌──────────────┐
│  app-python  │     │ app-python-  │
│  :8000       │     │ bonus :8001  │
└──────┬───────┘     └──────┬───────┘
       │  /metrics          │  /metrics
       ▼                    ▼
┌─────────────────────────────────────────────────────────┐
│                     Prometheus                          │
│          scrapes /metrics every 15 s                    │
│          TSDB storage, retention 15d / 10GB             │
│                       :9090                             │
└──────────────────────────┬──────────────────────────────┘
                           │  PromQL queries
                           ▼
                  ┌──────────────────┐
                  │     Grafana      │
                  │  (visualization) │
                  │       :3000      │
                  └──────────────────┘

Additional scrape targets:
  - prometheus (localhost:9090) — self-monitoring
  - loki (loki:3100)           — Loki internal metrics
  - grafana (grafana:3000)     — Grafana internal metrics
```

**Data flow:** Applications expose `/metrics` endpoint with Prometheus-format metrics → Prometheus scrapes (pulls) these endpoints on a 15-second interval → Time-series data is stored in TSDB → Grafana queries Prometheus using PromQL and renders dashboards.

**Integration with Lab 7 (Loki):** Both Prometheus and Loki feed into the same Grafana instance. Logs (Loki) answer *what happened*, metrics (Prometheus) answer *how much and how often*. Together they provide complete observability.

---

## 2. Application Instrumentation

### Metric definitions

| Metric Name | Type | Labels | Purpose |
|---|---|---|---|
| `http_requests_total` | Counter | `method`, `endpoint`, `status` | Total HTTP requests — the **R** in RED |
| `http_request_duration_seconds` | Histogram | `method`, `endpoint` | Request latency distribution — the **D** in RED |
| `http_requests_in_progress` | Gauge | — | Currently active requests |
| `devops_info_endpoint_calls` | Counter | `endpoint` | Business-level endpoint usage tracking |
| `devops_info_system_collection_seconds` | Histogram | — | Time spent collecting system info on `/` |

### Why these metrics?

The instrumentation follows the **RED method** (Rate, Errors, Duration) recommended for request-driven services:

- **Rate** — `http_requests_total` counter, use `rate()` to get req/s
- **Errors** — same counter filtered by `status=~"5.."` gives error rate
- **Duration** — `http_request_duration_seconds` histogram provides percentiles (p50, p95, p99)

Additionally:
- **Gauge** for in-progress requests helps detect thread/connection exhaustion
- **Business metrics** (`devops_info_endpoint_calls`) track feature usage

### Label design

Labels are kept low-cardinality:
- `endpoint` is normalized: `/`, `/health`, `/other` (not raw paths like `/user/123`)
- `status` is the HTTP status code as string
- `method` is the HTTP method

### Dependencies

Added `prometheus-client==0.23.1` to `requirements.txt` and updated `Dockerfile` to install it.

---

## 3. Prometheus Configuration

### `prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "prometheus"     # self-monitoring
    static_configs:
      - targets: ["localhost:9090"]

  - job_name: "app"            # Python applications
    static_configs:
      - targets: ["app-python:8000", "app-python-bonus:8000"]
    metrics_path: "/metrics"

  - job_name: "loki"           # Loki internal metrics
    static_configs:
      - targets: ["loki:3100"]

  - job_name: "grafana"        # Grafana internal metrics
    static_configs:
      - targets: ["grafana:3000"]
```

### Scrape targets

| Job | Target(s) | Port | Path | Purpose |
|---|---|---|---|---|
| `prometheus` | `localhost:9090` | 9090 | `/metrics` | Self-monitoring |
| `app` | `app-python:8000`, `app-python-bonus:8000` | 8000 | `/metrics` | Application RED metrics |
| `loki` | `loki:3100` | 3100 | `/metrics` | Loki internal stats |
| `grafana` | `grafana:3000` | 3000 | `/metrics` | Grafana internal stats |

### Retention

Configured via command-line flags:
- `--storage.tsdb.retention.time=15d` — keep data for 15 days
- `--storage.tsdb.retention.size=10GB` — hard limit on disk usage

---

## 4. Dashboard Walkthrough

The `grafana/dashboards/metrics.json` dashboard has 7 panels following the RED method:

| # | Panel | Type | PromQL Query | Purpose |
|---|---|---|---|---|
| 1 | Request Rate by Endpoint | Time series | `sum(rate(http_requests_total[5m])) by (endpoint)` | Shows req/s per endpoint — **Rate** |
| 2 | Error Rate (5xx) | Time series | `sum(rate(http_requests_total{status=~"5.."}[5m]))` | 5xx errors per second — **Errors** |
| 3 | Request Duration p95 | Time series | `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))` | 95th percentile latency — **Duration** |
| 4 | Request Duration Heatmap | Heatmap | `sum(increase(http_request_duration_seconds_bucket[5m])) by (le)` | Latency distribution visualization |
| 5 | Active Requests | Time series | `http_requests_in_progress` | Current concurrent request count |
| 6 | Status Code Distribution | Pie chart | `sum by (status) (increase(http_requests_total[5m]))` | Ratio of 2xx vs 4xx vs 5xx |
| 7 | Service Uptime | Stat | `up{job="app"}` | Whether services are UP (1) or DOWN (0) |

The dashboard is auto-provisioned via Grafana provisioning on startup.

---

## 5. PromQL Examples

### 1. Request rate per endpoint (Rate)
```promql
sum(rate(http_requests_total[5m])) by (endpoint)
```
Returns requests per second, grouped by endpoint. The `rate()` function handles counter resets.

### 2. Error rate percentage (Errors)
```promql
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100
```
Percentage of requests resulting in 5xx errors.

### 3. p95 latency per endpoint (Duration)
```promql
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))
```
95th percentile request duration — 95% of requests are faster than this value.

### 4. Services currently down
```promql
up == 0
```
Returns targets where the last scrape failed.

### 5. Total requests in the last hour
```promql
sum(increase(http_requests_total[1h]))
```
Absolute count of requests over the last hour.

### 6. Top endpoint by request volume
```promql
topk(3, sum by (endpoint) (rate(http_requests_total[5m])))
```
Top 3 busiest endpoints.

### 7. Prometheus scrape duration
```promql
scrape_duration_seconds{job="app"}
```
How long it takes Prometheus to scrape each app target.

---

## 6. Production Setup

### Health checks

| Service | Health endpoint | Method | Interval | Retries |
|---|---|---|---|---|
| Loki | `http://localhost:3100/ready` | wget | 10s | 5 |
| Grafana | `http://localhost:3000/api/health` | wget | 10s | 5 |
| Prometheus | `http://localhost:9090/-/healthy` | wget | 10s | 5 |
| app-python | `http://localhost:8000/health` | curl | 10s | 5 |
| app-python-bonus | `http://localhost:8000/health` | curl | 10s | 5 |

### Resource limits

| Service | CPU limit | Memory limit | CPU reservation | Memory reservation |
|---|---|---|---|---|
| Prometheus | 1.0 | 1 GB | 0.25 | 256 MB |
| Loki | 1.0 | 1 GB | 0.25 | 256 MB |
| Grafana | 1.0 | 512 MB | 0.25 | 128 MB |
| Promtail | 0.5 | 512 MB | 0.1 | 128 MB |
| App (each) | 0.5 | 256 MB | 0.1 | 64 MB |

### Retention policies

| System | Retention | Notes |
|---|---|---|
| Prometheus | 15 days / 10 GB | Whichever limit is hit first triggers cleanup |
| Loki | 168 hours (7 days) | Compactor purges expired chunks every 10 min |

### Persistent volumes

| Volume | Mounted to | Purpose |
|---|---|---|
| `prometheus-data` | `/prometheus` | TSDB storage |
| `loki-data` | `/loki` | Log chunks and indexes |
| `grafana-data` | `/var/lib/grafana` | Dashboards, settings, users |

Data survives `docker compose down` (without `-v` flag).

---

## 7. Testing Results

### Deploy and verify

```bash
cd monitoring

docker compose up -d --build
docker compose ps

# All services should show "healthy" status
```

### Generate traffic

```bash
for i in {1..50}; do curl -s http://localhost:8000/; done
for i in {1..30}; do curl -s http://localhost:8000/health; done
for i in {1..10}; do curl -s http://localhost:8000/nonexistent; done
for i in {1..20}; do curl -s http://localhost:8001/; done
```

### Verify metrics endpoint

```bash
curl -s http://localhost:8000/metrics | head -20
# Expected: Prometheus text format with http_requests_total, etc.
```

### Check Prometheus targets

Open http://localhost:9090/targets — all four jobs should show status **UP** (green).

### Test PromQL

In Prometheus UI (http://localhost:9090/graph), execute:
```promql
up
```
Expected: all scrape targets return `1`.

### Verify persistence

```bash
docker compose down
docker compose up -d
# Dashboards and Prometheus data should still be present
```

---

## 8. Challenges & Solutions

| Challenge | Solution |
|---|---|
| `prometheus_client` not available in stdlib-only Docker image | Created `requirements.txt` with `prometheus-client==0.23.1`, updated Dockerfile to `pip install -r requirements.txt` |
| `/metrics` endpoint recorded in its own metrics, causing self-referential noise | Excluded `/metrics` from the `finally` block — metrics requests don't increment counters |
| High label cardinality from raw URL paths (e.g., `/favicon.ico`, `/robots.txt`) | Normalized endpoints to `/`, `/health`, `/other` to keep cardinality low |
| Grafana dashboard not auto-detecting Prometheus datasource | Used `${DS_PROMETHEUS}` template variable with datasource type query |
| Prometheus container failing healthcheck on slow startup | Added `start_period: 15s` to give TSDB time to initialize |
| Heatmap panel not rendering histogram correctly | Used `increase()` instead of `rate()` with `format: heatmap` for proper bucket display |

---

## Metrics vs Logs — When to Use Each

| Aspect | Metrics (Prometheus) | Logs (Loki) |
|---|---|---|
| **Question answered** | How much? How often? How fast? | What happened? Why? |
| **Data model** | Numeric time series with labels | Structured text streams |
| **Storage cost** | Very low (8 bytes per data point) | High (full text of every event) |
| **Query speed** | Milliseconds (pre-aggregated) | Seconds (scans raw text) |
| **Use case** | Dashboards, alerting, SLOs | Debugging, audit trails, forensics |
| **Retention** | Weeks to months (cheap) | Days to weeks (expensive) |
| **Example** | "Error rate is 2.5% in the last 5min" | "User X got 500 on POST /api/order at 14:32:01" |

**Best practice:** Use metrics to **detect** problems (alert on error rate spike), then switch to logs to **diagnose** them (find the specific error message and stack trace).
