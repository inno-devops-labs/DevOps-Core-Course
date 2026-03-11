# Lab 7: Observability & Logging with Loki Stack

## 1. Architecture

```text
app-python (Flask, JSON logs)
        |
        | Docker container logs
        v
promtail (discovers containers via docker.sock, adds labels)
        |
        | /loki/api/v1/push
        v
loki (stores logs with TSDB schema v13, retention 7d)
        |
        v
grafana (queries Loki with LogQL, dashboards)
```

Network: `monitoring-logging`  
Ports:
- Grafana: `3000`
- Loki: `3100`
- Promtail targets page: `9080`
- App: `8000`

## 2. Setup Guide (Step by Step)

### Step 1: Prepare environment

```bash
cd monitoring
cp .env.example .env
```

What this does:
- Creates local runtime settings for Grafana auth and optional app image override.
- `.env` is ignored by git, so secrets are not committed.

### Step 2: Start the stack

```bash
docker compose up -d --build
docker compose ps
```

What this does:
- Builds `app-python` from `../app_python` so latest local code is used.
- Starts Loki, Promtail, Grafana, and app containers.

### Step 3: Verify health endpoints

```bash
curl http://localhost:3100/ready
curl http://localhost:3000/api/health
curl http://localhost:8000/health
```

Expected:
- Loki returns `ready`
- Grafana returns JSON with `"database":"ok"`
- App returns `{"status":"healthy", ...}`

### Step 4: Open Grafana

1. Open `http://localhost:3000`
2. Login with credentials from `monitoring/.env`
3. Loki data source and dashboard are provisioned automatically from repo files:
   - `monitoring/grafana/provisioning/datasources/loki.yml`
   - `monitoring/grafana/provisioning/dashboards/lab07.yml`
   - `monitoring/grafana/dashboards/lab07-monitoring.json`

If you already had old Grafana state in `grafana-data`, admin password and dashboard DB state may persist.
To reset to clean file-provisioned state:

```bash
docker compose down -v
docker compose up -d --build
```

## 3. Configuration Notes

### Loki (`monitoring/loki/config.yml`)
- `schema: v13` + `store: tsdb` for Loki 3.x.
- `object_store: filesystem` for single-host lab setup.
- `retention_period: 168h` (7 days).
- `compactor.retention_enabled: true` for cleanup of old logs.

### Promtail (`monitoring/promtail/config.yml`)
- Uses `docker_sd_configs` against `unix:///var/run/docker.sock`.
- Filters only containers with label `logging=promtail`.
- Maps container labels to log labels:
  - `container`
  - `app`
  - `job=docker`
- Stack containers are labeled for collection:
  - `devops-python`
  - `devops-loki`
  - `devops-promtail`
  - `devops-grafana`

### Compose (`monitoring/docker-compose.yml`)
- Named volumes for persistent Loki/Grafana data.
- Health checks for Loki, Grafana, and app.
- Resource limits/reservations included under `deploy.resources`.

## 4. Application Logging (JSON)

File: `app_python/app.py`

Implemented:
- Custom `JSONFormatter` that emits structured JSON to stdout.
- `@app.before_request` logs incoming request metadata.
- `@app.after_request` logs status and duration.
- Startup log includes host/port/debug.
- Error handlers log structured warnings/errors.

Example log line:

```json
{"timestamp":"2026-03-11T10:02:48.862Z","level":"INFO","logger":"devops-info-service","message":"request_completed","method":"GET","path":"/health","status_code":200,"client_ip":"172.19.0.1","duration_ms":0}
```

## 5. LogQL Queries

Use these in Grafana Explore:

1. All app logs:
```logql
{app=~"devops-.*"}
```

2. Warning/Error logs:
```logql
{app=~"devops-.*"} | json | __error__="" | level=~"WARNING|ERROR"
```

3. JSON parse + method filter:
```logql
{app="devops-python"} | json | __error__="" | method="GET"
```

4. Request rate by app:
```logql
sum by (app) (rate({app=~"devops-.*"}[1m]))
```

5. Log level distribution:
```logql
sum by (level) (count_over_time({app=~"devops-.*"} | json | __error__="" [5m]))
```

## 6. Dashboard Panels

Create dashboard with 4 panels:

1. Logs Table  
Query: `{app=~"devops-.*"}`

2. Request Rate (Time series)  
Query: `sum by (app) (rate({app=~"devops-.*"}[1m]))`

3. Error Logs (Logs panel)  
Query: `{app=~"devops-.*"} | json | __error__="" | level=~"WARNING|ERROR"`

4. Log Level Distribution (Pie/Stat)  
Query: `sum by (level) (count_over_time({app=~"devops-.*"} | json | __error__="" [5m]))`

## 7. Production Readiness

### Security
- For production, set in `.env`:
  - `GF_AUTH_ANONYMOUS_ENABLED=false`
  - strong `GF_SECURITY_ADMIN_PASSWORD`
- Keep `.env` out of git.

### Resources
- CPU/memory constraints are set per service in compose.

### Retention
- Loki retention is configured to 7 days (`168h`).

## 8. Testing Commands

Generate traffic:

```bash
for i in $(seq 1 20); do curl -s http://localhost:8000/ >/dev/null; done
for i in $(seq 1 20); do curl -s http://localhost:8000/health >/dev/null; done
```

Query Loki API directly:

```bash
curl -G 'http://localhost:3100/loki/api/v1/query' \
  --data-urlencode 'query={app="devops-python"}' \
  --data-urlencode 'limit=5'
```

Trigger warning logs (404):

```bash
curl -i http://localhost:8000/healt
curl -i http://localhost:8000/favicon.ico
```

Trigger error logs (500):

```bash
curl -i http://localhost:8000/boom
```

## 9. Evidence Collected

The following artifacts were captured and are ready for submission:

1. `docker compose ps` output showing running stack:
   - `app-python` healthy
   - `loki` healthy
   - `grafana` healthy
   - `promtail` up

2. Grafana login page at `/login` showing anonymous access is disabled.

3. Query proof for logs from 3+ containers:
   - `sum by (app) (count_over_time({app=~"devops-(python|loki|grafana)"}[1h]))`
   - returned series include: `devops-python`, `devops-loki`, `devops-grafana`

4. Error/warning logs panel with working query:
   - `{app=~"devops-.*"} | json | __error__="" | level=~"WARNING|ERROR"`
   - includes `404` warnings and `500` errors (`/boom`)

5. JSON parse + method filter panel with working query:
   - `{app="devops-python"} | json | __error__="" | method="GET"`

6. Full dashboard screenshot with all 4 required panels:
   - Log Level Distribution
   - Request Rate by App
   - Error Logs
   - All Application Logs

7. App container JSON log output from terminal:
   - `docker compose logs --tail=30 app-python`
   - fields visible: `timestamp`, `level`, `message`, `method`, `path`, `status_code`

## 10. Challenges and Fixes

1. Promtail health check failed (`wget` missing in image).  
Fix: removed Promtail healthcheck and used startup dependency instead.

2. App logs were not JSON in stack at first.  
Fix: switched app service to local build (`../app_python`) so latest code is used.

3. Duplicate plain-text request logs from Werkzeug.  
Fix: set `werkzeug` logger level to `WARNING`.
