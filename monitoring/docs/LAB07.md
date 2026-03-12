## 1. Architecture

- **Stack:** Loki 3.0 + Promtail 3.0 + Grafana 12.3 + two apps (Python, Go).
- **Flow:** Docker containers write logs → Promtail discovers containers via Docker socket → Promtail pushes logs to Loki → Grafana reads from Loki → dashboards & Explore show logs.
- **Labels:** Container name (`container`), app name (`app`), and log level/fields from JSON logs are used for filtering and aggregations.
- **Storage:** Loki uses TSDB + filesystem backend with 7‑day retention (schema v13, single instance).

## 2. Setup Guide

### 2.1 Prerequisites

- Docker and Docker Compose v2 installed.
- Python and Go images from previous labs built locally:
  - `devops-info-python:lab03` (Flask app).
  - `devops-info-go:lab03` (bonus app).

### 2.2 Start Monitoring Stack (local machine)

```bash
cd DevOps-Core-Course/monitoring
docker compose up -d
docker compose ps
```

Verify services:

```bash
curl http://localhost:3100/ready       # Loki
curl http://localhost:9080/targets     # Promtail
curl http://localhost:3000/api/health  # Grafana
```

Access Grafana UI in browser: `http://localhost:3000`.

## 3. Configuration

### 3.1 Docker Compose

- **Services:** `loki`, `promtail`, `grafana`, `app-python`, `app-bonus` on a shared `logging` network.
- **Volumes:** `loki-data` for Loki TSDB data, `grafana-data` for dashboards and settings.
- **Resource limits:** CPU and memory limits/reservations are set for each service to avoid resource exhaustion.
- **Health checks:** HTTP checks on Loki (`/ready`) and Grafana (`/api/health`) plus Promtail `/ready`.

### 3.2 Loki (`monitoring/loki/config.yml`)

- `auth_enabled: false` for local development.
- `server.http_listen_port: 3100`.
- `common.storage.filesystem` with chunk and rule directories under `/var/loki`.
- `schema_config` uses **schema v13** with `store: tsdb` and `object_store: filesystem`.
- `limits_config.retention_period: 168h` (7 days).
- `compactor` with `retention_enabled: true` to delete old logs.

### 3.3 Promtail (`monitoring/promtail/config.yml`)

- `server.http_listen_port: 9080` for readiness/targets endpoints.
- `clients` send to `http://loki:3100/loki/api/v1/push`.
- `docker_sd_configs` discovers Docker containers via `/var/run/docker.sock`.
- `relabel_configs` extract:
  - `container` label from `__meta_docker_container_name` (without leading `/`).
  - `container_id` from `__meta_docker_container_id`.
- `pipeline_stages.match` keeps only containers with label `logging="promtail"` so only selected apps are scraped.

## 4. Application Logging (Python App)

- Logging switched from plain text to **JSON** using a custom `JSONFormatter` for Python `logging`.
- Each log line includes:
  - `timestamp`, `level`, and `message`.
  - HTTP context: method, path, status code, client IP.
  - Service metadata: service name, version.
- Flask hooks:
  - `@app.before_request` logs incoming requests.
  - `@app.after_request` logs responses.
  - Error handlers log exceptions with level `ERROR`.
- JSON fields can be parsed with `| json` in LogQL and used in filters/aggregations.

## 5. Dashboard (Grafana)

### 5.1 Data Source

1. Open Grafana → **Connections → Data sources → Add data source**.
2. Choose **Loki**.
3. URL: `http://loki:3100`.
4. Click **Save & Test** (should report “Data source connected”).

### 5.2 Panels and Queries

Dashboard contains 4 panels using data source **Loki**:

1. **Logs Table** (Logs):
   - Query: `{app=~"devops-.*"}`.
   - Shows recent logs from all apps.
2. **Request Rate** (Time series):
   - Query: `sum by (app) (rate({app=~"devops-.*"}[1m]))`.
   - Shows logs per second per app.
3. **Error Logs** (Logs):
   - Query: `{app=~"devops-.*"} | json | level="ERROR"`.
   - Shows only error-level entries.
4. **Log Level Distribution** (Stat / Pie):
   - Query: `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))`.
   - Shows count of logs per level (INFO, ERROR, etc.).

## 6. Production Configuration

- **Resource limits:** All services have CPU and memory limits/reservations in `docker-compose.yml`.
- **Grafana security:**
  - Anonymous access disabled: `GF_AUTH_ANONYMOUS_ENABLED=false`.
  - Admin user/password provided via environment (`GF_SECURITY_ADMIN_USER`, `GF_SECURITY_ADMIN_PASSWORD`).
  - For real deployments, set these through a `.env` file and do not commit secrets.
- **Retention:** Loki keeps logs for 7 days via `limits_config.retention_period`.
- **Health checks:** Docker health checks ensure Loki, Promtail, and Grafana are healthy before use.

## 7. Testing

### 7.1 Generate Logs

```bash
# Python app
for i in {1..20}; do curl http://localhost:8000/; done
for i in {1..20}; do curl http://localhost:8000/health; done

# Bonus Go app (if available)
for i in {1..20}; do curl http://localhost:8001/; done
for i in {1..20}; do curl http://localhost:8001/health; done
```

### 7.2 LogQL Queries (Grafana → Explore)

- All logs for Python app:

```logql
{app="devops-python"}
```

- Only errors:

```logql
{app="devops-python"} |= "ERROR"
```

- Filter by JSON fields:

```logql
{app="devops-python"} | json | method="GET"
```

- Request rate by app:

```logql
sum by (app) (rate({app=~"devops-.*"}[1m]))
```

## 8. Challenges

- **Loki TSDB config:** Needed to carefully follow Loki 3.0 documentation for `common`, `schema_config`, and `storage_config` sections to avoid startup errors.
- **Docker discovery in Promtail:** Getting Docker service discovery and relabeling right was required so that container names appear cleanly as labels.
- **JSON logging integration:** Converting existing Flask logging to structured JSON while keeping request context required a custom formatter and hooks.
- **Security vs convenience:** Anonymous Grafana is very convenient for local testing, but the lab required turning it off and using environment variables for admin credentials.

