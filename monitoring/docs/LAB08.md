# Lab 08 — Metrics & Monitoring with Prometheus

## 1. Architecture

### Metric Flow
The monitoring flow in this lab is:

**app-python → Prometheus → Grafana**

The Python Flask application exposes Prometheus-compatible metrics on the `/metrics` endpoint. Prometheus scrapes those metrics every 15 seconds and stores them as time-series data. Grafana then uses Prometheus as a data source and visualizes the collected metrics through custom dashboard panels.

### Logical Diagram

```text
[ app-python ]
     |
     |  GET /metrics
     v
[ Prometheus ]
     |
     |  PromQL queries
     v
[ Grafana ]
```

### Components
- **app-python** — instrumented Flask service exposing application and runtime metrics
- **Prometheus** — metrics collector and storage backend
- **Grafana** — dashboarding and visualization layer
- **Loki / Promtail** — retained from Lab 7 for logs, complementing metrics with log-based observability

---

## 2. Application Instrumentation

The application was instrumented with the `prometheus-client` library, as required by the lab. A dedicated `/metrics` endpoint was added to expose metrics in Prometheus format.

### Added Metrics

#### 1. `http_requests_total` — Counter
Tracks the total number of HTTP requests handled by the application.

**Labels:**
- `method`
- `endpoint`
- `status_code`

**Why this metric was added:**
This is the core request counter used to calculate request rate and error rate. It is one of the main RED metrics for request-driven applications.

---

#### 2. `http_request_duration_seconds` — Histogram
Tracks request latency in seconds.

**Labels:**
- `method`
- `endpoint`

**Why this metric was added:**
This metric is used to analyze application latency and compute percentiles such as p95. It directly supports the **Duration** part of the RED method.

---

#### 3. `http_requests_in_progress` — Gauge
Tracks the number of requests currently being processed.

**Why this metric was added:**
This shows the current load on the application and helps understand short-term concurrency.

---

#### 4. `devops_info_endpoint_calls` — Counter
Tracks calls to application endpoints.

**Labels:**
- `endpoint`

**Why this metric was added:**
This is an application-specific metric that provides visibility into endpoint usage beyond generic HTTP request counting.

---

#### 5. `devops_info_system_collection_seconds` — Histogram
Tracks how long system information collection takes.

**Why this metric was added:**
This is another application-specific metric that helps measure internal processing overhead for the system info endpoint.

### Instrumentation Approach
Instrumentation was implemented using:
- `@app.before_request` to mark request start time and increment active requests
- `@app.after_request` to:
  - increment total request counter
  - record request duration
  - decrement active requests

This approach keeps instrumentation centralized and avoids duplicating metrics code inside every route handler.

---

## 3. Prometheus Configuration

Prometheus was added to the existing monitoring stack from Lab 7 and configured through `monitoring/prometheus/prometheus.yml`.

### Global Settings
- `scrape_interval: 15s`
- `evaluation_interval: 15s`

These settings match the lab requirements and provide frequent enough updates for dashboarding.

### Scrape Targets

| Job name | Target | Metrics path | Purpose |
|---|---|---|---|
| `prometheus` | `localhost:9090` | `/metrics` | Prometheus self-monitoring |
| `app` | `app-python:5000` | `/metrics` | Flask application metrics |
| `loki` | `loki:3100` | `/metrics` | Loki service metrics |
| `grafana` | `grafana:3000` | `/metrics` | Grafana service metrics |

### Retention Policy
Prometheus was started with:
- `--storage.tsdb.retention.time=15d`
- `--storage.tsdb.retention.size=10GB`

**Why retention was configured:**
- limits disk usage
- keeps the dataset manageable
- preserves recent operational data for analysis

### Deployment Notes
Prometheus was connected to the same Docker Compose monitoring network as the application, Loki, and Grafana. A persistent volume was mounted to `/prometheus` to keep time-series data across container restarts.

---

## 4. Dashboard Walkthrough

A custom Grafana dashboard called **App Monitoring Dashboard** was created with 7 working panels.

### 1. Request Rate
**Query**
```promql
sum(rate(http_requests_total[5m])) by (endpoint)
```

**Purpose**
Shows requests per second for each endpoint. This is the **Rate** part of the RED method.

---

### 2. Error Rate
**Query**
```promql
sum(rate(http_requests_total{status_code=~"5.."}[5m]))
```

**Purpose**
Tracks server-side 5xx errors over time. This is the **Errors** part of the RED method.

**Observed result**
The panel showed no data during testing, which is expected because no 5xx responses were generated.

---

### 3. Request Duration p95
**Query**
```promql
histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))
```

**Purpose**
Shows the 95th percentile latency for requests. This is the **Duration** part of the RED method.

---

### 4. Request Duration Heatmap
**Query**
```promql
rate(http_request_duration_seconds_bucket[5m])
```

**Purpose**
Visualizes the distribution of request latency across histogram buckets.

---

### 5. Active Requests
**Query**
```promql
http_requests_in_progress
```

**Purpose**
Shows the number of requests currently being processed by the application.

---

### 6. Status Code Distribution
**Query**
```promql
sum by (status_code) (rate(http_requests_total[5m]))
```

**Purpose**
Shows how responses are distributed by status code, for example 200, 404, or 500.

---

### 7. Uptime
**Query**
```promql
up{job="app"}
```

**Purpose**
Shows whether the application target is reachable by Prometheus.
- `1` = up
- `0` = down

---

## 5. PromQL Examples

Below are PromQL queries used in the lab and what they show.

### 1. Request rate by endpoint
```promql
sum(rate(http_requests_total[5m])) by (endpoint)
```
Shows requests per second grouped by endpoint.

