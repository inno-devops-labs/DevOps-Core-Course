# Lab 8 — Metrics & Monitoring with Prometheus

## 1. Architecture

```
┌─────────────┐        ┌──────────────┐        ┌──────────────┐
│  app-python  │◄─scrape─│  Prometheus  │        │   Grafana    │
│  :5000       │        │  :9090       │◄─query──│  :3000       │
│  /metrics    │        │              │        │              │
└─────────────┘        └──────────────┘        └──────────────┘
                              │                       │
                        scrape│                 query  │
                              ▼                       ▼
                       ┌──────────────┐        ┌──────────────┐
                       │    Loki      │        │  Dashboards  │
                       │   :3100      │        │  (metrics +  │
                       │   /metrics   │        │   logs)      │
                       └──────────────┘        └──────────────┘
                              ▲
                              │push
                       ┌──────────────┐
                       │   Promtail   │
                       │   :9080      │
                       └──────────────┘
                              ▲
                              │ Docker logs
                       ┌──────────────┐
                       │  Docker      │
                       │  containers  │
                       └──────────────┘
```

**Data flow:**

1. **app-python** exposes metrics at `/metrics` using `prometheus_client`.
2. **Prometheus** scrapes all targets every 15 seconds (app, itself, Loki, Grafana).
3. **Prometheus** stores time-series data locally with 15-day retention.
4. **Grafana** queries Prometheus via PromQL to render dashboard panels.
5. **Loki** receives logs from Promtail (push-based), while Prometheus scrapes Loki's own metrics.
6. **Grafana** combines both data sources for full observability (logs + metrics).

---

## 2. Application Instrumentation

### Metric Definitions

| Metric | Type | Labels | Purpose |
|--------|------|--------|---------|
| `http_requests_total` | Counter | `method`, `endpoint`, `status` | Tracks total HTTP requests (RED: Rate & Errors) |
| `http_request_duration_seconds` | Histogram | `method`, `endpoint` | Measures request latency distribution (RED: Duration) |
| `http_requests_in_progress` | Gauge | — | Tracks concurrent request count |
| `devops_info_endpoint_calls` | Counter | `endpoint` | Business metric: per-endpoint call count |
| `devops_info_system_collection_seconds` | Histogram | — | Business metric: time to gather system info |

### Why These Metrics?

The metrics follow the **RED method** (Rate, Errors, Duration), which is the standard approach for request-driven services:

- **Rate** (`http_requests_total`): How many requests per second are we serving? Helps understand load.
- **Errors** (`http_requests_total{status=~"5.."}`) : What fraction of requests fail? Detects outages.
- **Duration** (`http_request_duration_seconds`): How long do requests take? Identifies latency regressions.

Business metrics (`devops_info_endpoint_calls`, `devops_info_system_collection_seconds`) provide application-specific insight beyond generic HTTP telemetry.

### Label Cardinality

Endpoint labels are normalized to a fixed set (`/`, `/health`, `/metrics`, `other`) to prevent cardinality explosion from arbitrary paths (e.g., 404 scans).

### Implementation

Metrics are collected via a FastAPI middleware that wraps every request:

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
)
```

The `/metrics` endpoint returns Prometheus exposition format via `generate_latest()`.

---

## 3. Prometheus Configuration

### File: `monitoring/prometheus/prometheus.yml`

```yaml
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

### Scrape Targets

| Job | Target | Port | Path | Purpose |
|-----|--------|------|------|---------|
| `prometheus` | `localhost:9090` | 9090 | `/metrics` | Prometheus self-monitoring |
| `app` | `app-python:5000` | 5000 | `/metrics` | Application metrics |
| `loki` | `loki:3100` | 3100 | `/metrics` | Log aggregator metrics |
| `grafana` | `grafana:3000` | 3000 | `/metrics` | Dashboard service metrics |

### Retention Policy

Configured via command-line flags on the Prometheus container:

- **Time-based:** `--storage.tsdb.retention.time=15d` (keep data for 15 days)
- **Size-based:** `--storage.tsdb.retention.size=10GB` (cap disk usage at 10 GB)

Whichever limit is hit first triggers data deletion. This balances query depth with disk usage.

---

## 4. Dashboard Walkthrough

The **Application Metrics** dashboard (`uid: app-metrics`) has 7 panels:

### Panel 1 — Request Rate (Timeseries)

- **Query:** `sum(rate(http_requests_total[5m])) by (endpoint)`
- **Purpose:** Visualizes requests/second per endpoint. The primary indicator of traffic load.
- **Unit:** req/s

