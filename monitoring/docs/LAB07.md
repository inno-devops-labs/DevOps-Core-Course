# Lab 07 — Observability & Logging with Loki Stack

## 1. Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                       Docker Host                                │
│                                                                  │
│  ┌───────────┐    logs     ┌──────────┐   push    ┌──────────┐  │
│  │ app-python├────────────►│ Promtail ├──────────►│   Loki   │  │
│  │  :8000    │             │  :9080   │           │  :3100   │  │
│  └───────────┘             └──────────┘           └────┬─────┘  │
│                                                        │        │
│  ┌───────────┐    logs          ▲                      │        │
│  │  grafana  ├──────────────────┘             query    │        │
│  │  :3000    │◄───────────────────────────────────────┘        │
│  └───────────┘                                                  │
│                                                                  │
│  Network: logging (bridge)                                       │
└──────────────────────────────────────────────────────────────────┘
```

**Components:**

| Service   | Image                      | Port | Role                          |
|-----------|----------------------------|------|-------------------------------|
| Loki      | `grafana/loki:3.0.0`       | 3100 | Log storage & indexing (TSDB) |
| Promtail  | `grafana/promtail:3.0.0`   | 9080 | Log collector (Docker SD)     |
| Grafana   | `grafana/grafana:12.3.1`   | 3000 | Visualization & dashboards    |
| app-python| built from `../app_python` | 8000 | Application under monitoring  |

All services share the `logging` bridge network. Promtail scrapes Docker container logs via the Docker socket and forwards them to Loki. Grafana queries Loki to display and analyze logs.

---

## 2. Setup Guide

### Prerequisites
- Docker Engine 24+ with Compose v2
- Python app from Lab 1

### Deployment

```bash
cd monitoring

# Start the full stack
docker compose up -d

# Verify services
docker compose ps

# Check Loki readiness
curl http://localhost:3100/ready

# Check Promtail targets
curl http://localhost:9080/targets

# Access Grafana at http://localhost:3000
# Login: admin / SecurePass123!
```

### Configure Grafana Data Source

1. Open Grafana → **Connections** → **Data sources** → **Add data source**
2. Select **Loki**
3. URL: `http://loki:3100`
4. Click **Save & Test** → should report "Data source connected"

### Generate traffic

```bash
for i in {1..20}; do curl http://localhost:8000/; done
for i in {1..20}; do curl http://localhost:8000/health; done
```

---

## 3. Configuration

### Loki (`loki/config.yml`)

Key design decisions:

- **TSDB index** (`store: tsdb`, `schema: v13`) — Loki 3.0 default; up to 10× faster queries and lower memory usage compared to `boltdb-shipper`.
- **Filesystem object store** — suitable for single-node deployment; data stored in `/loki/chunks` (named volume `loki-data`).
- **7-day retention** (`retention_period: 168h`) with the compactor enabled to delete expired chunks automatically.
- **`auth_enabled: false`** — no multi-tenancy; acceptable for a dev/lab environment.

```yaml
schema_config:
  configs:
    - from: "2024-01-01"
      store: tsdb
      object_store: filesystem
      schema: v13
      index:
        prefix: index_
        period: 24h
```

### Promtail (`promtail/config.yml`)

- **Docker service discovery** (`docker_sd_configs`) — auto-discovers running containers through the Docker socket.
- **Label filter** (`logging=promtail`) — only containers labelled `logging: "promtail"` are scraped.
- **Relabelling** — extracts `container` name (strips leading `/`) and `app` label for use in LogQL selectors.

```yaml
relabel_configs:
  - source_labels: ["__meta_docker_container_name"]
    regex: "/(.*)"
    target_label: "container"
  - source_labels: ["__meta_docker_container_label_app"]
    target_label: "app"
```

---

## 4. Application Logging

The Python app uses a custom `JSONFormatter` that outputs one JSON object per log line:

```json
{
  "timestamp": "2026-02-21T12:00:00.123Z",
  "level": "INFO",
  "logger": "__main__",
  "message": "Request completed: GET / -> 200 (3.42ms)",
  "method": "GET",
  "path": "/",
  "status_code": 200,
  "client_ip": "172.20.0.1",
  "duration_ms": 3.42
}
```

