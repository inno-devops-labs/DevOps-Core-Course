# LAB07 — Observability & Logging with Loki Stack

## Architecture

```
┌─────────────┐   stdout/stderr   ┌──────────────┐    push     ┌───────────┐
│  python-app │ ─────────────────▶│   Promtail   │───────────▶│   Loki    │
│ (port 8000) │                   │  (port 9080) │            │(port 3100)│
└─────────────┘                   └──────────────┘            └───────────┘
                                  reads via                          │
                               Docker socket                         │ LogQL
                                                                     ▼
                                                             ┌───────────────┐
                                                             │    Grafana    │
                                                             │  (port 3000)  │
                                                             └───────────────┘
```

**Components:**
- **Loki 3.0** — log storage backend using TSDB index (schema v13), 7-day retention
- **Promtail 3.0** — log collection agent, reads container stdout/stderr via Docker socket
- **Grafana 12.3** — visualization, dashboards, and log exploration
- **python-app** — Flask application with structured JSON logging

---

## Setup Guide

### Prerequisites
- Docker Desktop installed and running
- Docker Compose v2 (built into Docker Desktop)

### Step 1 — Clone the repository and navigate to the directory

```bash
cd monitoring
```

### Step 2 — Create the `.env` file with Grafana credentials

```bash
# PowerShell
Set-Content -Path .env -Value "GF_ADMIN_USER=admin`nGF_ADMIN_PASSWORD=SuperSecretPass123!"
```

> ⚠️ The `.env` file is listed in `.gitignore` and must never be committed to the repository.

### Step 3 — Build and start the stack

```bash
docker compose up -d --build
```

### Step 4 — Verify all services are running

```bash
docker compose ps
```

Expected output — all services should show `healthy` status:

```
NAME         IMAGE                    STATUS
grafana      grafana/grafana:12.3.1   Up (healthy)
loki         grafana/loki:3.0.0       Up (healthy)
promtail     grafana/promtail:3.0.0   Up
python-app   monitoring-python-app    Up
```

### Step 5 — Verify service endpoints

```bash
# Loki readiness check
curl http://localhost:3100/ready
# Expected: ready

# Promtail targets
curl http://localhost:9080/targets

# Grafana health
curl http://localhost:3000/api/health
```

### Step 6 — Configure Loki Data Source in Grafana

1. Open http://localhost:3000
2. Login: `admin` / password from `.env`
3. Navigate to **Connections → Data sources → Add data source**
4. Select **Loki**
5. Set URL: `http://loki:3100`
6. Click **Save & Test** — should show "Data source successfully connected"

---

## Configuration

### Loki (`loki/config.yml`)

```yaml
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
      store: tsdb
      object_store: filesystem
      schema: v13
      index:
        prefix: index_
        period: 24h

limits_config:
  retention_period: 168h
  allow_structured_metadata: true
```

**Key configuration decisions:**
- `store: tsdb` with `schema: v13` — the recommended storage format in Loki 3.0, significantly faster than the legacy `boltdb-shipper`
- `retention_period: 168h` — logs are stored for exactly 7 days
- `replication_factor: 1` with `inmemory` ring — appropriate for single-node development setup
- `filesystem` object store — simple local storage, no external dependencies needed

### Promtail (`promtail/config.yml`)

```yaml
server:
  http_listen_port: 9080

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels: ["__meta_docker_container_name"]
        regex: "/(.*)"
        target_label: "container"
      - source_labels: ["__meta_docker_container_label_app"]
        target_label: "app"
      - source_labels: ["__meta_docker_container_label_com_docker_compose_service"]
        target_label: "service"
      - replacement: "docker"
        target_label: "job"
```

**Key configuration decisions:**
- `docker_sd_configs` — automatically discovers all running containers via Docker socket, no manual configuration needed per container
- `relabel_configs` — extracts useful metadata from Docker labels and container metadata as Loki labels
- The `app` label is populated from Docker label `app: "devops-python"` defined in `docker-compose.yml`, enabling per-application log filtering

---

## Application Logging

The Flask application (`app/app.py`) implements structured JSON logging using a custom `JSONFormatter`:

```python
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        # Attach HTTP context fields if present
        for field in ["method", "path", "status_code", "client_ip", "duration_ms"]:
            if hasattr(record, field):
                log_record[field] = getattr(record, field)
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)
```

Every HTTP request is logged via `@app.after_request` hook with full context:

```json
{
  "timestamp": "2026-03-12T18:12:20.140682+00:00",
  "level": "INFO",
  "message": "HTTP request",
  "logger": "devops-python",
  "method": "GET",
  "path": "/health",
  "status_code": 200,
  "client_ip": "172.25.0.1",
  "duration_ms": 0.41
}
```

Error events include a full exception traceback:

