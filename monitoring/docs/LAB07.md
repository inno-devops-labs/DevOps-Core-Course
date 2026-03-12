# Lab 7: Observability & Logging with Loki Stack

## 1. Overview

In this lab I deployed a complete logging stack using **Loki 3.0** (log storage with TSDB), **Promtail 3.0** (log collector), and **Grafana 12.3** (visualization). I integrated my containerized Python application (and optionally a bonus Go app) to produce structured JSON logs. Finally, I built a Grafana dashboard with four panels to explore and analyse the logs.

**Objectives achieved:**
- Loki, Promtail, Grafana running in Docker Compose.
- Python application logging in JSON format via `python-json-logger`.
- Promtail configured to scrape only containers labelled `logging=promtail`.
- Grafana data source connected to Loki.
- Dashboard with logs table, request rate, error logs, and log‑level distribution.

## 2. Architecture

The diagram below illustrates how the components interact:

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   App(s)    │ ──→ │   Promtail   │ ──→ │    Loki     │
│  (Python/Go)│ logs │  (collector) │ push │  (storage)  │
└─────────────┘      └─────────────┘      └─────────────┘
                                               │
                                               │ query
                                               ↓
                                         ┌─────────────┐
                                         │   Grafana   │
                                         │(visualisation│
                                         └─────────────┘
```

- **Promtail** reads container logs via the Docker socket, attaches labels (e.g. `app`, `container`), and forwards them to Loki.
- **Loki** stores logs and indexes them using TSDB (the default in Loki 3.0). A retention period of 7 days is configured.
- **Grafana** queries Loki and displays logs in dashboards.

All services run inside a Docker Compose project, share a dedicated network `logging`, and are configured with health checks and resource limits.

## 3. Setup Guide

### 3.1 Prerequisites
- Docker and Docker Compose v2 installed.
- Python application container image (from Lab 1) rebuilt with JSON logging (see Section 4).
- (Optional) Bonus Go container image.

### 3.2 Directory Structure
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

### 3.3 Start the Stack
```bash
cd monitoring
docker compose up -d
```

Check the status:
```bash
docker compose ps
```
All services should report `healthy`.

### 3.4 Verify Each Component

- **Loki** readiness:
  ```bash
  curl http://localhost:3100/ready
  # expected: "ready"
  ```

- **Promtail** targets:
  ```bash
  curl http://localhost:9080/targets
  # lists discovered containers (only those with label logging=promtail)
  ```

- **Grafana** health:
  ```bash
  curl http://localhost:3000/api/health
  # expected: {"database":"ok"}
  ```

### 3.5 Add Loki Data Source in Grafana
1. Open `http://localhost:3000` (login: `admin` / `admin`).
2. Go to **Connections** → **Data sources** → **Add data source** → **Loki**.
3. Set URL to `http://loki:3100`.
4. Click **Save & test** – success message confirms connection.

## 4. Configuration Files

### 4.1 Docker Compose (`docker-compose.yml`)

The file defines four services: `loki`, `promtail`, `grafana`, and the application(s). Key features:
- Named volumes for Loki and Grafana data persistence.
- Shared network `logging`.
- Resource limits and health checks for production readiness.
- Labels on applications to enable Promtail scraping.

**Relevant snippets:**

**Loki service:**
```yaml
loki:
  image: grafana/loki:3.0.0
  ports: ["3100:3100"]
  volumes:
    - ./loki/config.yml:/etc/loki/config.yml
    - loki-data:/loki
  command: -config.file=/etc/loki/config.yml
  healthcheck:
    test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:3100/ready || exit 1"]
```

**Promtail service:**
```yaml
promtail:
  image: grafana/promtail:3.0.0
  volumes:
    - ./promtail/config.yml:/etc/promtail/config.yml
    - /var/lib/docker/containers:/var/lib/docker/containers:ro
    - /var/run/docker.sock:/var/run/docker.sock:ro
  command: -config.file=/etc/promtail/config.yml
```

**Grafana service:**
```yaml
grafana:
  image: grafana/grafana:12.3.1
  ports: ["3000:3000"]
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
    - GF_AUTH_ANONYMOUS_ENABLED=false
  volumes:
    - grafana-data:/var/lib/grafana
  healthcheck:
    test: ["CMD-SHELL", "curl -f http://localhost:3000/api/health || exit 1"]
```

**Python application:**
```yaml
app-python:
  image: <your-dockerhub-username>/devops-info-service:json-logging
  ports: ["8000:8000"]
  labels:
    logging: "promtail"
    app: "devops-python"
  networks:
    - logging
```

### 4.2 Loki Configuration (`loki/config.yml`)

Based on Loki 3.0 best practices, this configuration uses **TSDB** for fast queries and sets a 7‑day retention.

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
  compaction_interval: 10m
  retention_enabled: true
  retention_delete_delay: 2h
  retention_delete_worker_count: 150
  delete_request_store: filesystem   # required when retention is enabled

limits_config:
  retention_period: 168h  # 7 days
  reject_old_samples: true
  reject_old_samples_max_age: 168h

table_manager:
  retention_deletes_enabled: true
  retention_period: 168h
```

### 4.3 Promtail Configuration (`promtail/config.yml`)

Promtail discovers Docker containers via the Docker socket, filters those with the label `logging=promtail`, and relabels them to add useful labels like `app` and `container`.

```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
        filters:
          - name: label
            values: ["logging=promtail"]
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container'
      - source_labels: ['__meta_docker_container_label_app']
        target_label: 'app'
      - source_labels: ['__meta_docker_container_label_logging']
        target_label: 'logging'
```

**Why these filters?**  
- The `filters` section prevents Promtail from scraping every container, reducing noise.
- Relabeling adds human‑readable labels that can be used in LogQL queries (e.g. `{app="devops-python"}`).

## 5. Application Logging

### 5.1 Adding JSON Logging to Python App

The original application from Lab 1 was extended to output logs in JSON format using the `python-json-logger` library. The updated code:

**`requirements.txt` addition:**
```
python-json-logger==2.0.7
```

**Key changes in `app.py`:**

1. **Configure JSON formatter**:
   ```python
   from pythonjsonlogger import jsonlogger

   logHandler = logging.StreamHandler()
   formatter = jsonlogger.JsonFormatter(
       fmt='%(asctime)s %(levelname)s %(name)s %(message)s',
       datefmt='%Y-%m-%dT%H:%M:%S%z'
   )
   logHandler.setFormatter(formatter)
   logging.getLogger().addHandler(logHandler)
   ```

2. **Middleware to log every HTTP request**:
   ```python
   @app.middleware("http")
   async def log_requests(request: Request, call_next):
       response = await call_next(request)
       logger.info(
           "HTTP Request",
           extra={
               "method": request.method,
               "path": request.url.path,
               "client_ip": request.client.host if request.client else None,
               "status_code": response.status_code,
           }
       )
       return response
   ```

3. **Error handlers** now include extra context.

After these changes, the image was rebuilt and pushed to Docker Hub with the tag `json-logging`.

### 5.2 Testing the Logs

After updating the Docker Compose to use the new image, traffic was generated:

```bash
for i in {1..20}; do curl -s http://localhost:8000/ > /dev/null; done
for i in {1..20}; do curl -s http://localhost:8000/health > /dev/null; done
```

In Grafana Explore, the following query shows JSON‑parsed logs:
```
{app="devops-python"} | json
```

Fields like `level`, `method`, `status_code` are extracted and can be used for filtering.

## 6. Grafana Dashboard

I created a dashboard named **Application Logs** with four panels.

### 6.1 Panel 1: Logs Table
- **Query:** `{app=~"devops-.*"}`
- **Visualisation:** Logs
- **Purpose:** Shows the most recent log lines from all applications, with colour coding and the ability to expand each entry.

### 6.2 Panel 2: Request Rate (Time Series)
- **Query:** `sum by (app) (rate({app=~"devops-.*"}[1m]))`
- **Visualisation:** Time series
- **Purpose:** Displays logs per second grouped by application, giving an overview of traffic.

### 6.3 Panel 3: Error Logs
- **Query:** `{app=~"devops-.*"} | json | level="ERROR"`
- **Visualisation:** Logs
- **Purpose:** Shows only ERROR level logs, helping to quickly spot issues.

### 6.4 Panel 4: Log Level Distribution
- **Query:** `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))`
- **Visualisation:** Pie chart
- **Purpose:** Visualises the proportion of log levels (INFO, ERROR, etc.) over the last 5 minutes.

All panels use the Loki data source and refresh automatically. The dashboard provides a comprehensive view of application behaviour.

## 7. Production‑Ready Configuration

### 7.1 Resource Limits
Each service includes `deploy.resources` with CPU and memory limits. For example:
```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### 7.2 Health Checks
Health checks are defined for Loki, Promtail, and Grafana. They ensure that containers are marked as unhealthy if the service is not responding, allowing orchestration tools to restart them.