**Why JSON?**
- LogQL `| json` parser can extract any field directly.
- Structured data enables filtering by `level`, `method`, `status_code`, etc.
- No complex regex needed for parsing.

The `@app.middleware("http")` logs both the incoming request and the completed response with duration.

---

## 5. Dashboard

Four panels are created in Grafana:

### Panel 1 — Logs Table
- **Type:** Logs visualization
- **Query:** `{app=~"devops-.*"}`
- Shows recent logs from all application containers.

### Panel 2 — Request Rate
- **Type:** Time series
- **Query:** `sum by (app) (rate({app=~"devops-.*"} [1m]))`
- Displays log throughput per application per second.

### Panel 3 — Error Logs
- **Type:** Logs visualization
- **Query:** `{app=~"devops-.*"} | json | level="ERROR"`
- Filters only ERROR-level log entries.

### Panel 4 — Log Level Distribution
- **Type:** Stat / Pie chart
- **Query:** `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))`
- Breaks down log volume by severity level.

### Additional useful queries

```logql
# All logs from Python app
{app="devops-python"}

# Only errors
{app="devops-python"} |= "ERROR"

# Parse JSON and filter by HTTP method
{app="devops-python"} | json | method="GET"

# Top 10 slowest requests
topk(10, {app="devops-python"} | json | unwrap duration_ms [5m])

# Requests to specific path
{app="devops-python"} | json | path="/health"
```

---

## 6. Production Config

### Resource Limits
Every service has `deploy.resources` with CPU/memory limits and reservations to prevent resource exhaustion:

| Service    | CPU limit | Memory limit | CPU reservation | Memory reservation |
|------------|-----------|--------------|-----------------|-------------------|
| Loki       | 1.0       | 1 GB         | 0.5             | 512 MB            |
| Promtail   | 0.5       | 512 MB       | 0.25            | 256 MB            |
| Grafana    | 1.0       | 1 GB         | 0.5             | 512 MB            |
| app-python | 0.5       | 256 MB       | 0.25            | 128 MB            |

### Security
- **Anonymous access disabled** — `GF_AUTH_ANONYMOUS_ENABLED=false`.
- **Admin credentials** stored in `monitoring/.env` (excluded from Git via `.gitignore`).
- **Docker socket** mounted read-only to Promtail (`/var/run/docker.sock:ro`).

### Health Checks
- **Loki:** `wget --spider http://localhost:3100/ready` (interval 10s, 5 retries, 20s start period)
- **Grafana:** `wget --spider http://localhost:3000/api/health` (interval 10s, 5 retries, 15s start period)

### Retention
- Logs are retained for **7 days** (168h) and the compactor runs automatically.
- All services have `restart: unless-stopped`.

---

## 7. Testing

```bash
# 1. Deploy
cd monitoring && docker compose up -d

# 2. Check all services are healthy
docker compose ps

# 3. Verify Loki is ready
curl -s http://localhost:3100/ready
# Expected: "ready"

# 4. Verify Promtail targets
curl -s http://localhost:9080/targets | head -20

# 5. App responds
curl -s http://localhost:8000/ | python -m json.tool
curl -s http://localhost:8000/health | python -m json.tool

# 6. Generate traffic
for i in {1..20}; do curl -s http://localhost:8000/ > /dev/null; done

# 7. Query Loki directly
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={app="devops-python"}' | python -m json.tool

# 8. Check Grafana login page (no anonymous access)
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/
# Expected: 302 (redirect to login)

# 9. Teardown
docker compose down
```

---

## 8. Challenges

| Problem | Solution |
|---------|----------|
| Promtail not discovering containers | Added `logging: "promtail"` label to all services and configured `filters` in `docker_sd_configs`. |
| Loki schema errors on startup | Used `schema: v13` with `store: tsdb` as required by Loki 3.0. |
| Uvicorn access logs duplicating app logs | Set `access_log=False` in `uvicorn.run()` so only the custom JSON middleware logs requests. |
| `.env` secrets ending up in Git | Added `monitoring/.env` to `.gitignore`. |
| Container name label including `/` prefix | Used `regex: "/(.*)"` in Promtail relabel config to strip it. |
