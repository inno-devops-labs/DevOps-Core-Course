# Lab 8 — Metrics & Monitoring with Prometheus

## 1. Architecture

The monitoring stack extends the Lab 7 logging setup:

- **App Python** (`devops-info-service`): Flask app instrumented with Prometheus metrics and `/metrics` endpoint.
- **Prometheus**: scrapes metrics from the app, Loki, Grafana, and itself.
- **Grafana**: visualizes metrics via Prometheus data source and dashboards.
- **Loki/Promtail**: remain as the logging backend and ship logs to Grafana (Lab 7).

Flow:

1. The Flask app exposes metrics at `http://app-python:8000/metrics`.
2. Prometheus scrapes metrics every 15s and stores them in its TSDB.
3. Grafana connects to Prometheus (`http://prometheus:9090`) as a data source.
4. Dashboards query metrics for RED method (Rate, Errors, Duration) and uptime.

## 2. Application Instrumentation

File: `app_python/app.py`

- Added `prometheus-client` to `requirements.txt` and imported `Counter`, `Gauge`, `Histogram`, and `generate_latest`.
- Defined core HTTP metrics:
  - `http_requests_total{method,endpoint,status}` (Counter) – total requests by method/endpoint/status.
  - `http_request_duration_seconds{method,endpoint}` (Histogram) – request latency in seconds.
  - `http_requests_in_progress` (Gauge) – concurrent in-flight requests.
- Defined app/business metrics:
  - `devops_info_endpoint_calls{endpoint}` (Counter) – counts calls to `/` and `/health`.
  - `devops_info_system_collection_seconds` (Histogram) – time to collect system info.
- Implemented hooks:
  - `@app.before_request` increments `http_requests_in_progress` and stores `g.request_start_time`.
  - `@app.after_request`:
    - Calculates duration and records it in `http_request_duration_seconds`.
    - Increments `http_requests_total` with labels `method`, `endpoint`, `status`.
    - Logs structured JSON request information (unchanged from Lab 7, now combined with metrics).
    - Decrements `http_requests_in_progress` in a `finally` block.
  - `@app.errorhandler(Exception)`:
    - Increments `http_requests_total` with `status="500"`.
    - Decrements `http_requests_in_progress`.
    - Logs error details and returns a 500 JSON response.
- Added `/metrics` endpoint:
  - `@app.route("/metrics")` returns `generate_latest()` with `CONTENT_TYPE_LATEST`.
- Updated existing endpoints:
  - `/` increments `devops_info_endpoint_calls{endpoint="/"}` and observes `devops_info_system_collection_seconds` for system info collection time.
  - `/health` increments `devops_info_endpoint_calls{endpoint="/health"}`.

These metrics cover RED method and basic business metrics for the service.

## 3. Prometheus Configuration

### 3.1 Docker Compose

File: `monitoring/docker-compose.yml`

- Added `prometheus-data` volume for TSDB persistence.
- Added `prometheus` service:
  - Image: `prom/prometheus:v3.9.0`.
  - Ports: `9090:9090`.
  - Config mount: `./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro`.
  - Data volume: `prometheus-data:/prometheus`.
  - Command flags:
    - `--config.file=/etc/prometheus/prometheus.yml`
    - `--storage.tsdb.retention.time=15d`
    - `--storage.tsdb.retention.size=10GB`
  - Network: `logging` (same as Loki, Grafana, app).
  - Healthcheck:
    - `wget --no-verbose --tries=1 --spider http://localhost:9090/-/healthy || exit 1`

### 3.2 Prometheus Scrape Targets

File: `monitoring/prometheus/prometheus.yml`

- Global settings:
  - `scrape_interval: 15s`
  - `evaluation_interval: 15s`
  - Storage retention:
    - `retention_time: 15d`
    - `retention_size: 10GB`
- Scrape configs:
  - `job_name: "prometheus"` – targets `localhost:9090`.
  - `job_name: "app"` – targets `app-python:8000` with `metrics_path: "/metrics"`.
  - `job_name: "loki"` – targets `loki:3100`.
  - `job_name: "grafana"` – targets `grafana:3000`.

## 4. Dashboards (Grafana)

In Grafana:

1. Added Prometheus data source:
   - Type: Prometheus.
   - URL: `http://prometheus:9090`.
2. Created an application dashboard with 6+ panels using PromQL:

Required panels and example queries:

1. **Request Rate (per endpoint)** – Time series  
   Query: `sum by (endpoint) (rate(http_requests_total[5m]))`

2. **Error Rate (5xx)** – Time series  
   Query: `sum(rate(http_requests_total{status=~"5.."}[5m]))`

