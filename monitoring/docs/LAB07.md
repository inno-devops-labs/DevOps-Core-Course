# Lab 7 — Observability & Logging with Loki Stack


## 1. Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  app-python     │     │  Loki           │     │  Grafana        │
│  (Flask)        │     │  (Log Storage)  │     │  (Visualization)│
│  Port 8000      │     │  Port 3100      │     │  Port 3000      │
└────────┬────────┘     └────────▲────────┘     └────────▲────────┘
         │                       │                       │
         │ JSON logs             │ push                  │ query
         │ (stdout)              │                       │
         ▼                       │                       │
┌─────────────────┐     ┌────────┴────────┐     ┌───────┴────────┐
│  Docker         │     │  Promtail       │     │  Loki Data     │
│  (json-file     │────▶│  (Log Collector)│────▶│  Source        │
│   log driver)   │     │  Port 9080      │     │  (preconfigured)│
└─────────────────┘     └─────────────────┘     └────────────────┘
         │                       │
         │ /var/lib/docker/      │ Docker SD
         │ containers            │ + filters
         └───────────────────────┘

All services run on the `logging` bridge network.
Promtail discovers containers via Docker socket, reads log files, and pushes to Loki.
```

**Component roles:**
- **Loki:** Stores logs with TSDB index; 7-day retention; compactor cleans old data
- **Promtail:** Discovers containers (label `logging=promtail`), reads Docker log files, pushes to Loki
- **Grafana:** Queries Loki via LogQL, dashboards, Explore

---

## 2. Setup Guide

### Prerequisites
- Docker and Docker Compose v2
- Lab 1 Python app built as `jambulancia/devops-info-service:latest`

### Deploy

```bash
cd monitoring
docker compose up -d
docker compose ps
```

### Verify

```bash
# Loki readiness
curl http://localhost:3100/ready

# Promtail targets (log discovery)
curl http://localhost:9080/targets

# Grafana
open http://localhost:3000
```

### Configure Loki Data Source in Grafana

1. **Connections** → **Data sources** → **Add data source** → **Loki**
2. URL: `http://loki:3100`
3. **Save & Test**

### Generate Logs

```bash
for i in {1..20}; do curl http://localhost:8000/; done
for i in {1..20}; do curl http://localhost:8000/health; done
```

### Alternative: Loki Docker Logging Driver

If Promtail Docker SD does not push logs in your environment, you can use the Loki Docker logging driver for the app:

```bash
docker plugin install grafana/loki-docker-driver:3.6.0 --alias loki --grant-all-permissions
```

Then add to `app-python` in docker-compose:

```yaml
    logging:
      driver: loki
      options:
        loki-url: "http://loki:3100/loki/api/v1/push"
        loki-external-labels: "job=docker,app=devops-python"
```

---

## 3. Configuration

### Loki (`loki/config.yml`)

- **Schema:** v13 with TSDB and filesystem storage
- **Retention:** 168h (7 days) via `limits_config.retention_period`
- **Compactor:** Enabled to delete data beyond retention

```yaml
limits_config:
  retention_period: 168h

compactor:
  retention_enabled: true
```

### Promtail (`promtail/config.yml`)

- **Docker SD:** Discovers containers with label `logging=promtail`
- **`__path__` relabel:** Points to `/var/lib/docker/containers/${id}/*.log` so Promtail reads Docker log files
- **Labels:** `container` (from name), `service` (from compose service label)
- **Pipeline:** `docker: {}` parses Docker JSON log wrapper

```yaml
relabel_configs:
  - source_labels: ['__meta_docker_container_id']
    regex: '(.+)'
    target_label: __path__
    replacement: /var/lib/docker/containers/${1}/*.log
  - source_labels: ['__meta_docker_container_name']
    regex: '/(.*)'
    target_label: 'container'
  - source_labels: ['__meta_docker_container_label_com_docker_compose_service']
    target_label: 'service'
```

---

## 4. Application Logging

The Python app uses `python-json-logger` when `LOG_FORMAT=json` is set.

- **Format:** `{"timestamp": "...", "level": "...", "message": "...", "method": "...", "path": "...", ...}`
- **Events logged:** Startup, request received, response sent, 404, 500
- **Context:** method, path, status_code, client_ip

```python
# app_python/app.py
from pythonjsonlogger import jsonlogger

if USE_JSON_LOGGING:
    formatter = jsonlogger.JsonFormatter()
    handler.setFormatter(formatter)
```

Docker Compose sets `LOG_FORMAT: "json"` for the app service.

---

## 5. Dashboard

Create a dashboard with 4 panels:

| Panel              | Type        | LogQL Query                                                                 |
|--------------------|-------------|-----------------------------------------------------------------------------|
| Logs Table         | Logs        | `{app=~"devops-.*"}`                                                        |
| Request Rate       | Time series | `sum by (app) (rate({app=~"devops-.*"} [1m]))`                              |
| Error Logs         | Logs        | `{app=~"devops-.*"} \| json \| level="ERROR"`                               |
| Log Level Distribution | Stat/Pie | `sum by (level) (count_over_time({app=~"devops-.*"} \| json [5m]))`        |

**How to create:**
1. **Dashboard** → **New** → **New Dashboard** → **Add visualization**
2. Select **Loki** data source
3. Enter LogQL and choose visualization type

---

## 6. Production Config

- **Resource limits:** All services have `deploy.resources.limits` (CPU, memory)
- **Health checks:** Loki (`/ready`), Grafana (`/api/health`)
- **Grafana security:** Disable anonymous auth for production:
  - `GF_AUTH_ANONYMOUS_ENABLED: "false"`
  - `GF_SECURITY_ADMIN_PASSWORD` from `.env` (do not commit)
- **Secrets:** Use `.env` for Grafana admin password; add to `.gitignore`

---

## 7. Testing

```bash
# Full stack health
cd monitoring
docker compose ps

# Loki
curl -s http://localhost:3100/ready

# Promtail targets
curl -s http://localhost:9080/targets | head -50

# Generate traffic
for i in {1..10}; do curl -s http://localhost:8000/ > /dev/null; done
for i in {1..10}; do curl -s http://localhost:8000/health > /dev/null; done
```

**Grafana Explore:** Run `{job="docker"}` or `{app="devops-python"}` to confirm logs appear.

---

## 8. Challenges & Solutions

| Challenge                          | Solution                                                                 |
|------------------------------------|--------------------------------------------------------------------------|
| Promtail Docker SD not pushing logs| Ensure Docker socket + `/var/lib/docker/containers` are mounted. Try `curl localhost:9080/targets`. Alternative: use [Loki Docker logging driver](https://grafana.com/docs/loki/latest/send-data/docker-driver/) |
| Too many containers discovered     | Use `filters: - name: label values: ["logging=promtail"]` in Docker SD   |
| JSON parsing in LogQL              | Use `\| json` pipeline stage; filter with `level="ERROR"`                |
| Label vs service name              | Use `__meta_docker_container_label_com_docker_compose_service` for app   |
| Loki compactor config error        | Add `delete_request_store: filesystem` when `retention_enabled: true`    |

---

## Evidence Checklist

- [x] Loki, Promtail, Grafana running via Docker Compose
- [x] Loki data source in Grafana
- [x] Python app with JSON logging
- [x] Logs visible in Grafana from all labeled containers
- [x] Dashboard with 4 panels
- [x] LogQL queries for streams, errors, rates, levels
- [x] Resource limits and health checks
- [x] LAB07.md with setup and config notes
