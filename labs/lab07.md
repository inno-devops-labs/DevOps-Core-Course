# Lab 7 — Observability & Logging with the Loki Stack

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Logging%20%26%20Observability-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![tech](https://img.shields.io/badge/tech-Loki%20|%20Alloy%20|%20Grafana-informational)

> **Goal:** stand up Loki + Grafana Alloy + Grafana with Docker Compose, ship your Lab 1 Python app's logs into it as structured JSON, and learn to ask questions of those logs with LogQL.
> **Deliverable:** a PR from `lab07` adding `monitoring/` (compose stack + Alloy + Loki configs + dashboard JSON), the JSON-logging patch to `app_python/`, and `monitoring/docs/LAB07.md` with the evidence captures.

---

## Overview

In this lab you will practice:
- Reading Alloy's River syntax and **wiring components by name** (`discovery.docker` → `discovery.relabel` → `loki.source.docker` → `loki.write`) instead of copy-pasting a YAML pipeline
- Writing a Docker Compose stack from a service-list spec (which images, which ports, which volumes, which network)
- Emitting structured JSON logs from a Python service
- Writing **LogQL** stream selectors + line filters + parsers + metric functions to answer real questions about your own app
- Hardening the stack: resource limits, retention compactor, health checks, no anonymous Grafana

> ⚠️ **Scope:** single-binary Loki on the local Docker host. No object storage, no multi-tenancy, no TLS — those come back in the K8s-era labs (12, 16). Don't tune for production; tune for *understanding the wires*.

> 🪦 **A note on Promtail.** Through 2025 the standard Loki agent was **Promtail**. It reached **End-of-Life on March 2, 2026** — no further releases, no security fixes. Its successor, **Grafana Alloy**, folds Promtail + the Prometheus agent + the OpenTelemetry Collector into one binary. This lab uses Alloy. You may still meet Promtail configs in brownfield systems, so the lecture slides 14–15 show the legacy syntax and how it maps to Alloy — but **do not stand up a new Promtail in 2026.** A Promtail `pipeline_stages` block does **not** translate 1:1 to Alloy; the equivalents are split across `loki.relabel` and `loki.process` and several stage names changed.

---

## Project State

**You should have from previous labs:**
- `app_python/` from Lab 1 — Flask/FastAPI service with `/` and `/health`
- A working Docker image of it from Lab 2 (registry-pushed or local tag)
- Comfort with Docker Compose v2 from Lab 6 (Jinja2-templated stack)

**This lab adds:**
- `monitoring/docker-compose.yml` — the Loki + Alloy + Grafana stack
- `monitoring/loki/config.yml` — provided plumbing
- `monitoring/alloy/config.alloy` — **YOU write the River pipeline**
- `monitoring/grafana/dashboards/lab07.json` — your exported 4-panel dashboard
- `monitoring/docs/LAB07.md` — submission report
- A JSON-logging upgrade to `app_python/app.py`

By Lab 16 you'll redeploy this same idea on Kubernetes as `kube-prometheus-stack` + a Loki Helm chart. The pieces you learn this week (label cardinality, LogQL, ConfigMap-mounted configs) all carry forward.

---

## Setup

Versions used in this lab — pin these in your compose file:

| Component | Tag | Released |
|---|---|---|
| `grafana/loki` | `3.7.0` | Mar 2026 |
| `grafana/alloy` | `v1.16.1` | May 6 2026 |
| `grafana/grafana` | `13.0.1` | May 12 2026 |

```bash
docker --version           # 28.x or 29.x
docker compose version     # v2.x — note the space, not a hyphen
curl --version             # for the verification commands below
```

Create the directory layout (you'll fill the files yourself):

```
monitoring/
├── docker-compose.yml             # YOU write this (§1.4)
├── loki/
│   └── config.yml                 # provided plumbing — copy from labs/lab07/loki/
├── alloy/
│   └── config.alloy               # YOU write this (§1.3)
├── grafana/
│   └── dashboards/
│       └── lab07.json             # exported from Grafana UI in Task 3
└── docs/
    └── LAB07.md                   # your submission report
```

Course-repo plumbing for this lab:
- `labs/lab07/loki/config.yml` — drop-in Loki config (see §1.2)
- `plumbing/echo/` — optional second log source (see §2.2)

---

## Task 1 — Deploy the Loki + Alloy + Grafana stack (3 pts)

### 1.1 — Read first, write second

Read these before you touch a config (they answer the questions the YOUR-TASK blocks ask of you):
- [Loki overview](https://grafana.com/docs/loki/latest/get-started/overview/) — distributor / ingester / querier; chunks vs index
- [Alloy components](https://grafana.com/docs/alloy/latest/) — `discovery.*`, `loki.source.*`, `loki.write`, how they reference each other by name
- [LogQL intro](https://grafana.com/docs/loki/latest/query/) — selectors, filters, parsers, metric queries

`YOUR TASK`: in `docs/LAB07.md`, answer these three questions in 2–4 sentences each. You'll come back and revise as you build:

1. How does Loki's **label** index differ from Elasticsearch's full-text index, and why is that cheaper at 100 GB/day?
2. What is a **stream** in Loki, and what happens to memory if you make `user_id` a label on a service with 10 M users?
3. Alloy components reference each other by **name** (e.g. `loki.write.default.receiver`). What's the export name, and why is it different from the block name (`loki.write "default"`)?

### 1.2 — Loki config (provided plumbing — do not rewrite)

The Loki config is the **one** fully-written file in this lab; it lives in the course repo as plumbing. Copy it into your stack:

```bash
cp labs/lab07/loki/config.yml monitoring/loki/config.yml
```

You don't write it — but you **must** be able to explain in your docs:
- Why `store: tsdb` + `schema: v13` (and what it replaced)
- Why `object_store: filesystem` is wrong for production
- Why the `compactor` block is non-negotiable when `retention_period` is set

> ⚠️ **Gotcha to internalise:** `retention_period` with no `compactor` block = logs never delete. Loki swallows the limit silently. This is the #1 reason teams blow past their disk budget. Reference this in your docs §3 ("Configuration choices").

### 1.3 — Alloy River config (YOUR TASK)

**File:** `monitoring/alloy/config.alloy`

Alloy is wired components, not a YAML pipeline. Four blocks, each feeding the next. The block names below are non-negotiable — but the arguments, labels, and references between them are the skill.

`YOUR TASK`: fill the blanks. The block names tell you the role each block plays; the comments tell you the contract.

```alloy
// 1) Discover Docker containers via the daemon socket
discovery.docker "containers" {
  host             = ___           // YOUR TASK: docker socket URL
  refresh_interval = "5s"
  ___                              // YOUR TASK: add a `filter { ... }` block — only
                                   //   scrape containers labelled `logging=alloy`
}

// 2) Promote useful Docker metadata to Loki labels — keep cardinality LOW
discovery.relabel "containers" {
  targets = ___                    // YOUR TASK: previous block's exported targets
  rule {
    source_labels = [___]          // YOUR TASK: Docker meta-label for container name
    regex         = ___            // YOUR TASK: strip the leading "/"
    target_label  = "container"
  }
  ___                              // YOUR TASK: second `rule { ... }` — copy Docker
                                   //   label `app` into Loki label `app`
}

// 3) Tail the discovered containers' log streams
loki.source.docker "default" {
  host       = ___                 // YOUR TASK: same socket as block 1
  targets    = ___                 // YOUR TASK: feed from the *relabel* block
  forward_to = [___]               // YOUR TASK: which loki.write receiver?
}

// 4) Ship everything to Loki
loki.write "default" {
  endpoint {
    url = ___                      // YOUR TASK: Loki push URL — which host, port, path?
  }
}
```

Notes on each block (don't skip these — they're the *why* behind the blanks):

- **Block 1** — `filter` is how you make logging opt-in. Without it, Alloy ships every container's stdout, including its own and Loki's, polluting your dashboards.
- **Block 2** — `discovery.relabel` rewrites label metadata before logs are scraped. The first rule normalises the container name (Docker prefixes it with `/`); the second copies a user-defined Docker label into a Loki label. **Stop and think about cardinality** before adding any third rule — anything with more than ~50 distinct values doesn't belong here.
- **Block 3** — `loki.source.docker` tails container stdout/stderr. Its `targets` should come from the **relabel** output (not the raw discovery), otherwise your labels never make it into Loki.
- **Block 4** — `loki.write` is the only block that talks HTTP. Its endpoint URL determines whether your stack is portable across networks; use the compose service name, not `localhost`.

<details>
<summary>💡 River-syntax hints</summary>

- A block is `<kind>.<subkind> "label" { … }`. The **label** in quotes (e.g. `"containers"`, `"default"`) is how other blocks refer to it.
- Each component has documented **exports**. `discovery.docker` exports `.targets`. `discovery.relabel` exports `.output`. `loki.write` exports `.receiver`. You wire blocks by writing the fully-qualified export — e.g. `discovery.relabel.containers.output`.
- Alloy serves a live UI on port **12345** showing the component graph. If a wire is broken, you'll see it red in the UI before you'll see it in Loki.
- Reference pages: [`discovery.docker`](https://grafana.com/docs/alloy/latest/reference/components/discovery/discovery.docker/), [`discovery.relabel`](https://grafana.com/docs/alloy/latest/reference/components/discovery/discovery.relabel/), [`loki.source.docker`](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.source.docker/), [`loki.write`](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.write/).
- The Loki push endpoint path is documented [here](https://grafana.com/docs/loki/latest/reference/loki-http-api/#ingest-logs).

</details>

### 1.4 — Docker Compose stack (YOUR TASK)

**File:** `monitoring/docker-compose.yml`

The stack has **four** services. The image tags + ports are given (so versions are pinned); the volumes, network membership, env vars, and `depends_on` are your job — those are the wires that make it actually work.

| Service | Image | Published ports | Why it's there |
|---|---|---|---|
| `loki` | `grafana/loki:3.7.0` | `3100:3100` | Storage + query engine |
| `alloy` | `grafana/alloy:v1.16.1` | `12345:12345` (live UI) | Collector — reads docker.sock, pushes to Loki |
| `grafana` | `grafana/grafana:13.0.1` | `3000:3000` | Dashboards + Explore UI |
| `app` | your Lab 2 image | `8000:8000` | Source of logs — Lab 1 service with JSON output (Task 2) |

`YOUR TASK`: write the compose file. Specifically you must figure out:

1. **Volumes for `loki`:** one bind mount makes the config file from §1.2 visible inside the container at `/etc/loki/config.yml`; one named volume persists `/loki` so chunks survive a restart. The container's command should be `-config.file=/etc/loki/config.yml`.
2. **Volumes for `alloy`:** one bind mount for the config from §1.3 (mounted **read-only**); one **read-only** mount of the host Docker socket so Alloy can discover and tail containers. Alloy's command needs three flags: `run`, `--server.http.listen-addr=0.0.0.0:12345`, `--storage.path=/var/lib/alloy/data`, then the config path.
3. **Env vars for `grafana`:** for this task only, enable anonymous admin access (`GF_AUTH_ANONYMOUS_ENABLED`, `GF_AUTH_ANONYMOUS_ORG_ROLE`). **You will turn this off in Task 4** — leave a comment now so you remember. Persist `/var/lib/grafana` in a named volume so your dashboard from Task 3 survives `docker compose down`.
4. **Labels on `app`:** the container must carry `logging: "alloy"` (opts into Alloy collection because of your `filter` in §1.3) and `app: "devops-python"` (becomes a Loki label via your relabel rule in §1.3). Without **both** of those labels, your dashboards in Task 3 will be empty.
5. **Network:** define a user-defined bridge network (call it `logging`) and put **all four** services on it so they resolve each other by service name. `loki` and `grafana` must wait for their dependencies before starting (`depends_on:`).

```yaml
# monitoring/docker-compose.yml — YOUR TASK
services:
  loki:
    image: grafana/loki:3.7.0
    command: ___                              # YOUR TASK: -config.file=/etc/loki/config.yml
    ports:
      - "3100:3100"
    volumes:
      - ___                                   # YOUR TASK: bind-mount loki/config.yml
      - ___                                   # YOUR TASK: named volume for /loki
    networks: [___]                           # YOUR TASK

  alloy:
    image: grafana/alloy:v1.16.1
    command:
      - run
      - --server.http.listen-addr=0.0.0.0:12345
      - --storage.path=/var/lib/alloy/data
      - ___                                   # YOUR TASK: path to mounted config.alloy
    ports:
      - "12345:12345"
    volumes:
      - ___                                   # YOUR TASK: bind-mount config.alloy :ro
      - ___                                   # YOUR TASK: bind-mount the Docker socket :ro
    networks: [___]                           # YOUR TASK: same network as loki
    depends_on: [___]                         # YOUR TASK: must start after which service?

  grafana:
    image: grafana/grafana:13.0.1
    ports:
      - "3000:3000"
    environment:
      - ___                                   # YOUR TASK: enable anonymous access (DEV ONLY — Task 4 turns this off)
      - ___                                   # YOUR TASK: anonymous role = Admin
    volumes:
      - ___                                   # YOUR TASK: persist /var/lib/grafana
    networks: [___]                           # YOUR TASK
    depends_on: [___]                         # YOUR TASK

  app:
    image: ___                                # YOUR TASK: your Lab 2 image (or `build:` block)
    ports:
      - "8000:8000"
    labels:
      ___: ___                                # YOUR TASK: opt into Alloy collection
      ___: ___                                # YOUR TASK: the `app` Loki label (matches §1.3 rule)
    networks: [___]                           # YOUR TASK

volumes:
  ___:                                        # YOUR TASK: declare named volume for loki
  ___:                                        # YOUR TASK: declare named volume for grafana

networks:
  ___:                                        # YOUR TASK: declare the user-defined bridge
    name: logging
```

> ⚠️ **Security note:** mounting `/var/run/docker.sock` gives Alloy a **powerful** view of the host — effectively root on the daemon. Fine for this lab; in production you'd use a socket proxy (Tecnativa's `docker-socket-proxy`) or file-based discovery. Note this trade-off in your docs.

### 1.5 — Bring it up and verify

```bash
cd monitoring
docker compose up -d
docker compose ps
```

Verify:

```bash
# Loki — ingester takes ~15s after process start to report ready.
# If you see "Ingester not ready" the first time, wait and retry; do NOT debug.
curl -s http://localhost:3100/ready          # expect: "ready"

# Loki's view of discovered labels — once Alloy is wired correctly, you should
# see at LEAST "container" and (after §2.2) "app" in the list:
curl -s http://localhost:3100/loki/api/v1/labels | jq -c .data
# (illustrative — your set will differ)
# ["container","service_name"]

# Alloy live component graph
open http://localhost:12345

# Grafana
open http://localhost:3000
# Add data source: Connections → Data sources → Loki → URL http://loki:3100 → Save & Test
```

### 1.6 — Proof of work

**Paste into `docs/LAB07.md`:**

- `docker compose ps` output showing all four services `Up` (and after Task 4, `healthy`)
- `curl -s http://localhost:3100/ready` output — literally the word `ready`
- `curl -s http://localhost:3100/loki/api/v1/labels | jq -c .data` — must include `container` (and `app` after §2.2)
- Screenshot of the Alloy live UI at `:12345` showing the four blocks wired with no red edges
- Screenshot of Grafana **Explore** running `{container=~".+"}` returning logs from at least two containers

---

## Task 2 — Integrate your app & ship JSON logs (3 pts)

### 2.1 — Add JSON logging to your Lab 1 Python app

Pick **one** library — both are fine; both produce JSON Loki can parse with `| json`.

| Library | When to pick | Trade-off |
|---|---|---|
| **`python-json-logger`** | Drop-in over `logging.basicConfig`. Minimal app changes. | Stdlib `logging`'s mental model — handlers, formatters, levels. |
| **`structlog`** | New code where you want context vars / processors / typed events. | Different API; richer ergonomics. |

`YOUR TASK`: upgrade `app_python/app.py` so that the following events emit one **JSON line per event** to stdout (which is what Docker captures and Alloy ships):

| Event | When | Required JSON fields |
|---|---|---|
| **Startup** | At process start | `level`, `msg`, `host`, `port`, `service` |
| **Every HTTP request** | After response | `level`, `msg`, `method`, `path`, `status`, `client_ip`, `duration_ms` |
| **Every error** | In a 500 handler or `try/except` | `level="ERROR"`, `msg`, `error_type`, the exception's string |

Hints:

- Flask: a `@app.before_request` to capture start time + `@app.after_request` to log; or use `werkzeug`'s built-in logger and replace its formatter with a JSON one.
- FastAPI: a single middleware with `time.perf_counter()` brackets is cleaner than per-route logging.
- **Do not** put `request_id` or `user_id` into a **label**. Put them in the JSON body — you'll filter on them at query time with `| json | user_id="alice"`. (Lecture 7, slide 12.)
- One JSON object per line. No trailing commas. Don't pretty-print — `docker logs` will then split your log lines on every internal newline and your dashboards will be a mess.

Update `app_python/requirements.txt`:
```
# python-json-logger>=3.4.0    # YOUR TASK: pin one of these to an exact version
# structlog>=25.4.0
```

Rebuild your image (Lab 2's Dockerfile) so the new dependency lands in the container.

### 2.2 — Add your app to the stack

You already declared the `app` service in §1.4. Two labels are non-negotiable:

```yaml
    labels:
      logging: "alloy"          # opts the container into Alloy collection (§1.3 filter)
      app: "devops-python"      # becomes a Loki label via the §1.3 relabel rule
```

**Optional but recommended — `plumbing/echo`.** The course repo ships a tiny Go service at `plumbing/echo` (you'll see it again in Lab 9). Add it as a second log source so your dashboards aren't single-app — same two labels, port `8081`, image or `build:` line of your choice.

### 2.3 — Generate traffic and query

```bash
# Generate at least 20 successful + 5 not-found + 1 error event
for i in $(seq 1 20); do curl -s http://localhost:8000/ > /dev/null; done
for i in $(seq 1 5);  do curl -s http://localhost:8000/nope > /dev/null; done
# Force an error: hit an endpoint that raises (add a /boom route or trip a 500 deliberately)
curl -s http://localhost:8000/boom > /dev/null
```

### 2.4 — Write the LogQL queries (YOUR TASK)

For each row below, write the LogQL that answers it. Don't copy from the lecture — answer the question, then verify by running it in Explore.

| # | Question | Hint |
|---|---|---|
| Q1 | All logs from your Python app | Stream selector on the `app` label, nothing else |
| Q2 | Only the JSON lines where `level` is `ERROR` | Stream selector → `\| json` → field equality on `level` |
| Q3 | Rate of errors per minute, per container | Metric query: `sum by (container) (rate(... [1m]))` — apply the error filter inside the selector before `rate` |
| Q4 | All requests to a path containing `health` (filter on the **JSON field `path`**, not a substring of the raw line) | `\| json` then a field-equality / regex filter on `path` |

> 💡 **Performance order:** stream selector → line filter → parser → field filter → metric. The cheapest filter goes first. Filters cascade left-to-right.

### 2.5 — Proof of work

**Paste into `docs/LAB07.md`:**

- One full JSON log line from `docker logs <app-container> | head -n 1` — must show all the required fields from §2.1
- `curl -s http://localhost:3100/loki/api/v1/label/container/values | jq -c .data` — must include your app container's name
- The output of running Q1–Q4 through the Loki HTTP query API (so the grader sees the data, not just a screenshot):
  ```bash
  curl --get http://localhost:3100/loki/api/v1/query_range \
       --data-urlencode 'query=<YOUR QUERY HERE>' \
       --data-urlencode 'limit=5' | jq '.data.result[0].values[0]'
  ```
  Show each of Q1–Q4 returning at least one of *your own app's* log lines. (Q3 returns a numeric series, not a log line — show `.data.result[0]` for that one.)
- The four LogQL queries themselves, in a code block, with one sentence each of what they do

---

## Task 3 — Build a log dashboard (2 pts)

### 3.1 — One question per panel

A dashboard answers **one question** for **one audience**. The four panels below cover the most common operational questions for a single service. The LogQL queries from Task 2 already cover most of what you need; one is new.

| Panel | Visualisation | Question it answers | Source query |
|---|---|---|---|
| 1 | Logs | *"What's happening right now?"* | Your Q1 (broaden to `app=~"devops-.*"` if you have multiple apps) |
| 2 | Time series | *"How busy are we, per app?"* | Request **rate** per app (write this — same shape as Q3 but no error filter) |
| 3 | Logs | *"What broke?"* | Your Q2 |
| 4 | Pie chart or Stat | *"How noisy is each level?"* | Distribution of `level` over 5 min — use `count_over_time` + `| json` + `sum by (level)` |

`YOUR TASK`: write the LogQL for panels 2 and 4 yourself (don't copy from §2.4). Panels 1 and 3 reuse Q1/Q2 verbatim.

### 3.2 — Build it

1. **Dashboards → New → New dashboard → Add visualization**. Pick the **Loki** data source.
2. Paste the LogQL. Choose the visualisation type from the table above.
3. Title each panel after the **question it answers**, not the data source. ("Errors per minute" beats "Loki query #3".)
4. Save the dashboard. Then **Share → Export → Save to file** and commit the JSON model to `monitoring/grafana/dashboards/lab07.json`.

> 💡 If a panel is empty, the cause is almost always missing labels, not bad LogQL. Run the panel's query in **Explore** first; if it works there but not in the panel, it's a time-range or data-source-default issue.

### 3.3 — Proof of work

**Paste into `docs/LAB07.md`:**

- Screenshot of the 4-panel dashboard showing real data on all four panels (generate fresh traffic right before the screenshot — empty panels = no credit)
- The four LogQL queries in a markdown table with the question each answers
- The committed JSON file path: `monitoring/grafana/dashboards/lab07.json`

---

## Task 4 — Production readiness (1 pt)

Harden the stack so it isn't a toy.

### 4.1 — Resource limits

`YOUR TASK`: add `deploy.resources.limits` (cpus + memory) and `reservations` to each of the four services. Pick sane numbers — Loki and Grafana need more memory than Alloy and the app; the app needs almost nothing. Document your choices in `LAB07.md`.

### 4.2 — Secure Grafana

`YOUR TASK`:
- Set `GF_AUTH_ANONYMOUS_ENABLED=false` (your DEV-ONLY comment in §1.4 reminded you).
- Set the admin password from a `.env` file: `GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}`.
- Add `.env` to **`.gitignore`** — and commit the `.gitignore` change.
- Commit a `.env.example` with the variable name and an empty placeholder so the grader knows the contract.

### 4.3 — Health checks

`YOUR TASK`: add a `healthcheck:` block to **Loki** (test against `:3100/ready`) and **Grafana** (test against `:3000/api/health`). Use `wget --spider` or `curl --fail` inside the container. Pick reasonable `interval`, `timeout`, `retries`, and `start_period` — Loki specifically takes ~15s to be ready after start, so `start_period` must give it that grace.

### 4.4 — Proof of work

**Paste into `docs/LAB07.md`:**

- `docker compose ps` output where Loki and Grafana both report `(healthy)`
- Screenshot of the Grafana **login page** (i.e. anonymous access is off)
- Listing of `monitoring/.env.example` and confirmation that `.env` is in `.gitignore` and **not** committed (a `git log -- monitoring/.env` returning nothing is fine evidence)

---

## Task 5 — Documentation (1 pt)

`YOUR TASK`: write `monitoring/docs/LAB07.md` with these sections, in order:

1. **Architecture** — a Mermaid diagram of app → Alloy → Loki → Grafana, with the network and the Docker socket marked
2. **Setup** — how to deploy (`docker compose up -d`) and the verification commands from §1.5
3. **Configuration choices** — your three answers from §1.1, plus a short note on each Loki block (schema, retention, compactor) and each Alloy component
4. **Application logging** — which library you picked + why + the field schema you emit
5. **Dashboard** — each panel, its LogQL, the question it answers, and a screenshot
6. **Production config** — your resource limits + reasoning, Grafana auth, the Docker-socket trade-off
7. **Challenges & solutions** — at least one real one (not "I was new to Loki")

Include config **snippets** (not whole files) and the captures from Tasks 1–4. Keep it readable; this is the artefact your future on-call self will read at 3 am.

---

## Bonus Task — Ansible automation (2 pts)

Automate the whole stack with Ansible, building on Lab 6.

`YOUR TASK`: create `roles/monitoring` that brings the entire stack up idempotently.

The role must:
- **Template** `loki/config.yml`, `alloy/config.alloy`, and `docker-compose.yml` from Jinja2 — image tags, ports, retention, and resource limits become role variables (defined in `defaults/main.yml`)
- **Deploy** with `community.docker.docker_compose_v2`
- **Wait** for Loki `:3100/ready` *and* Grafana `:3000/api/health` before reporting success (use `ansible.builtin.uri` with retries)
- Be **idempotent**: a second run reports `changed=0` (Lab 5's headline criterion still applies)

Less hand-holding than Task 1–5: figure out the directory layout, the variable names, and the readiness polling pattern yourself. Lab 6 covered the `docker_compose_v2` deploy mechanics.

**Evidence (paste into `docs/LAB07.md`):**

- First-run output (changes > 0) and second-run output (`changed=0`)
- The **rendered** (not template) `docker-compose.yml` from a real run
- Path: `ansible/roles/monitoring/` + `ansible/playbooks/deploy-monitoring.yml`

---

## How to Submit

```bash
git switch -c lab07
git add monitoring/
git add app_python/                            # JSON logging upgrade
git add ansible/roles/monitoring \
        ansible/playbooks/deploy-monitoring.yml   # only if bonus done
git commit -m "feat(lab07): loki + alloy + grafana observability stack"
git push -u origin lab07
```

Open **two** PRs:

- `your-fork:lab07` → `course-repo:master` *(reviewed)*
- `your-fork:lab07` → `your-fork:master` *(merges into your own main)*

PR checklist:

```text
- [ ] Task 1 done — stack up, Alloy pipeline wired, container labels visible
- [ ] Task 2 done — JSON logging in app_python, 4 LogQL queries verified via /query_range
- [ ] Task 3 done — 4-panel dashboard built, JSON exported into the repo
- [ ] Task 4 done — limits, healthchecks, anonymous off, .env gitignored
- [ ] Task 5 done — LAB07.md with all 7 sections + captures + screenshots
- [ ] Bonus done — idempotent Ansible role with readiness wait
```

---

## Acceptance Criteria

### Task 1 — Stack deployment (3 pts)
- ✅ `docker compose up -d` brings up loki, alloy, grafana, app
- ✅ `curl -s :3100/ready` returns `ready`
- ✅ `curl -s :3100/loki/api/v1/labels` includes `container` (and `app` after §2.2)
- ✅ Alloy live UI shows the four-block pipeline with no broken wires
- ✅ Grafana Explore `{container=~".+"}` returns logs from ≥ 2 containers

### Task 2 — App integration + JSON logging (3 pts)
- ✅ App emits one JSON object per line; required fields present per event type
- ✅ App container is labelled `logging=alloy` and `app=devops-python`
- ✅ Q1–Q4 each return real data via `/loki/api/v1/query_range` (CLI captures pasted)
- ✅ Q3 / Q4 use the JSON parser + field filters (not raw-line regex)

### Task 3 — Dashboard (2 pts)
- ✅ 4 panels, one per operational question, all showing live data
- ✅ Panel titles describe the question, not the query
- ✅ Dashboard JSON committed to `monitoring/grafana/dashboards/lab07.json`

### Task 4 — Production config (1 pt)
- ✅ All four services have CPU + memory limits and reservations
- ✅ Grafana anonymous OFF; admin password from `.env`; `.env` gitignored
- ✅ Loki and Grafana report `(healthy)` in `docker compose ps`

### Task 5 — Documentation (1 pt)
- ✅ All seven sections present in `monitoring/docs/LAB07.md`
- ✅ Research answers from §1.1 are in your own words
- ✅ Real screenshots + CLI captures (not placeholders)

### Bonus — Ansible (2 pts)
- ✅ Role templates all three configs from variables
- ✅ Deploy is idempotent — second run `changed=0`
- ✅ Readiness wait blocks success until Loki + Grafana respond
- ✅ Both playbook runs captured in docs

---

## Rubric

| Task | Points | Criteria |
|------|-------:|----------|
| **Task 1** — Stack deployment | **3** | All four services up; Alloy pipeline correctly wired (the four YOUR-TASKs in §1.3 + the volumes/network/labels in §1.4); `/ready` + `/labels` proofs |
| **Task 2** — App integration | **3** | JSON logging implemented; required fields; Q1–Q4 each return real data via the HTTP API |
| **Task 3** — Dashboard | **2** | 4 panels with appropriate LogQL; dashboard JSON committed |
| **Task 4** — Production config | **1** | Limits, anonymous off, healthchecks healthy |
| **Task 5** — Docs | **1** | All seven sections, real captures, research answers in your own words |
| **Bonus** — Ansible | **2** | Idempotent templated deployment with readiness wait |
| **Total** | **12** | 10 main + 2 bonus |

---

## Resources

<details>
<summary>📚 Loki</summary>

- [Loki overview](https://grafana.com/docs/loki/latest/get-started/overview/)
- [Loki configuration reference](https://grafana.com/docs/loki/latest/configure/)
- [TSDB storage](https://grafana.com/docs/loki/latest/operations/storage/tsdb/)
- [Retention & compactor](https://grafana.com/docs/loki/latest/operations/storage/retention/)
- [HTTP API — push & query](https://grafana.com/docs/loki/latest/reference/loki-http-api/)

</details>

<details>
<summary>⚡ Grafana Alloy (Promtail's successor)</summary>

- [Alloy documentation](https://grafana.com/docs/alloy/latest/)
- [`discovery.docker`](https://grafana.com/docs/alloy/latest/reference/components/discovery/discovery.docker/)
- [`discovery.relabel`](https://grafana.com/docs/alloy/latest/reference/components/discovery/discovery.relabel/)
- [`loki.source.docker`](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.source.docker/)
- [`loki.write`](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.write/)
- [Migrate from Promtail to Alloy](https://grafana.com/docs/alloy/latest/set-up/migrate/from-promtail/)

</details>

<details>
<summary>🔍 LogQL & Grafana</summary>

- [LogQL reference](https://grafana.com/docs/loki/latest/query/) — every operator with examples
- [Grafana dashboards](https://grafana.com/docs/grafana/latest/dashboards/)
- [Loki data source](https://grafana.com/docs/grafana/latest/datasources/loki/)
- [Explore logs](https://grafana.com/docs/grafana/latest/explore/logs-integration/)

</details>

<details>
<summary>📝 Structured logging</summary>

- [`structlog`](https://www.structlog.org/en/stable/)
- [`python-json-logger`](https://github.com/nhairs/python-json-logger)
- [The Twelve-Factor App: Logs](https://12factor.net/logs)
- [Python `logging` HOWTO](https://docs.python.org/3/howto/logging.html)

</details>

<details>
<summary>⚠️ Common Pitfalls (from real dry-runs)</summary>

- **"Ingester not ready, waiting 15s" on first push.** Loki's ingester takes ~15s after the process is alive to report ready. If you query immediately after `docker compose up -d` and see empty results, that's not a bug — it's startup. Wait, retry. Set `healthcheck.start_period: 30s` in Task 4 so compose stops claiming the service is healthy before it actually is.
- **High-cardinality labels = Loki OOM.** Never put `user_id`, `request_id`, `trace_id`, `email`, or any per-request value into a Loki label (Alloy `discovery.relabel` rule or otherwise). Each unique combination is a stream, each stream costs index + memory, and at 10 M users you'll crash the ingester. Per-request values go in the **JSON body** and you filter at query time with `| json | user_id="alice"`.
- **Docker socket permissions inside the Alloy container.** On a default Linux install, `/var/run/docker.sock` is owned by root and the `docker` group; inside the Alloy container, the runtime user may not be in that group. If Alloy logs `permission denied` reading the socket, either run the container with `user: root` for this lab (acceptable for dev) or pass `group_add: ["${DOCKER_GID}"]` after capturing the host's docker GID with `getent group docker | cut -d: -f3`.
- **`subPath` mounts don't refresh on ConfigMap changes** — you'll meet this hard wall in Lab 12 when you redo Loki on Kubernetes. For now, a Compose bind-mount of `loki/config.yml` *does* update when you `docker compose restart loki`, so changes are easy. Internalise the behaviour now; you'll need it later.
- **Promtail config syntax does NOT translate 1:1 to Alloy.** Promtail's flat list of `pipeline_stages` is split in Alloy between `loki.relabel` (label rewrites) and `loki.process` (parsing / line manipulation). Stage names changed (`docker:` → `stage.docker {}` block, `json:` → `stage.json {}`, etc.). If you have a Promtail config to migrate, use the [official migration tool](https://grafana.com/docs/alloy/latest/set-up/migrate/from-promtail/) rather than translating by hand — the field rename matrix is wider than it looks.
- **Returning a dict from FastAPI's middleware vs Flask's `after_request`.** FastAPI middleware is awaited; Flask hooks aren't. Don't `await` `request.json()` inside a Flask after_request — it's blocking. Pick one framework's pattern and stay consistent.
- **JSON log line split by `docker logs`.** If you pretty-print JSON (`json.dumps(obj, indent=2)`), `docker logs` (and therefore Alloy) treats each indented line as a separate log entry — and your `| json` parser will fail on every one of them. Always one JSON object per line, no indentation.
- **Anonymous Grafana left enabled in Task 4 "by accident".** You said "I'll remember to turn it off" in §1.4. You won't — the comment in your compose file is the only thing that will save you. Leave it.

</details>

<details>
<summary>🛠️ Dev tools worth knowing</summary>

- [`logcli`](https://grafana.com/docs/loki/latest/query/logcli/) — a CLI for LogQL; faster than the Grafana UI for one-shot queries
- [`jq`](https://jqlang.github.io/jq/) — JSON pretty-printer; chain `curl … | jq` everywhere
- [`hey`](https://github.com/rakyll/hey) — generate traffic against your app to populate dashboards

</details>

---

## Looking Ahead

| Lab | What it adds |
|---:|---|
| 8 | The **metrics** pillar — Prometheus + `/metrics` on your Lab 1 app, RED-method PromQL |
| 9 | Deploy this same app + the `echo` plumbing service on k3d Kubernetes |
| 12 | ConfigMaps + PVCs — re-mount the Loki config from a ConfigMap; meet the `subPath` foot-gun |
| 16 | `kube-prometheus-stack` + a Loki Helm chart — the K8s redo of this whole stack |

---

**Good luck!** 🚀

> **Remember:** Loki indexes *labels*, not text. Keep label cardinality low; per-request fields belong in the JSON body, filtered at query time with `| json | field="value"`. The Alloy pipeline is four wired components — not a YAML list — and the wires are export names (`.targets`, `.output`, `.receiver`), not block labels.
