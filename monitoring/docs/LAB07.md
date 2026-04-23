# Lab 7 — Observability & Logging with Loki Stack

**Name:** Makar
**Date:** 2026-03-12
**Lab Points:** 10 + 0 bonus

---

## 1. Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Docker Network: logging             │
│                                                      │
│  ┌─────────────┐    logs     ┌──────────────┐        │
│  │  app-python │───────────▶│   Promtail   │        │
│  │  :8000→5000 │             │  (collector) │        │
│  └─────────────┘             └──────┬───────┘        │
│                                     │ push           │
│  ┌─────────────┐                    ▼                │
│  │   Grafana   │  query       ┌──────────────┐       │
│  │   :3000     │◀──────────▶│    Loki      │       │
│  │ (dashboard) │              │   :3100      │       │
│  └─────────────┘              │ (TSDB store) │       │
│                               └──────────────┘       │
└──────────────────────────────────────────────────────┘
```

**Component roles:**
- **Loki 3.0** — Log aggregation and storage engine using TSDB index with filesystem backend. Unlike Elasticsearch, Loki only indexes labels (not full text), making it lightweight and efficient.
- **Promtail 3.0** — Agent that discovers Docker containers via the Docker socket, tails their logs, and pushes them to Loki with appropriate labels.
- **Grafana 12.3** — Visualization frontend. Queries Loki via LogQL and renders dashboards.
- **app-python** — The FastAPI application from Lab 1, now emitting structured JSON logs.

---

## 2. Setup Guide

### Prerequisites
- Docker Engine and Docker Compose v2 installed
- The `app_python/` directory with the updated app (JSON logging support)

### Deployment

```bash
cd monitoring

# Start the full stack
docker compose up -d

# Check service health
docker compose ps

# Verify Loki readiness
curl http://localhost:3100/ready

# Access Grafana
open http://localhost:3000
# Login: admin / (see .env file)
```

### Configure Grafana Data Source
1. Go to **Connections** → **Data sources** → **Add data source** → **Loki**
2. URL: `http://loki:3100`
3. Click **Save & Test** → should show "Data source connected"

### Generate Traffic
```bash
for i in {1..20}; do curl -s http://localhost:8000/; done
for i in {1..20}; do curl -s http://localhost:8000/health; done
```

---

## 3. Configuration

### Loki (`loki/config.yml`)

Key configuration choices:

```yaml
schema_config:
  configs:
    - from: "2024-01-01"
      store: tsdb              # TSDB: 10x faster queries than boltdb-shipper
      object_store: filesystem # Single-instance, local storage
      schema: v13              # Latest schema for Loki 3.0+

limits_config:
  retention_period: 168h       # 7-day retention
```

**Why TSDB over BoltDB?** Loki 3.0 introduced TSDB as the recommended index store. It provides up to 10x faster queries, lower memory usage, and better compression compared to the deprecated `boltdb-shipper`.

**Why `auth_enabled: false`?** Single-tenant deployment for development. Multi-tenancy would require an authentication proxy in production.

### Promtail (`promtail/config.yml`)

```yaml
scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
        filters:
          - name: label
            values: ["logging=promtail"]
```

**Docker service discovery** uses the Docker socket to automatically find containers. The `filters` setting ensures only containers with `logging=promtail` label are scraped — this prevents collecting logs from unrelated containers.

**Relabeling** extracts the container name (stripping the leading `/`) and the custom `app` label to use as Loki labels. This enables queries like `{app="devops-python"}`.

---

## 4. Application Logging

### JSON Formatter Implementation

Added a `JSONFormatter` class in `app_python/app.py`:

```python
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(...),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)
```

**Activation:** Controlled via `LOG_FORMAT` environment variable. When `LOG_FORMAT=json`, the JSON formatter is used; otherwise, the default text format is applied. This keeps backward compatibility.

**Middleware logging** now includes method, path, status code, and client IP:

```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    logger.info("method=%s path=%s status=%d client=%s",
                request.method, request.url.path,
                response.status_code, client_ip)
    return response
```

**Example JSON output:**
```json
{"timestamp": "2026-03-12T09:44:57.211Z", "level": "INFO", "logger": "devops-info-service", "message": "method=GET path=/ status=200 client=172.21.0.1"}
```

---

## 5. Dashboard