### Panel 2 — Error Rate (Timeseries)

- **Query:** `sum(rate(http_requests_total{status=~"5.."}[5m]))`
- **Purpose:** Tracks 5xx errors per second. A non-zero value signals application failures.
- **Thresholds:** green < 0.1/s, yellow < 1/s, red ≥ 1/s

### Panel 3 — Request Duration p95 (Timeseries)

- **Query:** `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))`
- **Purpose:** Shows 95th-percentile latency. Captures the "worst-case-for-most-users" experience.
- **Unit:** seconds

### Panel 4 — Request Duration Heatmap (Heatmap)

- **Query:** `sum(increase(http_request_duration_seconds_bucket[5m])) by (le)`
- **Purpose:** Visualizes latency distribution over time. Useful for spotting bimodal patterns.

### Panel 5 — Active Requests (Gauge)

- **Query:** `http_requests_in_progress`
- **Purpose:** Shows current concurrency level. High values indicate saturation.
- **Thresholds:** green < 5, yellow < 10, red ≥ 10

### Panel 6 — Status Code Distribution (Pie Chart)

- **Query:** `sum by (status) (rate(http_requests_total[5m]))`
- **Purpose:** Shows proportion of 2xx vs 4xx vs 5xx responses at a glance.

### Panel 7 — Service Uptime (Stat)

- **Query:** `up{job="app"}`
- **Purpose:** Binary indicator (UP/DOWN) of whether Prometheus can reach the application.
- **Mappings:** 1 → "UP" (green), 0 → "DOWN" (red)

---

## 5. PromQL Examples

### 1. Total request rate across all endpoints

```promql
sum(rate(http_requests_total[5m]))
```

Returns the aggregate requests per second over the last 5 minutes.

### 2. Error rate as a percentage

```promql
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100
```

Calculates the fraction of requests resulting in server errors.

### 3. 95th percentile latency per endpoint

```promql
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))
```

Shows the p95 latency broken down by endpoint.

### 4. Services that are currently down

```promql
up == 0
```

Returns any scrape target that Prometheus cannot reach.

### 5. CPU usage of the Python application process

```promql
rate(process_cpu_seconds_total{job="app"}[5m]) * 100
```

Approximates CPU usage percentage from the built-in process collector.

### 6. Top endpoints by request volume

```promql
topk(5, sum by (endpoint) (rate(http_requests_total[5m])))
```

Ranks endpoints by traffic, useful for capacity planning.

### 7. Histogram average request duration

```promql
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

Calculates the mean request duration from histogram sum and count.

---

## 6. Production Setup

### Health Checks

All services have Docker health checks configured:

| Service | Check | Interval | Timeout | Retries |
|---------|-------|----------|---------|---------|
| Loki | `wget http://localhost:3100/ready` | 10s | 5s | 5 |
| Prometheus | `wget http://localhost:9090/-/healthy` | 10s | 5s | 5 |
| Grafana | `wget http://localhost:3000/api/health` | 10s | 5s | 5 |
| app-python | `python urllib http://localhost:5000/health` | 10s | 5s | 5 |

### Resource Limits

| Service | CPU | Memory | Purpose |
|---------|-----|--------|---------|
| Prometheus | 1.0 | 1 GB | TSDB storage and query processing |
| Loki | 1.0 | 1 GB | Log indexing and query processing |
| Grafana | 0.5 | 512 MB | Dashboard rendering |
| Promtail | 0.5 | 512 MB | Log collection agent |
| app-python | 0.5 | 256 MB | Application container |

### Retention Policies

- **Prometheus:** 15 days / 10 GB (whichever triggers first)
- **Loki:** 168 hours (7 days), with compactor-based deletion

### Persistent Volumes

Three named Docker volumes ensure data survives container restarts:

| Volume | Mount Point | Service |
|--------|-------------|---------|
| `prometheus-data` | `/prometheus` | Prometheus TSDB |
| `loki-data` | `/loki` | Loki chunks and index |
| `grafana-data` | `/var/lib/grafana` | Grafana dashboards, settings, plugins |

**Persistence test:**

1. Deploy the stack: `docker compose up -d`
2. Create a dashboard or check that provisioned dashboards are loaded
3. Stop the stack: `docker compose down`
4. Restart: `docker compose up -d`
5. Dashboards and data remain intact because volumes are preserved (`docker compose down` without `-v` keeps volumes)

---

## 7. Testing Results

### Screenshots (what/where/how)

