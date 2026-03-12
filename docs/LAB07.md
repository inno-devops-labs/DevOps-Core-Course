# Lab 07 — Observability & Logging with Loki Stack

## 1. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Network: logging                  │
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────────┐  │
│  │  app-python  │     │   Promtail   │     │     Grafana    │  │
│  │  :8000       │────▶│   :9080      │────▶│     :3000      │  │
│  │  (FastAPI)   │logs │ (collector)  │push │ (visualization)│  │
│  └──────────────┘     └──────────────┘     └────────────────┘  │
│         │                    │                      │           │
│         │ stdout/stderr       │ /loki/api/v1/push   │ query     │
│         ▼                    ▼                      ▼           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Docker Daemon                        │   │
│  │              /var/lib/docker/containers                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                   │
│                             ▼                                   │
│                    ┌─────────────────┐                          │
│                    │      Loki       │                          │
│                    │     :3100       │                          │
│                    │  (log storage   │                          │
│                    │   with TSDB)    │                          │
│                    └─────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Setup Guide

### Steps

```bash
# 1. Clone / navigate to the repo
cd DevOps-Core-Course/monitoring

# 2. Copy the example env file and set a strong Grafana password
cp .env.example .env   # edit GF_ADMIN_PASSWORD before continuing

# 3. Pull images and start the stack in the background
docker compose up -d --build

# 4. Watch service health
docker compose ps

# 5. Confirm Loki is ready
curl http://localhost:3100/ready
# → ready

# 6. Confirm Promtail targets are being scraped
curl http://localhost:9080/targets

# 7. Open Grafana
open http://localhost:3000
# Login: admin / <password from .env>
```

### Add Loki Data Source (first run only)

1. **Connections** → **Data sources** → **Add data source** → **Loki**
2. URL: `http://loki:3100`
3. **Save & Test** — you should see _"Data source connected and labels found"_

### Tear down

```bash
docker compose down -v
```

---

## 3. Configuration

### 3.1 Loki (`loki/config.yml`)

```yaml
auth_enabled: false # single-tenant, no auth needed

server:
  http_listen_port: 3100

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
  replication_factor: 1 # single-node deployment
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2024-01-01
      store: tsdb # TSDB = 10x faster than boltdb-shipper
      object_store: filesystem
      schema: v13 # latest schema; required for Loki 3.0+
      index:
        prefix: index_
        period: 24h

limits_config:
  retention_period: 168h # 7 days
  allow_structured_metadata: true

compactor:
  retention_enabled: true
  delete_request_store: filesystem
```

**Key decisions:**
| Choice | Reason |
|--------|--------|
| `store: tsdb` | Recommended for Loki 3.0+; faster query performance and lower memory |
| `schema: v13` | Latest schema version; mandatory for TSDB in Loki 3.x |
| `retention_period: 168h` | 7-day rolling window; balances storage cost vs. useful history |
| `auth_enabled: false` | Single-node development setup; enable for multi-tenant production |

### 3.2 Promtail (`promtail/config.yml`)

```yaml
clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
        filters:
          - name: label
            values: ["logging=promtail"] # only scrape opt-in containers

    relabel_configs:
      - source_labels: [__meta_docker_container_name]
        regex: "/(.*)"
        target_label: container # strips leading "/"

      - source_labels: [__meta_docker_container_label_app]
        target_label: app # maps Docker label → Loki label
```

**Key decisions:**
| Choice | Reason |
|--------|--------|
| `filters: logging=promtail` | Opt-in model; infrastructure containers (Loki, Promtail itself) are excluded unless they carry the label |
| Docker socket mount (`:ro`) | Required for service discovery; read-only reduces attack surface |
| `relabel_configs` | Extracts human-readable `container` and `app` labels so LogQL queries are ergonomic |

---

## 4. Application Logging

The Python app (`app_python/main.py`) was updated to emit structured **JSON** logs using `python-json-logger`.

### Setup

```python
from pythonjsonlogger import jsonlogger

logger = logging.getLogger("app")
handler = logging.StreamHandler()
handler.setFormatter(
    jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
)
logger.addHandler(handler)
```

### What gets logged

| Event                  | Level | Extra fields                                                |
| ---------------------- | ----- | ----------------------------------------------------------- |
| App startup            | INFO  | `host`, `port`, `service_name`, `service_version`, `system` |
| HTTP request           | INFO  | `client_ip`, `method`, `path`, `status_code`, `user_agent`  |
| `/` endpoint hit       | INFO  | `path`, `method`                                            |
| `/health` endpoint hit | INFO  | `path`, `status`                                            |
| App shutdown           | INFO  | `uptime_seconds`, `uptime_human`                            |

### Example log line

```json
{
  "timestamp": "2025-07-20T12:34:56+0000",
  "level": "INFO",
  "name": "app",
  "message": "http request",
  "client_ip": "172.18.0.1",
  "method": "GET",
  "path": "/",
  "status_code": 200,
  "user_agent": "curl/8.4.0"
}
```

**Why JSON?**

- Loki's `| json` parser can extract any field as a label filter or metric.
- No custom regex pipelines needed — the structure is machine-readable from the start.
- Easy to extend: add a field to `extra={}` and it appears automatically in Grafana.

---

## 5. Dashboard

The dashboard is named **"Application Logs"** and contains 4 panels.

### Panel 1 — All Logs (Logs visualization)

