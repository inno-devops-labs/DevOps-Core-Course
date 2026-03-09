# Lab 7 — Observability & Logging with Loki Stack

## 1. Architecture

- **Loki**: log storage and query engine (TSDB on filesystem, 7‑day retention).
- **Promtail**: collects container logs from Docker and ships them to Loki.
- **Grafana**: visualizes logs and dashboards using LogQL.
- **App (FastAPI)**: `devops-info-service` container, logging JSON to stdout.
- All services run in `lab7c/docker-compose.yml` on a shared `logging` network.

## 2. Setup Guide

### 2.1 Stack deployment

```bash
cd monitoring
docker compose up -d
docker compose ps
```

Services:
- `loki` on `3100`
- `promtail` on `9080`
- `grafana` on `3000`
- `app-python` on `8000` (mapped to container 5000)

### 2.2 Verification

```bash
# Loki readiness
curl http://localhost:3100/ready

# Promtail targets
curl http://localhost:9080/targets

# Open Grafana (local)
http://localhost:3000
```

In Grafana:
1. **Connections → Data sources → Add data source → Loki**
2. URL: `http://loki:3100`
3. **Save & Test** → “Data source connected”
4. Go to **Explore**, choose **Loki**, run `{job="docker"}`.

## 3. Configuration

### 3.1 Docker Compose (`lab7c/docker-compose.yml`)

- Defines network `logging` and volumes `loki-data`, `grafana-data`.
- **Loki**:
  - Image `grafana/loki:3.0.0`
  - Mounts `./loki/config.yml` to `/etc/loki/config.yml`
  - Persists data in `loki-data:/loki`
  - Health check on `/ready`
  - Resource limits and reservations set.
- **Promtail**:
  - Image `grafana/promtail:3.0.0`
  - Mounts `./promtail/config.yml`
  - Mounts `/var/lib/docker/containers` and `/var/run/docker.sock` read‑only.
- **Grafana**:
  - Image `grafana/grafana:12.3.1`
  - Port `3000:3000`
  - Admin user/password via env (for dev: `admin` / `${GRAFANA_ADMIN_PASSWORD:-admin}`).
  - Health check on `/api/health`, resource limits.
- **app-python**:
  - Image `tsixphoenix/devops-info-python:latest`
  - Port `8000:5000`
  - Labels `logging="promtail"`, `app="devops-python"` for Promtail/Loki labels.

### 3.2 Loki (`lab7c/loki/config.yml`)

- `auth_enabled: false` for local testing.
- `server.http_listen_port: 3100`.
- `common`:
  - `path_prefix: /loki`
  - filesystem storage for chunks and rules.
  - in‑memory ring for a single instance.
- `schema_config`:
  - `store: tsdb`, `object_store: filesystem`, `schema: v13`, daily index.
- `storage_config`:
  - `tsdb_shipper` index in `/loki/index` with cache.
  - filesystem chunks in `/loki/chunks`.
- `limits_config.retention_period: 168h` (7 days).
- `compactor`:
  - cleans up old logs with `retention_enabled: true`.

### 3.3 Promtail (`lab7c/promtail/config.yml`)

- `server.http_listen_port: 9080`.
- `positions` stored in `/tmp/positions.yaml`.
- `clients` send to `http://loki:3100/loki/api/v1/push`.
- `scrape_configs` for **Docker**:
  - `docker_sd_configs` on `unix:///var/run/docker.sock`.
  - `relabel_configs`:
    - `container` label from `__meta_docker_container_name`.
    - `app` label from container label `app`.
    - `logging` label from container label `logging`.

## 4. Application Logging (JSON)

In `lab3c/app_python/app.py`:
- Switched to **JSON log lines** using the standard `logging` module.
- HTTP middleware logs:
  - `timestamp`, `level`, `service`, `method`, `path`, `status`, `client_ip`, `user_agent`.
- Logs are written to stdout and collected by Docker, then by Promtail.

Example JSON log line:
```json
{
  "timestamp": "2026-03-05T12:20:00Z",
  "level": "INFO",
  "service": "devops-info-service",
  "method": "GET",
  "path": "/health",
  "status": 200,
  "client_ip": "127.0.0.1",
  "user_agent": "curl/8.6.0",
  "message": "request"
}
```

Screenshots used in the report are stored in `lab7c/docs/`, for example:
- `lab7c/docs/grafana-explore.png` — Explore view with `{app="devops-python"}`.
- `lab7c/docs/grafana-dashboard.png` — dashboard with all four panels.

## 5. Dashboard & LogQL

### 5.1 Explore queries

In Grafana Explore (Loki data source):

- All logs for Python app:
```logql
{app="devops-python"}
```

- Only error logs:
```logql
{app="devops-python"} |= "ERROR"
```

- Parse JSON and filter by method:
```logql
{app="devops-python"} | json | method="GET"
```

### 5.2 Dashboard panels

Dashboard panels created (LogQL examples):

1. **Logs Table** (all apps):
   ```logql
   {app=~"devops-.*"}
   ```
2. **Request Rate** (time series):
   ```logql
   sum by (app) (rate({app=~"devops-.*"}[1m]))
   ```
3. **Error Logs**:
   ```logql
   {app=~"devops-.*"} | json | level="ERROR"
   ```
4. **Log Level Distribution**:
   ```logql
   sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))
   ```

## 6. Production Configuration

- **Resource limits**: all services have `deploy.resources` limits and reservations.
- **Grafana security**:
  - Anonymous access disabled (`GF_AUTH_ANONYMOUS_ENABLED=false`).
  - Admin credentials configured via environment variables / `.env`.
- **Health checks**:
  - Loki: `/ready` endpoint.
  - Grafana: `/api/health` endpoint.
- **Retention**:
  - Loki configured for 7 days (`retention_period: 168h`) with compactor cleanup.

## 7. Testing

1. Start stack: `docker compose up -d`.
2. Generate logs:
   ```bash
   for i in {1..20}; do curl http://localhost:8000/; done
   for i in {1..20}; do curl http://localhost:8000/health; done
   ```
3. In Grafana Explore, run:
   - `{app="devops-python"}`
   - `{app="devops-python"} | json | method="GET"`
   - `{app="devops-python"} | json | level="ERROR"`
4. Check dashboard panels render data.

## 8. Challenges

- **Docker TSDB configuration**: required reading Loki 3.0 docs to use `tsdb` with filesystem correctly.
- **Docker discovery**: Promtail needed correct Docker SD and relabeling to get `app` and `container` labels.
- **JSON logging**: changing logging format without breaking existing behavior and keeping logs parseable in Loki.

