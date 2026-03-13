
# LAB07 — Centralized Logging with Loki, Promtail and Grafana

## 1. Architecture

This lab implements a centralized logging stack using **Grafana Loki**, **Promtail**, and **Grafana**. The stack collects logs from a containerized Python application and allows querying and visualization of logs through Grafana dashboards.

### Components

- **Python Application**
  - FastAPI service running inside a Docker container
  - Generates application logs and HTTP request logs

- **Promtail**
  - Log collector agent
  - Reads container logs from Docker
  - Adds labels to logs
  - Sends logs to Loki

- **Loki**
  - Log storage and indexing system
  - Stores logs with labels
  - Provides LogQL query interface

- **Grafana**
  - Visualization platform
  - Connects to Loki as a data source
  - Used to explore logs and build dashboards

### Logging Flow

Python App → Docker Logs → Promtail → Loki → Grafana

---

## 2. Project Structure

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

---

## 3. Stack Deployment

The logging stack is deployed using **Docker Compose**.

### Services

- `loki`
- `promtail`
- `grafana`
- `python-app`

### Starting the stack

```bash
docker compose up -d
```

### Verifying containers

```bash
docker ps
```

Expected running containers:

```
loki
promtail
grafana
python-app
```

### Screenshot proof


![alt text](image.png)

---

## 4. Loki Configuration

Loki is configured using the file:

```
loki/config.yml
```

Key configuration elements:

### Storage

Logs are stored locally using the filesystem storage backend.

### Schema

Loki uses an indexed schema for efficient querying.

### HTTP Server

Loki exposes an HTTP API used by Promtail and Grafana.

Example snippet:

```yaml
server:
  http_listen_port: 3100
```

This allows Grafana and Promtail to connect to Loki at:

```
http://loki:3100
```

---

## 5. Promtail Configuration

Promtail is responsible for collecting logs and forwarding them to Loki.

Configuration file:

```
promtail/config.yml
```

### Log Source

Promtail reads container logs from:

```
/var/lib/docker/containers
```

### Labels

Promtail attaches labels to logs to allow filtering in Loki.

Example labels:

```
app
container
service_name
level
```

These labels are later used in **LogQL queries**.

### Loki Client

Promtail sends logs to Loki:

```yaml
clients:
  - url: http://loki:3100/loki/api/v1/push
```

---

## 6. Application Logging

A Python FastAPI application is deployed as a container:

```
darriyan0/app_python:latest
```

The application generates logs such as:

```
INFO: 192.168.65.1 - "GET / HTTP/1.1" 200 OK
INFO: 192.168.65.1 - "GET /health HTTP/1.1" 200 OK
```

These logs are written to container stdout and collected by Promtail.

### Endpoints

```
GET /
GET /health
```

Example request:

```bash
curl http://localhost:8000
curl http://localhost:8000/health
```

### Screenshot proof


![alt text](image-1.png)

---

## 7. Grafana Setup

Grafana runs on:

```
http://localhost:3000
```

Login:

```
username: admin
password: admin
```

### Loki Data Source

A Loki data source was configured using:

```
http://loki:3100
```

![alt text](image-2.png)

---

## 8. Log Exploration

Logs can be explored using the **Grafana Explore** interface.

Example queries:

### All application logs

```logql
{app="devops-python"}
```

### Health endpoint logs

```logql
{app="devops-python"} |= "/health"
```

### HTTP requests

```logql
{app="devops-python"} |= "GET"
```

### Successful responses

```logql
{app="devops-python"} |~ "200 OK"
```

### Screenshot proof

![alt text](image-4.png)

---

## 9. Grafana Dashboard

A Grafana dashboard named:

```
DevOps Monitoring
```

was created to visualize log activity.

### Panels

#### 1. Application Logs

Shows all logs from the Python application.

Query:

```logql
{app="devops-python"}
```

Visualization:

```
Logs
```

---

#### 2. Request Rate

Shows the rate of incoming requests.

Query:

```logql
sum(rate({app="devops-python"}[1m]))
```

Visualization:

```
Time series
```

---

#### 3. Health Checks

Counts requests to `/health`.

Query:

```logql
count_over_time({app="devops-python"} |= "/health"[5m])
```

Visualization:

```
Time series
```

---

#### 4. Errors

Displays error logs if they occur.

Query:

```logql
{app="devops-python"} |= "ERROR"
```

Visualization:

```
Logs
```

### Screenshot proof

![alt text](image-3.png)

---

## 10. Production Configuration

### Health Checks

Services include health checks to ensure reliability.

Example:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:3100/ready"]
```

### Resource Limits

Docker containers have resource limits to prevent excessive resource usage.

Example:

```yaml
deploy:
  resources:
    limits:
      cpus: "0.5"
      memory: 512M
    reservations:
      cpus: "0.25"
      memory: 256M
```

### Security

Grafana anonymous access is disabled to prevent unauthorized usage.

---

## 11. Testing

The logging pipeline was verified using test requests.

Example:

```bash
curl http://localhost:8000
curl http://localhost:8000/health
```

These requests generated logs that were successfully:

1. Collected by Promtail
2. Stored in Loki
3. Queried in Grafana
4. Visualized in the dashboard

---

## 12. Challenges

Several issues were encountered during the setup.

### 1. Docker Architecture Issue

The Docker image used for the Python application was built for `amd64`, while the host system uses Apple Silicon (`arm64`).

Solution:

```
platform: linux/amd64
```

was added to the Docker Compose service.

---

### 2. Port Mismatch

The application listens internally on port:

```
5000
```

but was initially accessed through port `8000`.

Solution:

```
8000:5000
```

port mapping in Docker Compose.

---

### 3. Prebuilt Application Logs

The Docker Hub image produces **standard Uvicorn logs** rather than structured JSON logs.

Despite this limitation, centralized log collection, querying and visualization work correctly.

Full JSON structured logging would require rebuilding the application image with a custom logging configuration.

---

## 13. Conclusion

In this lab a complete centralized logging pipeline was implemented using the Loki stack.

The system successfully:

- Collects logs from a containerized Python application
- Stores logs in Loki
- Allows querying with LogQL
- Visualizes logs and metrics using Grafana dashboards

The stack demonstrates how centralized logging can be implemented for containerized applications using open-source tools.
