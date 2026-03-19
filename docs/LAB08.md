# LAB08

## 1. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Compose Network                  │
│                                                             │
│  ┌──────────────┐   scrape /metrics    ┌────────────────┐  │
│  │  app-python  │ ◄──────────────────── │   Prometheus   │  │
│  │  :8000       │                       │   :9090        │  │
│  └──────────────┘                       └───────┬────────┘  │
│                                                 │           │
│  ┌──────────────┐   scrape /metrics             │           │
│  │    Loki      │ ◄─────────────────────────────┤           │
│  │  :3100       │                               │           │
│  └──────────────┘                               │           │
│                                                 │           │
│  ┌──────────────┐   scrape /metrics             │           │
│  │   Grafana    │ ◄─────────────────────────────┘           │
│  │  :3000       │                                           │
│  │              │ ◄── query PromQL ──── Prometheus          │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

**Metric flow:**

1. The Python app exposes live metrics at `GET /metrics` (prometheus_client format)
2. Prometheus scrapes all targets every 15 s and stores them in its TSDB
3. Grafana queries Prometheus via PromQL and renders dashboards

---

## 2. Application Instrumentation

### Metrics added (`app_python/main.py`)

| Metric                                  | Type      | Labels                              | Why                                                                     |
| --------------------------------------- | --------- | ----------------------------------- | ----------------------------------------------------------------------- |
| `http_requests_total`                   | Counter   | `method`, `endpoint`, `status_code` | Total number of HTTP requests - the **Rate** and **Errors** legs of RED |
| `http_request_duration_seconds`         | Histogram | `method`, `endpoint`                | Latency distribution - the **Duration** leg of RED                      |
| `http_requests_in_progress`             | Gauge     | -                                   | Concurrent in-flight requests at any moment                             |
| `devops_info_endpoint_calls_total`      | Counter   | `endpoint`                          | Business metric: per-endpoint call frequency                            |
| `devops_info_system_collection_seconds` | Histogram | -                                   | How long `system_info()` takes to run                                   |

### Implementation notes

- A FastAPI HTTP middleware (`metrics_middleware`) intercepts every request:
  - increments `http_requests_in_progress` on entry, decrements on exit
  - records `http_request_duration_seconds` with `time.perf_counter()`
  - increments `http_requests_total` with method / path / status labels
- The `/metrics` path is excluded from instrumentation to avoid self-referential noise
- `system_info()` is timed with a Histogram to catch any OS-call slowdowns
- Labels keep cardinality low - only the literal URL path is used (no dynamic IDs)

---

## 3. Prometheus Configuration

**File:** `monitoring/prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s # pull metrics every 15 seconds
  evaluation_interval: 15s # evaluate alerting rules every 15 seconds

storage:
  tsdb:
    retention_time: 15d # keep 15 days of data
    retention_size: 10GB # cap at 10 GB disk usage

scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  - job_name: "app"
    static_configs:
      - targets: ["app-python:8000"]
    metrics_path: "/metrics"

  - job_name: "loki"
    static_configs:
      - targets: ["loki:3100"]
    metrics_path: "/metrics"

  - job_name: "grafana"
    static_configs:
      - targets: ["grafana:3000"]
    metrics_path: "/metrics"
```

**Scrape targets summary:**

| Job        | Target     | Port | Path                 |
| ---------- | ---------- | ---- | -------------------- |
| prometheus | localhost  | 9090 | `/metrics` (default) |
| app        | app-python | 8000 | `/metrics`           |
| loki       | loki       | 3100 | `/metrics`           |
| grafana    | grafana    | 3000 | `/metrics`           |

**Retention policy:**

- Time-based: 15 days of history
- Size-based: capped at 10 GB - whichever limit is hit first, older data is dropped

---

## 4. Dashboard Walkthrough

The custom **DevOps Info Service** dashboard contains 7 panels.

### Panel 1 - Request Rate (Time series)

**Query:**

```promql
sum(rate(http_requests_total[5m])) by (endpoint)
```