3. **Request Duration p95** – Time series  
   Query: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`

4. **Request Duration Heatmap** – Heatmap  
   Query: `rate(http_request_duration_seconds_bucket[5m])`

5. **Active Requests** – Gauge or Time series  
   Query: `http_requests_in_progress`

6. **Status Code Distribution** – Pie chart  
   Query: `sum by (status) (rate(http_requests_total[5m]))`

7. **Uptime** – Stat  
   Query: `up{job="app"}`

Panel configuration notes:

- Time range: typically last 5–15 minutes for live debugging, last 1–24 hours for trends.
- Units:
  - Requests: `requests/sec`.
  - Duration: `seconds`.
- Legends:
  - Use `{{endpoint}}`, `{{status}}` where relevant.

An exported dashboard JSON file is stored as `monitoring/docs/grafana-app-dashboard.json`.

## 5. PromQL Examples

Examples used in Explore and dashboards:

1. Request rate per endpoint  
   `sum by (endpoint) (rate(http_requests_total[5m]))`

2. Error rate (5xx)  
   `sum(rate(http_requests_total{status=~"5.."}[5m]))`

3. 95th percentile latency  
   `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`

4. Active requests  
   `http_requests_in_progress`

5. Uptime for app  
   `up{job="app"}`

6. Endpoint calls (business metric)  
   `rate(devops_info_endpoint_calls[5m])`

7. System info collection time p95  
   `histogram_quantile(0.95, rate(devops_info_system_collection_seconds_bucket[5m]))`

## 6. Production Setup

### 6.1 Health Checks

File: `monitoring/docker-compose.yml`

- Prometheus:
  - `wget --no-verbose --tries=1 --spider http://localhost:9090/-/healthy || exit 1`
- App (`app-python`):
  - `curl -f http://localhost:8000/health || exit 1`
- Loki, Promtail, Grafana health checks remain from Lab 7.

### 6.2 Resource Limits

Configured via `deploy.resources.limits` and `deploy.resources.reservations`:

- Prometheus:
  - Limits: `cpus: "1.0"`, `memory: 1G`
  - Reservations: `cpus: "0.5"`, `memory: 512M`
- Loki:
  - Limits: `cpus: "1.0"`, `memory: 1G`
  - Reservations: `cpus: "0.5"`, `memory: 512M`
- Grafana:
  - Limits: `cpus: "0.5"`, `memory: 512M`
  - Reservations: `cpus: "0.25"`, `memory: 256M`
- App Python:
  - Limits: `cpus: "0.5"`, `memory: 256M`
  - Reservations: `cpus: "0.25"`, `memory: 128M`

This keeps the stack within predictable CPU and memory bounds.

### 6.3 Data Retention and Persistence

- Prometheus retention:
  - Configured via command flags:
    - `--storage.tsdb.retention.time=15d`
    - `--storage.tsdb.retention.size=10GB`
  - Mirrored in `prometheus.yml` `storage.tsdb` for clarity.
- Volumes:
  - `prometheus-data` – Prometheus TSDB.
  - `loki-data` – Loki storage.
  - `grafana-data` – Grafana dashboards and settings.

To verify persistence:

```bash
cd monitoring
docker compose up -d
docker compose ps

# After creating dashboards and generating data:
docker compose down
docker compose up -d
docker compose ps
```

Grafana dashboards and Prometheus/Loki data should survive restarts.

## 7. Testing & Verification

### 7.1 Run Stack

From repository root:

```bash
cd monitoring
docker compose up -d
docker compose ps
```

### 7.2 Generate Traffic

From host:

```bash
for i in {1..50}; do curl -s http://localhost:8000/ > /dev/null; done
for i in {1..50}; do curl -s http://localhost:8000/health > /dev/null; done
```

This generates both logs (Loki) and metrics (Prometheus).

### 7.3 Prometheus Checks

- Open Prometheus UI at `http://localhost:9090`.
- Visit `/targets` to confirm:
  - `prometheus`, `app`, `loki`, and `grafana` targets are `UP`.
- Run queries such as:
  - `up`
  - `http_requests_total`
  - `rate(http_requests_total[5m])`

## 8. Screenshots to Capture

Please capture these manually when you run the system:

1. **`/metrics` endpoint output**  
   - Start the app locally:  
     ```bash
     cd app_python
     pip install -r requirements.txt
     python app.py
     ```  
   - Visit `http://localhost:8000/metrics` in a browser or via `curl`.  
   - Screenshot of the metrics output showing `http_requests_total`, `http_request_duration_seconds`, `http_requests_in_progress`, and app-specific metrics.

2. **Prometheus `/targets` view**  
   - URL: `http://localhost:9090/targets`.  
   - All targets (`prometheus`, `app`, `loki`, `grafana`) should be `UP`.

3. **Prometheus query page**  
   - URL: `http://localhost:9090/graph`.  
   - Run a query like `sum(rate(http_requests_total[5m])) by (endpoint)` and show a non-empty graph.

4. **Grafana application dashboard**  
   - Dashboard with at least the 6 panels described above.  
   - Show live data for request rate, error rate, latency, active requests, status code distribution, and uptime.

5. **`docker compose ps` with all services healthy**  
   - From `monitoring` directory run `docker compose ps`.  
   - All services (`loki`, `promtail`, `grafana`, `prometheus`, `app-python`) should show as healthy.

6. **Persistence check (optional but recommended)**  
   - After `docker compose down` / `up -d`, show that dashboards and data are still present.

## 9. Challenges & Notes

- Combining logs and metrics in a small app required careful use of Flask hooks to ensure both logging and metrics run on every request (including errors) without double-counting.
- Gauge handling (`http_requests_in_progress`) needs `try/finally` and explicit decrement in the error handler to avoid negative values.
- Selecting the right metric types (Counter for totals, Histogram for latency, Gauge for in-progress) aligns with Prometheus best practices and the RED method.
- Using service names (`app-python`, `loki`, `grafana`, `prometheus`) as scrape targets keeps the configuration simple in Docker Compose without hard-coded IPs.

