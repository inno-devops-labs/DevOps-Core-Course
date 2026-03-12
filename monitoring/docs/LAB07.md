# Lab 7 — Observability & Logging with Loki Stack

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Logging%20%26%20Observability-blue)
![points](https://img.shields.io/badge/points-10%2B2.5-orange)
![tech](https://img.shields.io/badge/tech-Loki%20|%20Promtail%20|%20Grafana-informational)

> Deploy a logging stack with Loki, Promtail, and Grafana to aggregate and visualize logs from your containerized applications.

## Overview

Set up centralized logging for your applications using the Grafana Loki stack. You'll deploy Loki 3.0 (log storage with TSDB), Promtail 3.0 (log collector), and Grafana 12.3 (visualization), then integrate your apps from previous labs.

**What You'll Learn:**
- Loki 3.0 architecture with TSDB (10x faster queries!)
- Promtail configuration for Docker log collection
- LogQL query language basics
- Building interactive log dashboards in Grafana
- Production logging practices and retention policies

**Prerequisites:** Lab 1 (web apps), Lab 2 (Docker)

**Tech Stack:** Loki 3.0 + Promtail 3.0 + Grafana 12.3

---

## Screenshots

1. **Grafana Explore - Logs from 3+ containers** `[screenshot_01_loki_explore_logs.png]`
2. **Python App JSON Log Output** `[screenshot_02_python_json_logs.png]`
3. **Grafana - Logs from Both Apps** `[screenshot_03_both_apps_logs.png]`
4. **LogQL Query - INFO Level** `[screenshot_04_logql_info_logs.png]`
5. **LogQL Query - Request Rate** `[screenshot_05_logql_rate.png]`
6. **LogQL Query - Count by Level** `[screenshot_06_logql_count_by_level.png]`
7. **Complete Dashboard (4 panels)** `[screenshot_07_dashboard_complete.png]`
8. **Docker Compose Status** `[screenshot_08_docker_compose_ps.png]`
9. **Grafana Login Page** `[screenshot_09_grafana_login.png]`

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│             Docker Compose Network (monitoring_logging)            │
└────────────────────────────────────────────────────────────────────┘
                    │                │                │
                    ▼                ▼                ▼
            ┌───────────┐  ┌──────────────┐  ┌────────────┐
            │   Loki    │  │  Promtail    │  │  Grafana   │
            │  (3100)   │◄─│              │◄─│   (3000)   │
            │  TSDB     │  │  Collects    │  │  Visualize │
            └─────▲─────┘  │  logs        │  └─────▲──────┘
                  │        │  Docker SD   │        │
                  │        └──────────────┘        │
                  │                                │
                  │         ┌──────────────┐       │
                  └─────────│  JSON Logs   │───────┘
                            │  (stdout)    │
                    ┌───────┴─────┬────────┴────┐
                    │             │             │
                ┌───▼────┐    ┌───▼─────┐   ┌───▼─────┐
                │ Python  │   │   Go    │   │ Loki    │
                │   App   │   │   App   │   │Promtail │
                │ (:8000) │   │ (:8001) │   │ (self)  │
                └─────────    └─────────┘   └─────────┘
```

---

## Setup Guide

### Prerequisites
- Docker Engine running

### Deployment Steps

```bash
cd monitoring/
docker compose up -d
docker compose ps
```

### Testing

```bash
# Test services
curl http://localhost:3100/ready
curl http://localhost:8000/
curl http://localhost:8001/
curl http://localhost:3000/api/health

# Generate traffic
for i in {1..30}; do curl -s http://localhost:8000/ > /dev/null; done
```

### Access
- **Grafana**: http://localhost:3000 (admin/admin)
- **Dashboard**: http://localhost:3000/d/devops-logs-dashboard/devops-application-logs

---

## Configuration

### Loki Configuration (`loki/config.yml`)

Key settings:
- TSDB storage for 10x faster queries
- 7-day log retention (168h)
- Schema v13 optimized for TSDB
- Filesystem object store for single-instance setup

### Promtail Configuration (`promtail/config.yml`)

Key settings:
- File-based discovery for Docker logs
- Pipeline stages to handle Docker's JSON wrapper
- Position tracking to avoid re-processing

### Application Logging

**Python App** - JSON formatter with fields:
- timestamp, level, logger, message
- method, path, status, client_ip, duration_ms

**Go App** - JSON struct logging with fields:
- timestamp, level, logger, message
- method, path, status, client_ip, duration_ms

---

## Dashboard

Four-panel Grafana dashboard:

1. **Recent Logs** - `{job="container-logs"}`
2. **Request Rate** - `sum(rate({job="container-logs"}[1m]))`
3. **Error Logs** - `{job="container-logs", level="ERROR"}`
4. **Log Level Distribution** - `sum by (level) (count_over_time({job="container-logs"} | unwrap [5m]))`

---

## Production Config

**Security:**
- Grafana anonymous access disabled
- Admin password configurable

**Resource Limits:**
| Service | CPU Limit | Memory Limit |
|---------|-----------|--------------|
| Loki    | 1.0       | 1G           |
| Grafana  | 1.0       | 1G           |
| Promtail | 0.5       | 256M         |
| Apps     | 0.5       | 256M         |

**Health Checks:**
- Loki: `wget -q --spider http://localhost:3100/ready`
- Grafana: `wget -q --spider http://localhost:3000/api/health`
- Python app: `python -c "import urllib.request; ..."`
- Go app: `wget -q --spider http://localhost:8080/health`

**Retention:**
- 7 days in Loki (168h)
- Compaction every 10 minutes
- Docker logs: 10MB max, 3 files per container

---

## Testing

### LogQL Queries

```logql
# All logs
{job="container-logs"}

# INFO only
{job="container-logs"} | json | level="INFO"

# Error only
{job="container-logs"} | json | level="ERROR"

# Request rate
sum(rate({job="container-logs"}[1m]))

# Count by level
sum by (level) (count_over_time({job="container-logs"} | unwrap [5m]))

# By logger
{job="container-logs"} | json | logger="__main__"
```

---

## Evidence

- [x] Loki, Promtail, Grafana running via Docker Compose
- [x] Loki data source configured in Grafana
- [x] Python app logging in JSON format
- [x] Go app logging in JSON format
- [x] Logs visible in Grafana from all containers
- [x] Dashboard with 4 panels created
- [x] LogQL queries working
- [x] Resource limits on all services
- [x] Health checks added
- [x] Grafana secured (no anonymous access)
- [x] Complete documentation

---

## Resources

- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Promtail Documentation](https://grafana.com/docs/loki/latest/send-data/promtail/)
- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [LogQL Reference](https://grafana.com/docs/loki/latest/query/)
