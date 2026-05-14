
# Lab 7 — Observability & Logging with Loki Stack

## Overview
In this lab we deployed a centralized logging stack using **Grafana Loki**, **Promtail**, and **Grafana**.
The goal was to collect logs from Docker containers and visualize them in Grafana dashboards.

Stack used:

- Loki 3.0.0 — log storage and query engine
- Promtail 3.0.0 — log collector
- Grafana 12.3.1 — visualization platform
- Docker Compose v2 — orchestration

Logs from Docker containers are discovered via the Docker socket and forwarded to Loki by Promtail.

## Architecture

Application containers write logs to **stdout/stderr**.

Docker stores logs under:

`/var/lib/docker/containers`

Promtail discovers containers through:

`/var/run/docker.sock`

Pipeline:

Docker containers → Promtail → Loki → Grafana → Dashboards

## Docker Compose Stack

Main services deployed:

- Loki — log storage
- Promtail — log collector
- Grafana — visualization UI

Deployment command:

```
docker compose up -d
```

Verify containers:

```
docker compose ps
```
Screenshot: `screenshots/7-1-containers.png`

## Loki Configuration

Loki listens on port **3100** (default Loki HTTP API port).

Check Loki health:

```
curl http://localhost:3100/ready
```

Expected response:

```
ready
```

Screenshot: `screenshots/7-2-loki-promtail.png`

## Promtail Configuration

Promtail uses **Docker Service Discovery** to detect containers automatically.

Promtail reads logs from:

`/var/lib/docker/containers`

Promtail discovers containers such as:

- devops-app
- grafana
- loki
- promtail

Check targets:
```
curl http://localhost:9080/targets
```
Screenshot: `screenshots/7-2-loki-promtail.png`

## Application Logging

Application logs are collected directly from Docker container output.

Example log entry:

```
172.18.0.1 - - [12/Mar/2026:18:43:37 +0000] "GET / HTTP/1.1" 200
```

Promtail forwards logs to Loki with labels:

- container
- job
- service_name

Check labels in Loki:

```
curl http://localhost:3100/loki/api/v1/labels
```

## Grafana Setup

Grafana runs on port 3000 on my server

Steps:

1. Open Connections
2. Add data source
3. Select Loki
4. URL: `http://loki:3100`

Click **Save & Test**.

## LogQL Queries

All container logs:

```
{container=~".+"}
```

Application logs:

```
{container="devops-app"}
```

Log rate:

```
sum by (container) (rate({container=~".+"}[1m]))
```

Log volume:

```
sum by (container) (count_over_time({container=~".+"}[5m]))
```

All shown later in dashboard

## Dashboard Panels
Screenshot: `screenshots/7-4-dashboard.png`

Panel 1 — All logs  
Query:
```
{container=~".+"}
```

Panel 2 — Application logs  
Query:
```
{container="devops-app"}
```

Panel 3 — Log volume by container
Query:
```
sum by (container) (count_over_time({container=~".+"}[5m]))
```

Panel 4 — Log rate by container  
Query:
```
sum by (container) (rate({container=~".+"}[1m]))
```

Panel 5 — Error logs   
Query:
```
{container="devops-app"} |= "error"
```

## Testing

Generate logs:

```
for i in {1..20}; do curl http://localhost:5000; done
```

Logs appear in Grafana Explore and dashboard panels.

Screenshot: `screenshots/7-3-logs.png`

## Production Readiness

Recommended improvements:

- Disable anonymous Grafana login
- Set admin password
- Add resource limits
- Add health checks
- Store secrets in .env

## Conclusion

The Loki logging stack was successfully deployed and integrated with Docker containers.

The system provides:

- centralized log collection
- real‑time log analysis
- visualization in Grafana
- LogQL querying capabilities

This setup demonstrates modern observability practices for containerized applications.