### 7.3 Security
- Anonymous access to Grafana is disabled (`GF_AUTH_ANONYMOUS_ENABLED=false`).
- An admin password is set via environment variable (in production, this should be stored in a secret or .env file).
- Promtail has limited access to the Docker socket; it only reads container logs and metadata.

### 7.4 Data Retention
Loki is configured to keep logs for 7 days (168 hours). Older logs are automatically purged by the compactor.

## 8. Testing & Verification

### 8.1 Service Health
```bash
docker compose ps
```
All services are `Up` and `healthy`.

### 8.2 Log Availability
In Grafana Explore, a simple query:
```
{app="devops-python"}
```
returns a stream of log entries. Adding `| json` reveals the structured fields.

### 8.3 Dashboard Functionality
All four panels display data. The request rate graph shows activity when traffic is generated.

## 9. Challenges & Solutions

- **Loki configuration errors**: Initially the `compactor` section contained an invalid field `shared_store`. After consulting the Loki 3.0 documentation, I removed it and added the required `delete_request_store` field.
- **Promtail not scraping**: Forgot to add the `logging: promtail` label to the application service. Once added, Promtail targets showed the container.
- **Grafana data source connection**: At first I used `localhost:3100` instead of the Docker service name `loki:3100`. Changing to the service name resolved the issue because containers communicate via the internal network.

## 10. Conclusion

This lab successfully implemented a centralised logging solution using the Grafana Loki stack. The Python application now emits structured JSON logs, which are collected by Promtail and stored in Loki. A Grafana dashboard with four panels provides real‑time observability of application logs, request rates, and error distributions. The setup follows production best practices with resource limits, health checks, and a 7‑day retention policy.

All components are version‑controlled in the `monitoring/` directory and can be re‑deployed with a single `docker compose up -d` command.