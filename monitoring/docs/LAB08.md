# Lab 8 — Metrics & Monitoring with Prometheus

## Overview

In this lab, I instrumented my Python application with Prometheus metrics and deployed a complete monitoring stack using Prometheus and Grafana. The application now exposes a `/metrics` endpoint, Prometheus scrapes metrics from all configured targets, and Grafana visualizes the collected data through custom dashboards.

This lab extends the observability stack from Lab 7 by adding metrics-based monitoring on top of logs.

Technologies used:

- FastAPI
- prometheus_client
- Prometheus v3.9.0
- Grafana v12.3.1
- Docker Compose

---

## 1. Architecture

The monitoring architecture is based on a pull model.

**Metric flow:**

Application → `/metrics` endpoint → Prometheus scrapes metrics → Grafana queries Prometheus → dashboards visualize metrics

### Components

- **Python application** exposes Prometheus metrics on `/metrics`
- **Prometheus** scrapes metrics every 15 seconds
- **Grafana** uses Prometheus as a data source
- **Loki + Promtail** from Lab 7 remain available for logs

### Monitoring targets

The following targets were configured in Prometheus:

- `prometheus` → `localhost:9090`
- `app` → `app-python:5000/metrics`
- `loki` → `loki:3100/metrics`
- `grafana` → `grafana:3000/metrics`

---

## 2. Application Instrumentation

I added Prometheus instrumentation to the FastAPI application using the `prometheus_client` Python library.

### Installed dependency

```txt
prometheus-client==0.23.1
```

Metrics added  
1. http_requests_total

Type: Counter
Purpose: Counts total HTTP requests
Labels: method, endpoint, status

This metric is used to calculate request rate, request distribution, and error rate.

2. http_request_duration_seconds

Type: Histogram  
Purpose: Measures request latency in seconds
Labels: method, endpoint

This metric is used for latency analysis and percentile calculations such as p95.

3. http_requests_in_progress

Type: Gauge
Purpose: Tracks active requests currently being processed

This metric shows concurrency and current request load.

4. devops_info_endpoint_calls_total

Type: Counter
Purpose: Tracks how many times each application endpoint was called
Labels: endpoint

This is an application-specific metric.

5. devops_info_system_collection_seconds

Type: Histogram
Purpose: Measures how long system information collection takes

This is an internal business/application metric.

Why these metrics were chosen

The selected metrics follow the RED method:

Rate → request counters

Errors → request counters filtered by error status codes

Duration → latency histogram

This provides a strong baseline for monitoring a request-driven API service.

## 3. Metrics Endpoint

The application exposes a Prometheus-compatible endpoint:

/metrics

The endpoint returns metrics in Prometheus text exposition format.

Example output  
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{endpoint="/",method="GET",status="200"} 1.0

# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram

# HELP http_requests_in_progress HTTP requests currently being processed
# TYPE http_requests_in_progress gauge

The endpoint was tested locally and also through Docker Compose after deployment.

## 4. Prometheus Configuration

Prometheus was added to the Docker Compose monitoring stack.

Service image
prom/prometheus:v3.9.0
Exposed port
9090
Main configuration file

monitoring/prometheus/prometheus.yml

Configuration used
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  - job_name: "app"
    static_configs:
      - targets: ["app-python:5000"]
    metrics_path: /metrics

  - job_name: "loki"
    static_configs:
      - targets: ["loki:3100"]
    metrics_path: /metrics

  - job_name: "grafana"
    static_configs:
      - targets: ["grafana:3000"]
    metrics_path: /metrics
Scrape interval

scrape_interval: 15s

evaluation_interval: 15s

This is frequent enough for lab-scale monitoring and dashboard responsiveness.

## 5. Prometheus Verification

After deployment, I verified Prometheus through the web UI.

Prometheus endpoints tested

http://localhost:9090

http://localhost:9090/targets

http://localhost:9090/-/healthy

Result

All configured targets were successfully scraped and reported as UP:

app

grafana

loki

prometheus

This confirmed that the monitoring stack was working correctly and all services were reachable through the Docker network.

## 6. Grafana Prometheus Data Source

I added Prometheus as a Grafana data source.

Configuration

Type: Prometheus

URL: http://prometheus:9090

The data source test was successful and Grafana was able to query Prometheus metrics.

## 7. Dashboard Walkthrough

I created a custom metrics dashboard in Grafana.

The dashboard includes at least 6 panels and focuses on the RED method.

Panel 1 — Request Rate

Type: Time series

sum(rate(http_requests_total[5m])) by (endpoint)

Purpose: Shows requests per second for each endpoint.

