# Lab 7 — Observability & Logging with Loki Stack

## 1. Architecture

The logging stack consists of:

- **Loki**: central log store with TSDB + filesystem backend
- **Promtail**: log collector using Docker service discovery
- **Grafana**: UI for querying logs and building dashboards
- **App Python**: existing `devops-info-service` container from Labs 1–2

High‑level flow:

1. `app-python` container writes JSON logs to stdout.
2. Docker stores container logs under `/var/lib/docker/containers`.
3. Promtail discovers containers via the Docker socket, filters by label `logging=promtail`, and ships logs to Loki.
4. Loki stores logs on disk with 7‑day retention using TSDB (schema v13).
5. Grafana queries Loki and visualizes logs/dashboards.

## 2. Setup Guide

From repository root:

```bash
cd monitoring

# Start stack (detached)
docker compose up -d

# Check containers
docker compose ps
```

Verification commands (expected to be run locally when you test):

```bash
# Loki readiness
curl http://localhost:3100/ready

# Promtail targets
curl http://localhost:9080/targets

# Grafana UI
open http://localhost:3000   # or manually in browser
```

In Grafana:

1. Go to **Connections → Data sources → Add data source → Loki**.
2. URL: `http://loki:3100`.
3. Click **Save & test** (should show “Data source connected”).
4. Open **Explore**, select **Loki** data source.
5. Query `{job="docker"}` or `{app="devops-python"}` to see logs.

> **Screenshot to take:** Grafana Explore view showing logs from at least 3 containers (e.g. `loki`, `promtail`, `grafana`, `app-python`). Save as `monitoring/docs/screenshots/01-grafana-explore-multi-containers.png`.

## 3. Configuration

### 3.1 Docker Compose (`monitoring/docker-compose.yml`)

Key points:

- Single `logging` network shared by Loki, Promtail, Grafana, and `app-python`.
- Volumes:
  - `loki-data` for Loki TSDB data.
  - `grafana-data` for Grafana state.
  - `promtail-positions` for Promtail read positions.
- **Resource limits** and **reservations** for all services (cpus + memory).
- **Healthchecks**:
  - Loki: `http://localhost:3100/ready`
  - Promtail: `http://localhost:9080/ready`
  - Grafana: `http://localhost:3000/api/health`
- `app-python` service:
  - Image: `almax07082005/devops-info-service:latest`
  - Port mapping `8000:8000`
  - Labels: `logging="promtail"`, `app="devops-python"`

### 3.2 Loki (`monitoring/loki/config.yml`)

Important sections and reasons:

- `auth_enabled: false` — simplifies local testing (no auth).
- `server.http_listen_port: 3100` — HTTP API for reads/writes.
- `common` — shared config for paths and ring:
  - `path_prefix: /var/loki` — single root for all data.
  - `storage.filesystem` — local filesystem store.
  - `ring.kvstore.store: inmemory` — single‑node, no external KV store.
- `schema_config`:
  - `schema: v13` — TSDB schema for Loki 3.0+.
  - `store: tsdb`, `object_store: filesystem`.
  - Daily index period (`period: 24h`).
- `storage_config`:
  - `tsdb_shipper` indexes in `/var/loki/index` with filesystem backend.
  - `filesystem.directory: /var/loki/chunks` for chunks.
- `limits_config.retention_period: 168h` — 7‑day retention.
- `compactor`:
  - Runs compaction and enforces retention.
  - `retention_enabled: true`.

### 3.3 Promtail (`monitoring/promtail/config.yml`)

Key ideas:

- `server.http_listen_port: 9080` — exposes `/ready`, `/targets`.
- `positions.filename: /var/log/promtail/positions.yaml` — tracks offsets so restarts don’t re‑ingest logs.
- `clients`:
  - Single Loki client: `http://loki:3100/loki/api/v1/push`.
- `scrape_configs` with Docker service discovery:
  - `docker_sd_configs.host: unix:///var/run/docker.sock` — discovers running containers from Docker.
  - `relabel_configs`:
    - Keep only containers with `logging=promtail`:
      - `source_labels: [__meta_docker_container_label_logging]`
      - `regex: promtail`, `action: keep`.
    - Extract container name:
      - `source_labels: [__meta_docker_container_name]`
      - `regex: "/(.*)"` → `container` label without leading slash.
    - Map `app` container label to Loki label:
      - `source_labels: [__meta_docker_container_label_app]`
      - `target_label: app`.

## 4. Application Logging (JSON)

The Lab 1 Python app (`app_python/app.py`) is updated to use structured JSON logging with `python-json-logger`:

- Logs to **stdout** so Docker captures logs.
- Uses a **custom formatter** that emits JSON with fields:
  - `timestamp`, `level`, `logger`, `message`
  - `method`, `path`, `status_code`, `client_ip`, `user_agent`
- Hooks:
  - On startup: logs `"application_startup"`.
  - On every HTTP request: logs in `@app.after_request`.
  - On unhandled errors: logs via Flask error handler.

Example JSON log line (formatted for readability):