Shows how many requests per second each endpoint is receiving. Useful for spotting traffic spikes or drops.

### Panel 2 - Error Rate (Time series)

**Query:**

```promql
sum(rate(http_requests_total{status_code=~"5.."}[5m]))
```

Counts 5xx responses per second. A spike here means the app is failing.

### Panel 3 - p95 Request Duration (Time series)

**Query:**

```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

The 95th-percentile latency - 95 % of requests complete faster than this value. Key SLO indicator.

### Panel 4 - Request Duration Heatmap (Heatmap)

**Query:**

```promql
rate(http_request_duration_seconds_bucket[5m])
```

Visualises the full latency distribution over time. Reveals bimodal distributions and outliers.

### Panel 5 - Active Requests (Gauge)

**Query:**

```promql
http_requests_in_progress
```

Instantaneous count of requests being processed right now. Useful for detecting queue build-up.

### Panel 6 - Status Code Distribution (Pie chart)

**Query:**

```promql
sum by (status_code) (rate(http_requests_total[5m]))
```

Proportion of 2xx vs 4xx vs 5xx. Quickly shows the health/error mix of traffic.

### Panel 7 - App Uptime (Stat)

**Query:**

```promql
up{job="app"}
```

Returns `1` when Prometheus can scrape the app and `0` when it cannot. Green = healthy.

---

## 5. PromQL Examples

### 5.1 Total request rate across all endpoints

```promql
sum(rate(http_requests_total[5m]))
```

Aggregates every label combination into one number - useful for overall throughput.

### 5.2 Error rate as a percentage of total traffic

```promql
100 * sum(rate(http_requests_total{status_code=~"5.."}[5m]))
      /
      sum(rate(http_requests_total[5m]))
```

Returns a 0–100 % error ratio. A good SLO target is < 1 %.

### 5.3 p99 latency per endpoint

```promql
histogram_quantile(
  0.99,
  sum by (le, endpoint) (rate(http_request_duration_seconds_bucket[5m]))
)
```

Breaks the 99th-percentile latency out per endpoint, revealing which route is slowest.

### 5.4 Services that are currently DOWN

```promql
up == 0
```

Returns a result set only when a target fails to scrape - instantly shows broken services.

### 5.5 Endpoint call frequency

```promql
sum by (endpoint) (rate(devops_info_endpoint_calls_total[5m]))
```

Uses the app-specific counter to see which endpoints are most popular.

### 5.6 Average request duration per endpoint

```promql
rate(http_request_duration_seconds_sum[5m])
/
rate(http_request_duration_seconds_count[5m])
```

Mean latency per endpoint. Pair with p95/p99 to understand the full picture.

---

## 6. Production Setup

### Health checks

Every service in `compose.yml` has a `healthcheck` block:

| Service    | Check command                                    | Interval | Timeout | Retries |
| ---------- | ------------------------------------------------ | -------- | ------- | ------- |
| Prometheus | `wget --spider http://localhost:9090/-/healthy`  | 10 s     | 5 s     | 5       |
| Grafana    | `wget --spider http://localhost:3000/api/health` | 10 s     | 5 s     | 5       |
| Loki       | `wget --spider http://localhost:3100/ready`      | 10 s     | 5 s     | 5       |
| app-python | `wget --spider http://localhost:8000/health`     | 10 s     | 5 s     | 3       |

`depends_on: condition: service_healthy` ensures services start in the correct order.

### Resource limits

| Service    | CPU limit | Memory limit |
| ---------- | --------- | ------------ |
| Prometheus | 1.0       | 1 G          |
| Loki       | 1.0       | 1 G          |
| Grafana    | 0.5       | 512 M        |
| app-python | 0.5       | 256 M        |
| Promtail   | 0.5       | 256 M        |

### Data retention (Prometheus)

Configured both in `prometheus.yml` (storage block) and as CLI flags:

```yaml
command:
  - "--config.file=/etc/prometheus/prometheus.yml"
  - "--storage.tsdb.retention.time=15d"
  - "--storage.tsdb.retention.size=10GB"
```

The stricter of the two limits takes effect first.

