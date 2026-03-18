# Prometheus & Grafana Monitoring Lab Report

## Architecture

Application write his data to global variables (prometheus-client package) and exposes '/metrics' endpoint which returns current values.

Prometheus "asks" for metrics each known application by some interval (just GET request). And save to database.

Grafana just makes requests to Prometheus and visualize data.

Application <--- Prometheus <--- Grafana

## Application Instrumentation

| Metric | Type | Labels | Purpose |
| -- | -- | -- | - |
| `http_requests_total` | Counter | method, endpoint, status | Track API usage and error rates |
| `http_request_duration_seconds` | Histogram | method, endpoint | Monitor latency and performance |
| `http_requests_in_progress` | Gauge | none | Detect concurrency issues |
| `app_uptime_seconds` | Gauge | none | Detect unexpected restarts |
| `endpoint_response_size_bytes` | Histogram | endpoint | Monitor payload sizes and bandwidth |

## Prometheus Configuration

### prometheus.yml

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

storage:
  tsdb:
    retention_time: 15d
    retention_size: 10GB

scrape_configs:
  - job_name: "app"
    static_configs:
      - targets: ["app-python:5000"]
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  - job_name: 'loki'
    static_configs:
      - targets: ['loki:3100']
  - job_name: 'grafana'
    static_configs:
      - targets: ['grafana:3000']
```

## Dashboard Walkthrough

# Grafana Dashboard Visualizations Explained

![alt text](image-6.png)

## 1. Request Rate (Graph)

### Query

```promql
sum(rate(http_requests_total[5m])) by (endpoint)
```

### What It Shows

A line graph displaying requests per second for each endpoint over time. Each endpoint gets its own colored line.

## 2. Error Rate (Graph)

### Query

```promql
sum(rate(http_requests_total{status=~"5.."}[5m]))
```

### What It Shows

How many 5xx errors (server errors) are occurring per second. This is a critical health indicator.

## 3. Request Duration p95 (Graph)

### Query

```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### What It Shows

**The 95th percentile latency**: 95% of requests complete within this time; 5% are slower.

## 4. Request Duration Heatmap (Heatmap)

### Query

```promql
rate(http_request_duration_seconds_bucket[5m])
```

### What It Shows

**A 2D visualization showing the distribution of request latencies over time**.
## 5. Active Requests (Gauge/Graph)

### Query

```promql
http_requests_in_progress
```

### What It Shows

**Real-time count of requests currently being processed by the application**.

## 6. Status Code Distribution (Pie Chart)

### Query

```promql
sum by (status) (rate(http_requests_total[5m]))
```

### What It Shows

**Breakdown of request outcomes: successful (2xx), client errors (4xx), and server errors (5xx)**.

## 7. Uptime (Stat)

### Query

```promql
up{job="app"}
```

### What It Shows

**Whether the service is currently up (1) or down (0)**.

## PromQL Examples

### Query 1: Total Requests by Status Code

```promql
sum by (status) (http_requests_total)
```

**Explanation**: Groups all requests by HTTP status code (200, 404, 500, etc.) and sums them. Shows distribution of successful vs. failed requests.

**Use Case**: Quick overview of application health.

### Query 2: Request Rate by Endpoint

```promql
sum by (endpoint) (rate(http_requests_total[5m]))
```

**Explanation**: Calculates the rate of requests per endpoint over the last 5 minutes. Shows which endpoints are most heavily used.

**Use Case**: Identify traffic hotspots and optimize accordingly.

### Query 3: Average Latency Over Time

```promql
avg(rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m]))
```

**Explanation**: Divides the sum of durations by the count of requests to get average latency. Smoothed over 5 minutes.

**Use Case**: Track performance trends and detect degradation.

### Query 4: High Error Rate Alert

```promql
(sum(rate(http_requests_total{status=~"5.."}[1m])) / sum(rate(http_requests_total[1m]))) > 0.05
```

**Explanation**: Fires when error rate exceeds 5% over 1 minute. Detects sudden application failures.

**Use Case**: Trigger alerts to on-call engineers.

### Query 5: Requests Taking Longer Than 2 Seconds

```promql
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 2
```

**Explanation**: Shows when the 99th percentile latency exceeds 2 seconds. Indicates significant performance issues.

**Use Case**: SLA monitoring and performance budgets.

### Query 6: Application Restart Detection

```promql
increase(app_uptime_seconds[5m]) < 0
```

**Explanation**: Detects when uptime decreases (restart), which would show as negative increase.

**Use Case**: Alert on unexpected restarts.

## Production Setup

### Health Checks

## Prometheus health check

Every 10 seconds with timout of 5 seconds. Maximum 5 retries.

## App health check

Every 10 seconds with timout of 5 seconds. Maximum 5 retries.

### Resource Requirements

Prometheus: 1G memory, 1 CPU
Loki: 1G memory, 1 CPU
Grafana: 512M memory, 0.5 CPU
Apps: 256M memory, 0.5 CPU

### Prometheus retention

time: 15 days
size: 10Gb

## Testing Results

![alt text](image-3.png)

![alt text](image-4.png)

![alt text](image-5.png)

### After restart

![alt text](image-8.png)

![alt text](image-7.png)