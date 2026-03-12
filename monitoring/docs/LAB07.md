# LAB07 — Centralized Logging with Loki, Promtail and Grafana

## 1. Architecture

This lab implements a centralized logging stack using **Grafana Loki**, **Promtail**, and **Grafana**. The Python application generates structured logs in JSON format which are collected and visualized.

### Architecture Overview

Flow of logs:

Python App → Docker logs → Promtail → Loki → Grafana

Components:

* **Python Application** – generates structured JSON logs
* **Docker** – stores container logs
* **Promtail** – collects logs from Docker containers
* **Loki** – stores and indexes logs
* **Grafana** – visualizes logs and dashboards

```
+-------------+
| Python App  |
+-------------+
       |
       v
+-------------+
| Docker Logs |
+-------------+
       |
       v
+-------------+
|  Promtail   |
+-------------+
       |
       v
+-------------+
|    Loki     |
+-------------+
       |
       v
+-------------+
|   Grafana   |
+-------------+
```

---

# 2. Setup Guide

### 1. Clone the repository

```bash
git clone https://github.com/Gpshfrd/DevOps-Core-Course.git
cd monitoring
```

### 2. Start the monitoring stack

```bash
docker compose up -d --build
```

This starts the following services:

* Loki
* Promtail
* Grafana
* Python application

### 3. Verify services

```bash
docker compose ps
```

Expected output:

* Loki – healthy
* Grafana – healthy
* Python app – healthy
* Promtail – running

[terminal screenshot showing docker compose ps with healthy services]

---

# 3. Configuration

## Loki Configuration

Loki is configured to store and index logs.

Example snippet:

```yaml
server:
  http_listen_port: 3100
```

This configuration exposes the Loki API on port **3100**, allowing Promtail to push logs.

Storage is configured using a local volume for persistence.

Why this configuration:

* Simple setup for development
* Persistent storage using Docker volumes
* Compatible with Grafana data source

---

## Promtail Configuration

Promtail collects logs from Docker containers.

Example snippet:

```yaml
scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
```

Promtail dynamically discovers containers using the Docker socket.

Labels are extracted using relabel rules:

```yaml
relabel_configs:
  - source_labels: ['__meta_docker_container_label_app']
    target_label: 'app'
```

Why this configuration:

* Automatically detects new containers
* Uses container labels for filtering
* Enables querying logs by application

---

# 4. Application Logging

The Python application uses the **logging module** with **python-json-logger** to generate structured logs.

Example configuration:

```python
formatter = jsonlogger.JsonFormatter(
 "%(asctime)s %(levelname)s %(message)s %(method)s %(path)s %(status)s %(client_ip)s"
)
```

This produces logs in JSON format such as:

```json
{
 "timestamp": "...",
 "level": "INFO",
 "message": "Request received",
 "method": "GET",
 "path": "/",
 "client_ip": "127.0.0.1"
}
```

### Logged Events

The application logs:

* Application startup
* HTTP requests
* Response status codes
* Errors and exceptions

Middleware functions were implemented:

```python
@app.before_request
```

Logs incoming requests.

```python
@app.after_request
```

Logs responses and status codes.

This structure makes logs easy to parse with **LogQL**.

---

# 5. Dashboard

A Grafana dashboard was created to visualize application logs.

The dashboard contains **four panels**.

---

## Panel 1 — Logs Table

Shows recent logs from all applications.

LogQL query:

```
{app=~"devops-.*"}
```

Explanation:

* Selects all log streams where the `app` label matches `devops-*`
* Displays raw logs in real time.

![](screenshots/logs%20table%203.png)

---

## Panel 2 — Request Rate

Displays log rate per application.

LogQL query:

```
sum by (app) (rate({app=~"devops-.*"}[1m]))
```

Explanation:

* Calculates logs per second
* Groups results by application

Visualization type:

Time Series graph.

![](screenshots/request%20rate%203.png)

---

## Panel 3 — Error Logs

Displays only logs with error level.

LogQL query:

```
{app=~"devops-.*"} | json | level="ERROR"
```

Explanation:

* Parses JSON logs
* Filters logs where level equals ERROR.

![](screenshots/error%20logs%20visualisation%203.png)

---

## Panel 4 — Log Level Distribution

Shows the number of logs grouped by level.

LogQL query:

```
sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))
```

Explanation:

* Parses JSON logs
* Counts logs per level over time.

Visualization type:

Stat panel.

![](screenshots/log%20level%20distribution%203.png)

---

# 6. Production Configuration

Several improvements were implemented to make the stack production-ready.

### Resource Limits

Docker resource limits prevent containers from consuming too many resources.

Example:

```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
```

This protects the system from resource exhaustion.

---

### Grafana Security

Anonymous access was disabled.

```yaml
GF_AUTH_ANONYMOUS_ENABLED=false
```

Admin credentials are stored in a `.env` file:

```
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=securepassword
```

This prevents unauthorized access.

![](screenshots/no%20anonymous%204.png)

---

### Health Checks

Health checks verify service availability.

Example for Loki:

```yaml
healthcheck:
 test: ["CMD-SHELL", "wget --spider http://localhost:3100/ready || exit 1"]
```

Health checks allow Docker to detect failed services.

---

# 7. Testing

Several commands were used to test the logging stack.

### Generate application logs

```bash
for i in {1..20}; do curl http://localhost:8000/; done
```

```bash
for i in {1..20}; do curl http://localhost:8000/health; done
```

These commands generate HTTP traffic and produce logs.

---

### Verify Loki API

```bash
curl http://localhost:3100/ready
```

Response:

```
ready
```

---

### Query logs in Grafana

Example LogQL queries:

```
{app="devops-python"}
```

![](screenshots/logs%20app%20devops-python%202.png)

Shows all logs from the Python application.

```
{app="devops-python"} |= "error"
```

![](screenshots/logs%20app%20devops-python%20error%202.png)

Filters logs containing the word "error".

```
{app="devops-python"} | json | method="GET"
```

![](screenshots/logs%20app%20devops-python%20json%20method%20GET%202.png)

Parses JSON logs and filters by HTTP method.


---

# 8. Challenges

Several challenges occurred during implementation.

### Healthcheck failing

Problem:

The Python container healthcheck returned **unhealthy**.

Cause:

The container did not include `curl`, so the healthcheck command failed.

Solution:

Use Python for the healthcheck instead of curl.

---

### Promtail JSON parsing error

Problem:

Promtail configuration produced the error:

```
invalid json stage config
```

Cause:

Incorrect indentation in the `pipeline_stages` configuration.

Solution:

Fix YAML structure so that `expressions` is nested correctly.

---

### Docker service discovery

Problem:

Promtail initially did not detect container labels.

Solution:

Use `relabel_configs` to extract Docker labels such as `app`.

---

# 9. Evidence

Evidence of completed tasks includes:

* Working Loki logging pipeline
* JSON logs from the Python application
* Grafana dashboard with four panels
* LogQL queries working in Explore
* Health checks reporting healthy containers
* Grafana secured with login authentication

![](screenshots/docker%20compose%20ps%204.png)

---
