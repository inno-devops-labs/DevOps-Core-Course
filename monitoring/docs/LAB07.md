# Lab 07 — Observability & Logging with Loki Stack

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network: logging                   │
│                                                             │
│  ┌──────────────┐     ┌──────────────┐   ┌──────────────┐  │
│  │  app-python  │     │   Promtail   │   │    Grafana   │  │
│  │  port 8000   │────▶│  port 9080   │──▶│  port 3000   │  │
│  └──────────────┘     │  docker_sd   │   └──────┬───────┘  │
│         │             └──────┬───────┘          │          │
│         │ labels:            │ push             │ query    │
│         │ logging=promtail   ▼                  ▼          │
│         └──────────▶ ┌──────────────┐                      │
│    stdout/stderr      │    Loki      │◀─────────────────────┘
│    (Docker logs)      │  port 3100   │                      │
│                       │  TSDB store  │                      │
│                       └──────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

**Data flow:**
1. `app-python` writes JSON logs to stdout
2. Docker captures logs as container log files under `/var/lib/docker/containers/`
3. Promtail discovers containers via Docker socket, reads their logs, and ships to Loki
4. Loki stores logs indexed by labels in TSDB (fast range-scan queries)
5. Grafana queries Loki via HTTP and displays dashboards

---

## Setup Guide

### Prerequisites

- Docker Engine 24+ with Compose v2 plugin
- Linux host (Promtail needs `/var/lib/docker/containers` and the Docker socket)

### 1 — Clone and configure

```bash
cd monitoring
cp .env.example .env
# Edit .env — set GF_ADMIN_USER and GF_ADMIN_PASSWORD
```

### 2 — Deploy the stack

```bash
docker compose up -d
docker compose ps
```

Expected output (all services healthy):

```
NAME          IMAGE                        STATUS
app-python    112005/devops-lab3-python    Up
grafana       grafana/grafana:12.3.1       Up (healthy)
loki          grafana/loki:3.0.0           Up (healthy)
promtail      grafana/promtail:3.0.0       Up
```

### 3 — Verify services

```bash
# Loki ready
curl http://localhost:3100/ready
# → ready

# Promtail targets (should list app-python)
curl -s http://localhost:9080/targets | python3 -m json.tool | grep "container"

# Grafana API health
curl http://localhost:3000/api/health
```

### 4 — Access Grafana

Open http://localhost:3000, login with the credentials from `.env`.

The Loki data source is automatically provisioned via `grafana/provisioning/datasources/loki.yml`.

Navigate to **Explore → Loki** and run `{app="devops-python"}` to confirm logs arrive.

---

## Configuration

### Loki (`loki/config.yml`)

Key design decisions:

| Setting | Value | Reason |
|---------|-------|--------|
| `auth_enabled` | `false` | Single-tenant dev setup; no per-tenant auth needed |
| `store` | `tsdb` | TSDB is the recommended index for Loki 3.0+; up to 10× faster queries |
| `schema` | `v13` | Required for TSDB index type |
| `object_store` | `filesystem` | Sufficient for single-instance; swap to S3 for HA |
| `retention_period` | `168h` | 7 days — keeps storage bounded in dev |
| `compactor.retention_enabled` | `true` | Required to enforce the retention policy |
| `analytics.reporting_enabled` | `false` | No telemetry sent to Grafana Cloud |

**Snippet:**

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

compactor:
  working_directory: /loki/compactor
  retention_enabled: true
```

### Promtail (`promtail/config.yml`)

Key design decisions:

| Setting | Value | Reason |
|---------|-------|--------|
| `docker_sd_configs` | Docker socket | Automatic container discovery; no manual job per service |
| `filters: logging=promtail` | Label filter | Only scrape containers that opt-in via the Docker label |
| `relabel_configs` | Extracts `container`, `app` | Enriches each log stream with useful labels for LogQL filtering |

**Snippet:**

```yaml
scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
        filters:
          - name: label
            values: ["logging=promtail"]
    relabel_configs:
      - source_labels: [__meta_docker_container_name]
        regex: "/(.*)"
        target_label: container
      - source_labels: [__meta_docker_container_label_app]
        target_label: app
```

The `logging=promtail` label on each app service in `docker-compose.yml` acts as an opt-in:

```yaml
labels:
  logging: "promtail"
  app: "devops-python"
```

---

## Application Logging

### Implementation (`app_python/app.py`)

The Python app uses `python-json-logger` to emit structured JSON to stdout, which Docker captures and Promtail ingests.

**Custom formatter** — adds `timestamp`, `level`, and `service` to every log record:

```python
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = datetime.now(timezone.utc).isoformat()
        log_record["level"] = record.levelname
        log_record["service"] = "devops-info-service"
```

**Request/response hooks** — capture HTTP context on every request:

```python
@app.before_request
def log_request():
    g.start_time = datetime.now(timezone.utc)
    logger.info("http_request", extra={
        "method": request.method,
        "path": request.path,
        "client_ip": request.remote_addr,
    })

@app.after_request
def log_response(response):
    delta = datetime.now(timezone.utc) - g.start_time
    logger.info("http_response", extra={
        "status_code": response.status_code,
        "duration_ms": round(delta.total_seconds() * 1000, 2),
    })
    return response
