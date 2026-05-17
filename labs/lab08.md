# Lab 8 — Metrics & Monitoring with Prometheus

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Metrics%20%26%20Monitoring-blue)
![points](https://img.shields.io/badge/points-10%2B2.5-orange)
![tech](https://img.shields.io/badge/tech-Prometheus%20|%20Grafana%20|%20Docker%20Compose-informational)

> Instrument your applications with metrics and build a complete monitoring stack with Prometheus and Grafana.

## Overview

Add observability to your applications by exposing Prometheus metrics, then deploy Prometheus to collect them and Grafana to visualize. You'll instrument your app first, then build the monitoring infrastructure around it.

**What You'll Learn:**
- Application instrumentation with prometheus_client
- Prometheus scraping and metric types
- PromQL query language
- Building Grafana dashboards for metrics
- Monitoring best practices (RED method, resource limits)
- Integration with existing observability stack from Lab 7

**Tech Stack:** Prometheus 3.9+ | Grafana 12.3+ | prometheus_client | PromQL

**Prerequisites:** Lab 7 completed (Loki + Grafana stack), Python app from Lab 1-2

---

## Tasks

### Task 1 — Application Metrics (3 pts)

Add Prometheus metrics to your Python application.

#### 1.1 Understanding Application Metrics

**Why metrics matter:**
- **Logs** tell you what happened (Lab 7)
- **Metrics** tell you how much and how often
- **Together** they provide complete observability

**The RED Method (for request-driven apps):**
- **R**ate - Requests per second
- **E**rrors - Error rate
- **D**uration - Response time

<details>
<summary>💡 Prometheus Metric Types</summary>

**Counter** - Only goes up (total requests, errors)
```python
http_requests_total.inc()  # Increment by 1
```

**Gauge** - Can go up or down (memory usage, active connections)
```python
active_connections.set(42)
```

**Histogram** - Measures distribution (request duration, response size)
```python
request_duration_seconds.observe(0.25)  # Record 250ms request
```

**Summary** - Similar to histogram, with percentiles

**When to use what:**
- Counting events? → Counter
- Current state? → Gauge
- Distribution/percentiles? → Histogram

**Resources:**
- [Prometheus Metric Types](https://prometheus.io/docs/concepts/metric_types/)
- [Instrumentation Best Practices](https://prometheus.io/docs/practices/instrumentation/)

</details>

#### 1.2 Install Prometheus Client

**Add to `requirements.txt`:**
```txt
prometheus-client==0.23.1
```

**Install:**
```bash
pip install prometheus-client
```

#### 1.3 Implement Metrics Endpoint

**Add `/metrics` endpoint to your app:**

**Requirements:**
- Expose metrics at `/metrics` endpoint
- Track HTTP requests (counter)
- Track request duration (histogram)
- Track active requests (gauge)
- Use labels: `method`, `endpoint`, `status_code`

<details>
<summary>💡 Implementation Guidance</summary>

**Basic Setup (Flask):**
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Define metrics
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

@app.route('/metrics')
def metrics():
    return generate_latest()
```

**Instrumenting Requests:**
- Use `@app.before_request` to track start time
- Use `@app.after_request` to record metrics
- Increment counter with labels
- Observe histogram with duration
- Use gauge context manager for in-progress

**Label Best Practices:**
- Keep cardinality low (don't use user IDs as labels!)
- Use `/` for root, `/health` for health, group others
- Normalize endpoint names (e.g., `/user/{id}` not `/user/123`)

**Resources:**
- [prometheus_client docs](https://github.com/prometheus/client_python)
- [Python instrumentation guide](https://prometheus.io/docs/guides/python/)

</details>

#### 1.4 Add Application-Specific Metrics

**Beyond HTTP, track your app's business metrics:**
- Counter: API calls to external services
- Gauge: Items in cache, database pool size
- Histogram: Database query duration

**Example for your DevOps info service:**
```python
# Track endpoint usage
endpoint_calls = Counter('devops_info_endpoint_calls', 'Endpoint calls', ['endpoint'])

# Track system info collection time
system_info_duration = Histogram('devops_info_system_collection_seconds', 'System info collection time')
```

#### 1.5 Test Metrics Locally

**Run your app and test:**
```bash
python app.py
curl http://localhost:8000/metrics
```

**Expected output format:**
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/",status="200"} 42.0
http_requests_total{method="GET",endpoint="/health",status="200"} 15.0

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.005",method="GET",endpoint="/"} 10.0
http_request_duration_seconds_bucket{le="0.01",method="GET",endpoint="/"} 35.0
...
```

**Evidence Required:**
- Screenshot of `/metrics` endpoint output
- Code showing metric definitions
- Documentation explaining your metric choices

---

### Task 2 — Prometheus Setup (3 pts)

Deploy Prometheus and configure it to scrape your application metrics.

#### 2.1 Understanding Prometheus Architecture

<details>
<summary>💡 How Prometheus Works</summary>

**Pull-based model:**
1. Your app exposes `/metrics` endpoint
2. Prometheus scrapes (pulls) metrics on schedule
3. Stores time-series data locally
4. Provides PromQL for querying

**Key concepts:**
- **Target** - Endpoint to scrape (your app)
- **Job** - Collection of targets with same purpose
- **Scrape interval** - How often to collect (default: 15s)
- **TSDB** - Time-series database storing metrics

**vs Push-based (like StatsD):**
- Pull = simpler, apps don't need to know about Prometheus
- Better for service discovery
- Failed scrapes are visible

**Resources:**
- [Prometheus Overview](https://prometheus.io/docs/introduction/overview/)
- [First Steps with Prometheus](https://prometheus.io/docs/introduction/first_steps/)

</details>

#### 2.2 Add Prometheus to Docker Compose

**Extend `monitoring/docker-compose.yml`** from Lab 7:

**Requirements:**
- Prometheus service (image: `prom/prometheus:v3.9.0`, port 9090)
- Mount prometheus config: `./prometheus/prometheus.yml`
- Mount data volume for persistence: `prometheus-data`
- Connect to existing `logging` network from Lab 7

<details>
<summary>💡 Docker Compose Guidance</summary>

**Key points:**
- Use same network as Loki/Grafana from Lab 7
- Mount config to `/etc/prometheus/prometheus.yml`
- Use volume for data persistence: `/prometheus`
- Add `--config.file=/etc/prometheus/prometheus.yml` command argument

**Resource limits:**
```yaml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '1.0'
```

</details>

#### 2.3 Configure Prometheus

**File:** `monitoring/prometheus/prometheus.yml`

**Requirements:**
- Scrape Prometheus itself (job: `prometheus`)
- Scrape your Python app (job: `app`)
- Scrape Loki metrics (job: `loki`)
- Scrape Grafana metrics (job: `grafana`)
- Set scrape interval: 15s

<details>
<summary>💡 Prometheus Configuration Guide</summary>

**Basic structure:**
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

# Storage retention (Prometheus 3.x config-based retention)
storage:
  tsdb:
    retention_time: 15d
    retention_size: 10GB

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'app'
    static_configs:
      - targets: ['app-python:8000']
    metrics_path: '/metrics'
```

**For Docker Compose:**
- Use service names as hostnames (e.g., `loki:3100`)
- Prometheus self-scrape uses `localhost:9090`
- Check each service's metrics port:
  - Loki: port 3100, path `/metrics`
  - Grafana: port 3000, path `/metrics`
  - Your app: port 8000, path `/metrics`

**Resources:**
- [Prometheus Configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/)
- [Scrape Configs](https://prometheus.io/docs/prometheus/latest/configuration/configuration/#scrape_config)

</details>

#### 2.4 Deploy and Verify

**Deploy the updated stack:**
```bash
cd monitoring
docker compose up -d
docker compose ps
```

**Verify Prometheus:**
1. **Access UI:** http://localhost:9090
2. **Check targets:** http://localhost:9090/targets
   - All targets should be "UP" (green)
3. **Query metrics:** Try query `up` - should show all targets

**Troubleshooting targets:**
- **State: DOWN** → Check service is running, check port/path
- **State: UNKNOWN** → Prometheus just started, wait for first scrape
- **No target** → Check `prometheus.yml` syntax

**Evidence Required:**
- Screenshot of `/targets` page showing all targets UP
- Screenshot of a successful PromQL query
- `prometheus.yml` configuration file

---

### Task 3 — Grafana Dashboards (2 pts)

Build dashboards to visualize your application metrics.

#### 3.1 Add Prometheus Data Source

**In Grafana:**
1. **Connections** → **Data sources** → **Add data source** → **Prometheus**
2. URL: `http://prometheus:9090`
3. **Save & Test**

**Alternative:** Provision automatically (see Ansible bonus).

#### 3.2 Learn PromQL Basics

<details>
<summary>💡 PromQL Quick Reference</summary>

**Instant Vector (single value per time series):**
```promql
http_requests_total                                    # All request counters
http_requests_total{method="GET"}                      # Filter by label
http_requests_total{endpoint="/",status="200"}         # Multiple labels
```

**Range Vector (values over time range):**
```promql
http_requests_total[5m]                                # Last 5 minutes of data
```

**Functions:**
```promql
rate(http_requests_total[5m])                          # Requests per second
sum(rate(http_requests_total[5m]))                     # Total req/s across all series
sum by (endpoint) (rate(http_requests_total[5m]))      # Req/s per endpoint
histogram_quantile(0.95, http_request_duration_seconds_bucket)  # 95th percentile latency
```

**Operators:**
```promql
up == 0                                                # Services down
rate(http_requests_total{status="500"}[5m]) * 100     # Error rate percentage
```

**Common Queries:**
- Request rate: `rate(http_requests_total[5m])`
- Error rate: `sum(rate(http_requests_total{status=~"5.."}[5m]))`
- p95 latency: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
- CPU usage: `rate(process_cpu_seconds_total[5m]) * 100`

**Resources:**
- [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [PromQL Examples](https://prometheus.io/docs/prometheus/latest/querying/examples/)

</details>

#### 3.3 Create Application Dashboard

**Create dashboard with 6+ panels:**

1. **Request Rate** (Graph)
   - Query: `sum(rate(http_requests_total[5m])) by (endpoint)`
   - Shows requests/sec per endpoint

2. **Error Rate** (Graph)
   - Query: `sum(rate(http_requests_total{status=~"5.."}[5m]))`
   - Shows 5xx errors/sec

3. **Request Duration p95** (Graph)
   - Query: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
   - Shows 95th percentile latency

4. **Request Duration Heatmap** (Heatmap)
   - Query: `rate(http_request_duration_seconds_bucket[5m])`
   - Visualizes latency distribution

5. **Active Requests** (Gauge/Graph)
   - Query: `http_requests_in_progress`
   - Shows concurrent requests

6. **Status Code Distribution** (Pie Chart)
   - Query: `sum by (status) (rate(http_requests_total[5m]))`
   - Shows 2xx vs 4xx vs 5xx

7. **Uptime** (Stat)
   - Query: `up{job="app"}`
   - Shows if service is up (1) or down (0)

**Panel configuration tips:**
- Set appropriate time ranges
- Use legends with `{{label}}` syntax
- Set units (requests/sec, seconds, etc.)
- Add thresholds for alerting visualization

#### 3.4 Import Community Dashboards

**Grafana has pre-built dashboards:**

**For Prometheus metrics:**
- Dashboard ID: **3662** (Prometheus 2.0 Stats)

**For Loki:**
- Dashboard ID: **13407** (Loki Dashboard)

**To import:**
1. **Dashboards** → **New** → **Import**
2. Enter dashboard ID
3. Select Prometheus data source
4. **Import**

Customize these for your needs.

**Evidence Required:**
- Screenshot of your custom application dashboard with live data
- Screenshot showing all 6+ panels working
- Exported dashboard JSON file

---

### Task 4 — Production Configuration (2 pts)

Harden the monitoring stack for production use.

#### 4.1 Add Health Checks

**Add health checks to all services in `docker-compose.yml`:**

**Prometheus:**
```yaml
healthcheck:
  test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:9090/-/healthy || exit 1"]
  interval: 10s
  timeout: 5s
  retries: 5
```

**Your app:**
```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
  interval: 10s
  timeout: 5s
  retries: 5
```

#### 4.2 Configure Resource Limits

**Set limits on all services:**
- Prometheus: 1G memory, 1 CPU
- Loki: 1G memory, 1 CPU
- Grafana: 512M memory, 0.5 CPU
- Apps: 256M memory, 0.5 CPU

#### 4.3 Data Retention

**Configure retention periods:**

**Prometheus retention:**
```yaml
command:
  - '--config.file=/etc/prometheus/prometheus.yml'
  - '--storage.tsdb.retention.time=15d'
  - '--storage.tsdb.retention.size=10GB'
```

**Why retention matters:**
- Disk space management
- Query performance (smaller dataset = faster queries)
- Compliance requirements

#### 4.4 Persistent Volumes

**Ensure data survives container restarts:**
```yaml
volumes:
  prometheus-data:
  loki-data:
  grafana-data:
```

**Test persistence:**
1. Create dashboard
2. Stop containers: `docker compose down`
3. Start containers: `docker compose up -d`
4. Dashboard should still exist

**Evidence Required:**
- `docker compose ps` showing all services healthy
- Documentation of retention policies
- Proof of data persistence after restart

---

### Task 5 — Documentation (2 pts)

Create `monitoring/docs/LAB08.md` documenting your implementation.

**Required sections:**
1. **Architecture** - Diagram showing metric flow (app → Prometheus → Grafana)
2. **Application Instrumentation** - What metrics you added and why
3. **Prometheus Configuration** - Scrape targets, intervals, retention
4. **Dashboard Walkthrough** - Each panel's purpose and query
5. **PromQL Examples** - 5+ queries with explanations
6. **Production Setup** - Health checks, resources, retention policies
7. **Testing Results** - Screenshots showing everything working
8. **Challenges & Solutions** - Issues encountered and fixes

**Evidence:**
- Screenshots of dashboards with live data
- PromQL queries that demonstrate RED method
- Proof of all services healthy and scraping
- Comparison: metrics vs logs (Lab 7) - when to use each

---

## Bonus — Ansible Automation (2.5 pts)

Automate the complete observability stack (Loki + Prometheus + Grafana) deployment with Ansible.

**Extend your `monitoring` role from Lab 7** or create a comprehensive new one.

#### Bonus 1.1 Enhanced Monitoring Role

**Update `roles/monitoring/` to include:**
- Loki configuration (from Lab 7)
- Promtail configuration (from Lab 7)
- **Prometheus configuration** (new)
- Grafana data sources (Loki + Prometheus)
- Grafana dashboard provisioning (logs + metrics)

#### Bonus 1.2 Variables to Parameterize

**File:** `roles/monitoring/defaults/main.yml`

**Add Prometheus variables:**
```yaml
# Prometheus Configuration
prometheus_version: "3.9.0"
prometheus_port: 9090
prometheus_retention_days: 15
prometheus_retention_size: "10GB"
prometheus_scrape_interval: "15s"

# Scrape Targets
prometheus_targets:
  - job: "prometheus"
    targets: ["localhost:9090"]
  - job: "loki"
    targets: ["loki:3100"]
  - job: "grafana"
    targets: ["grafana:3000"]
  - job: "app"
    targets: ["app-python:8000"]
    path: "/metrics"
```

#### Bonus 1.3 Template Prometheus Config

**File:** `roles/monitoring/templates/prometheus.yml.j2`

**Use Jinja2 to generate config from variables:**
```yaml
global:
  scrape_interval: {{ prometheus_scrape_interval }}

scrape_configs:
{% for target in prometheus_targets %}
  - job_name: '{{ target.job }}'
    static_configs:
      - targets: {{ target.targets }}
    {% if target.path is defined %}
    metrics_path: '{{ target.path }}'
    {% endif %}
{% endfor %}
```

#### Bonus 1.4 Provision Grafana Dashboards

**Automatically provision dashboards:**

**File:** `roles/monitoring/files/grafana-app-dashboard.json`
- Export your application dashboard JSON
- Add to Ansible role files

**File:** `roles/monitoring/tasks/grafana.yml`
```yaml
- name: Provision Grafana dashboards
  copy:
    src: "{{ item }}"
    dest: "{{ monitoring_dir }}/grafana/provisioning/dashboards/"
  loop:
    - grafana-app-dashboard.json
    - grafana-logs-dashboard.json
```

#### Bonus 1.5 End-to-End Deployment

**Single playbook deploys everything:**
```bash
ansible-playbook playbooks/deploy-monitoring.yml
```

**Should deploy:**
- Loki + Promtail + Grafana (Lab 7)
- Prometheus (Lab 8)
- Grafana data sources (Loki + Prometheus)
- Grafana dashboards (logs + metrics)
- All with proper config, health checks, resources

**Evidence Required:**
- Ansible playbook execution showing idempotency
- Templated configuration files
- Screenshot of Grafana with both data sources working
- Both dashboards (logs + metrics) automatically provisioned
- Documentation of role structure and variables

---

## Checklist

**Before submitting:**
- [ ] `/metrics` endpoint added to Python app
- [ ] prometheus_client installed and configured
- [ ] Counter, Gauge, Histogram metrics implemented
- [ ] Prometheus deployed and scraping all targets
- [ ] All targets showing "UP" in Prometheus UI
- [ ] Prometheus data source added to Grafana
- [ ] Custom dashboard with 6+ panels created
- [ ] PromQL queries demonstrating RED method
- [ ] Health checks on all services
- [ ] Resource limits configured
- [ ] Data retention policies set
- [ ] Volumes persist after restart
- [ ] Complete LAB08.md documentation
- [ ] Screenshots of working dashboards

**Bonus (if attempting):**
- [ ] Ansible role extended for Prometheus
- [ ] Variables parameterize all configs
- [ ] Prometheus config templated with Jinja2
- [ ] Grafana dashboards auto-provisioned
- [ ] Single playbook deploys full stack
- [ ] Idempotency verified

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Application Metrics** | 3 pts | `/metrics` endpoint with Counter, Gauge, Histogram; proper labels |
| **Prometheus Setup** | 3 pts | Deployed, configured, scraping all targets successfully |
| **Grafana Dashboards** | 2 pts | Custom dashboard with 6+ panels, PromQL queries |
| **Production Config** | 2 pts | Health checks, resource limits, retention, persistence |
| **Documentation** | 2 pts | Complete LAB08.md with architecture, queries, evidence |
| **Bonus: Ansible** | 2.5 pts | Full stack automation with templates and provisioning |
| **Total** | 12.5 pts | 10 pts required + 2.5 bonus |

**Grading Scale:**
- **10/10:** All working, excellent dashboards, production-ready config, thorough docs
- **8-9/10:** All works, good dashboards, basic production config, good docs
- **6-7/10:** Core working, simple dashboards, minimal config, basic docs
- **<6/10:** Incomplete, missing components, needs revision

---

## Resources

<details>
<summary>📊 Prometheus Documentation</summary>

- [Prometheus Overview](https://prometheus.io/docs/introduction/overview/)
- [Prometheus Configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/)
- [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Metric Types](https://prometheus.io/docs/concepts/metric_types/)
- [Instrumentation Best Practices](https://prometheus.io/docs/practices/instrumentation/)

</details>

<details>
<summary>🐍 Python Instrumentation</summary>

- [prometheus_client GitHub](https://github.com/prometheus/client_python)
- [Python Instrumentation](https://prometheus.io/docs/guides/python/)
- [Flask Metrics Example](https://github.com/prometheus/client_python#flask)
- [Metric Naming](https://prometheus.io/docs/practices/naming/)

</details>

<details>
<summary>📈 Grafana & Dashboards</summary>

- [Grafana Prometheus Data Source](https://grafana.com/docs/grafana/latest/datasources/prometheus/)
- [Dashboard Best Practices](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/best-practices/)
- [PromQL in Grafana](https://grafana.com/docs/grafana/latest/datasources/prometheus/query-editor/)
- [Dashboard Provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/#dashboards)

</details>

<details>
<summary>📚 Observability Concepts</summary>

- [RED Method](https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/)
- [USE Method](http://www.brendangregg.com/usemethod.html) - For resources
- [The Four Golden Signals](https://sre.google/sre-book/monitoring-distributed-systems/)
- [Metrics vs Logs vs Traces](https://peter.bourgon.org/blog/2017/02/21/metrics-tracing-and-logging.html)

</details>

---

## Looking Ahead

- **Lab 9:** Kubernetes - Deploy your monitored apps to K8s
- **Lab 10:** Helm - Package your monitoring stack as Helm charts
- **Lab 16:** Kubernetes Monitoring - Full observability with init containers and probes

---

**Good luck!** 🚀
