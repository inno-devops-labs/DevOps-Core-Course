# Lab 8: Metrics & Monitoring with Prometheus

## Architecture
- **App**: Flask application with prometheus_client
- **Prometheus**: TSDB for metrics storage, scrapes every 15s
- **Grafana**: Visualization with PromQL

## Metrics Added
| Metric | Type | Labels | Purpose |
|--------|------|--------|---------|
| http_requests_total | Counter | method, endpoint, status | RED: Rate & Errors |
| http_request_duration_seconds | Histogram | method, endpoint | RED: Duration |
| http_requests_in_progress | Gauge | - | Current load |

## Prometheus Configuration
- Scrape interval: 15s
- Retention: 15 days / 10GB
- Targets: app, prometheus, loki, grafana (all UP)

## Dashboard Panels (6+)
1. **Request Rate** - `sum(rate(http_requests_total[5m])) by (endpoint)`
2. **Request Duration p95** - `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
3. **Active Requests** - `http_requests_in_progress`
4. **Status Code Distribution** - `sum by (status) (rate(http_requests_total[5m]))`
5. **Uptime** - `up{job="app"}`
6. **Error Rate** - `sum(rate(http_requests_total{status=~"5.."}[5m]))`

## Evidence

### /metrics endpoint
![metrics](screenshots_lab8/metrics.png)

### Prometheus Targets (all UP)
![prometheus targets](screenshots_lab8/prometheus-targets.png)

### Grafana Dashboard
![dashboard](screenshots_lab8/dashboard.png)