# Lab 07 — Centralized Logging with Grafana Stack

## Objective
Set up centralized logging for Docker containers using **Loki**, **Promtail**, and **Grafana** with Docker Compose.

## Project Structure

```text
monitoring/
├── docker-compose.yml
├── .env
├── loki/
│   └── config.yml
├── promtail/
│   └── config.yml
└── docs/
    └── LAB07.md
```

## Implemented Components

### Loki
Loki is used as the centralized log storage backend.

### Promtail
Promtail collects logs from Docker containers through Docker service discovery and pushes them to Loki.

### Grafana
Grafana is used to connect to Loki and visualize logs in dashboards.

## Configuration

### Environment Variables
File: `monitoring/.env`

```env
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin123
```

### Docker Compose
File: `monitoring/docker-compose.yml`

The stack contains 3 services:
- `loki`
- `promtail`
- `grafana`

Implemented features:
- named volumes for persistent storage
- shared Docker network
- container restart policy
- health checks for Loki and Grafana
- Grafana admin credentials from `.env`
- anonymous access disabled

### Loki Configuration
File: `monitoring/loki/config.yml`

Configured:
- `schema: v13`
- `store: tsdb`
- filesystem storage
- retention period enabled

### Promtail Configuration
File: `monitoring/promtail/config.yml`

Configured:
- Docker service discovery via `/var/run/docker.sock`
- labels for container, app, stream, and container id
- Docker log parsing pipeline

## Running the Stack

Commands used:

```bash
cd monitoring
docker compose up -d
docker compose ps
```

## Verification

### Loki health check
```bash
curl http://localhost:3100/ready
```
Result:
```text
ready
```

### Grafana health check
```bash
curl http://localhost:3000/api/health
```
Result:
```json
{
  "database": "ok",
  "version": "12.3.1"
}
```

## Grafana Access

URL:
```text
http://localhost:3000
```

Credentials:
```text
username: admin
password: admin123
```

## Loki Data Source
Added manually in Grafana with the following URL:

```text
http://loki:3100
```

Connection test was successful.

## Test Log Generator
A temporary container was started to generate logs:

```bash
docker run -d --name log-generator alpine sh -c 'while true; do echo "{\"level\":\"INFO\",\"message\":\"hello from container\"}"; sleep 2; done'
```

This container was used to verify that Promtail collects logs and sends them to Loki.

## Log Exploration
In Grafana Explore, logs were successfully queried with:

```logql
{app=~".+"}
```

## Dashboard
Dashboard title:

```text
Logs Monitoring Dashboard
```

Implemented panels:

1. **All Logs**
```logql
{app=~".+"}
```

2. **Error Logs**
```logql
{app=~".+"} | json | level="ERROR"
```

3. **Logs Rate**
```logql
sum(count_over_time({app=~".+"}[1m]))
```

4. **Log Level Distribution**
```logql
sum by (level) (count_over_time({app=~".+"} | json [5m]))
```

## Screenshots
Recommended screenshots for submission:
- `docker compose ps`
- Grafana data source connected
- Grafana Explore with logs visible
- final dashboard with 4 panels

## Notes
- Error Logs panel can be empty if no error-level logs were generated.
- The `log-generator` container is only for testing and can be removed after verification.

## Cleanup
Optional cleanup command:

```bash
docker rm -f log-generator
```
