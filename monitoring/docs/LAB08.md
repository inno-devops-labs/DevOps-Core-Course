# Lab 8 — Metrics & Monitoring with Prometheus

## 1. Architecture

```
┌──────────────┐     scrape /metrics     ┌──────────────┐     query      ┌──────────────┐
│  app-python  │◄────────────────────────│  Prometheus  │◄──────────────│   Grafana    │
│  (FastAPI)   │         :5000           │   (TSDB)     │    PromQL     │ (Dashboards) │
│  :5000/8000  │                         │   :9090      │               │   :3000      │
└──────────────┘                         └──────────────┘               └──────────────┘
       │                                        │                              │
       │  /metrics endpoint                     │  self-scrape                 │
       │  - http_requests_total                 │  + loki:3100/metrics         │
       │  - http_request_duration_seconds       │  + grafana:3000/metrics      │
       │  - http_requests_in_progress           │                              │
       │  - devops_info_endpoint_calls          │                              │
       │  - devops_info_system_collection_s     │                              │
       │                                        │                              │
       └──── logs ────► Loki ◄──── Promtail     │                              │
                        :3100      (docker)      │                              │
                          │                      │                              │
                          └──────────────────────┴──────────────────────────────┘
                                     Grafana datasources: Loki + Prometheus
```

**Data flow:**
1. Application exposes metrics at `/metrics` in Prometheus exposition format
2. Prometheus scrapes targets every 15s and stores time-series data in TSDB
3. Grafana queries Prometheus via PromQL and renders dashboards

## 2. Application Instrumentation

### Metrics Added

| Metric | Type | Labels | Purpose |
|--------|------|--------|---------|
| `http_requests_total` | Counter | method, endpoint, status | Total HTTP request count (RED: Rate) |
| `http_request_duration_seconds` | Histogram | method, endpoint | Request latency distribution (RED: Duration) |
| `http_requests_in_progress` | Gauge | — | Concurrent requests being processed |
| `devops_info_endpoint_calls` | Counter | endpoint | Business-level endpoint usage tracking |
| `devops_info_system_collection_seconds` | Histogram | — | Time to collect system info |

### Why These Metrics

- **RED Method** covered: Rate (`http_requests_total`), Errors (status=~"5.."), Duration (`http_request_duration_seconds`)
- **Counter** for cumulative events (requests, endpoint calls) — monotonically increasing
- **Histogram** for latency distributions — enables percentile calculations (p50, p95, p99)
- **Gauge** for current state (in-progress requests) — can go up and down

### Implementation

Metrics are defined in `app_python/metrics.py` and collected via FastAPI middleware in `app_python/app.py`:
- `@app.middleware("http")` intercepts all requests (except `/metrics` itself)
- Before request: increment `http_requests_in_progress`
- After request: record counter with labels, observe histogram duration, decrement gauge
- Business metrics tracked in individual services (`routes/root/service.py`, `routes/health_check/service.py`)

## 3. Prometheus Configuration

**File:** `monitoring/prometheus/prometheus.yml`

### Scrape Targets

| Job | Target | Metrics Path | Purpose |
|-----|--------|-------------|---------|
| `prometheus` | `localhost:9090` | `/metrics` | Self-monitoring |
| `app` | `app-python:5000` | `/metrics` | Application metrics |
| `loki` | `loki:3100` | `/metrics` | Log aggregator metrics |
| `grafana` | `grafana:3000` | `/metrics` | Dashboard tool metrics |

### Configuration

- **Scrape interval:** 15s (balance between granularity and load)
- **Evaluation interval:** 15s
- **Retention time:** 15 days
- **Retention size:** 10GB
- Docker service names used as hostnames (internal Docker DNS)

## 4. Dashboard Walkthrough

Dashboard: **Application Metrics** (`app-metrics`)

### Panels

1. **Request Rate by Endpoint** (Time Series)
   - Query: `sum(rate(http_requests_total[5m])) by (endpoint)`
   - Shows: requests/sec per endpoint over time
   - Unit: req/s

2. **Error Rate (5xx)** (Time Series)
   - Query: `sum(rate(http_requests_total{status=~"5.."}[5m]))`
   - Shows: server error rate
   - Color: red for visibility

3. **Request Duration p95** (Time Series)
   - Query: `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))`
   - Shows: 95th percentile latency per endpoint

4. **Request Duration Heatmap** (Heatmap)
   - Query: `sum(increase(http_request_duration_seconds_bucket[5m])) by (le)`
   - Shows: latency distribution over time

5. **Active Requests** (Time Series)
   - Query: `http_requests_in_progress`
   - Shows: concurrent in-flight requests

6. **Status Code Distribution** (Pie Chart)
   - Query: `sum by (status) (rate(http_requests_total[5m]))`
   - Shows: proportion of 2xx vs 4xx vs 5xx

7. **Service Uptime** (Stat)
   - Query: `up{job="app"}`
   - Shows: UP/DOWN status with color mapping

