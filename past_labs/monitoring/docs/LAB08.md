# Lab 8 — Metrics & Monitoring with Prometheus

## Architecture

This lab extends the observability stack from Lab 7 by adding metrics collection and visualization on top of centralized logging. The full flow is:

```text
Client -> FastAPI application -> /metrics endpoint -> Prometheus -> Grafana dashboards
                                  \-> JSON logs -> Promtail -> Loki -> Grafana logs
```

The application exposes Prometheus-compatible metrics at `/metrics`, Prometheus scrapes them every 15 seconds, and Grafana uses Prometheus as a data source for dashboards. In parallel, logs are still collected through Loki, so the stack now supports both metrics and logs in one place.

**Main components:**
- **FastAPI application** — exports application and process metrics.
- **Prometheus** — scrapes and stores time-series metrics.
- **Grafana** — visualizes metrics and logs.
- **Loki + Promtail** — keep the log pipeline from Lab 7.

**Architecture screenshot:**

![Prometheus targets](/monitoring/docs/screenshots/prometheus_targets.png)

## Application Instrumentation

I instrumented the Python application with `prometheus_client` and exposed a dedicated `/metrics` endpoint. The application exports both default Python/process metrics and custom application metrics.

### Implemented metric groups

#### 1. HTTP request counter
```text
http_requests_total{method="...", endpoint="...", status_code="..."}
```
This metric counts the total number of handled HTTP requests. It is a **Counter**, so it only increases. It is useful for request rate, error analysis, and status-code distribution.

#### 2. HTTP request duration histogram
```text
http_request_duration_seconds_bucket{method="...", endpoint="...", le="..."}
```
This metric stores request latency as a **Histogram**. It is used for latency panels and percentile calculations such as p95 response time.

#### 3. Active requests gauge
```text
http_requests_in_progress{method="...", endpoint="..."}
```
This metric is a **Gauge** and represents the number of requests currently being processed. Since the value can go up and down, Gauge is the correct type.

#### 4. Application-specific counter
```text
devops_info_endpoint_calls_total{endpoint="..."}
```
This metric tracks how often service endpoints are called. It is useful for understanding which routes are actually used.

#### 5. Application-specific histogram
```text
devops_info_system_collection_seconds_bucket{le="..."}
```
This metric measures how long it takes to collect system information inside the service.

### Why these metrics were chosen

The main goal was to follow the **RED method** for a request-based service:
- **Rate** — derived from `http_requests_total`
- **Errors** — derived from `http_requests_total` filtered by `status_code`
- **Duration** — derived from `http_request_duration_seconds`

I also added an **active requests** metric to observe concurrency and two application-specific metrics to go beyond generic HTTP monitoring.

### Example `/metrics` output

The exported metrics include Python runtime metrics, process metrics, HTTP metrics, and application-specific metrics:

```bash
zagur@LAPTOP-JONCQBVT:/mnt/c/Users/zagur/DevOps/DevOps-Core-Course/monitoring$ curl http://localhost:8000/metrics
# HELP python_gc_objects_collected_total Objects collected during gc
# TYPE python_gc_objects_collected_total counter
python_gc_objects_collected_total{generation="0"} 51230.0
python_gc_objects_collected_total{generation="1"} 4708.0
python_gc_objects_collected_total{generation="2"} 0.0
# HELP python_gc_objects_uncollectable_total Uncollectable objects found during GC
# TYPE python_gc_objects_uncollectable_total counter
python_gc_objects_uncollectable_total{generation="0"} 0.0
python_gc_objects_uncollectable_total{generation="1"} 0.0
python_gc_objects_uncollectable_total{generation="2"} 0.0
# HELP python_gc_collections_total Number of times this generation was collected
# TYPE python_gc_collections_total counter
python_gc_collections_total{generation="0"} 62.0
python_gc_collections_total{generation="1"} 5.0
python_gc_collections_total{generation="2"} 0.0
# HELP python_info Python platform information
# TYPE python_info gauge
python_info{implementation="CPython",major="3",minor="13",patchlevel="11",version="3.13.11"} 1.0
# HELP process_virtual_memory_bytes Virtual memory size in bytes.
# TYPE process_virtual_memory_bytes gauge
process_virtual_memory_bytes 1.66699008e+08
# HELP process_resident_memory_bytes Resident memory size in bytes.
# TYPE process_resident_memory_bytes gauge
process_resident_memory_bytes 5.490688e+07
# HELP process_start_time_seconds Start time of the process since unix epoch in seconds.
# TYPE process_start_time_seconds gauge
process_start_time_seconds 1.77325799615e+09
# HELP process_cpu_seconds_total Total user and system CPU time spent in seconds.
# TYPE process_cpu_seconds_total counter
process_cpu_seconds_total 48.32
# HELP process_open_fds Number of open file descriptors.
# TYPE process_open_fds gauge
process_open_fds 15.0
# HELP process_max_fds Maximum number of open file descriptors.
# TYPE process_max_fds gauge
process_max_fds 1.048576e+06
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{endpoint="/metrics",method="GET",status_code="200"} 1379.0
http_requests_total{endpoint="/health",method="GET",status_code="200"} 675.0
# HELP http_requests_created Total HTTP requests
# TYPE http_requests_created gauge
http_requests_created{endpoint="/metrics",method="GET",status_code="200"} 1.7732580016874638e+09
http_requests_created{endpoint="/health",method="GET",status_code="200"} 1.7732580016886492e+09
# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{endpoint="/metrics",le="0.005",method="GET"} 1310.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="0.01",method="GET"} 1378.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="0.025",method="GET"} 1378.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="0.05",method="GET"} 1378.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="0.075",method="GET"} 1378.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="0.1",method="GET"} 1378.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="0.25",method="GET"} 1379.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="0.5",method="GET"} 1379.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="0.75",method="GET"} 1379.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="1.0",method="GET"} 1379.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="2.5",method="GET"} 1379.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="5.0",method="GET"} 1379.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="7.5",method="GET"} 1379.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="10.0",method="GET"} 1379.0
http_request_duration_seconds_bucket{endpoint="/metrics",le="+Inf",method="GET"} 1379.0
http_request_duration_seconds_count{endpoint="/metrics",method="GET"} 1379.0
http_request_duration_seconds_sum{endpoint="/metrics",method="GET"} 3.339381251056693
http_request_duration_seconds_bucket{endpoint="/health",le="0.005",method="GET"} 669.0
http_request_duration_seconds_bucket{endpoint="/health",le="0.01",method="GET"} 669.0
http_request_duration_seconds_bucket{endpoint="/health",le="0.025",method="GET"} 669.0
http_request_duration_seconds_bucket{endpoint="/health",le="0.05",method="GET"} 671.0
http_request_duration_seconds_bucket{endpoint="/health",le="0.075",method="GET"} 675.0
http_request_duration_seconds_bucket{endpoint="/health",le="0.1",method="GET"} 675.0
http_request_duration_seconds_bucket{endpoint="/health",le="0.25",method="GET"} 675.0
http_request_duration_seconds_bucket{endpoint="/health",le="0.5",method="GET"} 675.0
http_request_duration_seconds_bucket{endpoint="/health",le="0.75",method="GET"} 675.0
http_request_duration_seconds_bucket{endpoint="/health",le="1.0",method="GET"} 675.0
http_request_duration_seconds_bucket{endpoint="/health",le="2.5",method="GET"} 675.0
http_request_duration_seconds_bucket{endpoint="/health",le="5.0",method="GET"} 675.0
http_request_duration_seconds_bucket{endpoint="/health",le="7.5",method="GET"} 675.0
http_request_duration_seconds_bucket{endpoint="/health",le="10.0",method="GET"} 675.0
http_request_duration_seconds_bucket{endpoint="/health",le="+Inf",method="GET"} 675.0
http_request_duration_seconds_count{endpoint="/health",method="GET"} 675.0
http_request_duration_seconds_sum{endpoint="/health",method="GET"} 0.5872745100277825
# HELP http_request_duration_seconds_created HTTP request duration in seconds
# TYPE http_request_duration_seconds_created gauge
http_request_duration_seconds_created{endpoint="/metrics",method="GET"} 1.7732580016875052e+09
http_request_duration_seconds_created{endpoint="/health",method="GET"} 1.7732580016886709e+09
# HELP http_requests_in_progress HTTP requests currently being processed
# TYPE http_requests_in_progress gauge
# HELP devops_info_endpoint_calls_total DevOps info service endpoint calls
# TYPE devops_info_endpoint_calls_total counter
# HELP devops_info_system_collection_seconds Time spent collecting system info (seconds)
# TYPE devops_info_system_collection_seconds histogram
devops_info_system_collection_seconds_bucket{le="0.005"} 0.0
devops_info_system_collection_seconds_bucket{le="0.01"} 0.0
devops_info_system_collection_seconds_bucket{le="0.025"} 0.0
devops_info_system_collection_seconds_bucket{le="0.05"} 0.0
devops_info_system_collection_seconds_bucket{le="0.075"} 0.0
devops_info_system_collection_seconds_bucket{le="0.1"} 0.0
devops_info_system_collection_seconds_bucket{le="0.25"} 0.0
devops_info_system_collection_seconds_bucket{le="0.5"} 0.0
devops_info_system_collection_seconds_bucket{le="0.75"} 0.0
devops_info_system_collection_seconds_bucket{le="1.0"} 0.0
devops_info_system_collection_seconds_bucket{le="2.5"} 0.0
devops_info_system_collection_seconds_bucket{le="5.0"} 0.0
devops_info_system_collection_seconds_bucket{le="7.5"} 0.0
devops_info_system_collection_seconds_bucket{le="10.0"} 0.0
devops_info_system_collection_seconds_bucket{le="+Inf"} 0.0
devops_info_system_collection_seconds_count 0.0
devops_info_system_collection_seconds_sum 0.0
# HELP devops_info_system_collection_seconds_created Time spent collecting system info (seconds)
# TYPE devops_info_system_collection_seconds_created gauge
devops_info_system_collection_seconds_created 1.773257998585445e+09
```

