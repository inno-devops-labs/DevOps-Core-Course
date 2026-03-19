# Lab 8 --- Metrics & Monitoring with Prometheus

## 1. Architecture

The monitoring stack implements full observability by combining metrics
and logs.

### Metric Flow:
```
Python App → Prometheus → Grafana
```

### Full Observability (Labs 7 + 8):
```
App → Promtail → Loki → Grafana (logs)\
App → Prometheus → Grafana (metrics)
```

### Description:

-   The application exposes metrics via `/metrics`
-   Prometheus scrapes metrics every 15 seconds
-   Grafana queries Prometheus and visualizes data

------------------------------------------------------------------------

## 2. Application Instrumentation

The application was instrumented using `prometheus_client`.

### Implemented Metrics:

#### Counter 
```
http_requests_total
```
Tracks total number of HTTP requests.

Labels: 
- method 
- endpoint 
- status

Used for: 
- request rate (RED method) 
- error rate

------------------------------------------------------------------------

#### Histogram 
```
http_request_duration_seconds
```

Tracks request latency distribution.

Used for: 
- response time 
- p95 latency 
- performance analysis

------------------------------------------------------------------------

#### Gauge 
```
http_requests_in_progress
```

Tracks active requests.

Used for: 
- system load 
- concurrency monitoring

------------------------------------------------------------------------

## 3. Prometheus Configuration

### Scrape Configuration:

-   Scrape interval: 15 seconds
-   Targets:
    -   app-python:5000 (/metrics)
    -   loki:3100
    -   grafana:3000
    -   localhost:9090

### Retention Policy:

-   15 days
-   10GB storage limit

------------------------------------------------------------------------

## 4. Dashboard Walkthrough

### Request Rate
```
sum(rate(http_requests_total\[5m\])) by (endpoint)
```

### Error Rate
```
sum(rate(http_requests_total{status=\~"5.."}\[5m\]))
```

### p95 Latency
```
histogram_quantile(0.95,
rate(http_request_duration_seconds_bucket\[5m\]))
```

### Heatmap
```
rate(http_request_duration_seconds_bucket\[5m\])
```

### Active Requests
```
http_requests_in_progress
```

### Status Codes
```
sum by (status) (rate(http_requests_total\[5m\]))
```

### Uptime
```
up{job="app"}
```
------------------------------------------------------------------------

## 5. PromQL Examples

-   rate(http_requests_total\[5m\])
-   sum(http_requests_total)
-   rate(http_requests_total{status=\~"5.."}\[5m\])
-   sum by (endpoint) (rate(http_requests_total\[5m\]))
-   histogram_quantile(0.95,
    rate(http_request_duration_seconds_bucket\[5m\]))

------------------------------------------------------------------------

## 6. Production Setup

### Health Checks

-   App: /health
-   Prometheus: /-/healthy
-   Grafana: /api/health
-   Loki: /ready

### Resource Limits

Configured for all services to prevent overuse.

### Persistence

Volumes: 
- prometheus-data 
- loki-data 
- grafana-data

Data persists after restart.

------------------------------------------------------------------------

## 7. Testing Results

### Metrics Endpoint

![Metrics](./screenshots/metrics%20endpoint.png)

### Prometheus Targets

![Targets](./screenshots/prometheus%20targets.png)

### Prometheus Query

![Query](./screenshots/prometheus%20query.png)

### Grafana Dashboard

![Dashboard](./screenshots/grafana%20dashboards.png)

### Persistence After Restart

![Persistence](./screenshots/persistence%20after%20restart.png)

------------------------------------------------------------------------

## 8. Challenges & Solutions

### Problem: /metrics returned 404

Solution: implemented metrics endpoint

### Problem: wrong port (8000 vs 5000)

Solution: fixed Prometheus target

### Problem: Grafana query error

Solution: switched to Prometheus data source

------------------------------------------------------------------------

## 9. Metrics vs Logs

 | Metrics             |  Logs
 | --------------------| --------------------
 | Aggregated data     |  Detailed events
 | Used for monitoring |  Used for debugging
 | Time-series         |  Raw text

### When to use:

-   Metrics → performance, alerts
-   Logs → debugging, root cause analysis

------------------------------------------------------------------------

## Final Result

-   Monitoring stack fully deployed
-   Prometheus scraping all services
-   Grafana dashboards visualizing metrics
-   Persistence verified
-   RED method implemented