## 5. PromQL Examples

### 1. Request rate per endpoint (RED: Rate)
```promql
sum(rate(http_requests_total[5m])) by (endpoint)
```
Per-second request rate averaged over 5 minutes, grouped by endpoint.

### 2. Error rate percentage (RED: Errors)
```promql
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100
```
Percentage of requests resulting in 5xx server errors.

### 3. 95th percentile latency (RED: Duration)
```promql
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
```
95% of requests complete within this duration.

### 4. Total requests by status code
```promql
sum by (status) (increase(http_requests_total[1h]))
```
Total request count per status code over the last hour.

### 5. Services that are down
```promql
up == 0
```
Lists all scrape targets that failed their last health check.

### 6. Prometheus CPU usage
```promql
rate(process_cpu_seconds_total{job="prometheus"}[5m]) * 100
```
CPU utilization percentage of the Prometheus process.

### 7. Endpoint call distribution
```promql
sum by (endpoint) (increase(devops_info_endpoint_calls_total[1h]))
```
Business metric showing which endpoints are most popular.

## 6. Production Setup

### Health Checks

| Service | Check | Interval | Retries |
|---------|-------|----------|---------|
| Loki | `wget http://localhost:3100/ready` | 10s | 5 |
| Grafana | `wget http://localhost:3000/api/health` | 10s | 5 |
| Prometheus | `wget http://localhost:9090/-/healthy` | 10s | 5 |
| app-python | `python urllib http://localhost:5000/health` | 10s | 5 |

### Resource Limits

| Service | CPU Limit | Memory Limit | CPU Reservation | Memory Reservation |
|---------|-----------|-------------|-----------------|-------------------|
| Prometheus | 1.0 | 1G | 0.5 | 512M |
| Loki | 1.0 | 1G | 0.5 | 512M |
| Grafana | 0.5 | 512M | 0.25 | 256M |
| app-python | 0.5 | 256M | 0.25 | 128M |

### Retention Policies

- **Prometheus TSDB:** 15 days or 10GB (whichever comes first)
  - Configured via CLI flags: `--storage.tsdb.retention.time=15d --storage.tsdb.retention.size=10GB`
- **Loki:** 168h (7 days) with compaction

### Persistent Volumes

| Volume | Service | Mount Point | Purpose |
|--------|---------|-------------|---------|
| `prometheus-data` | Prometheus | `/prometheus` | TSDB time-series data |
| `loki-data` | Loki | `/loki` | Log chunks and index |
| `grafana-data` | Grafana | `/var/lib/grafana` | Dashboards, users, settings |

## 7. Testing Results

### Verification Steps

1. **Deploy stack:** `cd monitoring && docker compose up -d`
2. **Check services:** `docker compose ps` — all services should be "healthy"
3. **Prometheus targets:** http://localhost:9090/targets — all targets UP
4. **Test metrics endpoint:** `curl http://localhost:8000/metrics`
5. **PromQL query:** Run `up` in Prometheus UI — shows all targets
6. **Grafana dashboard:** http://localhost:3000 → Application Metrics dashboard

### Expected `/metrics` Output
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/",status="200"} 5.0
http_requests_total{method="GET",endpoint="/health",status="200"} 10.0

# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.005",method="GET",endpoint="/"} 3.0
...

# HELP http_requests_in_progress HTTP requests currently being processed
# TYPE http_requests_in_progress gauge
http_requests_in_progress 0.0
```

## 8. Challenges & Solutions

### Challenge 1: Metrics endpoint being tracked
**Problem:** The `/metrics` endpoint was being counted in `http_requests_total`, inflating request counts since Prometheus scrapes every 15s.
**Solution:** Added early return in middleware to skip `/metrics` path from instrumentation.

### Challenge 2: FastAPI async middleware with gauge
**Problem:** Gauge for in-progress requests could become inconsistent if response processing fails.
**Solution:** Used try/finally block to ensure `http_requests_in_progress.dec()` always runs.

### Challenge 3: Docker internal ports vs exposed ports
**Problem:** Prometheus needs to reach app on internal Docker network port (5000), not the host-mapped port (8000).
**Solution:** Used container-internal port `app-python:5000` in prometheus.yml scrape config.

## 9. Metrics vs Logs — When to Use Each

| Aspect | Metrics (Prometheus) | Logs (Loki) |
|--------|---------------------|-------------|
| **What** | Numeric aggregates (counts, durations) | Event details (text, structured data) |
| **When** | Dashboards, alerting, trends | Debugging, audit, root cause analysis |
| **Cardinality** | Low (labels) | High (individual events) |
| **Storage** | Efficient (numeric time-series) | Heavy (full text) |
| **Query** | PromQL (aggregation-oriented) | LogQL (search-oriented) |
| **Example** | "500 errors spiked to 10/s" | "Error in /api/users: DB connection refused" |

**Use metrics** to detect problems (alerting on error rate spike).
**Use logs** to diagnose problems (finding the specific error message).
