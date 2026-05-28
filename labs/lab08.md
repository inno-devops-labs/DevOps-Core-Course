# Lab 8 — Metrics & Monitoring with Prometheus

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Metrics%20%26%20Monitoring-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![tech](https://img.shields.io/badge/tech-Prometheus%203.11%20|%20Grafana%2013%20|%20prometheus--client-informational)

> **Goal:** instrument your Lab 1 Python app with Prometheus metrics, deploy Prometheus 3.x next to last week's Loki stack to scrape them, and design a Grafana dashboard around the **RED method**.
> **Deliverable:** a PR from `lab08` adding the `/metrics` endpoint + instrumentation to `app_python/`, a `prometheus` service in `monitoring/docker-compose.yml`, `monitoring/prometheus/prometheus.yml`, a 6-panel RED dashboard JSON, and `monitoring/docs/LAB08.md` with the evidence captures.

---

## Overview

In Lab 7 you gave your service eyes (logs). This week you give it a **pulse** (metrics). You'll:
- Instrument an HTTP service with `prometheus_client` — declaring a **Counter**, a **Histogram**, and a `/metrics` endpoint
- Wire **Prometheus** into the Lab 7 Compose stack so it pulls `/metrics` from your app every few seconds
- Write **PromQL** for the **RED method** (Rate / Errors / Duration) — you write the queries, not copy them
- Design a Grafana dashboard around the three RED questions plus saturation
- Harden the stack: retention, resource limits, health checks, persistence

> ⚠️ **Scope:** single-binary Prometheus on the local Docker host. No Alertmanager, no `remote_write`, no Mimir — those are post-Core territory. The skill is **instrumentation + PromQL**, not running federated Prometheus.

> ✨ **Prometheus 3.x note.** This lab uses Prometheus 3.11.3 (current stable May 2026; 3.5 LTS is supported through Jul 2026). Versus 2.x it defaults to UTF-8 metric/label names, ships an OTLP receiver, and promotes **native histograms to GA**. You'll use classic histograms in the required tasks and may opt into native histograms as a stretch.

---

## Project State

**You should have from previous labs:**
- `app_python/` from Lab 1 — Flask/FastAPI service with `/` and `/health`
- A working Docker image of it from Lab 2
- The `monitoring/` compose stack from Lab 7 — `loki`, `alloy`, `grafana`, `app`, all on a `logging` network
- The JSON-logging upgrade to `app_python/` from Lab 7 (this lab adds *another* layer to the same `app.py`)

**This lab adds:**
- A `/metrics` endpoint + `Counter` + `Histogram` instrumentation in `app_python/app.py`
- `monitoring/prometheus/prometheus.yml` — YOU fill it from the scaffold
- A `prometheus` service in `monitoring/docker-compose.yml` (extends Lab 7, doesn't replace it)
- `monitoring/grafana/dashboards/lab08.json` — your exported 6-panel RED dashboard
- `monitoring/docs/LAB08.md` — submission report

By Lab 16 you'll redeploy this as `kube-prometheus-stack` on k3d with `ServiceMonitor` CRDs auto-discovering targets. Everything you learn this week — metric types, cardinality, PromQL, RED — carries forward unchanged.

---

## Setup

Versions used in this lab — pin these in your compose file and `requirements.txt`:

| Component | Tag / Version | Notes |
|---|---|---|
| `prom/prometheus` | `v3.11.3` | Current stable (May 2026); `v3.5.0` LTS is also acceptable |
| `grafana/grafana` | `13.0.1` | Already in your Lab 7 stack |
| `prometheus-client` (Python) | `0.23.1` | `0.23+` minimum; `0.25.x` is the latest patch line |

```bash
docker --version           # 28.x or 29.x
docker compose version     # v2.x
python --version           # 3.12+
```

Directory layout you'll build:

```
app_python/
├── app.py                            # YOU add instrumentation here (§1)
└── requirements.txt                  # YOU add prometheus-client (§1.2)

monitoring/
├── docker-compose.yml                # YOU extend with a `prometheus` service (§2.2)
├── prometheus/
│   └── prometheus.yml                # YOU fill the scaffold (§2.3)
├── grafana/
│   └── dashboards/
│       └── lab08.json                # exported from Grafana UI in Task 3
└── docs/
    └── LAB08.md                      # your submission report
```

Course-repo plumbing for this lab:
- `labs/lab8/prometheus/prometheus.yml` — **scaffold** with YOUR-TASK markers. Copy it into `monitoring/prometheus/prometheus.yml` and fill the blanks.

---

## Task 1 — Instrument the Python app (3 pts)

### 1.1 — Read first, write second

Read these before you touch `app.py` — they answer the questions the instrumentation asks of you:
- [Prometheus metric types](https://prometheus.io/docs/concepts/metric_types/) — Counter / Gauge / Histogram / Summary
- [Instrumentation best practices](https://prometheus.io/docs/practices/instrumentation/) — the "low cardinality" rule and metric naming
- [`prometheus_client` (Python)](https://github.com/prometheus/client_python) — Counter, Histogram, `generate_latest`, `CONTENT_TYPE_LATEST`

`YOUR TASK`: in `docs/LAB08.md`, answer these three questions in 2–4 sentences each. You'll come back and revise after Task 3:

1. When do you reach for a **Counter** vs a **Histogram**? Give one example of each from *your own* app.
2. Why do you query `rate(counter[5m])` instead of the counter's raw value? (Hint: counters reset on process restart.)
3. What is **label cardinality**, and why would `user_id` or `request_id` as a label eventually OOM Prometheus?

### 1.2 — Add the client library

Add the exact pin to `app_python/requirements.txt`:

```txt
prometheus-client==0.23.1
```

Rebuild your Lab 2 image so the dependency lands in the container.

### 1.3 — Define the metrics (`YOUR TASK`)

You'll add **two** metrics to `app_python/app.py`. The lecture (slides 8, 10, 13) names them, gives the labels, and shows the SRE-default bucket set. Your job is to declare them, give them sensible **help strings**, and pick the right label set — bounded enumerations only.

`YOUR TASK`: declare two module-level metrics:

| Variable | Type | Metric name | Labels | Notes |
|---|---|---|---|---|
| `REQUESTS` | `Counter` | `app_requests_total` | `method`, `endpoint`, `status` | Counts every HTTP request your service answers |
| `LATENCY` | `Histogram` | `app_request_duration_seconds` | `method`, `endpoint` | Buckets the request duration. Use the SRE defaults: `(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)` |

```python
# app.py — add to your Lab 1 service (Flask shown; adapt to FastAPI middleware)
import time
from flask import Flask, Response, request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# --- Metric definitions (low-cardinality labels only!) ---
REQUESTS = Counter(
    ___,                # YOUR TASK: metric name — see the table; ends in _total per Prom naming convention
    ___,                # YOUR TASK: help string — read by anyone debugging your metrics
    ___,                # YOUR TASK: label list — bounded enumerations only
)
LATENCY = Histogram(
    ___,                # YOUR TASK: metric name — _seconds suffix is the Prom convention for time
    ___,                # YOUR TASK: help string
    ___,                # YOUR TASK: label list — narrower than the counter's (no status)
    buckets=___,        # YOUR TASK: the SRE-default tuple from the table — bucket past your SLO ceiling
)
```

> ⚠️ **Cardinality is the #1 way to OOM Prometheus.** Each unique label combination is its own time series (~3–5 KB of RAM). Labels must be *bounded* enumerations: `method` (~8), `endpoint` (dozens, normalised), `status` (~10). **Never** put `user_id`, `request_id`, raw paths, emails, or timestamps in a label. Same lesson as Loki (Lec 7), same blast radius.

### 1.4 — Wire the hooks (`YOUR TASK`)

Flask gives you `before_request` (fires before the handler runs) and `after_request` (fires after — gets the `Response` object). The pattern is *start a timer in before, increment + observe in after*. The bodies are yours to write.

```python
@app.before_request
def _start_timer():
    request._t0 = ___                # YOUR TASK: capture a monotonic start time
                                     #   — hint: time.perf_counter(), NOT time.time()

@app.after_request
def _record(response):
    duration = ___                   # YOUR TASK: now - request._t0
    if ___:                          # YOUR TASK: skip /metrics — exclude its own path here
        return response              #            (otherwise scrape traffic poisons your counts)
    endpoint = ___                   # YOUR TASK: use request.url_rule.rule when matched,
                                     #            fall back to "unknown" when url_rule is None
    REQUESTS.labels(___).inc()       # YOUR TASK: method, endpoint, str(response.status_code)
    LATENCY.labels(___).observe(___) # YOUR TASK: (method, endpoint) labels + the duration
    return response

@app.route("/metrics")
def metrics():
    return Response(
        ___,                         # YOUR TASK: bytes from generate_latest()
        mimetype=___,                # YOUR TASK: CONTENT_TYPE_LATEST — wrong mimetype = silent
                                     #            parse failure on Prometheus's side
    )
```

Hints — *not* full code:
- **`request.url_rule.rule`** is `"/health"` or `"/"` for matched routes. It's `None` for 404s — fall back to `"unknown"` so cardinality stays bounded.
- **Cast the status** to `str(response.status_code)`. A label value must be a string.
- **FastAPI** equivalent: one `@app.middleware("http")` coroutine bracketing `await call_next(request)` with `time.perf_counter()`; expose `/metrics` with `Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)`.

### 1.5 — Test locally

```bash
python app.py                                 # or however you run your Lab 1 app
for i in $(seq 1 20); do curl -s localhost:8080/ > /dev/null; done
for i in $(seq 1 5);  do curl -s localhost:8080/health > /dev/null; done
curl -s localhost:8080/metrics | grep -E "^app_(requests_total|request_duration)"
```

The output is the Prometheus text exposition format. **Illustrative — your counts will differ:**

```
app_requests_total{endpoint="/",method="GET",status="200"} 20.0
app_requests_total{endpoint="/health",method="GET",status="200"} 5.0
app_request_duration_seconds_bucket{endpoint="/",method="GET",le="0.005"} 12.0
app_request_duration_seconds_bucket{endpoint="/",method="GET",le="0.01"}  18.0
app_request_duration_seconds_count{endpoint="/",method="GET"} 20.0
app_request_duration_seconds_sum{endpoint="/",method="GET"} 0.0421
```

**Sanity check:** call `curl -s localhost:8080/metrics > /tmp/m1.txt`, hit a route, `curl -s localhost:8080/metrics > /tmp/m2.txt`, diff. The total should **increase by exactly 1** for the route you hit — and the `endpoint="/metrics"` line should **not** exist. If `/metrics` is counting itself, your exclude in §1.4 is wrong.

### 1.6 — Proof of work

**Paste into `docs/LAB08.md`:**

- Full `curl -s localhost:8080/metrics | grep ^app_` output showing both `app_requests_total{...}` and `app_request_duration_seconds_{bucket,sum,count}` lines, with your real counts.
- The "no self-counting" proof: `curl -s localhost:8080/metrics | grep -c 'endpoint="/metrics"'` returning `0`.
- The metric-definition + hook code (snippet, not the whole file) committed to `app_python/app.py`.
- Your three written answers from §1.1.

---

## Task 2 — Deploy Prometheus & wire the scrape (3 pts)

### 2.1 — Understand the pull model

`YOUR TASK`: be able to answer these in `docs/LAB08.md` §3 (write the answers now, revise after §2.4):

1. Why does a *failed scrape* give you target health "for free" (`up == 0`), where a push model can't?
2. What's the difference between a **job**, a **target**, and the **scrape interval**?
3. In Docker Compose, why must Prometheus scrape `app:8080` (service name) and **not** `localhost:8080`?

### 2.2 — Add the Prometheus service (`YOUR TASK`)

**File:** `monitoring/docker-compose.yml` (extend the Lab 7 stack — don't replace it)

Prometheus joins the same `logging` network so it can reach Loki, Grafana, and your `app` by service name. The image + ports are given (so versions are pinned); the volumes, command flags, healthcheck, and network membership are your job.

```yaml
  # add to monitoring/docker-compose.yml, alongside loki/alloy/grafana/app from Lab 7
  prometheus:
    image: prom/prometheus:v3.11.3
    command:
      - ___                              # YOUR TASK: --config.file= path INSIDE the container
                                         #   (where you'll mount prometheus.yml below)
      - ___                              # YOUR TASK: --storage.tsdb.retention.time=
                                         #   (pick a value — Task 4 documents the trade-off)
      - ___                              # YOUR TASK: --storage.tsdb.retention.size=
                                         #   (defence in depth against disk fill)
    ports:
      - "9090:9090"
    volumes:
      - ___                              # YOUR TASK: bind-mount prometheus.yml :ro
      - ___                              # YOUR TASK: named volume for /prometheus (TSDB)
    networks: [___]                      # YOUR TASK: which network from Lab 7?
    healthcheck:
      test: ___                          # YOUR TASK: probe /-/healthy via wget --spider or curl --fail
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 15s

volumes:
  prometheus-data:                       # add alongside loki-data / grafana-data from Lab 7
```

Notes — don't skip these, they're the *why* behind the blanks:

- **`--config.file=`** must point at where you mounted `prometheus.yml` (typically `/etc/prometheus/prometheus.yml`). Mismatched paths give a clean "open ...: no such file" line in `docker compose logs prometheus` on startup — read the logs first when it won't come up.
- **Retention is a Prometheus CLI flag, not a config-file setting** (this is the most-Googled Prometheus 3.x footgun). `retention.time` (e.g. `15d`) AND `retention.size` (e.g. `2GB`) — whichever triggers first wins. Document your choices in §4.
- **TSDB volume:** without persistence, every `docker compose down` wipes your metrics history. Mount a named volume at `/prometheus` so dashboards don't go blank after a restart.
- **`logging` network** is the one from Lab 7. Putting Prometheus on a different network means it can't resolve `app` / `loki` / `grafana` — and you'd be debugging DNS instead of scraping.

### 2.3 — Fill the scrape config (`YOUR TASK`)

**File:** `monitoring/prometheus/prometheus.yml`

The structure (one `global` block, one `scrape_configs` list, one job per target) is non-negotiable Prometheus. The skill is **what cadence to scrape at**, **which hostname:port each target lives on**, and **what to name each job** (because the name shows up in every dashboard label and every alert).

Start from the scaffold:

```bash
cp labs/lab8/prometheus/prometheus.yml monitoring/prometheus/prometheus.yml
```

What you're filling in (the scaffold has the same blanks):

```yaml
global:
  scrape_interval:        # YOUR TASK: how often to scrape
                          #   — recall lecture §15: query ranges must be ≥ 4× this
  evaluation_interval:    # YOUR TASK: how often to evaluate rules (match scrape_interval)

scrape_configs:
  - job_name:             # YOUR TASK: short lowercase name, e.g. "prometheus"
    static_configs:
      - targets:          # YOUR TASK: Prometheus's own /metrics, from INSIDE the container
                          #   — this is the ONE target that uses localhost

  - job_name:             # YOUR TASK: a name you'll filter on later — e.g. up{job="..."}
    static_configs:
      - targets:          # YOUR TASK: your app's Compose service name + port
                          #   — NOT localhost; Prometheus runs in a different container

  - job_name:             # YOUR TASK
    static_configs:
      - targets:          # YOUR TASK: Loki's HTTP port on the logging network

  - job_name:             # YOUR TASK
    static_configs:
      - targets:          # YOUR TASK: Grafana's HTTP port on the logging network
```

Notes:
- `metrics_path:` defaults to `/metrics`, so omit it.
- **Service names are hostnames** on a Compose user-defined network — `loki:3100`, `grafana:3000`, `app:8080`. The Prometheus self-scrape is the only one using `localhost` because that traffic stays inside the Prometheus container.
- **Choose `scrape_interval` deliberately.** Too short (1s) burns CPU and inflates TSDB; too long (60s) makes percentile graphs jagged. The reference submission uses `5s` for a low-traffic lab; `15s` is the production default. Document your choice in §3.

<details>
<summary>💡 Optional second target — the course `echo` plumbing</summary>

The repo ships a tiny Go service at `plumbing/echo` (you'll meet it again in Lab 9) that already exposes its own metrics on `/metrics`. Adding it gives your dashboard a second instrumented service — useful when you build the `sum by (job)` panels:

Add an `echo` service (`build: ../plumbing/echo`, port `8081`, on the `logging` network) and a fifth scrape job pointing at `echo:8081`. Same pattern, no new concepts.

Not required for full marks; nice for the dashboard polish in Task 3.

</details>

### 2.4 — Bring it up and verify

```bash
cd monitoring
docker compose up -d
docker compose ps
```

Verify the proof-of-work commands you'll paste in §2.5:

```bash
# Prometheus is up
curl -s localhost:9090/-/healthy           # expect: "Prometheus Server is Healthy."

# Every job's target is UP — this is the proof your scrape config + service names are right.
# Run this AFTER one scrape_interval has elapsed.
curl -s localhost:9090/api/v1/targets \
  | jq -r '.data.activeTargets[] | "\(.labels.job): \(.health)"'
# (illustrative — every line must say "up"; if any says "down", that job's target field is wrong)
# <your_app_job>: up                       # YOUR TASK: this is the headline assertion —
# loki: up                                 #            the line for the job_name you picked in §2.3
# grafana: up                              #            for your app MUST say "up"
# prometheus: up
```

**Troubleshooting decision tree:**
- Target **down** → service name wrong, port wrong, or that service isn't running. `docker compose logs prometheus | grep -i scrape` shows the actual URL Prometheus tried.
- **No target at all** for a job → YAML indentation error in `prometheus.yml`. `docker compose logs prometheus` shows the parse error on startup.
- Target **unknown** → wait one `scrape_interval` and refresh; the first scrape hasn't happened yet.

### 2.5 — Proof of work

**Paste into `docs/LAB08.md`:**

- `docker compose ps` showing `prometheus` `Up` and `(healthy)` (the latter after start_period elapses).
- The exact `curl -s localhost:9090/api/v1/targets | jq ...` output from above — every job line must say `up`, with **`app: up`** clearly present. (This is the headline grading criterion for Task 2.)
- Screenshot of `http://localhost:9090/targets` confirming the same (UI version of the above).
- Your three written answers from §2.1.

---

## Task 3 — Grafana RED dashboard (2 pts)

### 3.1 — Add Prometheus as a data source

In the Grafana from Lab 7:

1. **Connections → Data sources → Add data source → Prometheus**.
2. URL: `http://prometheus:9090` — the service name on the `logging` network.
3. **Save & Test** → should report green.

> The bonus track provisions this automatically; doing it by hand once teaches you what the provisioning YAML encodes.

### 3.2 — Write the PromQL (`YOUR TASK`)

This is the heart of the lab. The lecture (slides 16, 18, 21) covers every function you need; you write the queries yourself.

For each row, write a PromQL expression that answers the question. Verify by running it in **Explore** (Prometheus data source) against real traffic — generate some first:

```bash
for i in $(seq 1 200); do curl -s localhost:8080/ > /dev/null; curl -s localhost:8080/health > /dev/null; done
```

| Question (RED) | Hint — one named function | Constraint |
|---|---|---|
| **Q1 — Rate.** Requests per second, broken down per endpoint. | `rate` | `sum by (endpoint) (...)` to keep `endpoint`, drop the rest |
| **Q2 — Errors.** 5xx requests per second, per endpoint. | `rate` with a `status=~"5.."` matcher | Same shape as Q1; the matcher goes **inside** the selector before `rate` |
| **Q3 — Duration.** p95 latency per endpoint. | `histogram_quantile` | The `sum by (endpoint, le)` goes **inside** `histogram_quantile`; never the reverse |
| **Q4 — Error ratio.** 5xx as a *fraction* of total requests. | Two `rate`s, divided | No grouping — single number; multiply by 100 for a percentage if you like |

`YOUR TASK`: write all four queries. Don't copy from the lecture verbatim — match them to *your* metric names from §1.3.

```promql
# Q1 — Rate (requests/sec per endpoint)
___                              # YOUR TASK: rate(...) + sum by (endpoint)

# Q2 — Errors (5xx requests/sec per endpoint)
___                              # YOUR TASK: same shape, status=~"5.." selector

# Q3 — Duration (p95 latency per endpoint)
___                              # YOUR TASK: histogram_quantile OUTSIDE sum by (endpoint, le)

# Q4 — Error ratio (5xx fraction of total)
___                              # YOUR TASK: rate(5xx) / rate(total) — no grouping
```

Notes (don't skip):

- **`rate()`** handles counter resets (process restarts); `irate()` and raw subtraction do **not**. Stick with `rate()` for graphs.
- **Range floor:** with `scrape_interval: 5s`, `rate(...[1m])` is the floor that doesn't lie. With `15s`, use `[5m]` or longer.
- **Never average a percentile.** `histogram_quantile()` goes *outside* the `sum by (le, …)`, never inside an `avg()`. Try the wrong nesting once and read Prometheus's error — it's instructive.
- **Use the lecture's metric name shape** if you're stuck on naming (`http_requests_total` etc.) — but Q1–Q4 must match the metric names you actually exposed in §1.3.

### 3.3 — Build the dashboard — 6 panels

Each panel answers one question. PromQL queries 1, 2, 3, 5, 6 are described below; panel 4 (heatmap) is one you write yourself in §3.2-extended.

| # | Panel | Visualisation | Query source | Answers |
|---|-------|---------------|---|---|
| 1 | **Request rate** | Time series | Your Q1 | *How busy?* |
| 2 | **Error rate** | Time series | Your Q2 | *How often failing?* |
| 3 | **p95 latency** | Time series | Your Q3 | *How slow at the 95th?* |
| 4 | **Latency heatmap** | Heatmap | YOUR TASK — same `_bucket` series, but `sum by (le)` *without* `histogram_quantile` (the heatmap panel computes percentiles itself) | *What does the long tail look like?* |
| 5 | **In-flight or total** | Gauge / Stat | `sum(rate(<your counter>[1m]))` | *How busy right now?* |
| 6 | **Service uptime** | Stat | `up{job="<your app job name>"}` | *Are we alive?* |

`YOUR TASK`: write panel 4's PromQL yourself — it's the only one not covered by Q1–Q4. The hint: the heatmap **does not** call `histogram_quantile`; it visualises the bucket counts directly. Same `sum by (le) (rate(...))` shape, no quantile wrapper.

**How to build (Grafana 13):**
1. **Dashboards → New → New dashboard → Add visualization** → pick the **Prometheus** data source.
2. Paste the PromQL; set the visualisation type from the table; title each panel **after the question it answers** ("Errors per second by endpoint" beats "Query 2").
3. Set sensible units: panel 1 = `req/s`; panel 3 = `seconds`; panels 2 = `req/s` with a threshold so non-zero errors turn the panel red.
4. Use `{{endpoint}}` (or `{{job}}`) in the legend so the lines are labelled, not "Series 1".
5. **Save dashboard**, then **Share → Export → Save to file**, commit to `monitoring/grafana/dashboards/lab08.json`.

> 💡 Want a head start on infrastructure panels? Import community dashboard **ID 3662** (Prometheus self-stats) via **Dashboards → New → Import** and bind it to your Prometheus data source. Your *own* 6-panel RED dashboard is what's graded.

### 3.4 — Proof of work

**Paste into `docs/LAB08.md`:**

- Screenshot of the 6-panel dashboard with **live data on every panel** (generate fresh traffic right before the screenshot — empty panels = no credit).
- The PromQL queries Q1–Q4 + the panel-4 heatmap query in a markdown table, each labelled with the question it answers.
- A real PromQL response from your own traffic, captured via the HTTP API (so the grader sees *your* numbers, not just a screenshot). Run the four queries through `/api/v1/query` and capture the output:
  ```bash
  curl -s --get http://localhost:9090/api/v1/query \
       --data-urlencode 'query=___' \
       | jq '.data.result'
  # YOUR TASK: substitute each of your Q1–Q4 queries in turn; paste the .data.result
  # (illustrative — your counts will differ)
  # [{"metric":{"endpoint":"/"},"value":[1716894123.456,"127"]},
  #  {"metric":{"endpoint":"/health"},"value":[1716894123.456,"54"]}]
  ```
- The committed JSON file path: `monitoring/grafana/dashboards/lab08.json`.

---

## Task 4 — Production readiness (1 pt)

Harden the stack so it isn't a toy. Everything here builds on the `prometheus` service you wrote in §2.2 — the blanks are already there, this task is where you *justify* the values you picked.

### 4.1 — Resource limits

`YOUR TASK`: add `deploy.resources` to the `prometheus` service. Pick sane numbers — Prometheus's RAM scales with active series count; for this lab a couple of hundred MiB is generous. Document the numbers + your reasoning in `LAB08.md`.

```yaml
    deploy:
      resources:
        limits:
          cpus: ___                 # YOUR TASK: ceiling — what's the most you'd let it eat?
          memory: ___               # YOUR TASK: RAM ceiling — keep series count in mind
        reservations:
          cpus: ___                 # YOUR TASK: guaranteed floor at scheduling time
          memory: ___               # YOUR TASK: guaranteed memory floor
```

### 4.2 — Retention

You stubbed the retention flags in §2.2. Document **why both** `retention.time` AND `retention.size` matter in `LAB08.md`: time is the SLA-driven knob, size is the defence-in-depth one against runaway cardinality.

### 4.3 — Health check & persistence

The healthcheck block from §2.2 should be filled in. Verify it works:

```bash
docker compose ps                              # prometheus reports (healthy) once start_period elapses
docker compose down && docker compose up -d
curl -s 'http://localhost:9090/api/v1/query?query=app_requests_total' | jq '.data.result | length'
# (illustrative — non-zero means your TSDB volume persisted history through the restart)
```

### 4.4 — Proof of work

**Paste into `docs/LAB08.md`:**

- `docker compose ps` output showing **all** services healthy, including `prometheus (healthy)`.
- Output of the `down` → `up` → query sequence above proving metric history survived.
- Your resource-limit values + one-sentence reasoning for each.

---

## Task 5 — Documentation (1 pt)

`YOUR TASK`: write `monitoring/docs/LAB08.md` with these sections, in order:

1. **Architecture** — a Mermaid diagram of `app → Prometheus → Grafana`, alongside the Lab 7 log path (so the same Grafana shows both pillars).
2. **Setup** — how to deploy (`docker compose up -d`) and the verification commands from §2.4.
3. **Instrumentation** — the metric names + types + labels you added, plus your answers from §1.1.
4. **Scrape config** — your job names, your `scrape_interval`, the pull model (answer the §2.1 questions).
5. **Dashboard** — the table from §3.4: question → PromQL → screenshot.
6. **Production config** — retention rationale, resource limits, healthcheck, persistence proof.
7. **Metrics vs logs** — one paragraph: when you'd reach for Prometheus vs the Lab 7 LogQL query.
8. **Challenges & solutions** — at least one real one (not "I was new to Prometheus").

Include config snippets (not whole files) and the captures from Tasks 1–4. Keep it readable — this is the artefact your future on-call self will read at 3 am.

---

## Bonus Task — Ansible automation (2 pts)

Extend the `roles/monitoring` role from Lab 6/7 so a single playbook deploys **logs + metrics** together.

`YOUR TASK`: update the role to:

- **Template** `prometheus/prometheus.yml` from Jinja2 — scrape interval, retention, **and the target list** become role variables (defined in `defaults/main.yml`). The same template renders correctly whether you have 4 targets or 14.
- **Extend** the templated `docker-compose.yml` from Lab 7 with the `prometheus` service + `prometheus-data` volume.
- **Provision** the Prometheus data source into Grafana via `grafana/provisioning/datasources/`.
- **Provision** your exported RED dashboard JSON via `grafana/provisioning/dashboards/`.
- **Wait** for Prometheus `:9090/-/healthy` before reporting success — same pattern as the Lab 7 readiness wait, just a different URL.
- Be **idempotent**: a second run reports `changed=0`.

Less hand-holding than Tasks 1–5: figure out the variable names, the template structure, and the readiness polling yourself. Lab 7's bonus already covered the `docker_compose_v2` deploy mechanics + the readiness loop pattern.

**Variables you'll need at minimum** (don't quote-and-paste — declare in your `defaults/main.yml`):
- `prometheus_version` (e.g. `v3.11.3`), `prometheus_port` (`9090`)
- `prometheus_retention_time` (`15d`), `prometheus_retention_size` (`2GB`)
- `prometheus_scrape_interval` (`15s`)
- `prometheus_targets` — a list of `{job, targets}` dicts, so a Jinja2 `{% for %}` renders the scrape config

**Evidence (paste into `docs/LAB08.md`):**

- First-run output (changes > 0) and second-run output (`changed=0`).
- The **rendered** (not template) `prometheus.yml` from a real run.
- Screenshot of Grafana showing **both** data sources (Loki + Prometheus) working with traffic.
- Path: `ansible/roles/monitoring/` + `ansible/playbooks/deploy-monitoring.yml`.

---

## How to Submit

```bash
git switch -c lab08
git add app_python/                                # instrumentation + requirements
git add monitoring/                                # compose + prometheus.yml + dashboard
git add ansible/roles/monitoring \
        ansible/playbooks/deploy-monitoring.yml    # only if bonus done
git commit -m "feat(lab08): prometheus metrics + RED dashboard"
git push -u origin lab08
```

Open **two** PRs:

- `your-fork:lab08` → `course-repo:master` *(reviewed)*
- `your-fork:lab08` → `your-fork:master` *(merges into your own main)*

PR checklist:

```text
- [ ] Task 1 done — Counter + Histogram + /metrics + before/after hooks; /metrics excluded from self-counting
- [ ] Task 2 done — prometheus service in compose, prometheus.yml filled, all targets `up`
- [ ] Task 3 done — 6-panel RED dashboard, JSON committed, real PromQL response captured
- [ ] Task 4 done — limits, retention, healthcheck healthy, persistence proven
- [ ] Task 5 done — LAB08.md with all 8 sections + captures
- [ ] Bonus done — idempotent Ansible role with readiness wait, both data sources working
```

---

## Acceptance Criteria

### Task 1 — Instrumentation (3 pts)
- ✅ `app_requests_total` Counter with labels `method, endpoint, status` declared
- ✅ `app_request_duration_seconds` Histogram with labels `method, endpoint` declared, SRE-default buckets
- ✅ `before_request` / `after_request` hooks observe **every** non-`/metrics` request
- ✅ `/metrics` returns valid Prometheus text format with the right `Content-Type`
- ✅ `/metrics` does **not** count itself (`grep -c 'endpoint="/metrics"' = 0`)
- ✅ Three written answers from §1.1 in `LAB08.md`

### Task 2 — Prometheus scrape (3 pts)
- ✅ `prometheus` service added on the `logging` network with retention flags + healthcheck
- ✅ `prometheus.yml` has `global` + 4 scrape jobs filled from the scaffold
- ✅ `curl -s localhost:9090/api/v1/targets | jq` shows **every** job `up`, with `app: up` clearly present
- ✅ Three written answers from §2.1 in `LAB08.md`

### Task 3 — RED dashboard (2 pts)
- ✅ 6 panels with appropriate visualisations; titles describe the question, not the query
- ✅ Q1–Q4 PromQL + panel-4 heatmap query all written by the student (not copy-pasted from the lecture)
- ✅ A real PromQL response from the student's own traffic captured via `/api/v1/query`
- ✅ Dashboard JSON committed to `monitoring/grafana/dashboards/lab08.json`

### Task 4 — Production config (1 pt)
- ✅ Resource limits + reservations on `prometheus`
- ✅ Retention flags (`time` and `size`) set on the command line
- ✅ Healthcheck reports `(healthy)`; metric history survives `down`/`up`

### Task 5 — Docs (1 pt)
- ✅ All 8 sections present in `monitoring/docs/LAB08.md`
- ✅ Research answers in the student's own words, not lecture quotes

### Bonus — Ansible (2 pts)
- ✅ `prometheus.yml` templated from a `prometheus_targets` list variable
- ✅ Data source + dashboard provisioned (no clicks in the Grafana UI)
- ✅ Deploy is idempotent — second run `changed=0`
- ✅ Readiness wait blocks success until Prometheus + Grafana respond
- ✅ Both data sources visible in Grafana

---

## Rubric

| Task | Points | Criteria |
|------|-------:|----------|
| **Task 1** — Instrumentation | **3** | Counter + Histogram declared correctly; hooks observe non-`/metrics` requests; valid exposition format |
| **Task 2** — Prometheus scrape | **3** | Service in compose, scrape config filled, `/api/v1/targets` shows `app: up` |
| **Task 3** — RED dashboard | **2** | 6 panels with student-written PromQL; real query response captured; JSON committed |
| **Task 4** — Production config | **1** | Limits, retention, healthcheck, persistence |
| **Task 5** — Docs | **1** | All 8 sections, captures present, answers in student's own words |
| **Bonus** — Ansible | **2** | Idempotent templated deployment of the full logs+metrics stack |
| **Total** | **12** | 10 main + 2 bonus |

---

## Resources

<details>
<summary>📊 Prometheus</summary>

- [Prometheus overview](https://prometheus.io/docs/introduction/overview/)
- [Prometheus 3.0 announcement](https://prometheus.io/blog/2024/11/14/prometheus-3-0/) — UTF-8, native histograms, OTLP
- [Configuration reference](https://prometheus.io/docs/prometheus/latest/configuration/configuration/)
- [`scrape_config`](https://prometheus.io/docs/prometheus/latest/configuration/configuration/#scrape_config)
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

</details>

<details>
<summary>⚠️ Common Pitfalls (from real dry-runs)</summary>

- **The `/metrics` self-counting trap.** If your `after_request` hook records the response to `/metrics` itself, every scrape increments `app_requests_total{endpoint="/metrics",...}` — and on a 5-second scrape interval that's twelve fake "requests per minute" that drown out your real traffic. **Always** exclude the `/metrics` path before incrementing; verify with `curl … | grep -c 'endpoint="/metrics"'` returning `0`. This is the #1 instrumentation bug — the ref submission's grading notes explicitly check for it.
- **Label cardinality = Prometheus OOM.** Each unique label combination is a time series (~3–5 KB RAM each). Putting `user_id`, `request_id`, `trace_id`, raw paths with IDs (`/user/123`), emails, or timestamps in a label is the fastest way to crash the ingester. **Use `request.url_rule.rule`** for the `endpoint` label — `request.path` includes `/user/123` and `/user/456` as two distinct series; the rule `/user/<id>` collapses them. Same lesson as Loki labels in Lab 7.
- **Counter vs Gauge confusion.** A counter only goes up (and resets to 0 on process restart). If you find yourself wanting `.dec()` or `.set()`, you reached for a counter when you needed a gauge. Conversely: querying a counter's raw value gives you "lifetime requests since boot" — almost never what you want. Always wrap with `rate()` or `increase()`.
- **Histogram bucket choice.** The default `prometheus_client` histogram buckets max out at **10 seconds**. If you're measuring database queries that can take 30 s, every slow query falls into the `+Inf` bucket and your p99 is a lie. Bucket your histograms for the *expected* range with one bucket past the tolerance ceiling — start with the SRE defaults `(.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10)` and tune from production data. Buckets too narrow on the low end is the symmetric trap: every fast request lands in the smallest bucket and you can't tell 1ms from 50µs.
- **Compose service-name DNS.** Prometheus scrapes targets by hostname over HTTP. Inside the `logging` Compose network, the hostname is the **service name** (`app`, `loki`, `grafana`) — **not** `localhost` and **not** the host IP. The only target legitimately on `localhost` is Prometheus's self-scrape (because that traffic stays inside the Prometheus container). Get this wrong and `up{job="app"}` returns 0 with no obvious error in the UI; check `docker compose logs prometheus | grep -i scrape`.
- **Retention is a CLI flag, not a config-file setting.** This catches everyone migrating from a 2.x article. `retention_period` in `prometheus.yml` is **ignored** — set `--storage.tsdb.retention.time=15d` and `--storage.tsdb.retention.size=2GB` on the `command:` list instead. Both can be present; whichever triggers first wins.
- **`scrape_interval` mismatch with PromQL window.** With `scrape_interval: 15s`, `rate(...[15s])` is degenerate (one or zero samples) and the graph is empty. The minimum query range that gives meaningful output is `≥ 4× scrape_interval`. With 5s scrapes → `[1m]` is safe; with 15s scrapes → `[5m]` is the floor.
- **`histogram_quantile` outside, `sum by (le)` inside — never the reverse.** The killer percentile query is `histogram_quantile(0.95, sum by (endpoint, le) (rate(*_bucket[5m])))`. Wrapping `histogram_quantile` *inside* an aggregator (e.g. `avg(histogram_quantile(...))`) is mathematical nonsense — averaging quantiles doesn't give you a quantile. Try it once, read the result, internalise.
- **`prometheus-client` >=0.23 emits `# HELP`, `# TYPE`, and `# UNIT`** — and Prometheus parses all three. If you wrote your own ad-hoc `/metrics` text by hand and skipped the `# TYPE` line, Prometheus silently treats every series as an untyped gauge, and `rate()` on it returns NaN. Always use `generate_latest()`.

</details>

<details>
<summary>🛠️ Dev tools worth knowing</summary>

- [`promtool`](https://prometheus.io/docs/prometheus/latest/command-line/promtool/) — ships in the Prometheus image; `promtool check config /etc/prometheus/prometheus.yml` validates before reload
- [`hey`](https://github.com/rakyll/hey) — generate steady traffic against your app to populate dashboards (`hey -n 5000 -c 10 http://localhost:8080/`)
- [`jq`](https://jqlang.github.io/jq/) — for parsing `/api/v1/targets` and `/api/v1/query` responses on the CLI

</details>

---

## Looking Ahead

| Lab | What it adds to this service |
|---:|---|
| 9 | k3d Kubernetes — deploy your instrumented app + the `echo` plumbing service as Pods, scrape via a sidecar |
| 10 | Helm 4 chart — package the app + Prometheus values |
| 12 | ConfigMaps + PVCs — re-mount Prometheus config from a ConfigMap; persist TSDB on a PVC |
| 16 | `kube-prometheus-stack` Helm chart with `ServiceMonitor` CRDs auto-discovering your app — same PromQL, K8s-native plumbing |

---

**Good luck!** 🚀

> **Remember:** Counters need `rate()`. Percentiles need `histogram_quantile()` *outside* the `sum by (le)`. A label must never be unique per request or per user. **RED for every service. USE for every resource.** And `/metrics` should never count itself.
