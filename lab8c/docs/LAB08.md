# Lab 8 — Metrics & Monitoring with Prometheus

## 1. Architecture

The app exposes metrics at `/metrics`. Prometheus scrapes that endpoint every 15 seconds, stores the time series, and Grafana queries Prometheus to draw dashboards.

Rough flow:

- **App** → exposes `/metrics` in Prometheus text format
- **Prometheus** → scrapes app, Loki, Grafana, and itself on the same Docker network (`logging`)
- **Grafana** → uses Prometheus as a data source (`http://prometheus:9090`) and shows RED metrics (rate, errors, duration) plus app health

So: app and other services are scraped by Prometheus; Grafana only talks to Prometheus (and Loki for logs from Lab 7 if you use that stack too).

## 2. Application instrumentation

The Python app lives in `lab3c/app_python`. I added `prometheus-client==0.23.1` to `requirements.txt` and wired up metrics in `app.py`.

**What’s exposed:**

- **http_requests_total** (counter) — total requests with labels `method`, `endpoint`, `status`. Used for request rate and error rate.
- **http_request_duration_seconds** (histogram) — request duration with `method` and `endpoint`. Used for latency percentiles (e.g. p95).
- **http_requests_in_progress** (gauge) — how many requests are in flight right now.
- **devops_info_endpoint_calls** (counter) — per-endpoint usage (e.g. `/`, `/health`).
- **devops_info_system_collection_seconds** (histogram) — how long it takes to gather system info on the root endpoint.

Paths are normalized to `/`, `/health`, `/metrics`, or `other` so we don’t blow up cardinality. A middleware records the start time, bumps the in-progress gauge, runs the handler, then records duration and status and decrements the gauge.

The `/metrics` route just returns `generate_latest()` with the right content type so Prometheus can scrape it.

## 3. Prometheus configuration

Config is in `lab8c/prometheus/prometheus.yml`.

- Global scrape interval: 15s.
- Four jobs: **prometheus** (self), **app** (`app-python:5000`, path `/metrics`), **loki** (`loki:3100`), **grafana** (`grafana:3000`).

Retention (15d, 10GB) is set on the command line in `docker-compose.yml`, not in this file.

## 4. Dashboard

The custom dashboard is in `lab8c/docs/grafana-app-dashboard.json`. It has seven panels:

1. **Request rate** — `sum(rate(http_requests_total[5m])) by (endpoint)` (requests per second per endpoint).
2. **Error rate (5xx)** — `sum(rate(http_requests_total{status=~"5.."}[5m]))`.
3. **Request duration p95** — `histogram_quantile(0.95, ...)` over the duration histogram.
4. **Active requests** — `http_requests_in_progress`.
5. **Status code distribution** — `sum by (status) (rate(http_requests_total[5m]))` (pie chart).
6. **Uptime (app)** — `up{job="app"}` (1 = up, 0 = down).
7. **Request duration heatmap** — `rate(http_request_duration_seconds_bucket[5m])`.

When you import the JSON in Grafana, it will ask for a Prometheus data source; pick the one you added (URL `http://prometheus:9090`).

## 5. PromQL examples

- `rate(http_requests_total[5m])` — request rate over the last 5 minutes.
- `sum(rate(http_requests_total[5m])) by (endpoint)` — same, broken down by endpoint.
- `sum(rate(http_requests_total{status=~"5.."}[5m]))` — 5xx error rate (RED: errors).
- `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))` — 95th percentile latency in seconds (RED: duration).
- `up{job="app"}` — 1 if the app target is up, 0 if down.
- `http_requests_in_progress` — current number of requests being processed.

## 6. Production-style setup

In `lab8c/docker-compose.yml`:

- **Health checks**: Prometheus uses `wget` on `/-/healthy`; the app uses `curl` on `/health`. Loki and Grafana keep their existing checks.
- **Resource limits**: Prometheus 1 CPU / 1G; Loki 1 CPU / 1G; Grafana 0.5 CPU / 512M; app 0.5 CPU / 256M.
- **Retention**: 15 days and 10GB via Prometheus command-line flags.
- **Volumes**: `prometheus-data`, `loki-data`, `grafana-data` so data survives restarts.

## 7. Testing

- Run the app locally from `lab3c/app_python`, then hit `http://localhost:8000/metrics` — you should see the usual Prometheus text output.
- Run the stack: `cd lab8c && docker compose up -d`. Open http://localhost:9090/targets and check that all targets (prometheus, app, loki, grafana) are UP. Run a few queries in the Prometheus UI (e.g. `up`, `rate(http_requests_total[5m])` after some traffic).
- In Grafana, add the Prometheus data source and import the dashboard from `lab8c/docs/grafana-app-dashboard.json`. Generate some traffic to the app and confirm the panels show data.

Screenshots to put in `lab8c/docs/`:

- `metrics-endpoint.jpg` — browser or terminal output of `/metrics`.
- `prometheus-targets.jpg` — Targets page with all UP.
- `prometheus-query.jpg` — e.g. result of `up` or `rate(http_requests_total[5m])`.
- `grafana-dashboard.jpg` — the custom dashboard with live data.

## 8. Challenges and fixes

- **Middleware order**: Metrics need the response status and duration, so the metrics middleware runs the handler first and then records counter/histogram/gauge. The logging middleware is separate and doesn’t affect the numbers.
- **Cardinality**: We only use a few endpoint labels (`/`, `/health`, `/metrics`, `other`) so we don’t get thousands of series from random paths.
- **Docker**: Prometheus config is mounted at `/etc/prometheus/prometheus.yml`. All scrape targets use service names on the `logging` network (`app-python:5000`, `loki:3100`, `grafana:3000`).

## 9. Metrics vs logs (Lab 7)

Logs (Loki) answer “what happened” — individual requests, errors, stack traces. Metrics (Prometheus) answer “how much” and “how often” — rates, percentiles, counts. You need both: use metrics for dashboards and alerts, and when something spikes, dig into the logs for context.
