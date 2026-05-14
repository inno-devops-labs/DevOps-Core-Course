## 1. Architecture

Describe the architecture and include a diagram showing how Grafana, Loki, Promtail, and your apps connect.

 - **Diagram:**

    ```
    Internet
      |
    [Load Balancer / Host]
      |
    +-------------------------------+
    |           Docker Host         |
    |  +---------+   +-----------+  |
    |  | app(s)  |   |  grafana  |  |
    |  |(python) |   +-----------+  |
    |  |labels:  |        |         |
    |  |app=...  |        |         |
    |  +----+----+        |         |
    |       |             |         |
    |  +----v----+   +----v----+    |
    |  | promtail |-->|  loki   |    |
    |  +---------+   +---------+    |
    +-------------------------------+

    - Promtail discovers container logs and pushes to Loki.
    - Grafana queries Loki to visualize logs and dashboards.
    ```
---

## 2. Setup Guide

Step-by-step deployment instructions to reproduce the stack locally.

- Prerequisites: Docker Engine, docker-compose v2
- Commands to run:

```bash
cd monitoring
docker compose up -d --build
```

---

## 3. Configuration

Explain key configuration snippets and why they were chosen.

- `loki/config.yml` highlights:
- `loki/config.yml` highlights (important excerpts):

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

storage_config:
  tsdb_shipper:
    active_index_directory: /loki/tsdb-index
    cache_location: /loki/tsdb-cache
  filesystem:
    directory: /loki/chunks

compactor:
  working_directory: /loki/compactor
  retention_enabled: true
  delete_request_store: filesystem

limits_config:
  retention_period: 168h
```

Notes: using TSDB (`store: tsdb`, `schema: v13`) with `filesystem` object store and `retention_period` = 168h (7 days).

- `promtail/config.yml` highlights (important excerpts):

```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /var/lib/promtail/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - target_label: 'job'
        replacement: 'docker'

      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container'
      - source_labels: ['__meta_docker_container_label_app']
        target_label: 'app'
```

Notes: Promtail discovers containers via Docker socket, persists read positions under `/var/lib/promtail`, and sets `job=docker` plus `container` and `app` labels used in LogQL queries.

- `docker-compose.yml` highlights (important excerpts):

```yaml
volumes:
  loki-data:
  grafana-data:
  promtail-data:

services:
  loki:
    image: grafana/loki:3.0.0
    ports:
      - "3100:3100"
    volumes:
      - ./loki/config.yml:/etc/loki/config.yml
      - loki-data:/loki
    command: -config.file=/etc/loki/config.yml

  promtail:
    image: grafana/promtail:3.0.0
    ports:
      - "9080:9080"
    volumes:
      - ./promtail/config.yml:/etc/promtail/config.yml
      - promtail-data:/var/lib/promtail
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro

  grafana:
    image: grafana/grafana:12.3.1
    ports:
      - "3000:3000"
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=false
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
    volumes:
      - grafana-data:/var/lib/grafana

  app-python:
    build:
      context: ../app_python
    ports:
      - "8000:5000"
    labels:
      app: devops-python
      logging: promtail
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.25'
          memory: 128M
```

Notes: named volumes provide persistence; Promtail mounts the Docker socket for discovery; Grafana is secured via env var-driven admin password; `app-python` has resource limits.

---

## 4. Application Logging

Describe how the Python app was updated for JSON structured logging and what fields are included.

- Key fields emitted: `timestamp`, `level`, `logger`, `message`, `method`, `path`, `status_code`, `client_ip`, `duration_ms`
- Example log (JSON):

```json
{
  "timestamp": "2026-05-14T02:00:00Z",
  "level": "INFO",
  "logger": "app",
  "message": "request_completed",
  "method": "GET",
  "path": "/",
  "status_code": 200,
  "client_ip": "127.0.0.1",
  "duration_ms": 12
}
```

- Screenshots:
  - Example JSON log from Grafana Explore
    - ![](/lab_solutions/lab1/monitoring/docs/lab7-evidence/logs-terminal.png)
  - Screenshot of Grafana showing logs from both applications
    - ![](/lab_solutions/lab1/monitoring/docs/lab7-evidence/logs-ev.png)

---

## 5. Dashboard

Explain the dashboard panels and include screenshots.

Panels to include:
- **Logs Table** — recent logs across apps
  - Query: `{app=~"devops-.*"}`

- **Request Rate** — time series of requests per second
  - Query: `sum by (app) (rate({app=~"devops-.*"}[1m]))`

- **Error Logs** — only ERROR level logs
  - Query: `{app=~"devops-.*"} | json | level="ERROR"`

- **Log Level Distribution** — counts by level
  - Query: `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))`

Include a full dashboard screenshot:
- ![](/lab_solutions/lab1/monitoring/docs/lab7-evidence/dashboard.png)

---

## 6. Production Config

Outline changes made for production readiness:
- Removed anonymous Grafana access
- Set Grafana admin password via `.env`
- Resource limits on services in `docker-compose.yml`
- Health checks for Loki/Grafana

- Screenshots:
  - Grafana login page (no anonymous access)
    - ![](/lab_solutions/lab1/monitoring/docs/lab7-evidence/grafana-login-page.png)
  - Services healthy
    - ![](/lab_solutions/lab1/monitoring/docs/lab7-evidence/docker-health.png)

---

## 7. Testing

Commands and verification steps used:

- Bring stack up

```bash
cd monitoring
docker compose up -d --build
```

- Generate traffic to the app

```bash
for i in {1..20}; do curl -s http://localhost:8000/ >/dev/null; done
curl -s http://localhost:8000/health
curl -s http://localhost:8000/error || true  # generates ERROR log
```

---

## 8. Challenges & Solutions

Document any problems encountered and how you fixed them.

- Promtail positions file rename error when bind-mounted — fixed by using a named volume and storing positions at `/var/lib/promtail/positions.yaml`.

---


## Appendix — Useful LogQL Queries

- All logs for Python app:
  - `{app="devops-python"}`

- Only errors:
  - `{app="devops-python"} | json | level="ERROR"`

- Request rate:
  - `sum by (app) (rate({app=~"devops-.*"}[1m]))`

- Count by level (5m window):
  - `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))`

---
