# LAB07 — Observability & Logging with Loki Stack

## Architecture

### Components
- **devops-info-service (FastAPI)** — application that writes structured JSON logs to stdout
- **Promtail** — collects container logs from Docker and ships them to Loki
- **Loki** — stores logs and provides LogQL query API
- **Grafana** — UI for log exploration and dashboards (Loki datasource)

### Diagram (data flow)

```text
+--------------------------+
| devops-info-service      |
| (Docker container)       |
| JSON logs -> stdout      |
+------------+-------------+
             |
             | Docker logs (/var/lib/docker/containers/*/*.log)
             v
+------------+-------------+
| Promtail (Docker)        |
| - docker_sd_configs      |
| - filters: logging=...   |
| - relabel: app, container|
+------------+-------------+
             |
             | push HTTP
             v
+------------+-------------+
| Loki (Docker)            |
| - TSDB storage           |
| - retention 7d           |
+------------+-------------+
             |
             | LogQL queries
             v
+--------------------------+
| Grafana (Docker)         |
| - Loki datasource        |
| - Dashboard panels       |
+--------------------------+
```

## Setup Guide

> Repository structure:
> 
- `monitoring/docker-compose.yml`
- `monitoring/loki/config.yml`
- `monitoring/promtail/config.yml`
- `monitoring/docs/LAB07.md`

### 1) Start stack

From `monitoring/` directory:

```bash
docker compose up -d
docker compose ps
```

### 2) Verify Loki/Promtail are reachable

```bash
curl -s http://localhost:3100/ready
curl -s http://localhost:9080/targets
```

### 3) Open Grafana and add Loki datasource

- Grafana: `http://localhost:3002` (port configured via `GF_SERVER_HTTP_PORT`)
- Add datasource:
    - **Connections → Data sources → Loki**
    - URL: `http://loki:3100`
    - Save & Test

### 4) Generate logs

```bash
for i in {1..20}; do curl -s http://localhost:8000/ >/dev/null; done
for i in {1..20}; do curl -s http://localhost:8000/health >/dev/null; done
```

### 5) Confirm logs in Explore

In Grafana → Explore → Loki:

```
{app="devops-python"}
```

**Screenshots:**

![](/monitoring/docs/screenshots/grafana_logs.png)
![](/monitoring/docs/screenshots/grafana_containers.png)

## Configuration

**Goal:** local single-node Loki with TSDB + filesystem storage and retention.

Snippet (`monitoring/loki/config.yml`):

```yaml
auth_enabled: false

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

**Why:**

- `auth_enabled: false` — simplifies local lab setup
- `store: tsdb` + `object_store: filesystem` — single-node storage without external dependencies
- `retention_period: 168h` — required 7 days retention policy

---

## Promtail config (highlights)

**Goal:** scrape Docker container logs and attach meaningful labels (`app`, `container`).

Snippet (`monitoring/promtail/config.yml`):

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
            values: ["logging=promtail"]

    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        target_label: container
        regex: '/(.*)'
        replacement: '$1'

      - source_labels: ['__meta_docker_container_label_app']
        target_label: app
```

**Why:**

- `docker_sd_configs` + `docker.sock` — dynamic discovery of containers
- `filters logging=promtail` — avoid collecting logs from every container (only targeted services)
- relabel rules:
    - `container` label helps identify source container
    - `app` label enables app-level queries (`{app="devops-python"}`)

## Application Logging

### JSON logging requirement

The app logs are structured as JSON for easy parsing and querying in Loki/Grafana.

**Implemented fields:**

- `asctime`, `levelname`, `name`, `message`
- `service`, `version`, `hostname`
- request context (for HTTP requests):
    - `method`, `path`, `status_code`, `client_ip`, `duration_ms`

### Implementation approach

- Use `python-json-logger` to format logs as JSON.
- Add `DefaultFieldsFilter` to prevent missing-field errors (ensures default values exist for log fields).
- Add FastAPI middleware to log each request with timing and status code.

Snippet (`app.py`):

```python
class DefaultFieldsFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, "service"):
            record.service = SERVICE_NAME
        if not hasattr(record, "version"):
            record.version = SERVICE_VERSION
        if not hasattr(record, "hostname"):
            record.hostname = socket.gethostname()
        for k in ("method", "path", "status_code", "client_ip", "duration_ms"):
            if not hasattr(record, k):
                setattr(record, k, None)
        return True
```

Middleware snippet:

```python
@app.middleware("http")
async def access_log_middleware(request: Request, call_next):
    start = time.perf_counter()
    client_ip = request.client.host if request.client else "unknown"
    response = await call_next(request)
    duration_ms = int((time.perf_counter() - start) * 1000)

    logger.info(
        "http_request",
        extra={
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "hostname": socket.gethostname(),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "client_ip": client_ip,
            "duration_ms": duration_ms,
        },
    )
    return response
```