```json
{
  "timestamp": "2026-03-12T10:15:30.123456Z",
  "level": "INFO",
  "logger": "devops-info-service",
  "message": "request",
  "method": "GET",
  "path": "/health",
  "status_code": 200,
  "client_ip": "172.19.0.1",
  "user_agent": "curl/7.88.1"
}
```

> **Screenshot to take:** Terminal/log viewer showing JSON log lines like above from `app-python` (container logs). Save as `monitoring/docs/screenshots/02-json-logs-app-python.png`.

## 5. Dashboard

In Grafana, build a dashboard with 4 panels using the Loki data source.

### 5.1 Example LogQL Queries

Used in Explore first, then turned into panels:

1. **Stream selection**  
   `{app="devops-python"}`

2. **Errors only**  
   `{app="devops-python"} |= "ERROR"`

3. **JSON parsing**  
   `{app="devops-python"} | json`

4. **Filter by level**  
   `{app="devops-python"} | json | level="INFO"`

5. **Request rate (all apps)**  
   `sum by (app) (rate({app=~"devops-.*"}[1m]))`

### 5.2 Required Panels

1. **Logs Table** (Logs)
   - Query: `{app=~"devops-.*"}`
   - Shows recent logs from `devops-python` (and bonus app if present).

2. **Request Rate** (Time series)
   - Query: `sum by (app) (rate({app=~"devops-.*"}[1m]))`
   - Shows logs‑per‑second by app.

3. **Error Logs** (Logs)
   - Query: `{app=~"devops-.*"} | json | level="ERROR"`

4. **Log Level Distribution** (Stat or Pie)
   - Query: `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))`

> **Screenshot to take:** Saved dashboard page with all 4 panels and real data. Save as `monitoring/docs/screenshots/03-grafana-dashboard.png`.

## 6. Production Configuration

### 6.1 Resource Limits

All services in `docker-compose.yml` include resource constraints:

- `deploy.resources.limits`:
  - Loki: `cpus: "1.0"`, `memory: 1G`
  - Grafana: `cpus: "1.0"`, `memory: 1G`
  - Promtail: `cpus: "1.0"`, `memory: 512M`
  - App: `cpus: "0.5"`, `memory: 512M`
- `deploy.resources.reservations` to guarantee minimal CPU/memory.

This prevents a misbehaving service from starving others on the host.

### 6.2 Securing Grafana

- Anonymous access is disabled:
  - `GF_AUTH_ANONYMOUS_ENABLED=false`
- Admin user is set via environment variables:
  - `GF_SECURITY_ADMIN_USER=admin`
  - `GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}`
- Secrets are provided via `.env` file (ignored by Git and **not** committed).

Example `.env` (create locally, do **not** add to repo):

```env
GRAFANA_ADMIN_PASSWORD=change_me_strong_password
```

> **Screenshot to take:** Grafana login page (showing that anonymous access is disabled). Save as `monitoring/docs/screenshots/04-grafana-login.png`.

### 6.3 Health Checks

Implemented via Docker Compose `healthcheck` blocks:

- Loki:
  - `curl -f http://localhost:3100/ready || exit 1`
- Promtail:
  - `curl -f http://localhost:9080/ready || exit 1`
- Grafana:
  - `curl -f http://localhost:3000/api/health || exit 1`

Then:

```bash
cd monitoring
docker compose ps   # Should show all services as healthy
```

> **Screenshot to take:** `docker compose ps` output with all services healthy. Save as `monitoring/docs/screenshots/05-docker-compose-ps-healthy.png`.

## 7. Testing

### 7.1 Generate Traffic

With the stack running:

```bash
# From host
for i in {1..20}; do curl http://localhost:8000/; done
for i in {1..20}; do curl http://localhost:8000/health; done
```

This generates JSON logs from `app-python` which Promtail ships to Loki.

### 7.2 Example LogQL Queries

Run in Grafana Explore:

```logql
{app="devops-python"}
{app="devops-python"} |= "ERROR"
{app="devops-python"} | json | method="GET"
```

You should see:

- Requests for `/` and `/health`.
- Filtered error logs when you simulate failures.
- Parsed JSON fields (`method`, `path`, `status_code`, `client_ip`).

## 8. Challenges & Notes

- **Loki TSDB configuration**: required switching to `store: tsdb` and `schema: v13` to be compatible with Loki 3.0. Using filesystem as `object_store` keeps setup simple for a single node.
- **Docker discovery & label filtering**: Promtail’s Docker SD exposes many meta labels; using `logging=promtail` avoids scraping every container on the host and keeps the system safer and cheaper.
- **JSON logging in app**: moving from plain text to structured logs required a dedicated formatter and hooking into `before_request`/`after_request`, but it makes LogQL queries much more powerful.

This setup satisfies the main Lab 7 requirements:

- Loki, Promtail, Grafana running via Docker Compose.
- Loki data source configured in Grafana.
- Python app logging in JSON format and visible in Grafana.
- Dashboard with 4+ panels using LogQL.
- Production‑ish settings: resource limits, health checks, secured Grafana, and basic retention.

