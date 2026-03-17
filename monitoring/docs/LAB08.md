# Lab 8 — Metrics & Monitoring with Prometheus

---

## 1. Architecture

```
Python App (/metrics) → Prometheus (scraping, TSDB) → Grafana (dashboards)
```

**Flow:**

1. Flask app exposes `/metrics`
2. Prometheus scrapes every 15s
3. Grafana visualizes via PromQL

---

## 2. Application Instrumentation

Metrics implemented using `prometheus_client`.

### Core HTTP Metrics (RED Method)

* **Counter** `http_requests_total`

  * Labels: `method`, `endpoint`, `status`
  * Tracks total requests (Rate & Errors)

* **Histogram** `http_request_duration_seconds`

  * Labels: `method`, `endpoint`
  * Tracks latency (Duration)

* **Gauge** `http_requests_in_progress`

  * Tracks active requests

Instrumentation is done using `before_request` and `after_request`.

---

### Custom Application Metrics

* **Counter** `external_api_calls_total`

  * Tracks calls to external services

* **Gauge** `cache_items`

  * Tracks cache size

* **Histogram** `db_query_duration_seconds`

  * Tracks DB query performance

These simulate real-world service monitoring.

---

![`/metrics` output screenshot](./metrics-output.png)

```python
# -----------------------------
# Metrics Definitions
# -----------------------------
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed'
)

external_api_calls_total = Counter(
    "external_api_calls_total",
    "Total calls made to external API",
    ["service_name"]
)

cache_items = Gauge(
    "cache_items",
    "Current number of items in the application cache"
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type"]
)

@app.before_request
def before_request():
    g.start_time = time.time()
    http_requests_in_progress.inc()

@app.after_request
def after_request(response):
    duration = time.time() - g.start_time
    endpoint = request.path

    http_request_duration_seconds.labels(request.method, endpoint).observe(duration)
    http_requests_total.labels(request.method, endpoint, response.status_code).inc()

    http_requests_in_progress.dec()
    return response
```

---

## 3. Prometheus Configuration

* Scrape interval: **15s**
* Retention: **15 days**
* Targets:

  * `app-python:8000`
  * `prometheus:9090`
  * `loki:3100`
  * `grafana:3000`

![Prometheus /targets showing UP](./prometheus-targets.png)
![Prometheus query up](./prometheus-up.png)

---

## 4. Dashboard Walkthrough

### Panels

1. **Request Rate**

```promql
sum(rate(http_requests_total[5m])) by (endpoint)
```

2. **Error Rate**

```promql
sum(rate(http_requests_total{status=~"5.."}[5m]))
```

3. **p95 Latency**

```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

4. **Latency Heatmap**

```promql
rate(http_request_duration_seconds_bucket[5m])
```

5. **Active Requests**

```promql
http_requests_in_progress
```

6. **Status Distribution**

```promql
sum by (status) (rate(http_requests_total[5m]))
```

7. **Uptime**

```promql
up{job="app"}
```

Dashboards json: `./grafana-dashboards.json`
![full Grafana dashboard](./grafana-dashboards.png)

---

## 5. PromQL Examples

```promql
# Total request rate
sum(rate(http_requests_total[5m]))

# Per endpoint traffic
sum by (endpoint) (rate(http_requests_total[5m]))

# Error %
sum(rate(http_requests_total{status=~"5.."}[5m]))
/ sum(rate(http_requests_total[5m])) * 100

# p95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Service health
up{job="app"}
```

---

## 6. Testing Results

* `/metrics` endpoint works
* Prometheus scraping successfully
* All targets **UP**
* Grafana shows live data

---

## 7. Challenges & Solutions

**Metrics not showing**

* Fixed incorrect service name / port

**Grafana no data**

* Verified Prometheus data source

**Latency calculation confusion**

* Used `histogram_quantile` correctly

---

## 8. Metrics vs Logs (Lab 7)

| Metrics             | Logs      |
| ------------------- | --------- |
| Trends & monitoring | Debugging |
| Prometheus          | Loki      |
| Aggregated          | Detailed  |

**Use metrics for:** performance, alerts
**Use logs for:** debugging errors

---

## ✅ Conclusion

Implemented full monitoring pipeline:

* App → Prometheus → Grafana
* Covers **Rate, Errors, Duration (RED)**
* Provides real-time observability
