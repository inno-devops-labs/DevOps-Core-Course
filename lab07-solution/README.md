# Lab 7 Solution

Minimal logging stack with Loki/Promtail/Grafana and JSON-logging Python app.

## Quick start

```powershell
cd lab07-solution/monitoring
# build and start all services including the app
docker compose up -d --build
# verify
docker compose ps
curl http://localhost:3100/ready
curl http://localhost:9080/targets
curl http://localhost:8000/
```