![Metrics endpoint output](/monitoring/docs/screenshots/browser_metrics.png)

## Prometheus Configuration

Prometheus was added to the monitoring stack and configured to scrape four jobs every 15 seconds:
- Prometheus itself
- the FastAPI application
- Loki
- Grafana

### Configuration used

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  - job_name: "app"
    metrics_path: "/metrics"
    static_configs:
      - targets: ["devops-info-service:5000"]

  - job_name: "loki"
    metrics_path: "/metrics"
    static_configs:
      - targets: ["loki:3100"]

  - job_name: "grafana"
    metrics_path: "/metrics"
    static_configs:
      - targets: ["grafana:3002"]
```

### Explanation

- `scrape_interval: 15s` means Prometheus collects fresh values every 15 seconds.
- The `app` job uses Docker Compose service discovery by targeting `devops-info-service:5000`.
- Loki and Grafana are also scraped, so infrastructure-level monitoring is available in the same Prometheus instance.
- Prometheus scrapes itself so that its own health and workload can also be observed.

The Prometheus targets page showed all configured services and allowed verification that scraping worked correctly.

![Prometheus targets](/monitoring/docs/screenshots/prometheus_targets.png)

## Dashboard Walkthrough

In Grafana, I configured Prometheus as a data source and built a dashboard around the main RED indicators plus operational metrics.

![Dashboard screenshot 1](/monitoring/docs/screenshots/dash1.png)
![Dashboard screenshot 2](/monitoring/docs/screenshots/dash2.png)

[Exported dashboard JSON file](/monitoring/docs/lab06_dashboard.json)

**Additional imported dashboards**

- Prometheus 2.0

  ![](/monitoring/docs/screenshots/prom.png)

- Loki 2.0

  ![](/monitoring/docs/screenshots/loki.png)

### Panel 1 — Request Rate
**Purpose:** show how many requests per second the application handles.

**Query:**
```promql
sum by (endpoint) (rate(http_requests_total{job="app"}[5m]))
```

This panel shows traffic intensity and makes it easy to compare endpoint load.

### Panel 2 — Status Code Distribution
**Purpose:** show the share of successful and failed requests.

**Query:**
```promql
sum by (status_code) (increase(http_requests_total{job="app"}[5m]))
```

This panel is useful for quickly seeing whether traffic is mostly 200, 404, or 500 responses.

### Panel 3 — Error Rate
**Purpose:** show the volume of server errors over time.

**Query:**
```promql
sum(rate(http_requests_total{job="app", status_code=~"5.."}[5m]))
```

This panel focuses only on 5xx failures and avoids showing “No data” when there are currently no server-side errors.

### Panel 4 — Error Rate (%)
**Purpose:** show the proportion of failed requests relative to all traffic.

**Query:**
```promql
100 * (
  sum(rate(http_requests_total{job="app", status_code=~"5.."}[5m]))
) / clamp_min(sum(rate(http_requests_total{job="app"}[5m])), 1e-9)
```

A percentage is often easier to interpret than raw failed requests per second.

### Panel 5 — Request Duration (p95)
**Purpose:** show the 95th percentile latency.

**Query:**
```promql
histogram_quantile(
  0.95,
  sum by (le, endpoint) (rate(http_request_duration_seconds_bucket{job="app"}[5m]))
)
```

This highlights slower requests without being distorted by only the average value.

### Panel 6 — Active Requests
**Purpose:** show how many requests are being processed right now.

**Query:**
```promql
sum(http_requests_in_progress)
```

This panel is most visible when slow or concurrent requests are generated intentionally during a demo.

### Panel 7 — Uptime / Service Availability
**Purpose:** verify that the application is currently reachable by Prometheus.

**Query:**
```promql
up{job="app"}
```

A value of `1` means the service is up and scraping works; `0` means Prometheus cannot reach it.

## PromQL Examples

Below are the main queries I used while building and validating the dashboard.

### 1. Check that all scrape targets are alive
```promql
up
```
Shows whether Prometheus can successfully scrape each configured target.

![](/monitoring/docs/screenshots/up.png)

### 2. Requests per second by endpoint
```promql
sum by (endpoint) (rate(http_requests_total{job="app"}[5m]))
```
Shows request intensity for each route.

![](/monitoring/docs/screenshots/endpoint.png)

### 3. Status code distribution over the last 5 minutes
```promql
sum by (status_code) (increase(http_requests_total{job="app"}[5m]))
```
Shows how many 200, 404, and 500 responses appeared recently.

![](/monitoring/docs/screenshots/status_code.png)

### 4. 5xx error rate
```promql
sum(rate(http_requests_total{job="app", status_code=~"5.."}[5m])) or vector(0)
```
Tracks server-side errors only.

![](/monitoring/docs/screenshots/rate_500.png)

### 5. p95 latency
```promql
histogram_quantile(
  0.95,
  sum by (le, endpoint) (rate(http_request_duration_seconds_bucket{job="app"}[5m]))
)
```
Estimates the 95th percentile request duration.

![](/monitoring/docs/screenshots/quantile.png)

### 6. Active requests right now
```promql
sum(http_requests_in_progress)
```
Useful for concurrent request observation.

![](/monitoring/docs/screenshots/in_progress.png)

### 7. CPU usage of the Python process
```promql
rate(process_cpu_seconds_total[5m]) * 100
```
Provides a rough CPU consumption trend for the application process.

![](/monitoring/docs/screenshots/cpu.png)

## Production Setup

This lab was built in Docker Compose, but several practices already move it closer to a production-style setup.

![](/monitoring/docs/screenshots/compose_ps.png)

### Health checks
Recommended health checks:

```yaml
healthcheck:
  test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:9090/-/healthy || exit 1"]
  interval: 10s
  timeout: 5s
  retries: 5
