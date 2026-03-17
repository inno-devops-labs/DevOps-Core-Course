# Lab 8 — Monitoring Stack Documentation

## 1. Architecture

```text
[App Python] --> [Prometheus] --> [Grafana]
             \--> [Promtail] --> [Loki]
```

* **App Python**: Instrumented with Prometheus metrics and JSON logging
* **Prometheus**: Scrapes metrics from app and itself, stores time series
* **Grafana**: Visualizes Prometheus metrics and Loki logs
* **Loki/Promtail**: Collects logs for observability

## 2. Application Instrumentation

Metrics added:

* `http_requests_total`: Counts all HTTP requests by method, endpoint, and status
* `http_request_duration_seconds`: Histogram of request durations
* `http_requests_in_progress`: Gauge of currently processing requests
* `devops_info_endpoint_calls`: Counter of endpoint usage
* `devops_info_system_collection_seconds`: Histogram of system info collection duration

**Reasoning**: Monitor traffic, latency, and system health. Allows RPS and response time dashboards.

## 3. Prometheus Configuration

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'app'
    static_configs:
      - targets: ['monitoring-app-python-1:8000']
    metrics_path: /metrics

  - job_name: 'loki'
    static_configs:
      - targets: ['loki:3100']

  - job_name: 'grafana'
    static_configs:
      - targets: ['grafana:3000']
```

* **Scrape Interval**: 15s
* **Retention**: 15 days, 10GB

## 4. Dashboard Walkthrough

* **RPS Panel**: `rate(http_requests_total[1m])`

  * Shows requests per second per endpoint
* **Response Time Panel**: `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[1m])) by (le, endpoint))`

  * 95th percentile latency
* **Active Requests**: `http_requests_in_progress`

  * Current in-flight requests
* **System Info Duration**: `devops_info_system_collection_seconds`

  * Time to collect system info
* **Endpoint Calls**: `devops_info_endpoint_calls`

  * Shows most frequently used endpoints

## 5. PromQL Examples

1. `rate(http_requests_total[5m])` — 5 min RPS
2. `sum(http_requests_total) by (status)` — Requests per status code
3. `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))` — 95th percentile latency
4. `http_requests_in_progress` — Current in-flight requests
5. `devops_info_endpoint_calls` — Endpoint usage breakdown

## 6. Production Setup

**Health Checks:**

* Prometheus: `wget --no-verbose --tries=1 --spider http://localhost:9090/-/healthy || exit 1`
* App: Python HTTP check to `/health`

**Resource Limits:**

* Prometheus: 1 CPU, 1G memory
* Loki: 1 CPU, 1G memory
* Grafana: 0.5 CPU, 512M memory
* App: 0.5 CPU, 256M memory

**Retention Policies:**

* Prometheus: 15 days / 10GB
* Grafana dashboards persisted via volume

## 7. Testing Results

* All services up and healthy (`docker compose ps`)
* Metrics visible at `/metrics` endpoint
* Dashboards show live data (RPS, response time)
* Screenshots captured during tests (include in final submission)

## 8. Challenges & Solutions

* **Issue**: Healthcheck showed `unhealthy`

  * **Solution**: Adjusted internal app port and replaced curl with Python-based check
* **Issue**: Metrics empty

  * **Solution**: Added Prometheus instrumentation decorators in Flask
* **Issue**: Missing Prometheus retention configuration

  * **Solution**: Added `--storage.tsdb.retention.time` and `--storage.tsdb.retention.size`