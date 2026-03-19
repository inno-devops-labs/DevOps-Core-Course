# Lab 08 — Metrics & Monitoring with Prometheus

## 1. Architecture

```
┌──────────────┐     scrape /metrics     ┌──────────────┐
│  app-python  │ ◄────────────────────── │  Prometheus   │
│  :5000       │                         │  :9090        │
└──────────────┘                         └──────┬───────┘
                                                │
┌──────────────┐     scrape /metrics            │
│    Loki      │ ◄──────────────────────────────┤
│  :3100       │                                │
└──────────────┘                                │
                                                ▼
┌──────────────┐                         ┌──────────────┐
│   Promtail   │ ──── push logs ──────►  │    Grafana    │
│              │                         │  :3000        │
└──────────────┘                         └──────────────┘
```

**Data flow:**
1. The Python application exposes metrics at `/metrics` using `prometheus_client`
2. Prometheus scrapes metrics from the app, Loki, Grafana, and itself every 15s
3. Grafana queries Prometheus (metrics) and Loki (logs) for visualization
4. Promtail collects container logs and pushes them to Loki

## 2. Application Instrumentation

### Metrics implemented

| Metric | Type | Labels | Purpose |
|--------|------|--------|---------|
| `http_requests_total` | Counter | method, endpoint, status | Track total HTTP requests (RED: Rate) |
| `http_request_duration_seconds` | Histogram | method, endpoint | Track request latency (RED: Duration) |
| `http_requests_in_progress` | Gauge | — | Track concurrent requests |
| `devops_info_endpoint_calls` | Counter | endpoint | Track business-level endpoint usage |
| `devops_info_system_collection_seconds` | Histogram | — | Track system info collection time |

### Why these metrics

- **Counter** (`http_requests_total`): Monotonically increasing — perfect for calculating request rates and error rates over time windows
- **Histogram** (`http_request_duration_seconds`): Provides bucketed latency distribution, enabling percentile calculations (p50, p95, p99)
- **Gauge** (`http_requests_in_progress`): Can go up and down — shows current load on the service
- **Business metrics** (`devops_info_endpoint_calls`): Track which endpoints are most popular beyond raw HTTP metrics

The `/metrics` endpoint itself is excluded from tracking to avoid feedback loops.

## 3. Prometheus Configuration

### Scrape targets

| Job | Target | Port | Path | Purpose |
|-----|--------|------|------|---------|
| `prometheus` | `localhost:9090` | 9090 | `/metrics` | Self-monitoring |
| `app` | `app-python:5000` | 5000 | `/metrics` | Application metrics |
| `loki` | `loki:3100` | 3100 | `/metrics` | Log storage metrics |
| `grafana` | `grafana:3000` | 3000 | `/metrics` | Dashboard service metrics |

### Configuration details

- **Scrape interval**: 15s (balance between granularity and resource usage)
- **Evaluation interval**: 15s (for future alerting rules)
- **Retention time**: 15 days (sufficient for trend analysis)
- **Retention size**: 10 GB (prevents disk exhaustion)
- **Storage**: Persistent Docker volume `prometheus-data` mounted at `/prometheus`

## 4. Dashboard Walkthrough

The provisioned dashboard (`DevOps Info Service — Application Metrics`) has 8 panels following the RED method:

### Panels

1. **Request Rate by Endpoint** (Time series)
   - Query: `sum(rate(http_requests_total[5m])) by (endpoint)`
   - Shows requests per second per endpoint

2. **Error Rate (5xx)** (Time series)
   - Query: `sum(rate(http_requests_total{status=~"5.."}[5m]))`
   - Threshold: red above 0.1 errors/s

3. **Request Duration p95** (Time series)
   - Query: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
   - Thresholds: yellow > 0.5s, red > 1s

4. **Request Duration Heatmap** (Heatmap)
   - Query: `rate(http_request_duration_seconds_bucket[5m])`
   - Visualizes latency distribution across buckets

5. **Active Requests** (Gauge)
   - Query: `http_requests_in_progress`
   - Thresholds: yellow > 10, red > 50

6. **Status Code Distribution** (Pie chart)
   - Query: `sum by (status) (rate(http_requests_total[5m]))`
   - Shows proportion of 2xx, 4xx, 5xx responses

7. **Service Uptime** (Stat)
   - Query: `up{job="app"}`
   - Value mapping: 1 = UP (green), 0 = DOWN (red)

