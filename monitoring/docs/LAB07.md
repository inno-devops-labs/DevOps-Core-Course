# Lab Report #7 — Observability & Logging with Loki Stack

## 1. Solution Architecture

A centralized log collection and visualization system has been implemented based on the **PLG stack (Promtail, Loki, Grafana)**.

* **Loki 3.0** – Log storage engine using the modern TSDB backend for efficient indexing and compression.
* **Promtail** – Log collection agent configured for automatic Docker Service Discovery via `/var/run/docker.sock`.
* **Grafana 12.3** – Visualization platform used for LogQL queries and dashboards.
* **Python App** – Application emitting structured JSON logs for easier analysis.

The architecture allows collecting logs from containers, storing them in Loki, and visualizing them through Grafana dashboards.

---

## 2. Component Configuration

### 2.1 Loki (Storage)

The `loki/config.yml` configuration includes:

* **Retention:** Logs are stored for **7 days (168h)**.
* **Storage:** Uses **TSDB index** and **local filesystem** for chunks.
* **Compactor:** Enabled for automatic cleanup of old data according to the retention policy.

This configuration ensures efficient storage and automatic removal of outdated logs.

---

### 2.2 Promtail (Log Collector)

The `promtail/config.yml` file implements **Docker service discovery** and **relabeling**.

Relabeling configuration:

* **Source label:** `__meta_docker_container_name`
* **Transformation:** Remove leading `/` from the container name
* **Result label:** `container`

Example transformation:

```
/monitoring-app-python-1 → monitoring-app-python-1
```

This label is then used in Grafana queries for filtering logs.

---

### 2.3 Docker Compose (Production Readiness)

The `docker-compose.yml` configuration was improved to follow **production-ready practices**.

**Resource Limits**

CPU and memory limits were configured to prevent resource exhaustion:

```
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

**Health Checks**

Health checks were implemented to verify service availability.

Loki:

```
wget --spider http://127.0.0.1:3100/ready
```

Grafana:

```
curl -f http://127.0.0.1:3000/api/health
```

**Security**

* Anonymous access in Grafana was disabled.
* Admin password is injected via environment variables.
* Secrets are stored in a `.env` file.

---

## 3. Application and Structured Logs

The application was configured to produce **JSON structured logs**.

Example log entry:

```json
{"timestamp": "2024-05-20T10:00:00.123Z", "level": "INFO", "method": "GET", "path": "/", "ip": "172.18.0.5", "message": "Request received"}
```

This allows advanced parsing using **LogQL**.

Example query:

```
{container="devops-python"} | json | level="INFO"
```

---

## 4. Visualization (Grafana Dashboard)

A dashboard was created in Grafana containing **four panels**.

**Logs Table**

Displays a real-time stream of logs from `devops-*` services.

**Request Rate**

Shows the number of logs per second (RPS) grouped by container.

**Error Logs**

Filters log entries with `ERROR` level from the JSON payload.

**Log Level Distribution**

A pie chart visualizing the distribution of log levels (INFO, WARNING, ERROR).

---

## 5. Health Status Verification

Service health was verified using:

```
docker compose ps
```

Example output:

```
loki: healthy
grafana: healthy
promtail: running
app-python: running
```

This confirms that all components of the logging stack are operational.

---

## 6. Challenges & Solutions

**Problem**

The default Loki health check using `curl` failed, causing the container status to remain `starting`.

**Cause**

The official `grafana/loki:3.0.0` image does not include the `curl` utility.

**Solution**

The health check was changed to:

```
wget --spider http://127.0.0.1:3100/ready
```

`wget` is available in the image and successfully verifies Loki readiness.

---

## Conclusion

The PLG logging stack was successfully deployed using Docker Compose.

Logs from the Python application are collected by Promtail, stored in Loki, and visualized in Grafana dashboards. The system supports structured logs, LogQL queries, health checks, and production-ready configuration.

The environment is ready for centralized logging and monitoring of containerized applications.