Panel 2 — Error Rate

Type: Time series

sum(rate(http_requests_total{status=~"5.."}[5m]))

Purpose: Shows the rate of server-side errors (5xx responses).

Panel 3 — Requests per Status

Type: Pie chart / Bar chart

sum(rate(http_requests_total[5m])) by (status)

Purpose: Visualizes the distribution of status codes.

Panel 4 — p95 Latency

Type: Time series

histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

Purpose: Shows the 95th percentile request duration.

Panel 5 — Active Requests

Type: Gauge

http_requests_in_progress

Purpose: Shows how many requests are currently in progress.

Panel 6 — Service Uptime

Type: Stat

up{job="app"}

Purpose: Indicates whether the application target is up (1) or down (0).

Optional extra panel — Endpoint Calls

Type: Time series

sum(rate(devops_info_endpoint_calls_total[5m])) by (endpoint)

Purpose: Shows per-endpoint business metric usage.

## 8. PromQL Examples

Below are several PromQL queries I used during testing and dashboard creation.

1. Check all targets
up
2. Request rate per endpoint
sum(rate(http_requests_total[5m])) by (endpoint)
3. Error rate
sum(rate(http_requests_total{status=~"5.."}[5m]))
4. p95 latency
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
5. Active requests
http_requests_in_progress
6. Status code distribution
sum(rate(http_requests_total[5m])) by (status)
7. Application-specific endpoint usage
sum(rate(devops_info_endpoint_calls_total[5m])) by (endpoint)
## 9. Production Configuration

I also applied production-oriented settings to the monitoring stack.

Health checks

Health checks were configured for key services:

Prometheus: http://localhost:9090/-/healthy

Grafana: http://localhost:3000/api/health

Loki: http://localhost:3100/ready

App: http://localhost:5000/health

This allows Docker to monitor service health and improves reliability.

Resource limits

Resource limits were added to prevent uncontrolled resource usage.

Configured examples:

Prometheus: 1G memory, 1 CPU

Loki: 1G memory, 1 CPU

Grafana: 512M memory, 0.5 CPU

App: 256M memory, 0.5 CPU

Data retention

Prometheus retention was configured with:

15d time retention

10GB storage limit

This helps control disk usage and improve query performance.

Persistent volumes

Persistent volumes were configured for:

Prometheus data

Loki data

Grafana data

This ensures dashboards and collected metrics survive restarts.

## 10. Testing Results
Metrics endpoint

The /metrics endpoint successfully returned:

default Python/process metrics

custom HTTP request metrics

custom application-specific metrics

Prometheus targets

All targets were visible and UP in the Prometheus /targets page.

Grafana dashboard

The Grafana dashboard displayed live data after generating traffic with curl requests.

Traffic generation used
for i in {1..50}; do curl http://localhost:8000/; done
for i in {1..50}; do curl http://localhost:8000/health; done

This generated request counters and histogram observations, allowing the dashboard to display non-empty charts.

## 11. Metrics vs Logs

This lab builds on Lab 7.

Logs are useful for:

investigating specific events

debugging failures

analyzing detailed request context

Metrics are useful for:

trend analysis

dashboards

alerting

performance and availability monitoring

Combined value

Logs explain what happened, while metrics show how much, how often, and how fast. Together they provide stronger observability.

## 12. Challenges and Solutions
Challenge 1 — Duplicate metrics registration

Initially, the app crashed due to duplicate Prometheus metric registration. This happened because uvicorn.run("app:app", ...) re-imported the module.

Solution:
Changed startup to:

uvicorn.run(app, host=HOST, port=PORT)

This prevented double import and duplicate metric registration.

Challenge 2 — Loki config mount issue

At one point Loki failed because config.yml was accidentally created as a directory instead of a file.

Solution:
Removed the directory, recreated config.yml as a proper file, and restarted the stack.

Challenge 3 — Promtail config mount issue

A similar mount issue occurred with Promtail.

Solution:
Recreated monitoring/promtail/config.yml as a file and restarted the stack.

Challenge 4 — Empty graphs in Grafana

Initially some panels showed no data.

Solution:
Generated traffic with repeated curl requests to populate the metrics.

## 13. Conclusion

In this lab, I successfully instrumented the FastAPI application with Prometheus metrics and deployed a complete monitoring stack with Prometheus and Grafana.

The final solution includes:

a working /metrics endpoint

request counters, latency histograms, and active request gauges

Prometheus scraping multiple services

Grafana dashboards for live metric visualization

production-related health checks, limits, retention, and persistence

This lab completed the metrics side of observability and complemented the logging setup from Lab 7.
