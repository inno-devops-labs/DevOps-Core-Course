# LAB07 - Loki Stack Observability

## Architecture

Centralized logging stack is deployed with Docker Compose:

```text
app-python ----\
                \
app-go ----------> Promtail -> Loki -> Grafana Explore/Dashboard
                /
Docker logs ----/
```

Components:
- `Loki` stores logs (index + chunks), optimized for labels and LogQL.
- `Promtail` discovers Docker containers and ships logs to Loki.
- `Grafana` queries Loki and visualizes logs/metrics.
- `app_python` and `app_go` generate application logs.

## Stack Study (Task 1.1)

- **Loki vs Elasticsearch:** Loki indexes only metadata labels, not full log bodies. This reduces storage/index costs and works well for high-volume container logs.
- **Log labels:** labels (for example `app`, `container`, `job`) identify log streams. Good labels make LogQL queries fast and precise.
- **Promtail container discovery:** Promtail uses Docker service discovery (`docker_sd_configs`) through `/var/run/docker.sock`, receives container metadata labels, and maps them with `relabel_configs`.

## Setup Guide

1. Go to monitoring folder:
   ```bash
   cd monitoring
   ```
2. Create local secrets file from template:
   ```bash
   cp .env.example .env
   # set GF_ADMIN_PASSWORD in .env
   ```
3. Start stack:
   ```bash
   docker compose up -d
   docker compose ps
   ```
4. Verify endpoints:
   ```bash
   curl http://localhost:3100/ready
   curl http://localhost:9080/targets
   curl http://localhost:3000/api/health
   ```
5. Grafana login: `http://localhost:3000` (anonymous access disabled).

## Configuration

### Loki (`monitoring/loki/config.yml`)

Key settings:
- HTTP server on port `3100`.
- TSDB storage backend with filesystem.
- Schema `v13`.
- Retention `168h` (7 days).

Snippet:
```yaml
schema_config:
  configs:
    - from: 2024-01-01
      store: tsdb
      object_store: filesystem
      schema: v13
limits_config:
  retention_period: 168h
```

### Promtail (`monitoring/promtail/config.yml`)

Key settings:
- Loki client endpoint: `http://loki:3100/loki/api/v1/push`.
- Docker service discovery from socket.
- Keep only containers with label `logging=promtail`.
- Extract labels `container` and `app`.

Snippet:
```yaml
docker_sd_configs:
  - host: unix:///var/run/docker.sock
relabel_configs:
  - source_labels: ['__meta_docker_container_label_logging']
    regex: promtail
    action: keep
  - source_labels: ['__meta_docker_container_name']
    target_label: container
    regex: '/?(.*)'
  - source_labels: ['__meta_docker_container_label_app']
    target_label: app
```

### Docker Compose (`monitoring/docker-compose.yml`)

- Services: `loki`, `promtail`, `grafana`, `app-python`, `app-go`.
- Shared network: `logging`.
- Persistent volumes: `loki-data`, `grafana-data`.
- Resource limits/reservations added for all services.
- Health checks for Loki and Grafana.
- Grafana security via `.env` (`GF_ADMIN_PASSWORD`), anonymous auth disabled.

## Application Logging

Python app (`app_python/app.py`) uses `logging` + `python-json-logger`.

Implemented:
- JSON output with `timestamp`, `level`, `message`.
- Request context fields: `method`, `path`, `status`, `ip`.
- Important events: startup, incoming request, response, 404/500 errors.

Example JSON log:
```json
{"timestamp":"2026-04-24 19:20:01,124","level":"INFO","message":"Request received","method":"GET","path":"/health","status":null,"ip":"172.20.0.1"}
```

## Dashboard

Dashboard includes 4 required panels:

1. **Logs Table** (Logs)  
   Query:
   ```logql
   {app=~"devops-.*"}
   ```
2. **Request Rate** (Time series)  
   Query:
   ```logql
   sum by (app) (rate({app=~"devops-.*"}[1m]))
   ```
3. **Error Logs** (Logs)  
   Query:
   ```logql
   {app=~"devops-.*"} | json | level="ERROR"
   ```
4. **Log Level Distribution** (Pie/Stat)  
   Query:
   ```logql
   sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))
   ```

Screenshots:
- `monitoring/docs/screenshots/dashboard.png`
- `monitoring/docs/screenshots/logs.png`
- `monitoring/docs/screenshots/error logs.png`
- `monitoring/docs/screenshots/json.png`
- `monitoring/docs/screenshots/login.png`
- `monitoring/docs/screenshots/app-python.png`

## Production Config

- **Security:** anonymous Grafana access disabled; admin password in `.env`.
- **Resources:** CPU/memory limits and reservations set in Compose.
- **Retention:** Loki keeps logs for 7 days (`168h`).
- **Health checks:** readiness/health endpoints for Loki and Grafana.

## Testing

Generate logs:
```bash
for i in {1..20}; do curl http://localhost:8000/; done
for i in {1..20}; do curl http://localhost:8000/health; done
for i in {1..20}; do curl http://localhost:8001/; done
```

Validate in Grafana Explore:
```logql
{app="devops-python"}
{app="devops-python"} |= "ERROR"
{app="devops-python"} | json | method="GET"
{app=~"devops-.*"}
```

Service checks:
```bash
docker compose ps
curl http://localhost:3100/ready
curl http://localhost:9080/targets
curl http://localhost:3000/api/health
```

## Challenges

1. **Loki/Grafana healthcheck command compatibility**  
   Some images may not include `curl`. Switched checks to `wget --spider`.

2. **Missing `app` labels in Loki streams**  
   Added Promtail relabel rules from Docker labels (`__meta_docker_container_label_app`).

3. **Secret handling for Grafana admin password**  
   Added `.env.example` and moved password source to `.env` file.
