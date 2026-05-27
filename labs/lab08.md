# Lab 8 — Metrics & Monitoring with Prometheus

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Metrics%20%26%20Monitoring-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![tech](https://img.shields.io/badge/tech-Prometheus%203.x%20|%20Grafana%2013%20|%20Docker%20Compose-informational)

> Instrument your Lab 1 Python app with metrics, then deploy Prometheus to scrape them and Grafana to visualise the **RED method** — alongside last week's Loki stack.

## Overview

In Lab 7 you gave your service *eyes* (logs). This week you give it a *pulse* (metrics). You'll add a `/metrics` endpoint to your Lab 1 Python app with `prometheus_client`, deploy **Prometheus 3.x** to scrape it on a 15-second schedule, and build a Grafana dashboard around the **R**ate / **E**rrors / **D**uration method. Prometheus joins the same `logging` Docker network you stood up in Lab 7, so by the end you have logs *and* metrics in one Grafana.

**What You'll Learn:**
- Application instrumentation with `prometheus_client` — counters, gauges, histograms
- Why Prometheus is **pull-based** and how scrape config + service discovery work
- **PromQL** for rates, percentiles, and per-endpoint aggregation
- Designing a dashboard around the **RED method** (Rate, Errors, Duration)
- Controlling **label cardinality** so you don't OOM your TSDB
- Production concerns: retention, resource limits, health checks, persistence

> ✨ **Prometheus 3.x note.** This lab uses Prometheus 3.x (3.11+), the current major. Versus 2.x it defaults to UTF-8 metric/label names, a built-in OTLP receiver, remote-write 2.0, and — most relevant here — **native histograms are GA** (auto-bucketed, ~5× cheaper than classic histograms, same `histogram_quantile()` query). You'll use classic histograms in the required tasks and may opt into native histograms as a stretch.

**Prerequisites:** Lab 1 (Python web app), Lab 6 (Docker Compose), Lab 7 (Loki + Alloy + Grafana stack — Prometheus extends that same `monitoring/` stack).

**Tech Stack:** Prometheus **3.11.3** (or 3.5 LTS) · Grafana **13** · `prometheus_client` **0.23+** · PromQL · Docker Compose v2

---

## Tasks

> **Point split:** Task 1 (3) + Task 2 (3) + Task 3 (2) + Task 4 (1) + Task 5 (1) = **10 pts**. Bonus = **2 pts**.
> Task 1 is self-contained: instrument the app and see `/metrics` locally — no Prometheus needed yet. Everything after builds on it.

### Task 1 — Instrument the Python App (3 pts)

Add a Prometheus `/metrics` endpoint to your Lab 1 service.

#### 1.1 Understand the metric types

Read these before you write code — they answer the questions the instrumentation asks of you:
- [Prometheus metric types](https://prometheus.io/docs/concepts/metric_types/)
- [Instrumentation best practices](https://prometheus.io/docs/practices/instrumentation/)
- [`prometheus_client` (Python)](https://github.com/prometheus/client_python)

**Be able to answer in your LAB08.md:**
- When do you reach for a **counter** vs a **gauge** vs a **histogram**? Give one example of each from your own app.
- Why do you query `rate(counter[5m])` instead of the counter's raw value?
- What is **label cardinality**, and why would `user_id` or `request_id` as a label eventually OOM Prometheus?

<details>
<summary>💡 The three types you'll use</summary>

| Type | Behaviour | Use for | Query with |
|------|-----------|---------|------------|
| **Counter** | Only goes up (resets to 0 on restart) | requests, errors, bytes | `rate()`, `increase()` |
| **Gauge** | Up *and* down | in-flight requests, queue depth, cache size | direct, `avg()`, `max()` |
| **Histogram** | Buckets a distribution | request latency, payload size | `histogram_quantile()` |

A classic histogram exposes three series families per label set: `*_bucket{le="..."}` (cumulative counts), `*_sum`, and `*_count`. That's what makes server-side percentiles possible.

</details>

#### 1.2 Add the client library

Add to `app_python/requirements.txt` (check PyPI for the current patch; `0.23+` is required, `0.25.x` is latest):

```txt
prometheus-client==0.23.1
```

```bash
pip install -r requirements.txt
```

#### 1.3 Implement the `/metrics` endpoint — YOUR TASK

Add HTTP instrumentation to your Lab 1 app. The skeleton below is **Flask**; adapt the hooks to FastAPI middleware if that's your stack. Fill in the `YOUR-TASK` markers.

```python
# app.py — add metrics to your Lab 1 service
import time
from flask import Flask, Response, request
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# --- Metric definitions (low-cardinality labels only!) ---
REQS = Counter(
    "http_requests_total", "Total HTTP requests",
    ["method", "endpoint", "status"],
)
LAT = Histogram(
    "http_request_duration_seconds", "HTTP request latency",
    ["method", "endpoint"],
    # SRE default buckets — tune from real traffic later
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
INF = Gauge("http_requests_in_progress", "In-flight HTTP requests")

@app.before_request
def _before():
    request._t0 = time.perf_counter()
    INF.inc()

@app.after_request
def _after(resp):
    duration = time.perf_counter() - request._t0
    # YOUR-TASK: use the ROUTE RULE, not request.path, as the `endpoint` label.
    # Why? request.path = "/user/123" creates a new series per id (cardinality bomb).
    # The route rule "/user/<id>" is bounded. Hint: request.url_rule.rule.
    endpoint = ...
    # YOUR-TASK: increment REQS with labels (method, endpoint, status_code)
    #            and observe LAT with (method, endpoint).
    INF.dec()
    return resp

@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
```

> ⚠️ **Cardinality is the #1 way to OOM Prometheus.** Each unique label combination is its own time series (~3–5 KB of RAM). Labels must be *bounded* enumerations: `method` (~8), `endpoint` (dozens, normalised), `status` (~10). **Never** put `user_id`, `request_id`, raw paths, emails, or timestamps in a label.

<details>
<summary>💡 Instrumentation hints</summary>

- `@app.before_request` records a start time and bumps the in-flight gauge; `@app.after_request` records the duration and increments the counter.
- `request.url_rule.rule` gives the matched route template (`/health`, `/`) — fall back to `"unknown"` when `url_rule` is `None` (404s).
- Cast the status to a string: `REQS.labels(request.method, endpoint, str(resp.status_code)).inc()`.
- FastAPI: do the same in an `@app.middleware("http")` coroutine; expose `/metrics` with `Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)`.
- Reference: [Python instrumentation guide](https://prometheus.io/docs/guides/python/), [metric naming](https://prometheus.io/docs/practices/naming/).

</details>

#### 1.4 Add one business metric

Beyond HTTP, add **one** metric meaningful to your DevOps info service. Examples:

```python
# Counter: how often each endpoint is hit (separate from the RED counter)
endpoint_calls = Counter("devops_info_endpoint_calls_total", "Endpoint calls", ["endpoint"])

# Histogram: time spent collecting system info for GET /
sysinfo_seconds = Histogram("devops_info_collection_seconds", "System info collection time")
```

#### 1.5 Test locally

```bash
python app.py
# generate a little traffic
for i in $(seq 1 20); do curl -s localhost:8000/ > /dev/null; done
curl -s localhost:8000/metrics | grep -E "http_requests_total|http_request_duration"
```

The output is the Prometheus text exposition format (the snippet below is **illustrative** — your counts and buckets will differ):

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/",status="200"} 20.0
# HELP http_request_duration_seconds HTTP request latency
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.005",method="GET",endpoint="/"} 12.0
http_request_duration_seconds_bucket{le="0.01",method="GET",endpoint="/"} 18.0
...
```

**Evidence:**
- Screenshot of `curl localhost:8000/metrics` output showing your counter, histogram, gauge, and business metric.
- The metric-definition code committed to `app_python/`.

---

### Task 2 — Deploy Prometheus & Scrape Config (3 pts)

Add Prometheus to the `monitoring/` stack from Lab 7 and point it at your app.

#### 2.1 Understand the pull model

**Be able to answer in your LAB08.md:**
- Why does a *failed scrape* give you target health "for free" (`up == 0`), where a push model can't?
- What's the difference between a **job**, a **target**, and the **scrape interval**?
- In Docker Compose, why do you scrape `app-python:8000` (service name) and not `localhost:8000`?

#### 2.2 Add the Prometheus service — YOUR TASK

**File:** `monitoring/docker-compose.yml` (extend the Lab 7 stack)

Prometheus joins the same `logging` network so it can reach Loki, Grafana, and your app by service name. Fill in the `YOUR-TASK` markers.

```yaml
  prometheus:
    image: prom/prometheus:v3.11.3      # 3.x major; or v3.5.0 LTS
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      # YOUR-TASK: add config-based retention flags (Task 4 hardens these):
      #   --storage.tsdb.retention.time=15d
      #   --storage.tsdb.retention.size=2GB
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    networks: [logging]

volumes:
  prometheus-data:      # add alongside loki-data / grafana-data
```

> The `logging` network and the `loki-data` / `grafana-data` volumes already exist from Lab 7 — you're adding `prometheus` as a fourth service and `prometheus-data` as a third named volume.

#### 2.3 Write the scrape config — YOUR TASK

**File:** `monitoring/prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # 1) Prometheus scrapes itself — the self-monitoring job.
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  # 2) YOUR-TASK: scrape your instrumented Python app.
  #    job_name: "app"; target: "app-python:8000"; metrics_path defaults to /metrics.

  # 3) Loki and Grafana both expose /metrics natively (no exporter needed).
  - job_name: "loki"
    static_configs:
      - targets: ["loki:3100"]
  - job_name: "grafana"
    static_configs:
      - targets: ["grafana:3000"]
```

<details>
<summary>💡 Scrape-config hints & the optional echo target</summary>

- `metrics_path` defaults to `/metrics`, so you only set it for non-standard paths.
- Service names are the hostnames on a Docker Compose network — `loki:3100`, `grafana:3000`, `app-python:8000`. Only Prometheus's *self*-scrape uses `localhost:9090`.
- **Optional second app target — the course `echo` plumbing.** The repo ships a tiny Go service at [`plumbing/echo`](../plumbing/echo) that already exposes `/metrics` (`echo_requests_total` counter, `echo_uptime_seconds` gauge). Adding it gives your dashboard a second instrumented service. You do **not** modify it — just add it to compose and to the scrape config:

  ```yaml
  # docker-compose.yml
    echo:
      build: ../plumbing/echo          # or image: ghcr.io/inno-devops-labs/echo:v1
      ports: ["8081:8081"]
      networks: [logging]
  ```
  ```yaml
  # prometheus.yml
    - job_name: "echo"
      static_configs:
        - targets: ["echo:8081"]
  ```

- Reference: [Prometheus configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/), [scrape_config](https://prometheus.io/docs/prometheus/latest/configuration/configuration/#scrape_config).

</details>

#### 2.4 Deploy and verify targets

```bash
cd monitoring
docker compose up -d        # v2 CLI — space, not hyphen
docker compose ps
```

1. **Prometheus UI:** open `http://localhost:9090`.
2. **Targets:** open `http://localhost:9090/targets` — every job (`prometheus`, `app`, `loki`, `grafana`, and `echo` if added) should be **UP** (green).
3. **First query:** in the UI (Graph tab) run `up` — each target returns `1`.

**Troubleshooting:**
- Target **DOWN** → the service isn't running, or the port/path is wrong. `docker compose logs prometheus`.
- Target **unknown / no data yet** → wait one scrape interval (15s).
- No target at all → YAML indentation error in `prometheus.yml`; check `docker compose logs prometheus` for a parse error.

**Evidence:**
- Screenshot of `/targets` showing all targets UP.
- Screenshot of the `up` query result.
- `prometheus.yml` committed to `monitoring/prometheus/`.

---

### Task 3 — Grafana RED Dashboard (2 pts)

Visualise your app's health with the **RED method**: **R**ate, **E**rrors, **D**uration.

#### 3.1 Add Prometheus as a data source

In the Grafana from Lab 7 (already has Loki):
1. **Connections → Data sources → Add data source → Prometheus**.
2. URL: `http://prometheus:9090` (service name on the `logging` network).
3. **Save & Test** → should report the data source is working.

> The bonus track provisions this automatically; doing it by hand once teaches you what the provisioning YAML encodes.

#### 3.2 Practise PromQL first

Run these in **Explore** (Prometheus data source) before building panels — they map directly to the panels below. **Generate traffic first** so the series aren't empty:

```bash
for i in $(seq 1 200); do curl -s localhost:8000/ > /dev/null; curl -s localhost:8000/health > /dev/null; done
```

```promql
# Rate — requests/sec per endpoint
sum by (endpoint) (rate(http_requests_total[5m]))

# Errors — 5xx requests/sec
sum by (endpoint) (rate(http_requests_total{status=~"5.."}[5m]))

# Duration — p95 latency (note: histogram_quantile OUTSIDE the sum by le)
histogram_quantile(0.95,
  sum by (endpoint, le) (rate(http_request_duration_seconds_bucket[5m])))

# Error ratio — 5xx as a fraction of all requests
sum(rate(http_requests_total{status=~"5.."}[5m]))
  / sum(rate(http_requests_total[5m]))
```

<details>
<summary>💡 PromQL quick reference</summary>

- **Instant vector** `http_requests_total{status="500"}` — one sample per series. **Range vector** `http_requests_total[5m]` — all samples in a window; can't be graphed until you collapse it with a function.
- **`rate()`** handles counter resets (pod restarts); raw subtraction and `irate()` do not — use `rate()` for graphs.
- Keep the range `[Xm]` ≥ 4× the scrape interval. With 15s scrapes, `[1m]` is the floor that doesn't lie.
- **Never average a percentile.** `histogram_quantile()` goes *outside* the `sum by (le, …)`, never inside an `avg()`.
- Reference: [PromQL basics](https://prometheus.io/docs/prometheus/latest/querying/basics/), [examples](https://prometheus.io/docs/prometheus/latest/querying/examples/).

</details>

#### 3.3 Build the dashboard — 6 panels

Each panel answers one question. (PromQL is real; any described "values" are **illustrative** — yours depend on your traffic.)

| # | Panel | Visualisation | Query | Answers |
|---|-------|---------------|-------|---------|
| 1 | **Request rate** | Time series | `sum by (endpoint) (rate(http_requests_total[5m]))` | *How busy?* |
| 2 | **Error rate** | Time series | `sum by (endpoint) (rate(http_requests_total{status=~"5.."}[5m]))` | *How often failing?* |
| 3 | **p95 latency** | Time series | `histogram_quantile(0.95, sum by (endpoint, le) (rate(http_request_duration_seconds_bucket[5m])))` | *How slow (95th)?* |
| 4 | **Latency heatmap** | Heatmap | `sum by (le) (rate(http_request_duration_seconds_bucket[5m]))` | *What's the long tail?* |
| 5 | **In-flight requests** | Gauge / Stat | `http_requests_in_progress` | *How many right now?* |
| 6 | **Service uptime** | Stat | `up{job="app"}` | *Are we alive (1/0)?* |

**How to build:**
1. **Dashboards → New → New dashboard → Add visualization**, pick the **Prometheus** data source.
2. Enter the PromQL; set the visualisation type and a clear title.
3. Set **units** (panel 1: `req/s`; panel 3: `seconds`), a `{{endpoint}}` legend, and a threshold on the error panel.
4. **Save dashboard**, then export the JSON model into `monitoring/`.

> 💡 Want a head start on infrastructure panels? Import community dashboard **ID 3662** (Prometheus self-stats) via **Dashboards → New → Import** and bind it to your Prometheus data source. Your *own* 6-panel RED dashboard is what's graded.

**Evidence:**
- Screenshot of your 6-panel RED dashboard with live data from a `curl` loop.
- The exported dashboard JSON committed to `monitoring/`.

---

### Task 4 — Production Configuration (1 pt)

Harden the metrics stack so it isn't a toy.

#### 4.1 Resource limits

Cap Prometheus so a cardinality spike can't starve the host (apply to the other services too):

```yaml
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 1G
        reservations:
          cpus: "0.25"
          memory: 256M
```

#### 4.2 Retention

Prometheus 3.x retention is set on the command line (you stubbed these in Task 2.2):

```yaml
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.retention.time=15d"
      - "--storage.tsdb.retention.size=2GB"
```

Document *why* retention matters: disk management, faster queries on a smaller dataset, and (in the real world) compliance.

#### 4.3 Health check & persistence

```yaml
    healthcheck:
      test: ["CMD-SHELL", "wget -q --spider http://localhost:9090/-/healthy || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 15s
```

Confirm the `prometheus-data` volume survives a restart:

```bash
docker compose down && docker compose up -d
# the up query still shows history; dashboards still present
```

**Evidence:**
- `docker compose ps` showing services `healthy`.
- A note (or screenshot) proving metrics history survived `down`/`up`.

---

### Task 5 — Documentation (1 pt)

Write `monitoring/docs/LAB08.md`.

**Required sections:**
1. **Architecture** — a diagram (Mermaid or image) of `app → Prometheus → Grafana`, alongside the Lab 7 log path.
2. **Instrumentation** — which metrics you added, their types, your label choices, and how you kept cardinality bounded (answer the Task 1.1 questions).
3. **Scrape config** — your jobs, the 15s interval, the pull model (answer the Task 2.1 questions).
4. **Dashboard** — each RED panel, its PromQL, and the question it answers.
5. **Production config** — retention rationale, resource limits, health check, persistence proof.
6. **Metrics vs logs** — one paragraph: when you'd reach for Prometheus vs the Lab 7 Loki query.
7. **Challenges** — problems you hit and how you solved them.

Include config snippets (not whole files) and the screenshots from Tasks 1–4.

---

## Bonus — Ansible Automation (2 pts)

Automate the metrics stack with Ansible, extending the `roles/monitoring` role from Lab 7.

Update the role so a single playbook deploys **logs + metrics** together:
- Template `prometheus/prometheus.yml` from Jinja2 — scrape targets, interval, retention as variables.
- Add the `prometheus` service (and `prometheus-data` volume) to the templated `docker-compose.yml`.
- Provision the Prometheus data source into Grafana (`grafana/provisioning/datasources/`).
- Provision your exported RED dashboard JSON (`grafana/provisioning/dashboards/`).
- Wait for Prometheus `:9090/-/healthy` before reporting success.

**Requirements:**
- Parameterise: `prometheus_version` (`v3.11.3`), `prometheus_port` (`9090`), `prometheus_retention_time` (`15d`), `prometheus_scrape_interval` (`15s`), and a `prometheus_targets` list.
- Idempotent — a second run reports `changed=0`.
- Compatible with ansible-core 2.18+; deploy with `community.docker.docker_compose_v2`.
- Playbook: `playbooks/deploy-monitoring.yml`.

<details>
<summary>💡 Variables & template sketch</summary>

```yaml
# roles/monitoring/defaults/main.yml
prometheus_version: "v3.11.3"
prometheus_port: 9090
prometheus_retention_time: "15d"
prometheus_scrape_interval: "15s"
prometheus_targets:
  - { job: "prometheus", targets: ["localhost:9090"] }
  - { job: "app",        targets: ["app-python:8000"] }
  - { job: "loki",       targets: ["loki:3100"] }
  - { job: "grafana",    targets: ["grafana:3000"] }
```

```jinja
{# roles/monitoring/templates/prometheus.yml.j2 #}
global:
  scrape_interval: {{ prometheus_scrape_interval }}

scrape_configs:
{% for t in prometheus_targets %}
  - job_name: "{{ t.job }}"
    static_configs:
      - targets: {{ t.targets | to_json }}
{% endfor %}
```

</details>

**Evidence:**
- Playbook run output (first run: changes; second run: `changed=0`).
- The rendered (templated) `prometheus.yml` and the provisioned data source + dashboard.
- Screenshot of Grafana with **both** data sources (Loki + Prometheus) working.

---

## How to Submit

1. **Create a branch:**
   ```bash
   git checkout -b lab08
   ```
2. **Commit your work:**
   ```bash
   git add app_python/ monitoring/
   # if you did the bonus:
   git add ansible/roles/monitoring ansible/playbooks/deploy-monitoring.yml
   git commit -m "feat: lab08 metrics & monitoring with prometheus"
   git push -u origin lab08
   ```
3. **Open Pull Requests:**
   - **PR #1:** `your-fork:lab08` → `course-repo:master`
   - **PR #2:** `your-fork:lab08` → `your-fork:master`
4. **Verify:** `/metrics` code, `prometheus.yml`, dashboard JSON, and `LAB08.md` all committed; screenshots present.

---

## Acceptance Criteria

### Main Tasks (10 points)

**App Instrumentation (3 pts):**
- [ ] `/metrics` endpoint exposes a counter, a histogram, and a gauge.
- [ ] HTTP requests labelled `method`, `endpoint`, `status` — with the route rule (not raw path) as `endpoint`.
- [ ] One app-specific business metric present.
- [ ] `curl localhost:8000/metrics` returns valid Prometheus text format.

**Prometheus & Scrape Config (3 pts):**
- [ ] Prometheus 3.x added to the `monitoring/` stack on the `logging` network.
- [ ] `prometheus.yml` scrapes `prometheus`, `app`, `loki`, `grafana` (and optionally `echo`).
- [ ] `/targets` shows all targets UP; `up` query returns `1` per target.

**Grafana Dashboard (2 pts):**
- [ ] 6-panel RED dashboard (rate, errors, p95, heatmap, in-flight, uptime) with live data.
- [ ] Prometheus data source connected; dashboard JSON exported into the repo.

**Production Config (1 pt):**
- [ ] Resource limits on Prometheus (and peers).
- [ ] Retention flags set; health check present; `docker compose ps` shows `healthy`.
- [ ] Data persists across `down`/`up`.

**Documentation (1 pt):**
- [ ] `monitoring/docs/LAB08.md` complete with architecture, instrumentation rationale, scrape config, dashboard, production config, and metrics-vs-logs.

### Bonus (2 points)
- [ ] `roles/monitoring` templates `prometheus.yml` from variables.
- [ ] Prometheus service + data source + RED dashboard provisioned by the role.
- [ ] `docker_compose_v2` deploy is idempotent (2nd run `changed=0`).
- [ ] Readiness wait for Prometheus `:9090/-/healthy`; both data sources shown working.

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **App Instrumentation** | 3 pts | `/metrics` with counter/histogram/gauge; bounded labels; business metric |
| **Prometheus & Scrape Config** | 3 pts | Prometheus 3.x deployed; all targets scraped and UP |
| **Grafana Dashboard** | 2 pts | 6-panel RED dashboard with PromQL + exported JSON |
| **Production Config** | 1 pt | Resource limits, retention, health check, persistence |
| **Documentation** | 1 pt | Complete `LAB08.md` with rationale and evidence |
| **Bonus: Ansible** | 2 pts | Idempotent templated deployment of the full logs+metrics stack |
| **Total** | 12 pts | **10 pts required + 2 bonus** |

**Grading scale:**
- **10/10:** App instrumented cleanly, all targets UP, sharp RED dashboard, hardened, excellent docs.
- **8–9/10:** All works, good docs, minor gaps.
- **6–7/10:** Metrics + Prometheus + a basic dashboard present.
- **<6/10:** `/metrics` missing or targets not scraping.

---

## Resources

<details>
<summary>📊 Prometheus</summary>

- [Prometheus overview](https://prometheus.io/docs/introduction/overview/)
- [Prometheus 3.0 announcement](https://prometheus.io/blog/2024/11/14/prometheus-3-0/) — UTF-8, native histograms, OTLP
- [Configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/)
- [Metric types](https://prometheus.io/docs/concepts/metric_types/)
- [Native histograms](https://prometheus.io/docs/specs/native_histograms/)

</details>

<details>
<summary>🐍 Python instrumentation</summary>

- [`prometheus_client` (GitHub)](https://github.com/prometheus/client_python)
- [Python instrumentation guide](https://prometheus.io/docs/guides/python/)
- [Instrumentation best practices](https://prometheus.io/docs/practices/instrumentation/)
- [Metric naming](https://prometheus.io/docs/practices/naming/)

</details>

<details>
<summary>📈 PromQL & Grafana</summary>

- [PromQL basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [PromQL examples](https://prometheus.io/docs/prometheus/latest/querying/examples/)
- [Grafana Prometheus data source](https://grafana.com/docs/grafana/latest/datasources/prometheus/)
- [Dashboard provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/#dashboards)

</details>

<details>
<summary>📚 Observability methods</summary>

- [RED method (Tom Wilkie, Grafana)](https://grafana.com/blog/the-red-method-how-to-instrument-your-services/)
- [USE method (Brendan Gregg)](https://www.brendangregg.com/usemethod.html)
- [The Four Golden Signals (Google SRE)](https://sre.google/sre-book/monitoring-distributed-systems/)
- [Metrics, tracing, and logging (Peter Bourgon)](https://peter.bourgon.org/blog/2017/02/21/metrics-tracing-and-logging.html)

</details>

---

## Looking Ahead

- **Lab 9:** Kubernetes Fundamentals — deploy your instrumented app + the `echo` service to K8s.
- **Lab 10:** Helm — package the app and monitoring as charts.
- **Lab 16:** Kubernetes Monitoring — today's compose stack becomes a `kube-prometheus-stack` Helm chart with `ServiceMonitor`/`PodMonitor` CRDs auto-discovering targets.

---

**Good luck!** 🚀

> **Remember:** counters need `rate()`, percentiles need `histogram_quantile()` *outside* the `sum by (le)`, and a label must never be unique per request or per user. RED for every service.