### Panel 1: Logs Table
- **Type:** Logs visualization
- **Query:** `{app=~"devops-.*"}`
- **Purpose:** Shows recent logs from all applications in real time

### Panel 2: Request Rate
- **Type:** Time series graph
- **Query:** `sum by (app) (rate({app=~"devops-.*"} [1m]))`
- **Purpose:** Shows logs per second by application, useful for spotting traffic spikes

### Panel 3: Error Logs
- **Type:** Logs visualization
- **Query:** `{app=~"devops-.*"} | json | level="ERROR"`
- **Purpose:** Filtered view showing only ERROR-level logs for quick incident detection

### Panel 4: Log Level Distribution
- **Type:** Stat/Pie chart
- **Query:** `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))`
- **Purpose:** Breakdown of log volumes by level (INFO, WARNING, ERROR) — helps assess health at a glance

### Additional LogQL queries:

```logql
# All Python app logs
{app="devops-python"}

# Only errors
{app="devops-python"} |= "ERROR"

# Parse JSON and filter by method
{app="devops-python"} | json | message=~".*method=GET.*"

# Count logs per minute
count_over_time({app="devops-python"}[1m])

# Logs containing "health"
{app="devops-python"} |= "health"
```

---

## 6. Production Configuration

### Resource Limits

All services have `deploy.resources` constraints:

| Service | CPU Limit | Memory Limit | CPU Reserved | Memory Reserved |
|---------|-----------|-------------|-------------|-----------------|
| Loki | 1.0 | 1G | 0.25 | 256M |
| Promtail | 0.5 | 512M | 0.1 | 128M |
| Grafana | 1.0 | 1G | 0.25 | 256M |
| app-python | 0.5 | 256M | 0.1 | 64M |

### Security

- **Anonymous access disabled:** `GF_AUTH_ANONYMOUS_ENABLED=false`
- **Admin credentials** stored in `.env` file (excluded via `.gitignore`)
- **Promtail Docker socket access** is read-only (`:ro`) to minimize attack surface

### Health Checks

- **Loki:** `wget --spider http://localhost:3100/ready` (10s interval, 15s start period)
- **Grafana:** `wget --spider http://localhost:3000/api/health` (10s interval, 15s start period)
- **Dependency ordering:** Promtail and Grafana wait for Loki to be healthy before starting

### Log Retention

- 7-day retention (`168h`) configured in Loki
- Compactor runs every 10 minutes to clean up expired logs
- Retention delete delay of 2 hours provides a safety buffer

---

## 7. Testing

### Verify all services are running:
```bash
docker compose ps
# Expected: all services healthy/running
```

### Verify Loki:
```bash
curl -s http://localhost:3100/ready
# Expected: "ready"
```

### Verify application logging:
```bash
# Generate traffic
for i in {1..20}; do curl -s http://localhost:8000/; done
curl -s http://localhost:8000/health

# Check logs reach Loki
curl -s 'http://localhost:3100/loki/api/v1/query?query={app="devops-python"}' | python3 -m json.tool
```

### Verify Grafana:
```bash
curl -s http://localhost:3000/api/health
# Expected: {"commit":"...","database":"ok","version":"12.3.1"}
```

### LogQL test queries in Grafana Explore:
1. `{job="docker"}` — all container logs
2. `{app="devops-python"}` — Python app logs only
3. `{app="devops-python"} | json | level="INFO"` — parsed JSON filtering
4. `rate({app="devops-python"}[1m])` — request rate metric

---

## 8. Challenges

1. **Loki 3.0 TSDB configuration:** The schema v13 + TSDB store requires specific `common.storage` configuration. Older Loki examples use `boltdb-shipper` which is deprecated. The `common` section in Loki 3.0 simplifies the config considerably by reducing duplication between `storage_config` and `schema_config`.

2. **Promtail Docker SD filtering:** Without the `filters` option in `docker_sd_configs`, Promtail would scrape all containers including itself and Loki, creating a log feedback loop. Using `logging=promtail` label to opt-in containers prevents this.

3. **JSON logging backward compatibility:** Using an environment variable (`LOG_FORMAT=json`) to toggle JSON output ensures the app works both in development (human-readable text) and production (machine-parseable JSON) without code changes. Existing tests pass unchanged.

4. **Log retention + compactor:** Retention in Loki only works when the compactor is enabled with `retention_enabled: true`. Without the compactor section, Loki silently ignores `retention_period` in `limits_config`.
