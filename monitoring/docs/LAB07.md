## Lab 7 — Loki Stack Monitoring

### 1. Architecture

- **Loki**: single instance with TSDB + filesystem storage, 7 days retention.
- **Promtail**: collects Docker container logs via Docker service discovery, filters by `logging=promtail` label, enriches with `container` and `app` labels.
- **Grafana**: visualizes logs from Loki, dashboards built on LogQL queries.
- **Apps**: `app-python` (FastAPI) container joined to `logging` network, logs to stdout in JSON format.

### 2. Setup Guide

1. Build and start the stack:
   ```bash
   cd monitoring
   docker compose up -d --build
   docker compose ps
   ```
2. Check health:
   ```bash
   curl http://localhost:3100/ready      # Loki
   curl http://localhost:9080/targets   # Promtail UI shows 1/1 docker target for app-python
   curl http://localhost:3000/api/health  # Grafana
   ```
3. Open Grafana at `http://localhost:3000` and add Loki data source with URL `http://loki:3100` 
![setup](docs/screens/lab07/loki_setup.png)

### 3. Configuration Overview

- **Loki** (`loki/config.yml`):
  - Uses `schema_config` v13 with `store: tsdb` and `object_store: filesystem`.
  - `limits_config.retention_period: 168h` enables 7 day retention.
  - `compactor` with `retention_enabled: true` cleans up old chunks.
- **Promtail** (`promtail/config.yml`):
  - `docker_sd_configs` with Docker socket for auto-discovery.
  - `filters` keep only containers with label `logging=promtail`.
  - `relabel_configs` create labels `container`, `app`, `container_id`.

### 4. Application Logging (JSON)

- Updated `app_python/app.py` to use a custom `JSONFormatter` for the standard `logging` module.
- All logs are emitted as JSON with fields like:
  - `timestamp`, `level`, `message`, `logger`, `module`, `function`, `line`.
  - Request context from middleware: `method`, `path`, `status_code`, `client_ip`, `duration_ms`.
- Logs are written to stdout and collected by Docker → Promtail → Loki.

### 5. Dashboard

Single dashboard **"Lab07 - Loki logs"** contains 4 panels built on Loki data source  
![dash](docs/screens/lab07/dashboards.png):

1. **Logs Table** (All app logs):
   ```logql
   {app="devops-python"}
   ```
   Shows recent logs from the Python app in logs view.

2. **Request Rate by App** (Time series):
   ```logql
   sum by (app) (rate({app=~"devops-.*"}[1m]))
   ```
   Visualizes log rate over time grouped by `app` label.

3. **Error Logs** (Logs):
   ```logql
   {app="devops-python"} | json | level="error"
   ```
   Shows only error-level logs; when no errors are generated the panel intentionally displays "No data".

4. **Log Level Distribution (last 5m)** (Stat):
   ```logql
   sum by (level) (count_over_time({app="devops-python"} | json [5m]))
   ```
   Shows distribution of log levels for the last 5 minutes (in current setup almost all logs are `info`).

### 6. Production Configuration

- **Resources**: `deploy.resources` limits/reservations configured for Loki, Promtail, Grafana, and `app-python`.
- **Security**:
  - Anonymous access to Grafana is disabled (`GF_AUTH_ANONYMOUS_ENABLED=false`).
  - Admin user and password are provided via environment variables (`GF_SECURITY_ADMIN_USER`, `GF_SECURITY_ADMIN_PASSWORD`) from `monitoring/.env` (not committed to git).
  - When opeming the `http://localhost:3000` shows login page Grafana  
  ![login](docs/screens/lab07/login.png)
- **Retention**: Loki retention set to 7 days (can be tuned via config).

### 7. Testing

1. Generate logs:
   ```bash
   # traffic to main endpoint
   for i in {1..50}; do curl http://localhost:8000/; done

   # traffic to health endpoint
   for i in {1..50}; do curl http://localhost:8000/health; done
   ```
2. In Grafana → Explore → Loki:
   - Verify `{app="devops-python"}` returns JSON logs.
   - Try queries (see screenshots in `docs/screens/lab07/query_1.png`, `query_2.png`, `query_3.png`):
     - `{app="devops-python"} | json`
     - `{app="devops-python"} | json | level="info"`
     - `{app="devops-python"} | json | method="GET"`

### 8. Challenges

- Aligning Loki 3.0 TSDB configuration with filesystem storage and single-node setup.
- Correctly configuring Promtail Docker service discovery and label-based filtering.
- Implementing structured JSON logging in FastAPI while keeping performance reasonable.

### 9. Bonus — Ansible Automation

- Created Ansible role `roles/monitoring` that:
  - Renders Docker Compose v2 file and Loki/Promtail configs from Jinja2 templates into `/opt/monitoring`.
  - Deploys the stack using `community.docker.docker_compose_v2` with project name `monitoring`.
  - Waits for Loki and Grafana health endpoints (best effort, non-fatal on connection errors).
- Added playbook `ansible/playbooks/deploy-monitoring.yml` that runs the role on `webservers` hosts (reusing existing `docker` role for Docker installation).
- Verified idempotency by running:
  ```bash
  cd ansible
  ansible-playbook playbooks/deploy-monitoring.yml -i inventory/hosts.ini
  ansible-playbook playbooks/deploy-monitoring.yml -i inventory/hosts.ini
  ```
  The second run reports no changes in configuration tasks on the target VM.