```

For the application:

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:5000/health').read()"]
  interval: 10s
  timeout: 3s
  retries: 5
```

### Resource limits
Suggested resource limits:
- **Prometheus** — 1 CPU, 1 GB RAM
- **Loki** — 1 CPU, 1 GB RAM
- **Grafana** — 0.5 CPU, 512 MB RAM
- **Application** — 0.5 CPU, 256 MB RAM

### Persistence
Persistent Docker volumes should be used for:
- Prometheus TSDB data
- Loki data
- Grafana dashboards and configuration

This prevents dashboards and collected metrics from being lost after container restarts.

![](/monitoring/docs/screenshots/persistence.png)

You can see `up{job="app"}` query for the last 7 days, when container was up and down and all metrics were saved.

### Retention
A practical Prometheus retention policy is:

```yaml
command:
  - '--config.file=/etc/prometheus/prometheus.yml'
  - '--storage.tsdb.retention.time=15d'
  - '--storage.tsdb.retention.size=10GB'
```

This gives a balance between historical visibility and disk usage.

## Testing Results

The monitoring stack was tested in several steps:

1. **Metrics endpoint validation** — opening `/metrics` confirmed that the app exported Prometheus-compatible metrics.
2. **Prometheus target validation** — the `/targets` page showed the configured jobs and whether they were reachable.
3. **Grafana dashboard validation** — dashboard panels displayed live values from Prometheus.
4. **Error simulation** — test endpoints returning `404` and `500` were used to verify status-code and error panels.
5. **Concurrency testing** — a slow endpoint was used to make the `http_requests_in_progress` gauge visible in Grafana.

