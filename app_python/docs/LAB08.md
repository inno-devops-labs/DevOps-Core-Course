# LAB 08 — Metrics & Monitoring with Prometheus

## Overview

In this lab, a full monitoring stack was implemented using Prometheus and Grafana.  
A Python Flask application was instrumented with Prometheus metrics and integrated into the observability system.

The goal was to collect, store, and visualize metrics following modern monitoring practices.

## Architecture

Metrics pipeline:

Application → Prometheus → Grafana

- The application exposes metrics at `/metrics`
- Prometheus scrapes metrics every 15 seconds
- Grafana visualizes metrics via dashboards

## Application Instrumentation

The Flask application was extended using `prometheus_client`.

### Implemented metrics

- Counter: `http_requests_total`
- Histogram: `http_request_duration_seconds`
- Gauge: `http_requests_in_progress`

### Labels

- method
- endpoint
- status

### Metrics endpoint

```
/metrics
```

Example output:

```
http_requests_total{method="GET",endpoint="/",status="200"} 10
```

Screenshot: `screenshots/8-3-metrics.png`

## Prometheus Setup

Prometheus was added to Docker Compose.

Screenshot: `screenshots/8-4-docker.png`

### Configuration file

`monitoring/prometheus/prometheus.yml`

### Scrape targets

- prometheus (self)
- app-python:5000
- loki:3100
- grafana:3000

Screenshot: `screenshots/8-1-targets.png`

### Settings

- scrape_interval: 15s
- retention: 15 days / 10GB

## Grafana Dashboards

A dashboard with 6 panels was created.

### Panels

1. Request rate
```
sum(rate(http_requests_total[5m])) by (endpoint)
```

2. Error rate
```
sum(rate(http_requests_total{status=~"5.."}[5m]))
```

3. Latency p95
```
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
```

4. Active requests
```
http_requests_in_progress
```

5. Status distribution
```
sum by (status) (rate(http_requests_total[5m]))
```

6. Uptime
```
up{job="app"}
```

Screenshot: `screenshots/8-2-dashboard.png`

## Testing

Load was generated:

```
for i in {1..50}; do curl http://localhost:5000 >/dev/null; done
```

Metrics were successfully observed in Prometheus and Grafana.

## Production Configuration

### Health checks

- Application: `/health`
- Prometheus: `/-/healthy`

### Resource limits

- Prometheus: 1GB RAM
- Grafana: 512MB RAM
- Application: 256MB RAM

### Persistence

Volumes used:

- prometheus-data
- grafana-data
- loki-data

## Challenges

1. No data in Grafana  
Cause: no traffic  
Solution: generate load using curl

2. Prometheus target DOWN  
Cause: wrong hostname  
Solution: use `app-python:5000`

3. Missing metrics  
Cause: no `/metrics` endpoint  
Solution: add prometheus_client

## Metrics vs Logs

| Logs | Metrics |
|------|--------|
| detailed events | aggregated data |
| debugging | monitoring |
| text | numeric |
| Loki | Prometheus |

## Conclusion

The monitoring stack was successfully implemented.

Achievements:

- Application instrumentation with Prometheus
- Metrics collection via Prometheus
- Visualization in Grafana
- Implementation of RED monitoring method

This provides a solid foundation for observability in containerized environments.