```

**Sample log output:**

```json
{"timestamp": "2024-12-01T10:00:00+00:00", "level": "INFO", "name": "app", "message": "http_request", "method": "GET", "path": "/health", "client_ip": "172.18.0.1"}
{"timestamp": "2024-12-01T10:00:00+00:00", "level": "INFO", "name": "app", "message": "http_response", "status_code": 200, "duration_ms": 1.23}
```

### Dependency

Added to `requirements.txt`:

```
python-json-logger==2.0.7
```

---

## Dashboard

### Panel 1 — All Logs (Logs visualization)

Shows the live log stream from all monitored apps.

```logql
{app=~"devops-.*"}
```

**Purpose:** Quick overview / tail of recent activity.

### Panel 2 — Request Rate (Time series)

Shows log ingestion rate per app in logs/second.

```logql
sum by (app) (rate({app=~"devops-.*"}[1m]))
```

**Purpose:** Detects traffic spikes and burst patterns.

### Panel 3 — Error Logs (Logs visualization)

Filters to JSON-parsed ERROR records only.

```logql
{app=~"devops-.*"} | json | level="ERROR"
```

**Purpose:** Immediate signal when errors occur; reduces noise.

### Panel 4 — Log Level Distribution (Bar chart / Pie chart)

Counts log records grouped by `level` label.

```logql
sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))
```

**Purpose:** Shows whether INFO traffic overwhelms ERROR signals; validates that JSON parsing works.

### Additional useful queries

```logql
# HTTP 5xx responses
{app="devops-python"} | json | status_code >= 500

# Slow requests (>100 ms)
{app="devops-python"} | json | duration_ms > 100

# Request rate by path
sum by (path) (rate({app="devops-python"} | json [5m]))
```

---

## Production Config

### Security

| Measure | Implementation |
|---------|----------------|
| Anonymous access disabled | `GF_AUTH_ANONYMOUS_ENABLED=false` in Grafana env |
| Admin credentials from secrets | `GF_SECURITY_ADMIN_USER/PASSWORD` read from `.env` file |
| `.env` not committed | Covered by `.gitignore` |
| Grafana embedding blocked | `GF_SECURITY_ALLOW_EMBEDDING=false` |
| Telemetry disabled | `GF_ANALYTICS_REPORTING_ENABLED=false` in Loki config |
| Docker socket read-only | `/var/run/docker.sock:ro` in Promtail |

### Resource limits

All services have `deploy.resources.limits` to prevent runaway consumption:

| Service | Memory limit | CPU limit |
|---------|-------------|-----------|
| Loki | 1G | 1.0 |
| Promtail | 256M | 0.5 |
| Grafana | 512M | 1.0 |
| app-python | 256M | 0.5 |

### Health checks

Both Loki and Grafana include Docker `healthcheck` blocks:

```yaml
healthcheck:
  test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:3100/ready || exit 1"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 30s
```

Promtail depends on `loki: condition: service_healthy`, so it only starts after Loki passes its health check.

### Log retention

Loki retains logs for 7 days (`retention_period: 168h`) with the compactor enforcing deletion. Adjust in `loki/config.yml` under `limits_config`.

---

## Testing

### Smoke test

```bash
# Deploy
cd monitoring
docker compose up -d

# Wait for health checks
docker compose ps

# Loki ready
curl http://localhost:3100/ready

# Grafana health
curl http://localhost:3000/api/health

# Promtail targets (lists scraped containers)
curl -s http://localhost:9080/targets

# Generate traffic
for i in $(seq 1 20); do curl -s http://localhost:8000/ > /dev/null; done
for i in $(seq 1 20); do curl -s http://localhost:8000/health > /dev/null; done

# Query logs via Loki API
curl -G 'http://localhost:3100/loki/api/v1/query_range' \
  --data-urlencode 'query={app="devops-python"}' \
  --data-urlencode 'limit=5' | python3 -m json.tool
```

### Verify JSON logging

```bash
docker logs devops-python 2>&1 | head -5 | python3 -m json.tool
```

Expected: pretty-printed JSON with `timestamp`, `level`, `service`, `message` fields.

### Idempotency check (Docker Compose)

```bash
docker compose up -d  # second run — no containers recreated
```

### Ansible role idempotency (bonus)

```bash
# First run
ansible-playbook playbooks/deploy-monitoring.yml

# Second run — all tasks should show ok, none changed
ansible-playbook playbooks/deploy-monitoring.yml
```

---

## Challenges

### 1 — Loki 3.0 config schema changes

**Problem:** Loki 3.0 deprecated the `boltdb-shipper` index type and several top-level config keys changed from earlier versions.

**Solution:** Used the `tsdb` index with `schema: v13` (the current recommended schema). The `common:` block in Loki 3.0 simplifies storage config by providing shared path/storage defaults, reducing repetition.

### 2 — Promtail Docker socket and container filesystem access

**Problem:** Promtail needs `/var/lib/docker/containers` mounted read-only to read actual log files, but also needs the Docker socket to perform container service discovery. These are different mount purposes.

**Solution:** Mounted both explicitly in the compose file with `:ro` flags where possible. The socket is read-only for discovery; actual log files are also `:ro`.

### 3 — JSON log double-encoding in Promtail

**Problem:** Loki/Promtail stores the raw log line as the `line` field. When Grafana's `| json` parser runs, it parses the outer Docker log wrapper, not the inner JSON payload, depending on driver.

**Solution:** Configured Promtail with `docker_sd_configs` (rather than `file_sd` with Docker log paths), which handles Docker's JSON log driver output automatically and exposes the inner log line correctly.

### 4 — Grafana data source provisioning timing

**Problem:** If Grafana starts before Loki is healthy, the provisioned datasource `Save & Test` step can fail silently.

**Solution:** Added `depends_on: loki: condition: service_healthy` in the compose file, ensuring Grafana only starts once Loki passes its health check.