### What worked
- Prometheus successfully scraped the application, Loki, Grafana, and itself.
- Grafana displayed request counters, status-code distribution, and latency.
- The dashboard made it easy to correlate traffic patterns with failures.
- Metrics complemented logs from Lab 7: logs show detailed events, while metrics show trends and aggregates.

### Metrics vs logs
- **Metrics** are best for trends, rates, latency, alerts, and dashboard visualization.
- **Logs** are best for detailed debugging, request context, error messages, and investigation of a specific incident.
- Using both gives much better observability than using only one of them.

## Challenges & Solutions

### 1. “No data” in the Error Rate panel
**Problem:** the original query used the wrong metric name and label name.

**Fix:** I switched to the application metric and the correct label:
```promql
sum(rate(http_requests_total{job="app", status_code=~"5.."}[5m]))
```

### 2. “No data” in the Active Requests panel
**Problem:** `http_requests_in_progress` existed as a metric definition, but the gauge was not being incremented and decremented around request handling.

**Fix:** I updated the middleware to call `inc()` before request processing and `dec()` in `finally`, then used:
```promql
sum(http_requests_in_progress)
```

### 3. Multiple gauges appeared instead of one
**Problem:** Grafana displayed one gauge per label combination (`method`, `endpoint`).

**Fix:** I aggregated the values with:
```promql
sum(http_requests_in_progress)
```
This produced one clean “Active Requests” panel.

### 4. Active requests stayed at zero
**Problem:** normal endpoints were too fast, so Prometheus rarely scraped during request execution.

**Fix:** I added a slow debug endpoint and generated concurrent requests. This allowed Prometheus to capture non-zero values for the in-progress gauge.

### 5. Distinguishing metrics from infrastructure noise
**Problem:** scrape traffic to `/metrics` can dominate counters and distort the dashboard.

**Fix:** I kept this in mind while interpreting charts and, where needed, filtered queries by endpoint or excluded noise in the application middleware.
