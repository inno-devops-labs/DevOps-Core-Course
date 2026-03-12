# LAB07 - Observability & Logging with Loki Stack

## 1. Architecture

```text
+------------------+         +------------------+
|  app-python      | stdout  |  Docker Engine   |
|  (Flask, JSON)   +-------->+  json-file logs  |
+------------------+         +---------+--------+
                                       |
                                       | docker_sd_configs
                                       v
                              +--------+--------+
                              |   Promtail 3.0  |
                              | label filter:   |
                              | logging=promtail|
                              +--------+--------+
                                       |
                                       | /loki/api/v1/push
                                       v
                              +--------+--------+
                              |    Loki 3.0     |
                              | TSDB + FS store |
                              | retention 168h  |
                              +--------+--------+
                                       |
                                       | datasource
                                       v
                              +--------+--------+
                              | Grafana 12.3.1  |
                              | Explore + Dash  |
                              +-----------------+
```

## 2. Setup Guide

1. Create secrets file:
```bash
cd monitoring
cp .env.example .env
# set a strong GRAFANA_ADMIN_PASSWORD in .env
```

2. Build and start stack:
```bash
docker compose up -d --build
docker compose ps
```

3. Verify services:
```bash
curl -fsS http://localhost:3100/ready
curl -fsS http://localhost:9080/targets
curl -fsS http://localhost:3000/api/health
```

4. Generate logs:
```bash
for i in {1..20}; do curl -fsS http://localhost:8000/ > /dev/null; done
for i in {1..20}; do curl -fsS http://localhost:8000/health > /dev/null; done
```

## 3. Configuration

### Loki (`monitoring/loki/config.yml`)
- `schema: v13` and `store: tsdb` for Loki 3.0 single-binary setup.
- `object_store: filesystem` for local persistent storage in `loki-data` volume.
- Retention configured with:
```yaml
limits_config:
  retention_period: 168h
compactor:
  retention_enabled: true
```

### Promtail (`monitoring/promtail/config.yml`)
- Docker service discovery via Docker socket.
- Promtail collects only containers labeled `logging=promtail`.
- Relabeling maps:
  - `container` from `__meta_docker_container_name`
  - `app` from `__meta_docker_container_label_app`

## 4. Application Logging

Structured JSON logging implemented in `app_python/app.py`:
- Custom `JSONFormatter` for every log line.
- Startup event (`application_startup`) with app metadata.
- Request started/completed logs with context:
  - `method`, `path`, `status_code`, `client_ip`
- Error logs use `logging.exception(...)` with request context.

Example log line:
```json
{"timestamp":"2026-03-12T16:20:00+00:00","level":"INFO","message":"http_request_completed","method":"GET","path":"/health","status_code":200,"client_ip":"127.0.0.1","app":"devops-info-service"}
```

## 5. Dashboard

Dashboard is provisioned from:
- `monitoring/grafana/dashboards/lab07-logs-dashboard.json`

Panels and queries:
1. Logs Table: `{app=~"devops-.*"}`
2. Request Rate: `sum by (app) (rate({app=~"devops-.*"}[1m]))`
3. Error Logs: `{app=~"devops-.*"} | json | level="ERROR"`
4. Log Level Distribution: `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))`

## 6. Production Config

Implemented hardening and operational settings:
- Anonymous Grafana access disabled (`GF_AUTH_ANONYMOUS_ENABLED=false`).
- Admin password comes from `.env` (not committed).
- Resource constraints for all services (`deploy.resources`).
- Health checks enabled for Loki, Promtail, Grafana, and app container.
- Persistent named volumes for Loki and Grafana data.

## 7. Testing

### Automated tests
```bash
pytest app_python/tests monitoring/tests
```

### Compose validation
```bash
cd monitoring
docker compose config
```

### Runtime checks
```bash
docker compose ps
curl -fsS http://localhost:3100/ready
curl -fsS http://localhost:9080/targets
curl -fsS http://localhost:3000/api/health
```

### LogQL checks
```logql
{app="devops-python"}
{app="devops-python"} |= "ERROR"
{app="devops-python"} | json | method="GET"
```

## 8. Challenges

1. Loki 3.0 config format changed compared to older tutorials.
- Solution: use `common` section + TSDB schema `v13`.

2. Keeping dashboard reproducible for grading.
- Solution: provision datasource and dashboard from repo files.

3. Verifying logging requirements with tests.
- Solution: add pytest coverage for JSON formatter, startup event, and request completion context.

## Evidence

 `monitoring/docs/screenshots/`:
- `grafana-explore-app-logs.png` (logs from 3+ containers)
- `grafana-dashboard-4-panels.png`
- `grafana-login-no-anonymous.png`
- `docker-compose-ps-healthy.png`
