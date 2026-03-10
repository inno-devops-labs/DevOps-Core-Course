# Lab 07 — Observability & Logging with Loki Stack

## 1. Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  app-python  │     │ app-python-  │     │   (other     │
│  :8000       │     │ bonus :8001  │     │  containers) │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │  stdout/stderr     │                    │
       ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────┐
│                Docker Engine (log driver: json-file)    │
│   /var/lib/docker/containers/*/*.log                    │
└──────────────────────────┬──────────────────────────────┘
                           │  reads via Docker socket
                           ▼
                  ┌──────────────────┐
                  │    Promtail      │
                  │  (log collector) │
                  └────────┬─────────┘
                           │  POST /loki/api/v1/push
                           ▼
                  ┌──────────────────┐
                  │      Loki        │
                  │  (log storage)   │
                  │  TSDB + FS :3100 │
                  └────────┬─────────┘
                           │  LogQL queries
                           ▼
                  ┌──────────────────┐
                  │    Grafana       │
                  │  (visualization) │
                  │       :3000      │
                  └──────────────────┘
```

**Data flow:** Applications write logs to stdout → Docker captures them as JSON files → Promtail discovers containers via Docker socket and reads their logs → Promtail pushes log streams to Loki → Grafana queries Loki using LogQL and displays results on dashboards.

**Key design decisions:**
- **Loki** stores only labels (metadata indexes), not full-text — much lighter than Elasticsearch.
- **TSDB** (Time Series Database) backend in Loki 3.0 provides up to 10× faster queries than the older BoltDB shipper.
- **Promtail** uses Docker service discovery (`docker_sd_configs`) to automatically find containers with the label `logging=promtail`.

---

## 2. Setup Guide

### Prerequisites

- Docker Engine 24+
- Docker Compose v2 (the `docker compose` plugin)

### Quick start

```bash
cd monitoring

# Start the entire stack
docker compose up -d

# Verify everything is running
docker compose ps

# Test Loki readiness
curl http://localhost:3100/ready

# Generate sample traffic
for i in {1..20}; do curl -s http://localhost:8000/; done
for i in {1..20}; do curl -s http://localhost:8000/health; done
for i in {1..5};  do curl -s http://localhost:8000/nonexistent; done

# Open Grafana
open http://localhost:3000
```

**Grafana credentials** are read from `monitoring/.env` (not committed to git):

| Variable | Default |
|---|---|
| `GF_SECURITY_ADMIN_USER` | `admin` |
| `GF_SECURITY_ADMIN_PASSWORD` | (set in .env) |

The Loki data source and a pre-built dashboard are **auto-provisioned** at startup — no manual steps needed.

### Teardown

```bash
docker compose down            # stop containers
docker compose down -v         # stop + remove volumes
```

---

## 3. Configuration

### Loki (`loki/config.yml`)

| Section | Purpose |
|---|---|
| `auth_enabled: false` | Single-tenant mode (no auth between services) |
| `schema_config` → `store: tsdb`, `schema: v13` | Loki 3.0 TSDB backend for fast queries |
| `common.storage.filesystem` | Local filesystem storage (single-node setup) |
| `limits_config.retention_period: 168h` | Auto-delete logs older than 7 days |
| `compactor.retention_enabled: true` | Enables background cleanup of expired logs |

### Promtail (`promtail/config.yml`)

| Section | Purpose |
|---|---|
| `clients[0].url` | Sends logs to `http://loki:3100/loki/api/v1/push` |
| `docker_sd_configs` | Discovers containers via Docker socket |
| `filters: label logging=promtail` | Only collects logs from opted-in containers |
| `relabel_configs` | Extracts `container` and `app` labels from Docker metadata |

### Docker Compose

- All services share the `logging` bridge network.
- Named volumes `loki-data` and `grafana-data` persist data across restarts.
- Grafana provisioning directory mounts datasource and dashboard configs automatically.

---

## 4. Application Logging

The Python application (`monitoring/app/app.py`) implements structured JSON logging:

```python
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            ...
        }
        return json.dumps(log_entry)
```

**Logged events:**
- **Startup** — app name, port
- **Every HTTP request** — method, path, client IP
- **Every response** — status code
- **Errors/exceptions** — full traceback in `exception` field

**Example output:**
```json
{"timestamp": "2026-03-10T12:00:00+00:00", "level": "INFO", "message": "Root endpoint served", "logger": "devops-app", "method": "GET", "path": "/", "status_code": 200, "client_ip": "172.19.0.1"}
```

---

## 5. Dashboard

The provisioned dashboard (`grafana/dashboards/logs.json`) contains 5 panels:

| # | Panel | Visualization | LogQL Query |
|---|---|---|---|
| 1 | Logs Table — All Applications | Logs | `{app=~"devops-.*"}` |
| 2 | Request Rate by Application | Time series | `sum by (app) (rate({app=~"devops-.*"} [1m]))` |
| 3 | Error Logs | Logs | `{app=~"devops-.*"} \| json \| level="ERROR"` |
| 4 | Log Level Distribution | Pie chart | `sum by (level) (count_over_time({app=~"devops-.*"} \| json [5m]))` |
| 5 | Logs per Second (total) | Stat | `sum(rate({app=~"devops-.*"} [5m]))` |

### Useful LogQL queries

```logql
# All logs from Python app
{app="devops-python"}

# Only errors
{app="devops-python"} |= "ERROR"

# Parse JSON and filter by HTTP method
{app="devops-python"} | json | method="GET"

# Filter by path
{app="devops-python"} | json | path="/health"

# Count requests per minute grouped by status code
sum by (status_code) (count_over_time({app="devops-python"} | json [1m]))

# Top apps by log volume
topk(5, sum by (app) (rate({app=~"devops-.*"} [5m])))
```

---

## 6. Production Configuration

### Security

- **Anonymous access disabled** (`GF_AUTH_ANONYMOUS_ENABLED=false`).
- Admin credentials sourced from `.env` file (excluded from git via `.gitignore`).
- Promtail Docker socket is mounted read-only (`:ro`).

### Resource limits

| Service | CPU limit | Memory limit | CPU reservation | Memory reservation |
|---|---|---|---|---|
| Loki | 1.0 | 1 GB | 0.25 | 256 MB |
| Promtail | 0.5 | 512 MB | 0.1 | 128 MB |
| Grafana | 1.0 | 512 MB | 0.25 | 128 MB |
| App (each) | 0.5 | 256 MB | 0.1 | 64 MB |

### Health checks

- **Loki:** `wget --spider http://localhost:3100/ready` (interval 10s, 5 retries, 20s start period)
- **Grafana:** `wget --spider http://localhost:3000/api/health` (interval 10s, 5 retries, 15s start period)
- Promtail and apps depend on Loki being healthy (`depends_on.condition: service_healthy`).

### Retention

- Loki retention: **168 hours (7 days)**.
- Compactor runs every 10 minutes and purges expired chunks after a 2-hour delete delay.

---

## 7. Testing

```bash
# 1. Start the stack
cd monitoring && docker compose up -d

# 2. Wait for healthy status
docker compose ps   # all services should show "healthy"

# 3. Verify Loki
curl -s http://localhost:3100/ready
# Expected: "ready"

# 4. Generate logs
for i in {1..20}; do curl -s http://localhost:8000/; done
for i in {1..20}; do curl -s http://localhost:8000/health; done
for i in {1..5};  do curl -s http://localhost:8000/nonexistent; done
for i in {1..10}; do curl -s http://localhost:8001/; done

# 5. Query Loki directly via API
curl -sG http://localhost:3100/loki/api/v1/query \
  --data-urlencode 'query={app="devops-python"}' | python3 -m json.tool

# 6. Open Grafana and check dashboard
open http://localhost:3000
# Login → Dashboards → "Application Logs Dashboard"
```

---

## 8. Challenges & Solutions

| Challenge | Solution |
|---|---|
| Promtail not discovering containers | Added `filters: [label logging=promtail]` and ensured every service has `labels: logging: "promtail"` in compose |
| Loki `tsdb` config errors on startup | Used `schema: v13` (required for TSDB in Loki 3.0) with a valid `from` date |
| Grafana data source not auto-configured | Used provisioning directory (`grafana/provisioning/datasources/loki.yml`) mounted into the container |
| Docker socket permission denied | Mounted socket as read-only (`:ro`) and ensured Promtail container has sufficient permissions |
| Logs not appearing immediately | Set Promtail `refresh_interval: 5s` and generated traffic to produce log entries |
| Dashboard empty on first load | Pre-provisioned dashboard JSON with correct Loki datasource type reference |
