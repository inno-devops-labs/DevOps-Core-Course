# Evidence
## Task 1
![Grafana logs in grafana](./grafana_logs.png)
![Loki logs in grafana](./loki_logs.png)
![Prometheus logs in grafana](./prometheus_logs.png)

## Task 2
![JSON output from application](./python_json_log.png)
![Grafana showing logs from both apps](./grafana_both_logs.png)
Log QL Queries used:
- `{container="monitoring-infoservice-python-1"} |= ""`
- `{container="monitoring-infoservice-python-1"} |= "ERROR"`
- `{container="monitoring-infoservice-python-1"} | json | __error__=''`

## Task 3
![Working dashboard](./dashboard.png)

## Task 4
![`docker compose ps` output](./docker_ps.png)
![Logged grafana](./grafana_logged.png)

# Architecture
# Setup Guide
# Configuration
# Application Logging
# Dashboard
# Production Config
# Testing
# Challenges
- There is no `curl` in some images to check health, therefore had to use `wget` instead.