```json
{
  "timestamp": "2026-03-12T18:12:20.140278+00:00",
  "level": "ERROR",
  "message": "Unhandled error occurred",
  "method": "GET",
  "path": "/error",
  "exception": "Traceback (most recent call last):\n  ...\nValueError: This is a test error"
}
```

**Application endpoints:**
- `GET /` — returns `{"status": "ok", "message": "Hello from DevOps Python App!"}`
- `GET /health` — returns health status with timestamp
- `GET /error` — intentionally raises a `ValueError` to generate ERROR-level logs

---

## Dashboard

The Grafana dashboard **"DevOps Logs"** contains 4 panels:

### Panel 1 — All App Logs
- **Visualization type:** Logs
- **Query:** `{app=~"devops-.*"}`
- **Purpose:** Shows all recent log lines from all application containers. The `=~` operator uses regex matching to capture all apps with names starting with `devops-`.

### Panel 2 — Request Rate
- **Visualization type:** Time series
- **Query:** `sum by (app) (rate({app=~"devops-.*"}[1m]))`
- **Purpose:** Displays log ingestion rate (logs per second) over time, grouped by application. Useful for detecting traffic spikes or anomalies.

### Panel 3 — Error Logs
- **Visualization type:** Logs
- **Query:** `{app=~"devops-.*"} | json | level="ERROR"`
- **Purpose:** Filters and displays only ERROR-level log entries. Uses `| json` pipeline to parse JSON log format, then filters by the `level` field.

### Panel 4 — Log Level Distribution
- **Visualization type:** Pie chart
- **Query:** `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))`
- **Purpose:** Shows the proportion of log entries by severity level (INFO vs ERROR) over the last 5 minutes. Useful for quick health assessment.

---

## Production Configuration

### Resource Limits

All services have CPU and memory constraints defined in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: "1.0"
      memory: 1G
    reservations:
      cpus: "0.5"
      memory: 512M
```

This prevents any single service from consuming all available system resources.

### Security

- `GF_AUTH_ANONYMOUS_ENABLED=false` — anonymous access to Grafana is disabled
- Admin credentials are stored in `.env` file (excluded from version control via `.gitignore`)
- `GF_USERS_ALLOW_SIGN_UP=false` — self-registration is disabled

### Health Checks

```yaml
# Loki
healthcheck:
  test: ["CMD-SHELL", "wget -q --tries=1 -O- http://localhost:3100/ready || exit 1"]
  interval: 15s
  timeout: 5s
  retries: 5
  start_period: 20s

# Grafana
healthcheck:
  test: ["CMD-SHELL", "wget -q --tries=1 -O- http://localhost:3000/api/health || exit 1"]
  interval: 15s
  timeout: 5s
  retries: 5
  start_period: 20s
```

Services that depend on Loki (Promtail, Grafana, python-app) use `condition: service_healthy` to ensure correct startup order.

### Log Retention

Logs are automatically deleted after 7 days (`retention_period: 168h`) via Loki's compactor.

---

## Testing

### Generate test traffic (PowerShell)

```powershell
# Normal requests
1..20 | ForEach-Object { Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing | Out-Null }
1..20 | ForEach-Object { Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing | Out-Null }

# Generate error logs
1..5 | ForEach-Object {
    Invoke-WebRequest -Uri "http://localhost:8000/error" -UseBasicParsing -ErrorAction SilentlyContinue | Out-Null
}

# Verify JSON log format
docker compose logs python-app | Select-Object -Last 10
```

### LogQL queries used for verification

```logql
# Query 1: All logs from all containers
{job="docker"}

# Query 2: All logs from python app
{app="devops-python"}

# Query 3: Only ERROR level logs
{app="devops-python"} | json | level="ERROR"

# Query 4: Filter by HTTP method
{app="devops-python"} | json | method="GET"

# Query 5: Request rate per second
rate({app="devops-python"}[1m])
```

---

## Challenges & Solutions

**Challenge 1: Loki 3.0 fails to start with `permission denied`**

Error: `mkdir /loki/data/rules: permission denied`

Root cause: Loki container runs as a non-root user by default and cannot create directories in the mounted volume.

Solution: Added `user: "0"` to the Loki service in `docker-compose.yml` to run as root inside the container.

---

**Challenge 2: Loki 3.0 schema configuration**

Loki 3.0 requires `store: tsdb` and `schema: v13`. The older `boltdb-shipper` format is deprecated and causes startup errors.

Solution: Used the correct schema configuration as documented in the Loki 3.0 migration guide.

---

**Challenge 3: Bash syntax not available on Windows**

Loop commands like `for i in {1..20}; do curl ...; done` do not work in PowerShell.

Solution: Used PowerShell equivalent: `1..20 | ForEach-Object { Invoke-WebRequest -Uri "..." -UseBasicParsing | Out-Null }`

---

**Challenge 4: Container name conflict on restart**

Error: `Conflict. The container name "/python-app" is already in use`

Solution: Removed the conflicting container with `docker rm -f python-app` before running `docker compose up -d`.