Create a folder (already exists in repo from Lab 7):

- `monitoring/docs/evidence/`

Save **all new Lab 8 screenshots** into that folder and then reference them in the sections below.

#### Required screenshots checklist (Lab 8)

1. **`/metrics` output**
   - **What to capture**: Browser or terminal output showing `http_requests_total`, `http_request_duration_seconds_*`, `http_requests_in_progress`, and `devops_info_*` metrics.
   - **Where to get it**:
     - **Terminal (recommended)**: `curl http://localhost:8000/metrics | head -80`
     - Or open in browser: `http://localhost:8000/metrics`
   - **Save as**: `monitoring/docs/evidence/lab08-metrics-endpoint.png`
   - **Insert here**: under **“Metrics Endpoint”** section.

2. **Prometheus Targets page (all UP)**
   - **What to capture**: Prometheus UI `/targets` page with jobs `prometheus`, `app`, `loki`, `grafana` in **green UP**.
   - **Where to get it**:
     - Browser: `http://localhost:9090/targets`
   - **Save as**: `monitoring/docs/evidence/lab08-prometheus-targets.png`
   - **Insert here**: under **“Prometheus Targets”** section.

3. **Prometheus PromQL query result**
   - **What to capture**: Prometheus UI showing a successful query result (for example `up` or `sum(rate(http_requests_total[5m]))`).
   - **Where to get it**:
     - Browser: `http://localhost:9090` → “Graph” → enter query
   - **Save as**: `monitoring/docs/evidence/lab08-prometheus-query-up.png`
   - **Insert here**: under **“Prometheus Targets”** or a new subsection “Prometheus Query Evidence”.

4. **Grafana dashboard with 6+ panels working**
   - **What to capture**: Grafana dashboard “Application Metrics” showing live graphs (request rate, p95, heatmap, etc.).
   - **Where to get it**:
     - Browser: `http://localhost:3000` → open dashboard “Application Metrics”
   - **Save as**: `monitoring/docs/evidence/lab08-grafana-app-dashboard.png`
   - **Insert here**: under **“Grafana Dashboards”** section.

5. **`docker compose ps` showing healthy**
   - **What to capture**: terminal output where all services are **Up (healthy)**.
   - **Where to get it**:
     - Terminal: `cd monitoring && docker compose ps`
   - **Save as**: `monitoring/docs/evidence/lab08-docker-compose-ps.png`
   - **Insert here**: under **“Container Health”** section.

> If you are collecting evidence on the remote server via SSH, replace `localhost` with SSH port-forwarding (see “How to run / how to access” below).

### Metrics Endpoint

After starting the application, `curl http://localhost:8000/metrics` returns:

**Screenshot placeholder:** `monitoring/docs/evidence/lab08-metrics-endpoint.png`  
**How to get it (terminal):**

```bash
cd monitoring
docker compose up -d
curl http://localhost:8000/metrics | head -80
```

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/",status="200"} 5.0
http_requests_total{method="GET",endpoint="/health",status="200"} 12.0

# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.005",method="GET",endpoint="/"} 4.0
...

# HELP http_requests_in_progress HTTP requests currently being processed
# TYPE http_requests_in_progress gauge
http_requests_in_progress 0.0

# HELP devops_info_endpoint_calls Endpoint calls by endpoint name
# TYPE devops_info_endpoint_calls counter
devops_info_endpoint_calls{endpoint="/"} 5.0
devops_info_endpoint_calls{endpoint="/health"} 12.0
```

### Prometheus Targets

All four scrape targets show **UP** status on `http://localhost:9090/targets`:

**Screenshot placeholder:** `monitoring/docs/evidence/lab08-prometheus-targets.png`  
**How to get it (UI):** open `http://localhost:9090/targets`

- `prometheus` — UP
- `app` — UP
- `loki` — UP
- `grafana` — UP

### Prometheus Query Evidence

**Screenshot placeholder:** `monitoring/docs/evidence/lab08-prometheus-query-up.png`  
**How to get it (UI):** open `http://localhost:9090` → query `up` (or `sum(rate(http_requests_total[5m]))`)

### Grafana Dashboards

- Prometheus and Loki data sources auto-provisioned and connected
- Application Metrics dashboard auto-provisioned with 7 panels showing live data
- All panels rendering correctly with real-time metrics from the application

**Screenshot placeholder:** `monitoring/docs/evidence/lab08-grafana-app-dashboard.png`  
**How to get it (UI):** open `http://localhost:3000` → dashboards → “Application Metrics”

### Container Health