Displays a real-time stream of every log line from all monitored apps.

```logql
{app=~"devops-.*"}
```

- Visualization: **Logs**
- Useful for: tail-like live monitoring, quick incident triage.

### Panel 2 — Request Rate (Time series)

Shows log throughput (lines/second) per application, revealing traffic spikes and drops.

```logql
sum by (app) (rate({app=~"devops-.*"}[1m]))
```

- Visualization: **Time series**
- Unit: `logs/sec`
- Useful for: traffic pattern analysis, capacity planning.

### Panel 3 — Error Logs (Logs visualization)

Filters down to only `ERROR`-level log lines so errors are easy to spot.

```logql
{app=~"devops-.*"} | json | level="ERROR"
```

- Visualization: **Logs**
- Useful for: on-call alerting, debugging production issues.

### Panel 4 — Log Level Distribution (Pie chart)

Shows the proportion of `INFO` vs `WARN` vs `ERROR` logs over the dashboard time range.

```logql
sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))
```

- Visualization: **Pie chart**
- Useful for: health at a glance; a rising ERROR slice indicates degradation.

---

## 6. Production Configuration

### Resource Limits

Every service in `docker-compose.yml` has a `deploy.resources` block:

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

| Service    | CPU limit | Memory limit | Rationale                                   |
| ---------- | --------- | ------------ | ------------------------------------------- |
| loki       | 1.0       | 1G           | Index + chunk cache can be memory-intensive |
| promtail   | 0.5       | 256M         | Lightweight tail process                    |
| grafana    | 1.0       | 512M         | Rendering dashboards can spike CPU          |
| app-python | 0.5       | 256M         | Small FastAPI service                       |

### Grafana Security

Anonymous access is **disabled** in production:

```yaml
environment:
  - GF_AUTH_ANONYMOUS_ENABLED=false # no unauthenticated access
  - GF_SECURITY_ADMIN_USER=${GF_ADMIN_USER}
  - GF_SECURITY_ADMIN_PASSWORD=${GF_ADMIN_PASSWORD} # sourced from .env
  - GF_USERS_ALLOW_SIGN_UP=false # no self-registration
```

Credentials live in `.env` which is listed in `.gitignore` and never committed.

### Health Checks

```yaml
healthcheck:
  test:
    [
      "CMD-SHELL",
      "wget --no-verbose --tries=1 --spider http://localhost:3100/ready || exit 1",
    ]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 30s
```

- `start_period` gives Loki time to initialise its TSDB index before checks begin.
- `depends_on: condition: service_healthy` ensures Promtail and Grafana wait for Loki.

### Log Retention

Configured in Loki with a 7-day rolling window:

```yaml
limits_config:
  retention_period: 168h

compactor:
  retention_enabled: true
  compaction_interval: 10m
```

The compactor runs every 10 minutes and deletes chunks older than 168 hours.

---

## 7. Testing

### Verify services are up and healthy

```bash
docker compose ps
# All services should show "healthy" status
```

### Confirm Loki is ready

```bash
curl -s http://localhost:3100/ready
# → ready
```

### Check Promtail has discovered targets

```bash
curl -s http://localhost:9080/targets | python3 -m json.tool | grep "app-python"
```

### Generate test traffic

```bash
for i in {1..20}; do curl -s http://localhost:8000/ > /dev/null; done
for i in {1..20}; do curl -s http://localhost:8000/health > /dev/null; done
```

### Query Loki directly via the API

```bash
# All labels available
curl -s "http://localhost:3100/loki/api/v1/labels" | python3 -m json.tool

# Recent log lines from the Python app
curl -s -G "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={app="devops-python"}' \
  --data-urlencode 'limit=5' | python3 -m json.tool
```

### Query via Grafana Explore

Open `http://localhost:3000` → **Explore** → **Loki** and run:

```logql
# All app logs
{app="devops-python"}

# Errors only
{app="devops-python"} |= "ERROR"

# Parse JSON and filter by HTTP method
{app="devops-python"} | json | method="GET"

# Request rate per second over 1-minute windows
rate({app="devops-python"}[1m])

# Count logs by level
sum by (level) (count_over_time({app="devops-python"} | json [5m]))
```

---

## 8. Challenges & Solutions

### Challenge 1 — Loki 3.0 schema breaking changes

**Problem:** Config examples from older tutorials use `boltdb-shipper` and schema `v11`/`v12`, which produce warnings or errors in Loki 3.0.

**Solution:** Switch to `store: tsdb` and `schema: v13` as required by Loki 3.0+. The `common:` block (new in 3.0) greatly simplifies the config by sharing storage settings across components.

---

### Challenge 2 — Container name label has a leading slash

**Problem:** Docker reports container names as `/app-python` (with a leading `/`), so the `container` label in Loki becomes `/app-python` instead of `app-python`, making queries ugly.

**Solution:** Added a relabel rule with `regex: "/(.*)"` that strips the slash:

```yaml
- source_labels: [__meta_docker_container_name]
  regex: "/(.*)"
  target_label: container
```

---

### Challenge 3 — Grafana image version `12.3.1` not published at lab time

**Problem:** Pulling `grafana/grafana:12.3.1` failed with "manifest not found" on some systems.

**Solution:** Pin to the latest available stable tag (`grafana/grafana:latest` or the most recent patch release). The lab specifies `12.3.1` as a target; substitute the closest available tag if it is not yet published.