### 2. Error rate
```promql
sum(rate(http_requests_total{status_code=~"5.."}[5m]))
```
Shows the frequency of 5xx server errors.

### 3. p95 latency
```promql
histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))
```
Shows the 95th percentile request duration.

### 4. Active requests
```promql
http_requests_in_progress
```
Shows the number of in-flight requests.

### 5. Target availability
```promql
up
```
Shows whether each monitored target is reachable by Prometheus.

### 6. Status code distribution
```promql
sum by (status_code) (rate(http_requests_total[5m]))
```
Shows response-code mix over time.

### 7. Raw request counter
```promql
http_requests_total
```
Shows raw cumulative request counts by label set.

### RED Method Demonstration
The RED method was implemented and demonstrated with:
- **Rate** → `sum(rate(http_requests_total[5m])) by (endpoint)`
- **Errors** → `sum(rate(http_requests_total{status_code=~"5.."}[5m]))`
- **Duration** → `histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))`

---

## 6. Production Setup

The monitoring stack was hardened with production-style settings in Docker Compose.

### Health Checks
Health checks were configured for:
- **app-python** via `/health`
- **loki** via `/ready`
- **grafana** via `/api/health`
- **prometheus** via `/-/healthy`

This ensures container health is visible through `docker compose ps`.

### Resource and Operational Controls
The stack includes:
- persistent volumes for Prometheus, Loki, and Grafana
- explicit retention settings for Prometheus
- restart policy `unless-stopped`

### Retention Policies
- **Prometheus**: 15 days or 10GB, whichever limit is hit first

### Persistence
The following volumes were used:
- `prometheus-data`
- `loki-data`
- `grafana-data`

This ensured that dashboards and stored metrics survived container restarts.

---

## 7. Testing Results

### Local Metrics Verification
The instrumented Flask app was started locally and checked with:
- `curl http://localhost:5000/`
- `curl http://localhost:5000/health`
- `curl http://localhost:5000/metrics`

The `/metrics` output included:
- `http_requests_total`
- `http_request_duration_seconds`
- `http_requests_in_progress`

### Unit Tests
Application tests were run with:
```bash
python -m pytest
```

Result:
- all existing tests passed successfully

### Prometheus Target Verification
Prometheus targets were checked through the API and all required targets were reported as **up**:
- `app`
- `prometheus`
- `loki`
- `grafana`

The `up` query also returned value `1` for all targets.

### Docker Health Verification
After deployment with Docker Compose, service health was checked through:
```bash
docker compose -f monitoring/docker-compose.yml ps
```

Observed result:
- `app-python` — healthy
- `grafana` — healthy
- `loki` — healthy
- `prometheus` — healthy

### Persistence Verification
The monitoring stack was restarted with:
```bash
docker compose -f monitoring/docker-compose.yml down
docker compose -f monitoring/docker-compose.yml up -d
```

After restart:
- containers returned to healthy state
- the **App Monitoring Dashboard** still existed in Grafana

This confirmed data and dashboard persistence.

### Screenshots / Evidence
The following evidence files should be included in `monitoring/docs/screenshots/`:
- `lab08-dashboard.png` — custom Grafana dashboard with live data
- Prometheus targets page screenshot showing all targets UP
- screenshot of `docker compose ps` showing healthy services

---

## 8. Challenges & Solutions

### Challenge 1 — No existing app service in monitoring stack
**Issue:**  
The Lab 7 monitoring stack had Loki, Promtail, and Grafana, but no Python application service connected to the monitoring network.

**Solution:**  
A new `app-python` service was added to `monitoring/docker-compose.yml` using the existing `app_python/Dockerfile`.

---

### Challenge 2 — Error Rate panel showed no data
**Issue:**  
The Grafana panel based on 5xx responses displayed no data.

**Solution:**  
This was expected behavior because no 5xx errors were generated during testing. The query was correct, and the empty panel reflected a healthy application state.

---

### Challenge 3 — Services initially showed `health: starting`
**Issue:**  
Immediately after `docker compose up -d`, services were still in starting state.

**Solution:**  
The stack was given additional startup time, and then `docker compose ps` was run again. All required services became healthy.

---

### Challenge 4 — Dashboard export path in Grafana UI differed slightly
**Issue:**  
The expected JSON export option appeared under the Grafana **Export** menu rather than the exact path initially assumed.

**Solution:**  
The dashboard was exported through the available UI path and saved to `monitoring/docs/app-dashboard.json`.

---

## 9. Metrics vs Logs (Comparison with Lab 7)

Lab 7 focused on logs with Loki and Promtail, while Lab 8 adds metrics with Prometheus.

### When to Use Metrics
Metrics are best for:
- trends over time
- alerting
- dashboards
- latency, rate, and error tracking
- resource and availability monitoring

Metrics answer questions like:
- How many requests per second are we serving?
- What is our p95 latency?
- Is the service up?

### When to Use Logs
Logs are best for:
- detailed event inspection
- debugging failures
- viewing exact request or error context
- tracing what happened during a specific incident

Logs answer questions like:
- What exact error occurred?
- Which request failed?
- What was the stack trace or message?

### Why Both Are Needed
Metrics provide a high-level operational view, while logs provide detailed forensic context. Together they create a more complete observability stack:
- **metrics** detect and summarize problems
- **logs** explain and diagnose them

---

## 10. Conclusion

In this lab, the Python application was instrumented with Prometheus metrics, Prometheus was deployed and configured to scrape multiple targets, and Grafana was used to build a custom dashboard with panels covering the RED method and service health.

The final stack now includes:
- application metrics
- Prometheus scraping and storage
- Grafana dashboards
- persistent observability components
- integration with the logging stack from Lab 7

This provides a much more complete monitoring setup than logs alone and prepares the project for further observability work in future labs.
