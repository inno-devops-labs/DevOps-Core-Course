# Lab 7 — Observability & Logging with the Loki Stack

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Logging%20%26%20Observability-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![tech](https://img.shields.io/badge/tech-Loki%20|%20Alloy%20|%20Grafana-informational)

> Deploy a centralised logging stack — Loki, **Grafana Alloy**, and Grafana — to aggregate, query, and visualise logs from your containerised applications.

## Overview

You'll stand up the Grafana logging stack with Docker Compose, ship your Lab 1 Python app's logs into it, and learn to ask questions of those logs with LogQL. By the end you can answer "what just broke?" from a single Grafana query instead of SSH + grep.

**What You'll Learn:**
- Loki 3.7 architecture: label-based indexing on a TSDB schema (cheap storage, fast queries)
- **Grafana Alloy** config (River/Alloy syntax) for Docker log collection — the agent that replaced Promtail
- Emitting structured **JSON logs** from a Python service
- The **LogQL** query language: stream selectors, line filters, parsers, and metric queries
- Building a Grafana dashboard that answers one operational question per panel
- Production logging concerns: retention, resource limits, health checks, and securing Grafana

> 🪦 **A note on Promtail.** Through 2025 the standard Loki agent was **Promtail**. It reached **End-of-Life on March 2, 2026** — no further releases, no security fixes. Its successor, **Grafana Alloy**, folds Promtail, the Prometheus agent, and the OpenTelemetry Collector into one binary. This lab uses Alloy. You may still meet Promtail configs in brownfield systems, so the lecture (slides 14–15) shows the legacy syntax and how it maps to Alloy — but **do not stand up a new Promtail in 2026.**

**Prerequisites:** Lab 1 (Python web app), Lab 2 (Docker), Lab 6 (Docker Compose).

**Tech Stack:** Loki **3.7** · Grafana Alloy **1.16.1** · Grafana **13** · Docker Compose v2

---

## Tasks

> **Point split:** Task 1 (3) + Task 2 (3) + Task 3 (2) + Task 4 (1) + Task 5 (1) = **10 pts**. Bonus = **2 pts**.
> Task 1 is self-contained: deploy the stack and see container logs in Grafana. Everything after builds on it.

### Task 1 — Deploy the Loki + Alloy + Grafana Stack (3 pts)

Create a Docker Compose stack with Loki (storage), Alloy (collector), and Grafana (UI).

#### 1.1 Study the components

Read these before you start — they answer the questions the config asks of you:
- [Loki overview](https://grafana.com/docs/loki/latest/get-started/overview/) — how Loki stores and indexes logs
- [Grafana Alloy](https://grafana.com/docs/alloy/latest/) — the agent, its config language, and components
- [LogQL introduction](https://grafana.com/docs/loki/latest/query/) — the query language

**Be able to answer in your LAB07.md:**
- How does Loki's label index differ from Elasticsearch's full-text index, and why is that cheaper?
- What is a *stream* in Loki, and why does high label cardinality hurt?
- How does Alloy discover Docker containers (`discovery.docker`) and forward their logs (`loki.source.docker` → `loki.write`)?

#### 1.2 Create the project structure

```
monitoring/
├── docker-compose.yml
├── loki/
│   └── config.yml
├── alloy/
│   └── config.alloy
└── docs/
    └── LAB07.md
```

#### 1.3 Configure Loki

**File:** `monitoring/loki/config.yml`

This is provided plumbing — a working single-binary Loki 3.7 config (schema v13, TSDB, 7-day retention). Copy it in and read the comments; you'll explain the choices in your docs.

```yaml
# loki/config.yml — Loki 3.7, single-binary, schema v13
auth_enabled: false

server:
  http_listen_port: 3100

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2024-01-01
      store: tsdb               # replaces the old boltdb-shipper
      object_store: filesystem  # swap to s3/gcs/minio in production
      schema: v13               # latest stable schema
      index:
        prefix: index_
        period: 24h

limits_config:
  retention_period: 168h        # 7 days

compactor:
  working_directory: /loki/compactor
  retention_enabled: true       # REQUIRED for retention to actually delete
  delete_request_store: filesystem
```

> ⚠️ **Gotcha:** setting `retention_period` *without* the `compactor` block means logs never actually delete — Loki silently ignores the limit.

#### 1.4 Configure Alloy — YOUR TASK

**File:** `monitoring/alloy/config.alloy`

Alloy config is written in the **River/Alloy** syntax (HCL-like blocks). The pipeline is three components wired together: **discover** Docker containers → **read** their logs → **write** to Loki. Fill in the `YOUR-TASK` markers.

```hcl
// alloy/config.alloy — discover Docker containers, ship their logs to Loki

// 1) Discover containers via the Docker socket.
discovery.docker "containers" {
  host             = "unix:///var/run/docker.sock"
  refresh_interval = "5s"

  // YOUR-TASK: only scrape containers that opt in with the label `logging=alloy`.
  // Hint: a `filter` block with name = "label" and values = ["logging=alloy"].
}

// 2) Promote useful Docker metadata to Loki labels (keep cardinality LOW).
discovery.relabel "containers" {
  targets = discovery.docker.containers.targets

  rule {
    source_labels = ["__meta_docker_container_name"]
    regex         = "/(.*)"           // strip the leading "/"
    target_label  = "container"
  }

  // YOUR-TASK: add a second rule that copies the Docker label `app`
  // (source label "__meta_docker_container_label_app") into a Loki label "app".
}

// 3) Read the discovered containers' log streams.
loki.source.docker "containers" {
  host       = "unix:///var/run/docker.sock"
  targets    = discovery.relabel.containers.output
  forward_to = [loki.write.default.receiver]
}

// 4) Push everything to Loki.
loki.write "default" {
  endpoint {
    url = "http://loki:3100/loki/api/v1/push"
  }
}
```

<details>
<summary>💡 Alloy hints</summary>

- The pipeline mirrors Promtail's three stages (discover → scrape → push), just expressed as wired components instead of a YAML list.
- `discovery.docker` finds containers; `discovery.relabel` rewrites their labels; `loki.source.docker` tails the logs; `loki.write` ships them.
- Each component references the previous one by its fully-qualified name (e.g. `discovery.relabel.containers.output`).
- The `filter` block is how you make logging **opt-in** — only containers you explicitly label with `logging=alloy` get scraped. This keeps the stack's own noise out.
- Alloy serves a live config/graph UI on **port 12345** — useful for debugging the pipeline.
- Reference: [`discovery.docker`](https://grafana.com/docs/alloy/latest/reference/components/discovery/discovery.docker/), [`loki.source.docker`](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.source.docker/), [`loki.write`](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.write/).

</details>

#### 1.5 Configure Docker Compose — YOUR TASK

**File:** `monitoring/docker-compose.yml`

Wire the three services together. Fill in the `YOUR-TASK` markers.

```yaml
# monitoring/docker-compose.yml
services:
  loki:
    image: grafana/loki:3.7.0
    command: -config.file=/etc/loki/config.yml
    ports:
      - "3100:3100"
    volumes:
      - ./loki/config.yml:/etc/loki/config.yml:ro
      - loki-data:/loki
    networks: [logging]

  alloy:
    image: grafana/alloy:v1.16.1
    # Alloy needs the config path + the data/storage path on its command line:
    command:
      - run
      - --server.http.listen-addr=0.0.0.0:12345
      - --storage.path=/var/lib/alloy/data
      - /etc/alloy/config.alloy
    ports:
      - "12345:12345"   # Alloy live UI
    volumes:
      - ./alloy/config.alloy:/etc/alloy/config.alloy:ro
      # YOUR-TASK: Alloy needs read access to the Docker socket to discover
      # containers and tail their logs. Mount it read-only.
      # Hint: /var/run/docker.sock:/var/run/docker.sock:ro
    networks: [logging]
    depends_on: [loki]

  grafana:
    image: grafana/grafana:13.0.1
    ports:
      - "3000:3000"
    environment:
      # DEV ONLY — anonymous admin so you can click around quickly.
      # You will turn this OFF in Task 4.
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
    volumes:
      - grafana-data:/var/lib/grafana
    networks: [logging]
    depends_on: [loki]

volumes:
  loki-data:
  grafana-data:

networks:
  logging:
    name: logging
```

> ⚠️ **Security note:** mounting `/var/run/docker.sock` gives Alloy a powerful view of the host. It's fine for this lab; in production you'd prefer file-based discovery or a dedicated socket proxy. Call this out in your docs.

#### 1.6 Deploy and verify

```bash
cd monitoring
docker compose up -d      # v2 CLI — space, not hyphen
docker compose ps
```

Verify each service:

```bash
# Loki ready?
curl -s http://localhost:3100/ready          # expect: "ready"

# Alloy live UI (open in a browser to see the component graph)
open http://localhost:12345

# Grafana
open http://localhost:3000
```

In Grafana, add the Loki data source:
1. **Connections → Data sources → Add data source → Loki**
2. URL: `http://loki:3100`
3. **Save & Test** → should report the data source is working.
4. **Explore → Loki**, run `{container=~".+"}` — you should see logs from the stack's own containers.

> 💡 Tip: at this stage only the stack's containers carry the `logging=alloy` label if you set the filter, so you may need to add the label to a container (Task 2) before logs appear. To smoke-test immediately, you can temporarily drop the `filter` block in Alloy and re-run.

**Evidence:** screenshot of Grafana Explore showing logs from at least two containers, plus the Alloy UI showing the component graph healthy.

---

### Task 2 — Integrate Your Applications & Structured Logging (3 pts)

Make your apps emit JSON logs and ship them into Loki.

#### 2.1 Add JSON logging to your Lab 1 Python app

Upgrade your Lab 1 service to log in **structured JSON**. Pick one idiomatic path:

```python
# Option A — python-json-logger (drop-in, minimal app changes)
import logging
from pythonjsonlogger.json import JsonFormatter

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s",
    rename_fields={"asctime": "ts", "levelname": "level"},
))
logging.basicConfig(level=logging.INFO, handlers=[handler])

logging.info("service starting", extra={"port": 8000})
```

```python
# Option B — structlog (richer; context vars; recommended for new code)
import structlog
log = structlog.get_logger()
log.info("request", method="GET", path="/health", status=200, client_ip="127.0.0.1")
```

**Requirements — log at least these events as JSON:**
- App **startup** (with config: host, port).
- Every **HTTP request**: `method`, `path`, `status`, `client_ip` (use Flask `@app.before_request`/`@app.after_request` or FastAPI middleware).
- Every **error / exception**, at `ERROR` level.

> ✅ **Definition of done for logging:** `curl localhost:8000/health` produces a single JSON line in `docker logs <container>`, with a `level` field you can later filter on in LogQL.

#### 2.2 Add your apps to the stack and label them for Alloy

Extend `monitoring/docker-compose.yml` with your service(s). The **label is what opts a container into log collection** — Alloy only scrapes containers carrying `logging=alloy`.

```yaml
  app-python:
    image: your-username/devops-info-service:latest   # built in Lab 2
    ports:
      - "8000:8000"
    networks: [logging]
    labels:
      logging: "alloy"          # opt in to Alloy collection
      app: "devops-python"      # becomes a Loki label via discovery.relabel
```

**Optional — the course `echo` plumbing service.** The repo ships a tiny instructor-maintained Go service at [`plumbing/echo`](../plumbing/echo) (used heavily from Lab 9). It writes plain-text request logs and is a convenient *second* log source so your dashboard isn't single-app. Add it the same way:

```yaml
  echo:
    build: ../plumbing/echo        # or image: ghcr.io/inno-devops-labs/echo:v1
    ports:
      - "8081:8081"
    networks: [logging]
    labels:
      logging: "alloy"
      app: "echo"
```

> You do **not** modify `plumbing/echo` — it's course-maintained. Including it is optional but recommended for a richer dashboard.

#### 2.3 Generate logs and query them

```bash
# Generate some traffic
for i in $(seq 1 20); do curl -s http://localhost:8000/ > /dev/null; done
for i in $(seq 1 20); do curl -s http://localhost:8000/health > /dev/null; done
# If you added echo:
for i in $(seq 1 20); do curl -s http://localhost:8081/ping > /dev/null; done
```

Now query in Grafana **Explore** (Loki data source):

```logql
# All logs from the Python app
{app="devops-python"}

# Only error lines
{app="devops-python"} |= "ERROR"

# Parse JSON and filter on a field
{app="devops-python"} | json | level="INFO"

# (if echo is running) compare both apps
{app=~"devops-python|echo"}
```

**Evidence:**
- Screenshot of a JSON log line from your app (in `docker logs` or Grafana).
- Screenshot of Grafana showing logs from your app (bonus: a second app too).
- At least **3 different LogQL queries** that return results.

---

### Task 3 — Build a Log Dashboard (2 pts)

Build a Grafana dashboard where **each panel answers one operational question**.

#### 3.1 Practise LogQL first

Run these in Explore before building panels — they map directly to the four panels below:

```logql
{app=~"devops-.*"}                                         # 1. recent activity
sum by (app) (rate({app=~"devops-.*"} [1m]))               # 2. traffic per app
{app=~"devops-.*"} | json | level="ERROR"                  # 3. errors only
sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))  # 4. level mix
```

<details>
<summary>💡 LogQL quick reference</summary>

**Stream selectors:** `{label="v"}` exact · `{label=~"re"}` regex · `{label!="v"}` not-equal
**Line filters:** `|= "x"` contains · `!= "x"` excludes · `|~ "re"` regex · `!~ "re"` not-regex
**Parsers:** `| json` (JSON → fields) · `| logfmt` (key=value) · `| line_format "..."` (rewrite line)
**Metric queries:** `rate([5m])` lines/sec · `count_over_time([5m])` total in window · `sum by (label) (...)` group

Put the cheapest, most-selective filter first — filters cascade left to right.
Reference: [LogQL docs](https://grafana.com/docs/loki/latest/query/).

</details>

#### 3.2 Create the dashboard — 4 panels

1. **Recent logs** (Logs visualisation) — `{app=~"devops-.*"}` — *"What's happening right now?"*
2. **Request rate** (Time series) — `sum by (app) (rate({app=~"devops-.*"} [1m]))` — *"How busy are we?"*
3. **Errors only** (Logs visualisation) — `{app=~"devops-.*"} | json | level="ERROR"` — *"What broke?"*
4. **Log-level distribution** (Pie chart or Stat) — `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))` — *"How noisy is the app?"*

**How to build:**
1. **Dashboards → New → New dashboard → Add visualization**, pick the **Loki** data source.
2. Enter the LogQL (use the code editor or the query builder).
3. Choose the visualisation type (Logs / Time series / Pie chart / Stat).
4. Set a clear panel title, then **Save dashboard**. Export the JSON model into your repo.

> 💡 The `app` label only exists if your Alloy `discovery.relabel` rule (Task 1.4) and your container labels (Task 2.2) are both in place. If panels are empty, check the label exists in Explore first.

**Evidence:** screenshot of the dashboard showing all 4 panels with real data, plus the exported dashboard JSON committed to `monitoring/`.

---

### Task 4 — Production Readiness (1 pt)

Harden the stack so it isn't a toy.

#### 4.1 Resource limits

Add limits to each service so a log spike can't starve the host:

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

#### 4.2 Secure Grafana

- Set `GF_AUTH_ANONYMOUS_ENABLED=false`.
- Set the admin password from a `.env` file (`GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}`), and **do not commit `.env`** — add it to `.gitignore`.

#### 4.3 Health checks

Add `healthcheck:` blocks so `docker compose ps` reports real health:

```yaml
    healthcheck:
      test: ["CMD-SHELL", "wget -q --spider http://localhost:3100/ready || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 15s
```

Wire Loki to `:3100/ready` and Grafana to `:3000/api/health`.

**Evidence:**
- `docker compose ps` output showing services reporting `healthy`.
- Screenshot of the Grafana **login page** (proving anonymous access is off).

---

### Task 5 — Documentation (1 pt)

Write `monitoring/docs/LAB07.md`.

**Required sections:**
1. **Architecture** — a diagram (Mermaid or image) of apps → Alloy → Loki → Grafana.
2. **Setup** — how to deploy (`docker compose up -d`) and verify.
3. **Configuration** — explain your Loki schema/retention choices and your Alloy pipeline (discover → relabel → write); answer the Task 1.1 research questions.
4. **Application logging** — how you implemented JSON logging and what fields you emit.
5. **Dashboard** — each panel, its LogQL query, and the question it answers.
6. **Production config** — resource limits, retention, Grafana auth, the Docker-socket security trade-off.
7. **Challenges** — problems you hit and how you solved them.

Include config snippets (not whole files) and the screenshots from Tasks 1–4.

---

## Bonus — Ansible Automation (2 pts)

Automate the whole stack with Ansible, building on Labs 5–6.

Create an Ansible role `roles/monitoring` that:
- Creates the `monitoring/` directory structure.
- Templates `loki/config.yml`, `alloy/config.alloy`, and `docker-compose.yml` from Jinja2 (versions, ports, retention as variables).
- Deploys the stack idempotently with `community.docker.docker_compose_v2`.
- Waits for Loki `:3100/ready` and Grafana `:3000/api/health` before reporting success.

**Requirements:**
- Parameterise: image tags (`loki: 3.7.0`, `alloy: v1.16.1`, `grafana: 13.0.1`), ports, retention (`168h`), schema (`v13`), resource limits.
- Idempotent — a second run reports `changed=0`.
- Compatible with ansible-core 2.18+.
- Playbook: `playbooks/deploy-monitoring.yml`.

<details>
<summary>💡 Role structure</summary>

```
roles/monitoring/
├── defaults/main.yml          # versions, ports, retention, limits
├── tasks/
│   ├── main.yml               # orchestrate setup → deploy → wait
│   ├── setup.yml              # create dirs, template configs
│   └── deploy.yml             # docker_compose_v2 + readiness wait
├── templates/
│   ├── docker-compose.yml.j2
│   ├── loki-config.yml.j2
│   └── config.alloy.j2
└── meta/main.yml              # depends_on: docker role
```

</details>

**Evidence:**
- Playbook run output (first run: changes; second run: `changed=0`).
- The rendered (templated) config files.

---

## How to Submit

1. **Create a branch:**
   ```bash
   git checkout -b lab07
   ```
2. **Commit your work:**
   ```bash
   git add monitoring/ app_python/
   # if you did the bonus:
   git add ansible/roles/monitoring ansible/playbooks/deploy-monitoring.yml
   git commit -m "feat: lab07 observability stack (loki + alloy + grafana)"
   git push -u origin lab07
   ```
3. **Open Pull Requests:**
   - **PR #1:** `your-fork:lab07` → `course-repo:master`
   - **PR #2:** `your-fork:lab07` → `your-fork:master`
4. **Verify:** all config files committed, screenshots present, `LAB07.md` complete.

---

## Acceptance Criteria

### Main Tasks (10 points)

**Stack Deployment (3 pts):**
- [ ] `docker compose up -d` brings up Loki, Alloy, and Grafana.
- [ ] Loki `:3100/ready` returns `ready`; Alloy UI on `:12345` shows a healthy graph.
- [ ] Loki data source connected in Grafana; container logs visible in Explore.
- [ ] Alloy config completes the `discovery.docker` filter, the `app` relabel rule, and the Docker-socket mount.

**App Integration & JSON Logging (3 pts):**
- [ ] Lab 1 Python app emits structured JSON (startup, requests, errors).
- [ ] App container labelled `logging=alloy` and `app=…`; its logs reach Loki.
- [ ] At least 3 working LogQL queries demonstrated.

**Dashboard (2 pts):**
- [ ] 4-panel dashboard (recent logs, request rate, errors, level distribution) with real data.
- [ ] Dashboard JSON exported into the repo.

**Production Config (1 pt):**
- [ ] Resource limits on all services.
- [ ] Grafana anonymous auth disabled, admin password from `.env` (uncommitted).
- [ ] Health checks present; `docker compose ps` shows `healthy`.

**Documentation (1 pt):**
- [ ] `monitoring/docs/LAB07.md` complete with architecture, config rationale, dashboard explanation, and the Task 1.1 research answers.

### Bonus (2 points)
- [ ] `roles/monitoring` templates all three configs from variables.
- [ ] `docker_compose_v2` deploy is idempotent (2nd run `changed=0`).
- [ ] Readiness wait for Loki + Grafana before success.
- [ ] Playbook output (both runs) and rendered configs included.

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Stack Deployment** | 3 pts | Loki + Alloy + Grafana up; Alloy pipeline completed; logs in Grafana |
| **App Integration** | 3 pts | JSON logging in Python app; labelled + shipped to Loki; LogQL queries work |
| **Dashboard** | 2 pts | 4 panels with appropriate LogQL + exported JSON |
| **Production Config** | 1 pt | Resource limits, Grafana secured, health checks |
| **Documentation** | 1 pt | Complete `LAB07.md` with rationale and evidence |
| **Bonus: Ansible** | 2 pts | Idempotent templated deployment of the full stack |
| **Total** | 12 pts | **10 pts required + 2 bonus** |

**Grading scale:**
- **10/10:** Stack fully working, JSON logs, clean dashboard, hardened, excellent docs.
- **8–9/10:** All works, good docs, minor gaps.
- **6–7/10:** Core stack + integration present, basic dashboard/docs.
- **<6/10:** Stack incomplete or logs not flowing.

---

## Resources

<details>
<summary>📚 Loki</summary>

- [Loki overview](https://grafana.com/docs/loki/latest/get-started/overview/)
- [Loki configuration](https://grafana.com/docs/loki/latest/configure/)
- [Storage / TSDB](https://grafana.com/docs/loki/latest/operations/storage/tsdb/)
- [Retention & compactor](https://grafana.com/docs/loki/latest/operations/storage/retention/)

</details>

<details>
<summary>⚡ Grafana Alloy (Promtail's successor)</summary>

- [Alloy documentation](https://grafana.com/docs/alloy/latest/)
- [`discovery.docker`](https://grafana.com/docs/alloy/latest/reference/components/discovery/discovery.docker/)
- [`loki.source.docker`](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.source.docker/)
- [`loki.write`](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.write/)
- [Migrate from Promtail to Alloy](https://grafana.com/docs/alloy/latest/set-up/migrate/from-promtail/)

</details>

<details>
<summary>🔍 LogQL & Grafana</summary>

- [LogQL query language](https://grafana.com/docs/loki/latest/query/)
- [Grafana dashboards](https://grafana.com/docs/grafana/latest/dashboards/)
- [Loki data source in Grafana](https://grafana.com/docs/grafana/latest/datasources/loki/)
- [Explore logs](https://grafana.com/docs/grafana/latest/explore/logs-integration/)

</details>

<details>
<summary>📝 Structured logging</summary>

- [structlog](https://www.structlog.org/en/stable/)
- [python-json-logger](https://github.com/nhairs/python-json-logger)
- [The Twelve-Factor App: Logs](https://12factor.net/logs)
- [Python Logging HOWTO](https://docs.python.org/3/howto/logging.html)

</details>

---

## Looking Ahead

- **Lab 8:** Metrics with Prometheus — add the metrics pillar to complement these logs. (Your `echo` service already exposes `/metrics`.)
- **Lab 9:** Kubernetes Fundamentals — deploy your app + the `echo` service to K8s.
- **Lab 10–12:** Helm, Secrets, ConfigMaps — package and configure K8s deployments.
- **Lab 16:** Kubernetes Monitoring — full observability on the cluster.

---

**Good luck!** 🚀

> **Remember:** Loki indexes *labels*, not text. Keep labels low-cardinality; put per-request fields in the JSON body and filter with `| json` at query time.