**Screenshots:**

![](/monitoring/docs/screenshots/log_line.png)

## Dashboard

Dashboard contains 4 panels required by the lab.

### Panel 1 — Logs Table (all apps)

Shows recent logs from all matching apps.

Query:

```graphql
{app=~"devops-.*"}
```

Explanation:

- Uses regex to include multiple apps (python + bonus, if present).

---

### Panel 2 — Request Rate (logs per second)

Time series showing how many logs per second are produced per app.

Query:

```graphql
sum by (app) (rate({app=~"devops-.*"}[1m]))
```

Explanation:

- `rate([...])` estimates log lines per second over the last minute.
- `sum by(app)` groups the series by application label.

---

### Panel 3 — Error logs

Shows only error logs.

Query:

```graphql
{app=~"devops-.*"} | json | level="error"
```

Alternative (if you store uppercase):

```graphql
{app=~"devops-.*"} | json | level=~"error|ERROR"
```

Explanation:

- Parse JSON (`| json`) and filter by severity field.

---

### Panel 4 — Log level distribution

Counts logs by severity level.

Query:

```
sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))
```

Explanation:

- `count_over_time` counts how many log lines over a time window.
- Group by the `level` field.

**Screenshot:** 

![](/monitoring/docs/screenshots/dashboard.png)

## Production Config

### Security (Grafana authentication)

Anonymous auth is disabled, admin user/password are set via `.env` (not committed).

Snippet (`docker-compose.yml`):

```yaml
environment:
  - GF_AUTH_ANONYMOUS_ENABLED=false
  - GF_SECURITY_ADMIN_USER=${GRAFANA_ADMIN_USER}
  - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
```

`.env` example (NOT committed):

```
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=********
```

![](/monitoring/docs/screenshots/auth.png)

### Resources

Resource limits configured for each service.

Snippet (`docker-compose.yml`):

```yaml
deploy:
  resources:
    limits:
      cpus: "0.50"
      memory: 512M
```

### Retention

Loki retention is configured to 7 days (`168h`).

Snippet:

```yaml
limits_config:
  retention_period: 168h
```

### Healthchecks

Loki and Grafana healthchecks ensure container health status is visible.

Snippet:

```yaml
healthcheck:
  test: ["CMD-SHELL", "wget -qO- http://localhost:3100/ready || exit 1"]
  interval: 10s
  timeout: 3s
  retries: 10
```

Grafana:

```yaml
healthcheck:
  test: ["CMD-SHELL", "wget -qO- http://localhost:3002/api/health | grep -q ok"]
  interval: 10s
  timeout: 5s
  retries: 10
```

**Screenshot:** 

![](/monitoring/docs/screenshots/docker_compose_ps.png)

## Testing

### 1) Check containers are up

```bash
docker compose ps
```

### 2) Health endpoints

```bash
curl -s http://localhost:3100/ready
curl -s http://localhost:3002/api/health
```

### 3) Promtail targets

```bash
curl -s http://localhost:9080/targets
```

### 4) Generate traffic and confirm logs

```bash
curl -s http://localhost:8000/ >/dev/null
curl -s http://localhost:8000/health >/dev/null
```

### 5) Example LogQL queries

1. All logs of python app:

```graphql
{app="devops-python"}
```

![](/monitoring/docs/screenshots/query2.png)

2. Only errors:

```graphql
{app="devops-python"} | json | level="error"
```

![](/monitoring/docs/screenshots/query3.png)

3. Filter by request method:

```graphql
{app="devops-python"} | json | method="GET"
```

![](/monitoring/docs/screenshots/query1.png)

## Challenges

### 1) JSON logger crash due to missing fields

**Problem:** `python-json-logger` formatter may crash if referenced fields are not present on every record.

**Solution:** Added `DefaultFieldsFilter` that sets defaults for required fields (`method`, `path`, etc.) so that non-request logs (e.g., startup logs) do not break formatting.

### 2) Error panel returned “No data”

**Problem:** LogQL filtered by the wrong field name/value (e.g., using `levelname="ERROR"` while logs had `level="error"`).

**Solution:** Verified field names in Grafana “Log line” view and updated LogQL to match actual JSON keys/values:

```graphql
{app=~"devops-.*"} | json | level="error"
```

### 3) Collecting too many container logs

**Problem:** Promtail scraped logs from all containers by default.

**Solution:** Added docker discovery filter to only scrape containers labeled `logging=promtail`.