# Lab 7 — Observability & Logging with Loki Stack

**Name:** egrapa  \
**Date:** 2026-03-05  \
**Lab Points:** 10 + 0 bonus

---

## Architecture

Docker Compose brings four containers onto a `logging` bridge network:

```
[Docker containers]
     | (stdout + docker socket)
     v
 +-----------+       push        +------------+
 |  Promtail | ---------------> |    Loki    |
 | 9080 HTTP |    LogQL labels  | 3100 HTTP  |
 +-----------+                  +------------+
       ^                               |
       |      Explore + Dashboards     v
       |<--------------------------+-------+
       |                           |Grafana|
       |                           | 3000  |
       |                           +-------+
       |
 +-----------------------+
 | devops-info-service   |
 | Flask app on 8000     |
 | labels: logging=promtail,
 |         app=devops-python |
 +-----------------------+
```

Logs stay on the host filesystem: Loki TSDB data under the `loki-data`
volume, Grafana state in `grafana-data`, and Promtail read offsets in
`promtail-positions`.

---

## Setup Guide

1. Copy secrets: `cp monitoring/.env.example monitoring/.env` and set
   `GF_SECURITY_ADMIN_PASSWORD`.
2. Start stack: `cd monitoring && docker compose up -d`.
3. Verify containers: `docker compose ps`.
4. Health checks: `curl -f http://localhost:3100/ready` (Loki),
   `curl -f http://localhost:9080/ready` (Promtail),
   `curl -f http://localhost:3000/api/health` (Grafana).
5. Generate traffic so logs appear:

   ```bash
   for i in {1..20}; do curl -s http://localhost:8000/; done
   for i in {1..20}; do curl -s http://localhost:8000/health; done
   ```

6. In Grafana → Connections → Data sources → Loki, set URL
   `http://loki:3100` and click **Save & test**.
7. Explore logs with `{app="devops-python"}` and build the dashboard
   (queries listed below).

---

## Configuration

**Docker Compose** (`monitoring/docker-compose.yml`)

- Loki 3.0.0, Promtail 3.0.0, Grafana 12.3.1, Flask app.
- Shared `logging` network; persistent named volumes for Loki/Grafana
  data and Promtail positions.
- Health checks on Loki `/ready` and Grafana `/api/health`.
- Resource guards applied to every service
  (`limits: cpus/memory`, `reservations`).

**Loki** (`monitoring/loki/config.yml`)

- TSDB storage with filesystem object store and schema v13.
- Path prefix `/loki`, in-memory ring, embedded cache for query range.
- Retention set to `168h` with compactor enabled for cleanup.
- Auth disabled for lab simplicity.

_Snippet:_

```yaml
schema_config:
  configs:
    - from: 2024-01-01
      store: tsdb
      object_store: filesystem
      schema: v13
      index:
        prefix: index_
        period: 24h
limits_config:
  retention_period: 168h
```

**Promtail** (`monitoring/promtail/config.yml`)

- Scrapes Docker via socket (`docker_sd_configs`).
- Keeps only containers labeled `logging=promtail` and forwards labels to
  Loki (`app`, `container`).
- Uses Docker pipeline stage so JSON logs remain structured.

_Snippet:_

```yaml
scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    pipeline_stages:
      - docker: {}
    relabel_configs:
      - source_labels: [__meta_docker_container_label_logging]
        regex: promtail
        action: keep
      - source_labels: [__meta_docker_container_label_app]
        target_label: app
```

---

## Application Logging

The Flask app now emits structured JSON to stdout using a custom
`JSONFormatter` (see `app_python/app.py`). Every record includes
`timestamp`, `level`, `logger`, and `message`, plus contextual fields
passed via `extra`.

Key events logged:
- `event: startup` — service version, host/port, debug flag.
- `event: request_received` — method, path, client IP, user agent.
- `event: response_sent` — status, duration_ms, content_length.
- `event: not_found` and `event: internal_error` with request context and
  stack traces on exceptions.

Example log line:

```json
{"timestamp": "2026-03-05T12:00:00+00:00", "level": "INFO", "logger": "devops-info-service", "message": "response_sent", "event": "response_sent", "method": "GET", "path": "/health", "status": 200, "client_ip": "127.0.0.1", "duration_ms": 2, "content_length": 67}
```

Promtail attaches labels `app="devops-python"` and
`container="app-python"` so queries stay simple.

---

## Dashboard

Create a Grafana dashboard with four panels using the Loki data source:

1. **Logs Table** — `{app=~"devops-.*"}` (Logs view)
2. **Request Rate** — `sum by (app) (rate({app=~"devops-.*"} [1m]))`
   (Time series)
3. **Error Logs** — `{app=~"devops-.*"} | json | level="ERROR"`
   (Logs)
4. **Log Level Distribution** —
   `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))`
   (Pie or Stat)

Run sample queries in Explore first:
- `{app="devops-python"}`
- `{app="devops-python"} |= "ERROR"`
- `{app="devops-python"} | json | method="GET"`
- `rate({app="devops-python"}[1m])`

Capture screenshots of Explore and the dashboard once data is flowing.

---

## Production Config

- Anonymous Grafana access disabled; admin password supplied through
  `.env` (`GF_AUTH_ANONYMOUS_ENABLED=false`).
- Resource limits/reservations on all services to prevent noisy
  neighbors.
- Loki retention at 7 days with compactor cleanup; filesystem storage for
  single-node lab use.
- Health checks ensure orchestrator restarts unhealthy containers.
- Sensitive env vars kept out of git via `.env` (only `.env.example`
  committed).

---

## Testing

- `docker compose ps` — confirm all services `Up (healthy)`.
- Loki ready: `curl -f http://localhost:3100/ready`.
- Promtail targets: `curl -s http://localhost:9080/targets | jq .`.
- Grafana health: `curl -f http://localhost:3000/api/health`.
- Generate traffic with the curl loops above; verify logs appear with
  `{app="devops-python"}`.
- LogQL filters: `{app="devops-python"} |= "ERROR"` and
  `{app="devops-python"} | json | method="GET"` should return entries
  after traffic.

---

## Challenges

- Structured logging without external deps: solved with a small custom
  `JSONFormatter` that flattens `extra` fields and preserves stack
  traces.
- Promtail label hygiene: used Docker label-based relabeling to keep only
  intended containers and propagate `app` for concise queries.
- Security vs. convenience: Grafana anonymous auth disabled; `.env`
  placeholder added to keep secrets out of git while keeping setup
  reproducible.
