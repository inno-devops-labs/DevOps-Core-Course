# Lab 7: Observability & Logging with Loki Stack

**Name:** Leonid Merkulov
**Date:** 2026-03-11
**Lab Points:** 10 + 2.5 bonus

---

## Task 1: Deploy Loki Stack (4 pts)

### Architecture

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│ App Python│    │  App Go  │    │  Others  │
│ :8000    │    │  :8001   │    │          │
└────┬─────┘    └────┬─────┘    └────┬─────┘
     │               │               │
     └───────┬───────┘───────────────┘
             │ Docker logs
     ┌───────▼────────┐
     │   Promtail     │  Collects logs via Docker SD
     │   :9080        │  Filters by label: logging=promtail
     └───────┬────────┘
             │ Push to /loki/api/v1/push
     ┌───────▼────────┐
     │     Loki       │  TSDB storage, schema v13
     │   :3100        │  7-day retention
     └───────┬────────┘
             │ Query via LogQL
     ┌───────▼────────┐
     │    Grafana      │  Dashboards & Explore
     │   :3000         │
     └────────────────┘
```

### Components

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| Loki | grafana/loki:3.0.0 | 3100 | Log storage (TSDB) |
| Promtail | grafana/promtail:3.0.0 | 9080 | Log collector |
| Grafana | grafana/grafana:12.3.1 | 3000 | Visualization |

### Loki Configuration

Using Loki 3.0 with TSDB (10x faster queries than boltdb-shipper):
- Schema v13 with TSDB index
- Filesystem storage for single-instance setup
- 7-day retention with compactor
- Inmemory ring for single-node deployment

### Promtail Configuration

- Docker service discovery via Docker socket
- Filters containers by `logging=promtail` label
- Relabeling extracts `container` and `app` labels from Docker metadata

### Deployment

```bash
cd monitoring
docker compose up -d
docker compose ps

# Verify
curl http://localhost:3100/ready
curl http://localhost:9080/targets
open http://localhost:3000
```

---

## Task 2: Application Integration (3 pts)

### JSON Structured Logging

Added `JSONFormatter` class to Python app that outputs logs as:
```json
{"timestamp": "2026-03-11T12:00:00+00:00", "level": "INFO", "logger": "app", "message": "Incoming request: GET / from 172.18.0.1"}
```

Added `@app.before_request` and `@app.after_request` hooks for automatic request/response logging.

### Apps in Docker Compose

Both apps are included in the monitoring docker-compose.yml:
- `app-python` (merkulovlr05/devops-info) on port 8000
- `app-go` (merkulovlr05/devops-info-go) on port 8001

Both have `logging: "promtail"` and `app: "<name>"` labels for Promtail filtering.

### LogQL Queries

```logql
# All logs from Python app
{app="devops-python"}

# Only errors
{app="devops-python"} |= "ERROR"

# Parse JSON and filter by level
{app="devops-python"} | json | level="INFO"

# Logs from all apps
{app=~"devops-.*"}

# Request rate per app
sum by (app) (rate({app=~"devops-.*"} [1m]))

# Error count by app
sum by (app) (count_over_time({app=~"devops-.*"} |= "ERROR" [5m]))
```

---

## Task 3: Dashboard (2 pts)

### Panels

1. **Logs Table** — `{app=~"devops-.*"}` — Recent logs from all apps
2. **Request Rate** — `sum by (app) (rate({app=~"devops-.*"} [1m]))` — Time series of logs/second
3. **Error Logs** — `{app=~"devops-.*"} | json | level="ERROR"` — Filtered error logs
4. **Log Level Distribution** — `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))` — Pie chart of log levels

---

## Task 4: Production Readiness (1 pt)

### Resource Limits

All services have `deploy.resources` with CPU and memory limits:
- Loki: 1 CPU / 1G RAM
- Grafana: 1 CPU / 512M RAM
- Promtail: 0.5 CPU / 512M RAM
- Apps: 0.5 CPU / 256M RAM

### Security

- `GF_AUTH_ANONYMOUS_ENABLED=false` — No anonymous access
- Admin password via environment variable from `.env` file (not committed)
- `.env` added to `.gitignore`

### Health Checks

- Loki: `wget http://localhost:3100/ready`
- Grafana: `curl http://localhost:3000/api/health`
- Both with 10s interval, 5 retries, start_period for grace

---

## Bonus: Ansible Automation (2.5 pts)

### Role Structure

```
roles/monitoring/
├── defaults/main.yml          # Versions, ports, retention
├── tasks/main.yml             # Setup + deploy
├── templates/
│   ├── docker-compose.yml.j2
│   ├── loki-config.yml.j2
│   └── promtail-config.yml.j2
└── meta/main.yml              # Depends on docker role
```

### Key Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `monitoring_loki_version` | 3.0.0 | Loki image tag |
| `monitoring_grafana_version` | 12.3.1 | Grafana image tag |
| `monitoring_retention_period` | 168h | Log retention (7 days) |
| `monitoring_grafana_admin_password` | admin | Grafana password |

### Deployment

```bash
ansible-playbook playbooks/deploy_monitoring.yml
```

The role:
1. Creates directory structure
2. Templates all config files with Jinja2
3. Pulls and deploys via docker compose
4. Waits for Loki and Grafana health checks
5. Configures Loki data source in Grafana via API

### Loki vs Elasticsearch

- Loki indexes only labels, not full text → much less storage
- Loki uses LogQL (similar to PromQL), Elasticsearch uses its own DSL
- Loki is simpler to operate (no cluster management for basic setup)
- Elasticsearch better for full-text search at massive scale

### Research Answers

**How is Loki different from Elasticsearch?**
Loki only indexes metadata (labels), not log content. This makes it cheaper to run but requires knowing what to search for. Elasticsearch indexes everything.

**What are log labels and why do they matter?**
Labels are key-value pairs (like `app=devops-python`) that identify log streams. They're used for stream selection in queries and are the primary way to filter logs efficiently.

**How does Promtail discover containers?**
Via Docker service discovery (`docker_sd_configs`), connecting to the Docker socket to list running containers and their metadata. Relabeling rules extract useful labels from Docker metadata.
