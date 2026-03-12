# Lab 7: Observability & Logging with Loki Stack

**Lab Points:** 8 (Task 3 Dashboard and Bonus skipped)

---

## 1. Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│  app-python     │     │   Promtail   │     │    Loki     │
│  (port 5000)   │────▶│  (port 9080) │────▶│ (port 3100) │
│  JSON logs      │     │  Docker SD   │     │  TSDB store │
└─────────────────┘     └──────────────┘     └──────┬──────┘
        │                       │                    │
        │                       │                    │
        └───────────────────────┴────────────────────┘
                                │
                        ┌───────▼───────┐
                        │   Grafana     │
                        │  (port 3000)  │
                        │  Explore/DS   │
                        └───────────────┘
```

**Flow:** Application emits JSON logs to stdout → Docker captures them → Promtail discovers containers via Docker socket, tails log files → Sends to Loki → Grafana queries Loki via LogQL.

---

## 2. Setup Guide

### Prerequisites

- Docker and Docker Compose v2
- Python app image: build with `docker build -t devops-info-service:latest .` from repo root, or use `DOCKER_IMAGE=your-username/devops-info-service:latest`

### Deployment

```bash
# Build app image first (from repo root)
docker build -t devops-info-service:latest .

cd monitoring

# Deploy stack (uses devops-info-service:latest by default)
docker compose up -d

# Verify
docker compose ps
```

### Verify Services

```bash
# Loki ready
curl http://localhost:3100/ready

# Promtail targets
curl http://localhost:9080/targets

# Grafana (login: admin / password from GRAFANA_ADMIN_PASSWORD)
open http://localhost:3000
```

### Configure Loki Data Source in Grafana

1. **Connections** → **Data sources** → **Add data source** → **Loki**
2. URL: `http://loki:3100`
3. **Save & Test**

### Generate Logs

```bash
for i in {1..20}; do curl http://localhost:5000/; done
for i in {1..20}; do curl http://localhost:5000/health; done
```

---

## 3. Configuration

### Loki (`loki/config.yml`)

- **Storage:** TSDB with filesystem (Loki 3.0)
- **Schema:** v13
- **Retention:** 7 days (168h)
- **Compactor:** Runs every 5m, retention enabled

### Promtail (`promtail/config.yml`)

- **Docker discovery:** `unix:///var/run/docker.sock`, refresh 5s
- **Relabeling:** Extracts `container` from `__meta_docker_container_name`, `app` from label
- **Optional filter:** Uncomment `filters` to only scrape containers with `logging=promtail`

### Application Logging

- **Format:** JSON via `python-json-logger`
- **Fields:** timestamp, level, message, method, path, status_code, client_ip
- **Events:** Startup, each request (start + complete), errors

---

## 4. Application Logging Implementation

**File:** `app_python/logging_config.py`

- `CustomJsonFormatter` extends `python-json-logger` to output structured JSON
- `setup_json_logging()` configures root and uvicorn loggers
- Middleware logs each request with method, path, status_code, client_ip

**Example log line:**

```json
{"timestamp": "2025-03-05T12:00:00.000Z", "level": "INFO", "message": "Request completed", "method": "GET", "path": "/health", "status_code": 200, "client_ip": "172.18.0.1"}
```

---

## 5. Dashboard (Task 3 Skipped)

Task 3 (Grafana dashboard with 4 panels) was skipped as requested. When Grafana is available, create:

1. **Logs Table:** `{app=~"devops-.*"}` or `{job="docker"}`
2. **Request Rate:** `sum by (app) (rate({app=~"devops-.*"} [1m]))`
3. **Error Logs:** `{app=~"devops-.*"} | json | level="ERROR"`
4. **Log Level Distribution:** `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))`

---

## 6. Production Config

### Resource Limits

All services have `deploy.resources`:

- **Loki:** 1 CPU, 1G memory (reservations: 0.25 CPU, 256M)
- **Promtail:** 0.5 CPU, 512M
- **Grafana:** 1 CPU, 1G
- **app-python:** 0.5 CPU, 512M

### Security

- `GF_AUTH_ANONYMOUS_ENABLED=false` — no anonymous access
- Admin password via `GRAFANA_ADMIN_PASSWORD` (use `.env`, do not commit)
- Copy `monitoring/.env.example` to `monitoring/.env`

### Health Checks

- **Loki:** `GET http://localhost:3100/ready`
- **Grafana:** `GET http://localhost:3000/api/health`

---

## 7. Testing

```bash
# Stack health
docker compose ps
# All services should show "healthy" or "running"

# Loki
curl -s http://localhost:3100/ready
# Expected: ready

# Promtail targets
curl -s http://localhost:9080/targets | head -50

# App logs (JSON)
curl http://localhost:5000/health
docker logs devops-python 2>&1 | tail -5
```

### Example LogQL Queries

```
# All Docker container logs
{job="docker"}

# Python app by container name
{container=~".*devops-python.*"}

# Parse JSON and filter by level
{job="docker"} | json | level="INFO"

# Request rate
rate({job="docker"}[1m])
```

---

## 8. Challenges

1. **Promtail Docker discovery:** Required correct volume mounts (`/var/lib/docker/containers`, `/var/run/docker.sock`) for container log access.
2. **JSON logging with FastAPI:** Uvicorn configures logging early; setup must run at module load before uvicorn starts.
3. **Loki 3.0 config:** Used `schema_config` with v13 and TSDB; added `compactor` for retention.
4. **Grafana security:** Switched from anonymous auth to password-based; `.env` used for secrets.
