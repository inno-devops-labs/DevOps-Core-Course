# Lab 8: Metrics & Monitoring with Prometheus

## 1. Architecture

The monitoring stack consists of the following components:

- **Python application** (container `app-python`) exposes metrics at `/metrics`.
- **Prometheus** scrapes metrics from the application, Loki, Grafana, and itself.
- **Grafana** visualizes the metrics using a custom dashboard.

All components run inside Docker Compose, share the `logging` network, and have health checks and resource limits configured.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Python    │ ──→ │  Prometheus │ ──→ │   Grafana   │
│    App      │     │   (scraper) │     │ (dashboard) │
└─────────────┘     └─────────────┘     └─────────────┘
```

## 2. Application Instrumentation

### 2.1 Metrics Added

The Python application was instrumented using the `prometheus_client` library. The following metrics were added:

| Metric Name                          | Type      | Labels                     | Purpose |
|--------------------------------------|-----------|----------------------------|---------|
| `http_requests_total`                | Counter   | method, endpoint, status   | Count total HTTP requests |
| `http_request_duration_seconds`      | Histogram | method, endpoint           | Measure request duration distribution |
| `http_requests_in_progress`          | Gauge     | –                          | Track concurrent requests |
| `devops_info_endpoint_calls_total`   | Counter   | endpoint                   | Count calls per endpoint (custom business metric) |

### 2.2 `/metrics` Endpoint

The `/metrics` endpoint is implemented using FastAPI:

```python
@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(REGISTRY), media_type="text/plain")
```

### 2.3 Instrumentation Middleware

A FastAPI middleware was added to capture request data:

```python
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    # increment in-progress gauge, record duration, update counters
    ...
```

## 3. Prometheus Deployment

### 3.1 Docker Compose Service

Prometheus was added to the existing `docker-compose.yml` from Lab 7:

```yaml
prometheus:
  image: prom/prometheus:v3.9.0
  ports: ["9090:9090"]
  volumes:
    - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
    - prometheus-data:/prometheus
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.retention.time=15d'
    - '--storage.tsdb.retention.size=10GB'
  healthcheck: ...
  deploy: ...
```

### 3.2 Prometheus Configuration (`prometheus.yml`)

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'app'
    static_configs:
      - targets: ['app-python:8000']
    metrics_path: '/metrics'

  - job_name: 'loki'
    static_configs:
      - targets: ['loki:3100']
    metrics_path: '/metrics'

  - job_name: 'grafana'
    static_configs:
      - targets: ['grafana:3000']
    metrics_path: '/metrics'
```

## 4. Grafana Dashboards

### 4.1 Adding Prometheus Data Source

In Grafana, a new Prometheus data source was added with URL `http://prometheus:9090`. The connection test succeeded.

### 4.2 Dashboard Overview

The dashboard **"Application Metrics – Prometheus"** contains 7 panels. Below is a description of each panel and the associated PromQL query.

| Panel                     | Query                                                                 | Visualization |
|---------------------------|-----------------------------------------------------------------------|---------------|
| Request Rate by Endpoint  | `sum(rate(http_requests_total[5m])) by (endpoint)`                   | Time series   |
| Error Rate                | `sum(rate(http_requests_total{status=~"5.."}[5m]))`                  | Time series   |
| 95th Percentile Latency   | `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))` | Time series |
| Latency Heatmap           | `rate(http_request_duration_seconds_bucket[5m])`                     | Heatmap       |
| Active Requests           | `http_requests_in_progress`                                           | Stat          |
| Status Code Distribution  | `sum(rate(http_requests_total[5m])) by (status)`                     | Pie chart     |
| Service Uptime            | `up{job="app"}`                                                       | Stat          |

## 5. Production Configurations

### 5.1 Health Checks

Every service in `docker-compose.yml` includes a `healthcheck` block. Example for Prometheus:

```yaml
healthcheck:
  test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:9090/-/healthy || exit 1"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 10s
```

All services are now reported as `healthy`:

```
$ docker compose ps
NAME                IMAGE                           STATUS
app-python          acecution/...:metrics           Up (healthy)
grafana             grafana/grafana:12.3.1          Up (healthy)
loki                grafana/loki:3.0.0              Up (healthy)
prometheus          prom/prometheus:v3.9.0          Up (healthy)
promtail            grafana/promtail:3.0.0          Up (healthy)
```

### 5.2 Resource Limits

Each service has CPU and memory limits defined under `deploy.resources`. Example for Prometheus:

```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### 5.3 Data Retention

Prometheus retention is configured via command-line flags:
- `--storage.tsdb.retention.time=15d` (keep data for 15 days)
- `--storage.tsdb.retention.size=10GB` (maximum size 10 GB)

Loki retains logs for 7 days (configured in `loki/config.yml`).

### 5.4 Persistent Volumes

Named volumes are used for all stateful services:
- `prometheus-data`
- `loki-data`
- `grafana-data`

After restarting the stack (`docker compose down && docker compose up -d`), all dashboards and data persisted, confirming proper volume configuration.

## 6. PromQL Examples

Here are five PromQL queries that demonstrate useful analyses:

1. **Requests per second by endpoint**  
   `sum(rate(http_requests_total[5m])) by (endpoint)`

2. **95th percentile latency over the last 10 minutes**  
   `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[10m])) by (le))`

3. **Error percentage (5xx / total)**  
   `(sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))) * 100`

4. **Active requests (current)**  
   `http_requests_in_progress`

5. **Memory usage of the app container (using cAdvisor or built-in metrics if available)**  
   `container_memory_usage_bytes{container="app-python"}` (requires cAdvisor; not implemented here)

## 7. Challenges & Solutions

- **Prometheus target down:** Initially the `app` target was DOWN because the service name `app-python` was misspelled. Corrected in `prometheus.yml`.
- **Missing metrics:** The application initially lacked a `/metrics` endpoint; added with correct instrumentation.
- **Retention not working:** Forgot to add retention flags to Prometheus command; added `--storage.tsdb.retention.time=15d` and `--storage.tsdb.retention.size=10GB`.
- **Grafana data source connection refused:** Used `localhost:9090` instead of the Docker service name `prometheus:9090`. Changed to service name.