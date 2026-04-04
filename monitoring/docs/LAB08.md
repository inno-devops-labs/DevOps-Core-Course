# lab 08: metrics & monitoring with prometheus

## 1. architecture overview

### components

| component | purpose | port |
|-----------|---------|------|
| prometheus | metrics collection and storage | 9090 |
| loki | log aggregation and storage | 3100 |
| promtail | log collection agent | 9080 |
| grafana | visualization and dashboards | 3000 |
| app-python | application with metrics endpoint | 8000 |

### data flow

```
┌─────────────────┐     ┌─────────────┐     ┌─────────────┐
│   prometheus    │     │    loki     │     │   grafana   │
│   (metrics)     │     │   (logs)    │     │    (viz)    │
└───────┬─────────┘     └──────┬──────┘     └──────┬──────┘
        │                      │                   │
        │ scrape               │ push              │ query
        ▼                      ▼                   │
┌─────────────────────────────────────────┐        │
│              app-python                 │◀───────┘
│   /metrics (prometheus endpoint)        │
│   /health (health check)                │
│   stdout (json logs) ──▶ promtail       │
└─────────────────────────────────────────┘
```

---

## 2. prometheus setup

### project structure

```
monitoring/
├── docker-compose.yml
├── .env.example
├── prometheus/
│   └── config.yml           # NEW: scrape configuration
├── loki/
│   └── config.yml
├── promtail/
│   └── config.yml
├── grafana/
│   └── provisioning/
│       ├── datasources/
│       │   └── datasources.yml  # UPDATED: added prometheus
│       └── dashboards/
│           ├── dashboards.yml
│           └── json/
│               ├── devops-logs-dashboard.json
│               └── devops-metrics-dashboard.json  # NEW
└── docs/
    ├── LAB07.md
    └── LAB08.md
```

### configuration files

| file | purpose |
|------|---------|
| [docker-compose.yml](../docker-compose.yml) | stack definition with prometheus |
| [prometheus/config.yml](../prometheus/config.yml) | scrape targets and retention |
| [grafana/provisioning/datasources/datasources.yml](../grafana/provisioning/datasources/datasources.yml) | prometheus data source |
| [grafana/provisioning/dashboards/json/devops-metrics-dashboard.json](../grafana/provisioning/dashboards/json/devops-metrics-dashboard.json) | metrics dashboard |

### key configuration concepts

**prometheus:**

| concept | value | why |
|---------|-------|-----|
| `scrape_interval: 15s` | 15 seconds | balance granularity with overhead |
| `retention.time: 15d` | 15 days | extended retention for analysis |
| `retention.size: 10GB` | 10 gb | prevent disk overflow |
| `web.enable-lifecycle` | enabled | hot reload without restart |

**scrape targets:**

| job | target | description |
|-----|--------|-------------|
| prometheus | localhost:9090 | self-monitoring |
| app-python | app-python:5000 | python application metrics |
| loki | loki:3100 | loki internal metrics |
| grafana | grafana:3000 | grafana internal metrics |

### deployment

```bash
cd monitoring
docker compose up -d
docker compose ps

CONTAINER ID   IMAGE                                       COMMAND                  CREATED         STATUS                   PORTS                                                                                      NAMES
425e04d82cf3   grafana/grafana:12.3.1                      "/run.sh"                3 minutes ago   Up 2 minutes (healthy)   0.0.0.0:3000->3000/tcp, [::]:3000->3000/tcp                                                grafana
3b49860b4dce   prom/prometheus:v3.9.0                      "/bin/prometheus --c…"   3 minutes ago   Up 2 minutes (healthy)   0.0.0.0:9090->9090/tcp, [::]:9090->9090/tcp                                                prometheus
51fce5e1786c   onemoreslacker/devops-info-service:latest   "uvicorn app:app --h…"   3 minutes ago   Up 2 minutes (healthy)   0.0.0.0:8000->5000/tcp, [::]:8000->5000/tcp                                                devops-python
d59fd5c01011   grafana/promtail:3.0.0                      "/usr/bin/promtail -…"   3 minutes ago   Up 2 minutes             0.0.0.0:9080->9080/tcp, [::]:9080->9080/tcp                                                promtail
002638e1700c   grafana/loki:3.0.0                          "/usr/bin/loki -conf…"   3 minutes ago   Up 3 minutes (healthy)   0.0.0.0:3100->3100/tcp, [::]:3100->3100/tcp, 0.0.0.0:9096->9096/tcp, [::]:9096->9096/tcp   loki
```

### verification

```bash
curl http://localhost:9090/-/healthy
Prometheus Server is Healthy.

curl http://localhost:9090/api/v1/targets | python3 -m json.tool
```

---

## 3. application metrics

### implementation

**file:** [app_python/metrics.py](../../app_python/metrics.py)

**metrics exposed:**

| metric | type | description | labels |
|--------|------|-------------|--------|
| `http_requests_total` | counter | total http requests | method, endpoint, status_code |
| `http_request_duration_seconds` | histogram | request latency | method, endpoint |
| `http_requests_active` | gauge | active requests | method, endpoint |
| `app_info` | gauge | application info | version, python_version |