### Persistent volumes

```yaml
volumes:
  prometheus-data: # /prometheus - TSDB blocks survive restarts
  loki-data: # /loki       - Loki chunks survive restarts
  grafana-data: # /var/lib/grafana - dashboards & data sources survive restarts
```

To verify persistence:

```bash
docker compose down
docker compose up -d
```

---

## 7. Testing Results

### 7.1 `/metrics` endpoint

```bash
python app_python/main.py &
curl http://localhost:8000/
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

Expected output (excerpt):

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{endpoint="/",method="GET",status_code="200"} 1.0
http_requests_total{endpoint="/health",method="GET",status_code="200"} 1.0

# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{endpoint="/",le="0.005",method="GET"} 1.0
...

# HELP http_requests_in_progress HTTP requests currently being processed
# TYPE http_requests_in_progress gauge
http_requests_in_progress 0.0
```

### 7.2 Stack deployment

```bash
cd monitoring
docker compose up -d
docker compose ps
```

All services should show `healthy`:

```
NAME            IMAGE                         STATUS
app-python      polinanime/devops-info-service  Up (healthy)
grafana         grafana/grafana:12.3.5          Up (healthy)
loki            grafana/loki:3.6.7              Up (healthy)
prometheus      prom/prometheus:v3.9.0          Up (healthy)
promtail        grafana/promtail:3.6.7          Up
```

### 7.3 Prometheus targets

Open http://localhost:9090/targets - all four jobs should show state **UP**:

- `prometheus` (localhost:9090)
- `app` (app-python:8000)
- `loki` (loki:3100)
- `grafana` (grafana:3000)

### 7.4 PromQL smoke test

In the Prometheus UI expression browser run:

```promql
up
```

Should return four results all equal to `1`.

---

## 8. Challenges & Solutions

### Challenge 1 - Prometheus `storage` block ignored on older images

**Problem:** The top-level `storage.tsdb` block in `prometheus.yml` is a Prometheus 3.x feature. Older images silently ignore it.
**Solution:** Also pass `--storage.tsdb.retention.time` and `--storage.tsdb.retention.size` as CLI `command` arguments in Docker Compose - these work across all versions.

### Challenge 2 - `/metrics` counted as a real request

**Problem:** Without exclusion, Prometheus scraping `/metrics` every 15 s would inflate `http_requests_total` and skew latency histograms.
**Solution:** Added an early-return guard in the middleware:

```python
if request.url.path == "/metrics":
    return await call_next(request)
```

### Challenge 3 - High-cardinality labels

**Problem:** Using the full request URL (e.g. `/user/123`) as an `endpoint` label creates one time series per unique user ID, exhausting Prometheus memory.
**Solution:** Only the path template is used (e.g. `/user/{id}` - or the literal path for fixed routes like `/`, `/health`). Dynamic segments should be normalised before labelling.

### Challenge 4 - Grafana data source not auto-configured

**Problem:** After `docker compose up`, Grafana starts empty - the Prometheus data source must be added manually.
**Solution (manual):** Connections → Data sources → Add → Prometheus → URL `http://prometheus:9090` → Save & Test.
**Solution (automated):** Use Grafana provisioning YAML or the Ansible bonus role to provision the data source automatically on startup.

---

## Metrics vs Logs - When to use each

|                      | Logs (Lab 7 - Loki)                          | Metrics (Lab 8 - Prometheus)                    |
| -------------------- | -------------------------------------------- | ----------------------------------------------- |
| **What**             | Discrete events with full context            | Numeric measurements aggregated over time       |
| **Best for**         | Debugging a specific request, tracing errors | Alerting on SLOs, capacity planning, dashboards |
| **Storage cost**     | Higher (full text)                           | Lower (numbers only)                            |
| **Query latency**    | Slower (full-text search)                    | Fast (pre-aggregated TSDB)                      |
| **Example question** | "What was the exact error for request X?"    | "What is my p99 latency over the last hour?"    |

Use **both together**: metrics alert you that something is wrong, logs tell you exactly what happened.