8. **Endpoint Calls** (Bar chart)
   - Query: `sum(rate(devops_info_endpoint_calls[5m])) by (endpoint)`
   - Shows business-level endpoint usage

## 5. PromQL Examples

### Basic queries

```promql
# 1. Total requests to the / endpoint
http_requests_total{endpoint="/"}

# 2. Request rate per second (averaged over 5 minutes)
rate(http_requests_total[5m])

# 3. Total request rate across all endpoints
sum(rate(http_requests_total[5m]))

# 4. Request rate grouped by endpoint
sum by (endpoint) (rate(http_requests_total[5m]))

# 5. Error rate (5xx responses)
sum(rate(http_requests_total{status=~"5.."}[5m]))
```

### Advanced queries

```promql
# 6. 95th percentile latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# 7. Error percentage
sum(rate(http_requests_total{status=~"5.."}[5m])) /
sum(rate(http_requests_total[5m])) * 100

# 8. Services that are down
up == 0

# 9. Average request duration
rate(http_request_duration_seconds_sum[5m]) /
rate(http_request_duration_seconds_count[5m])

# 10. Top endpoints by request count
topk(5, sum by (endpoint) (rate(http_requests_total[5m])))
```

## 6. Production Setup

### Health checks

| Service | Check | Interval | Retries |
|---------|-------|----------|---------|
| Prometheus | `wget http://localhost:9090/-/healthy` | 10s | 5 |
| Loki | `wget http://localhost:3100/ready` | 10s | 5 |
| Grafana | `curl http://localhost:3000/api/health` | 10s | 5 |
| app-python | `urllib.request.urlopen('http://localhost:5000/health')` | 10s | 5 |

### Resource limits

| Service | CPU Limit | Memory Limit | CPU Reserved | Memory Reserved |
|---------|-----------|--------------|--------------|-----------------|
| Prometheus | 1.0 | 1 GB | 0.25 | 256 MB |
| Loki | 1.0 | 1 GB | 0.25 | 256 MB |
| Grafana | 0.5 | 512 MB | 0.25 | 256 MB |
| app-python | 0.5 | 256 MB | 0.1 | 64 MB |
| Promtail | 0.5 | 512 MB | 0.1 | 128 MB |

### Retention policies

- **Prometheus**: 15 days / 10 GB (whichever is reached first)
- **Loki**: 168 hours (7 days), configured via `limits_config.retention_period`

### Persistent volumes

| Volume | Service | Mount Point | Purpose |
|--------|---------|-------------|---------|
| `prometheus-data` | Prometheus | `/prometheus` | TSDB storage |
| `loki-data` | Loki | `/loki` | Log chunks and index |
| `grafana-data` | Grafana | `/var/lib/grafana` | Dashboards, users, settings |

Data survives `docker compose down` + `docker compose up -d`.

## 7. Testing Results

### Verification steps

```bash
# Start the stack
cd monitoring
docker compose up -d

# Check all services are healthy
docker compose ps

# Verify Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[].health'

# Verify app metrics
curl http://localhost:8000/metrics

# Verify Grafana data source
curl -u admin:admin http://localhost:3000/api/datasources

# Test persistence
docker compose down
docker compose up -d
# Dashboards and data should persist
```

## 8. Metrics vs Logs — When to Use Each

| Aspect | Metrics (Prometheus) | Logs (Loki) |
|--------|---------------------|-------------|
| **Purpose** | Numeric measurements over time | Event records with context |
| **Use when** | "How many?", "How fast?", "How much?" | "What happened?", "Why did it fail?" |
| **Alerting** | Ideal — threshold-based alerts on rates | Possible but less efficient |
| **Storage** | Compact (numeric time series) | Verbose (full text) |
| **Query** | PromQL — aggregations, rates, percentiles | LogQL — filter, parse, aggregate |
| **Example** | "Error rate > 5% in last 5 min" | "Show me the stack trace for request X" |
| **Cardinality** | Keep low (avoid high-cardinality labels) | Naturally high (each log is unique) |

**Best practice**: Use metrics for detection (something is wrong), logs for investigation (why it's wrong).

## 9. Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| Metrics endpoint creating feedback loops | Excluded `/metrics` path from request tracking in `before_request`/`after_request` hooks |
| Grafana data source UID mismatch | Used provisioning YAML to auto-configure Prometheus and Loki data sources |
| Prometheus container health check | Used `wget` instead of `curl` since `prom/prometheus` image is Alpine-based |
| Dashboard persistence across restarts | Used Grafana provisioning with JSON files mounted as volumes |