**key concepts:**

| concept | implementation |
|---------|----------------|
| counter for requests | monotonically increasing, perfect for rate calculations |
| histogram for latency | provides quantile calculations (p50, p95, p99) |
| gauge for active | can go up/down as requests start/end |
| endpoint normalization | prevents high cardinality from dynamic paths |

### metrics endpoint

[metrics endpoint output](screenshots/metrics-endpoint.png)

### cardinality control

endpoints are normalized to prevent high cardinality:
- `/`, `/health`, `/metrics` - kept as-is
- other paths - normalized to `/other`

this prevents metrics explosion from dynamic paths like `/user/123`, `/user/456`, etc.

### requirements update

**file:** [app_python/requirements.txt](../../app_python/requirements.txt)

added: `prometheus-client==0.21.1`

---

## 4. promql queries

### basic queries

```promql
# request rate (requests per second)
rate(http_requests_total[5m])

# request rate by endpoint
sum(rate(http_requests_total[5m])) by (endpoint)

# error rate (5xx errors)
sum(rate(http_requests_total{status_code=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))

# active requests
sum(http_requests_active) by (endpoint)
```

### latency queries

```promql
# p50 latency
histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

# p95 latency by endpoint
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))

# p99 latency (overall)
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

# average latency
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

### aggregation queries

```promql
# total requests by status code (last hour)
sum(increase(http_requests_total[1h])) by (status_code)

# top endpoints by traffic
topk(5, sum(rate(http_requests_total[5m])) by (endpoint))

# request distribution by method
sum(rate(http_requests_total[5m])) by (method)
```

### verification

[/targets pages screenshot](screenshots/prom-targets.png)

[successful PromQL query screenshot](screenshots/prom-query.png)

---

## 5. grafana dashboard

### configuration files

| file | purpose |
|------|---------|
| [grafana/provisioning/datasources/datasources.yml](../grafana/provisioning/datasources/datasources.yml) | prometheus data source |
| [grafana/provisioning/dashboards/json/devops-metrics-dashboard.json](../grafana/provisioning/dashboards/json/devops-metrics-dashboard.json) | metrics dashboard |

### dashboard panels

| panel | type | query |
|-------|------|-------|
| request rate | time series | `sum(rate(http_requests_total[5m])) by (endpoint)` |
| error rate | time series | `sum(rate(http_requests_total{status_code=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))` |
| p95 latency | time series | `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))` |
| active requests | time series | `sum(http_requests_active) by (endpoint)` |
| status code distribution | pie chart | `sum(increase(http_requests_total[1h])) by (status_code)` |
| p99 latency (current) | stat | `histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) * 1000` |
| total requests (1h) | stat | `sum(increase(http_requests_total[1h]))` |
| service status | stat | `up{job="app-python"}` |

### access

1. open http://localhost:3000
2. login with admin/admin
3. navigate to dashboards
4. select "devops metrics dashboard"

### dashboard screenshot

[grafana dashboard with metrics panels](screenshots/grafana-metrics-dashboard.png)

---

## 6. production configuration

### resource limits

| service | cpu limit | memory limit | cpu reserved | memory reserved |
|---------|-----------|--------------|--------------|-----------------|
| prometheus | 1.0 | 1g | 0.25 | 256m |
| loki | 1.0 | 1g | 0.25 | 256m |
| grafana | 0.5 | 512m | 0.1 | 128m |
| promtail | 0.5 | 512m | 0.1 | 128m |
| app-python | 0.5 | 512m | 0.1 | 128m |

### retention

| system | retention period | size limit |
|--------|------------------|------------|
| prometheus | 15 days | 10 gb |
| loki | 7 days | - |

### persistent volumes

| volume | purpose |
|--------|---------|
| prometheus-data | tsdb storage for metrics |
| loki-data | log chunks and index |
| grafana-data | dashboards and settings |
| promtail-positions | read positions for log collection |

---

## 8. challenges

### application image rebuild required

**problem**: adding metrics requires code changes to the python application.

**solution**: the docker image needs to be rebuilt and pushed:
```bash
cd app_python
docker build -t onemoreslacker/devops-info-service:latest .
docker push onemoreslacker/devops-info-service:latest
```

### prometheus dns resolution

**problem**: prometheus needs to resolve container names for scraping.

**solution**: all services are on the same docker network (`logging`), enabling dns resolution via container names (e.g., `app-python:5000`).

### high cardinality prevention

**problem**: dynamic paths could create too many metric series.

**solution**: endpoint normalization in middleware groups unknown paths under `/other`, limiting label values.

---

## 9. comparison: lab 07 vs lab 08

| aspect | lab 07 (logs) | lab 08 (metrics) |
|--------|---------------|------------------|
| primary tool | loki | prometheus |
| data type | unstructured logs | numeric time series |
| query language | logql | promql |
| collection | push (promtail) | pull (prometheus scrapes) |
| retention | 7 days | 15 days |
| use case | debugging, error analysis | trending, alerting, slos |