`docker compose ps` shows all services in **healthy** state:

**Screenshot placeholder:** `monitoring/docs/evidence/lab08-docker-compose-ps.png`  
**How to get it (terminal):**

```bash
cd monitoring
docker compose ps
```

```
NAME         SERVICE       STATUS                 PORTS
app-python   app-python    Up (healthy)           0.0.0.0:8000->5000/tcp
grafana      grafana       Up (healthy)           0.0.0.0:3000->3000/tcp
loki         loki          Up (healthy)           0.0.0.0:3100->3100/tcp
prometheus   prometheus    Up (healthy)           0.0.0.0:9090->9090/tcp
promtail     promtail      Up                     0.0.0.0:9080->9080/tcp
```

---

## 8. Metrics vs Logs — When to Use Each

| Aspect | Metrics (Prometheus) | Logs (Loki) |
|--------|---------------------|-------------|
| **Data type** | Numeric time-series | Unstructured/structured text |
| **Use case** | "How much?" / "How fast?" | "What happened?" / "Why?" |
| **Alerting** | Ideal for threshold alerts | Better for pattern-based alerts |
| **Cost** | Low storage per data point | High storage (full text) |
| **Cardinality** | Must keep low | Naturally high |
| **Retention** | Weeks-months (aggregated) | Days-weeks (verbose) |
| **Example** | "Error rate is 5%" | "NullPointerException at line 42" |

**Best practice:** Use metrics to detect a problem (alert on error rate spike), then use logs to diagnose the root cause (find the stack trace).

---

## 9. Challenges & Solutions

### Challenge 1: Endpoint Label Cardinality

**Problem:** Arbitrary URL paths (e.g., 404 scanners hitting random URLs) could create thousands of unique label values, bloating Prometheus storage.

**Solution:** Normalize endpoint labels to a fixed set (`/`, `/health`, `/metrics`, `other`). Unknown paths are grouped under `other`.

### Challenge 2: Health Check Without curl

**Problem:** The `python:3.13-slim` Docker image doesn't include `curl` or `wget`, so the standard health check pattern doesn't work.

**Solution:** Used Python's built-in `urllib.request` module for the health check:
```yaml
test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"]
```

### Challenge 3: Grafana Datasource Provisioning

**Problem:** Manually configuring data sources after each deployment is error-prone and not reproducible.

**Solution:** Used Grafana's file-based provisioning to auto-configure both Prometheus and Loki data sources on startup via YAML files mounted into `/etc/grafana/provisioning/`.

### Challenge 4: Prometheus Retention Tuning

**Problem:** Unbounded retention can fill disk; too-short retention loses historical data for trend analysis.

**Solution:** Dual retention policy — 15-day time limit AND 10 GB size cap — so whichever threshold is reached first triggers cleanup.

---

## 10. Ansible Automation (Bonus)

The `monitoring` Ansible role was extended to deploy the complete observability stack with a single command:

```bash
ansible-playbook playbooks/deploy-monitoring.yml
```

### Role Structure

```
roles/monitoring/
├── defaults/main.yml                          # All configurable variables
├── meta/main.yml                              # Role dependencies (docker)
├── files/
│   └── grafana-app-dashboard.json             # Dashboard JSON
├── tasks/
│   ├── main.yml                               # Includes setup + deploy
│   ├── setup.yml                              # Directories, templates, files
│   └── deploy.yml                             # Pull images, compose up, health waits
└── templates/
    ├── docker-compose.yml.j2                  # Full stack compose file
    ├── loki-config.yml.j2                     # Loki configuration
    ├── promtail-config.yml.j2                 # Promtail configuration
    ├── prometheus.yml.j2                      # Prometheus scrape config
    ├── grafana-datasources.yml.j2             # Auto-provision data sources
    └── grafana-dashboards-provider.yml.j2     # Dashboard file provider
```

### Key Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `monitoring_prometheus_version` | `3.9.0` | Prometheus image tag |
| `monitoring_prometheus_port` | `9090` | External Prometheus port |
| `monitoring_prometheus_retention_days` | `15` | Data retention period |
| `monitoring_prometheus_retention_size` | `10GB` | Max storage size |
| `monitoring_prometheus_scrape_interval` | `15s` | Scrape frequency |
| `monitoring_prometheus_targets` | (list) | Scrape target definitions |

### Idempotency

The playbook is fully idempotent:
- `file` module checks directory existence before creation
- `template` module only writes when content changes
- `copy` module checksums files before copying
- `docker compose up -d` only recreates changed containers
