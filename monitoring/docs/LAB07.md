# Lab 7: Observability & Logging with Loki Stack - Submission

**Name:** Sergey
**Date:** 2026-03-12
**Lab Points:** 10

---

## Task 1: Deploy Loki Stack (4 pts)

### Project Structure

```
monitoring/
├── docker-compose.yml
├── loki/
│   └── config.yml
├── promtail/
│   └── config.yml
└── docs/
    └── LAB07.md
```

### Loki Configuration

**File:** `monitoring/loki/config.yml`

Key settings:
- Schema: v13 with TSDB (10x faster queries)
- Storage: filesystem for single-instance
- Retention: 168h (7 days)
- Port: 3100
- Compactor enabled for automatic cleanup

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

### Promtail Configuration

**File:** `monitoring/promtail/config.yml`

Docker service discovery setup:
- Filters containers with label `logging=promtail`
- Extracts container name, app label
- Refresh interval: 5s

```yaml
scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        filters:
          - name: label
            values: ["logging=promtail"]
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container'
      - source_labels: ['__meta_docker_container_label_app']
        target_label: 'app'
```

### Docker Compose

**File:** `monitoring/docker-compose.yml`

Services deployed:
- Loki 3.0.0 (port 3100)
- Promtail 3.0.0
- Grafana 11.3.0 (port 3000)
- app-python (port 8000)

All services:
- Connected to `logging` network
- Have labels `logging: "promtail"` and `app: "<name>"`
- Use named volumes for persistence
- Have health checks (Loki, Grafana)
- Have resource limits configured

### Deployment

```bash
cd monitoring
docker compose up -d
docker compose ps
```

Verification:
```bash
curl http://localhost:3100/ready          # Loki ready
curl http://localhost:9080/targets         # Promtail targets
curl http://localhost:3000/api/health      # Grafana health
```

Grafana data source:
- URL: `http://loki:3100`
- Test query: `{job="docker"}`

---

## Task 2: Integrate Applications (3 pts)

### JSON Logging Implementation

**Updated:** `app_python/app.py`

Custom JSONFormatter:

```python
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "client_ip"):
            log_data["client_ip"] = record.client_ip
            
        return json.dumps(log_data)
```

HTTP middleware for request/response logging:

```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    
    logger.info("Incoming request", extra={
        "method": request.method,
        "path": request.url.path,
        "client_ip": client_ip,
    })
    
    response = await call_next(request)
    
    logger.info("Request completed", extra={
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "client_ip": client_ip,
    })
    
    return response
```

Example JSON log output:

```json
{
  "timestamp": "2026-03-12T19:30:45.123456Z",
  "level": "INFO",
  "logger": "__main__",
  "message": "Incoming request",
  "module": "app",
  "function": "log_requests",
  "line": 45,
  "method": "GET",
  "path": "/",
  "client_ip": "172.18.0.1"
}
```

### Application in Docker Compose

```yaml
app-python:
  image: 4hellboy4/devops-info-service:latest
  container_name: devops-python
  ports:
    - "8000:8000"
  networks:
    - logging
  labels:
    logging: "promtail"
    app: "devops-python"
  restart: unless-stopped
```

### LogQL Queries

```logql
# All logs from Python app
{app="devops-python"}

# Only ERROR logs
{app="devops-python"} | json | level="ERROR"

# Filter by HTTP method
{app="devops-python"} | json | method="GET"

# Filter by status code
{app="devops-python"} | json | status_code >= 400

# Search text
{app="devops-python"} |= "Incoming request"
```

---

## Task 3: Build Log Dashboard (2 pts)

### Dashboard Panels

**Panel 1: Logs Table**
- Query: `{app=~"devops-.*"}`
- Shows recent logs from all applications

**Panel 2: Request Rate**
- Query: `sum by (app) (rate({app=~"devops-.*"} [1m]))`
- Time series graph of logs/sec by app

**Panel 3: Error Logs**
- Query: `{app=~"devops-.*"} | json | level="ERROR"`
- Shows only ERROR level logs

**Panel 4: Log Level Distribution**
- Query: `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))`
- Count of logs by level (INFO, ERROR, etc.)

---

## Task 4: Production Readiness (1 pt)

### Resource Limits

All services have resource constraints:

| Service | CPU Limit | Memory Limit | CPU Reserve | Memory Reserve |
|---------|-----------|--------------|-------------|----------------|
| Loki | 1.0 | 1G | 0.5 | 512M |
| Promtail | 0.5 | 512M | 0.25 | 256M |
| Grafana | 1.0 | 1G | 0.5 | 512M |
| app-python | 0.5 | 512M | 0.25 | 256M |

### Grafana Security

```yaml
environment:
  - GF_AUTH_ANONYMOUS_ENABLED=false
  - GF_SECURITY_ADMIN_USER=admin
  - GF_SECURITY_ADMIN_PASSWORD=admin
  - GF_USERS_ALLOW_SIGN_UP=false
```

Anonymous access disabled, authentication required.

### Health Checks

Loki and Grafana have health checks:

```yaml
healthcheck:
  test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:3100/ready || exit 1"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 10s
```

Verification:
```bash
docker compose ps
# Shows (healthy) status for Loki and Grafana
```

---

## Summary

Deployed complete Loki stack:
- ✅ Loki 3.0 with TSDB
- ✅ Promtail with Docker service discovery
- ✅ Grafana 11.3 with Loki data source
- ✅ Python app with JSON logging
- ✅ Dashboard with 4 panels
- ✅ Resource limits on all services
- ✅ Health checks configured
- ✅ Secured Grafana
- ✅ 7-day log retention

All services running and logs visible in Grafana.
