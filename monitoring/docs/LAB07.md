# lab 07: observability & logging with loki stack

## 1. architecture overview

### components

| component | purpose | port |
|-----------|---------|------|
| loki | log aggregation and storage | 3100 |
| promtail | log collection agent | 9080 |
| grafana | visualization and dashboards | 3000 |
| app-python | application with json logging | 8000 |

### data flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   promtail   │────▶│     loki     │◀────│    grafana   │
│  (collector) │     │   (storage)  │     │(visualization)│
└──────┬───────┘     └──────────────┘     └──────────────┘
       │
       │ reads logs from
       ▼
┌──────────────────────────────────────────────────────┐
│           docker containers (json logs)              │
│  ┌─────────────────┐                                 │
│  │   app-python    │                                 │
│  │   (devops-*)    │                                 │
│  └─────────────────┘                                 │
└──────────────────────────────────────────────────────┘
```

---

## 2. stack deployment

### project structure

```
monitoring/
├── docker-compose.yml
├── .env.example
├── loki/
│   └── config.yml
├── promtail/
│   └── config.yml
├── grafana/
│   └── provisioning/
│       ├── datasources/
│       │   └── datasources.yml
│       └── dashboards/
│           ├── dashboards.yml
│           └── json/
│               └── devops-logs-dashboard.json
└── docs/
    └── LAB07.md
```

### configuration files

| file | purpose |
|------|---------|
| [docker-compose.yml](../docker-compose.yml) | main stack definition |
| [loki/config.yml](../loki/config.yml) | loki storage and retention |
| [promtail/config.yml](../promtail/config.yml) | log collection and discovery |
| [grafana/provisioning/datasources/datasources.yml](../grafana/provisioning/datasources/datasources.yml) | loki data source |
| [.env.example](../.env.example) | environment template |

### key configuration concepts

**loki:**

| concept | value | why |
|---------|-------|-----|
| `auth_enabled: false` | disabled | single-tenant dev setup, no multi-tenancy needed |
| `store: tsdb` | tsdb | loki 3.0+ default, 10x faster queries than boltdb |
| `schema: v13` | v13 | latest schema, required for tsdb |
| `retention_period: 168h` | 7 days | balance storage cost with debugging needs |
| `retention_enabled: true` | enabled | compactor auto-deletes old logs |

**promtail:**

| concept | value | why |
|---------|-------|-----|
| `docker_sd_configs` | docker socket | auto-discover containers without manual config |
| `filters: logging=promtail` | label filter | only scrape labeled containers, reduce noise |
| `positions file` | `/tmp/positions.yaml` | track read position, avoid duplicate logs |
| `relabel_configs` | extract labels | container name and app label become loki labels |

**grafana:**

| concept | value | why |
|---------|-------|-----|
| provisioning | auto-config | data source created automatically, no manual setup |
| `isDefault: true` | default ds | queries use loki by default |
| environment vars | `.env` file | secrets not in compose file, easier rotation |

### deployment

```bash
cd monitoring
docker compose up -d
docker compose ps

NAME            IMAGE                                       COMMAND                  SERVICE      CREATED          STATUS                    PORTS
devops-python   onemoreslacker/devops-info-service:latest   "uvicorn app:app --h…"   app-python   34 minutes ago   Up 34 minutes (healthy)   0.0.0.0:8000->5000/tcp, [::]:8000->5000/tcp
grafana         grafana/grafana:12.3.1                      "/run.sh"                grafana      42 minutes ago   Up 41 minutes (healthy)   0.0.0.0:3000->3000/tcp, [::]:3000->3000/tcp
loki            grafana/loki:3.0.0                          "/usr/bin/loki -conf…"   loki         42 minutes ago   Up 41 minutes (healthy)   0.0.0.0:3100->3100/tcp, [::]:3100->3100/tcp, 0.0.0.0:9096->9096/tcp, [::]:9096->9096/tcp
promtail        grafana/promtail:3.0.0                      "/usr/bin/promtail -…"   promtail     13 minutes ago   Up 13 minutes             0.0.0.0:9080->9080/tcp, [::]:9080->9080/tcp
```

### verification

```bash
curl http://localhost:3100/ready
ready

curl http://localhost:9080/ready
Ready

curl http://localhost:3000/api/health
{
  "database": "ok",
  "version": "12.3.1",
  "commit": "3a1c80ca7ce612f309fdc99338dd3c5e486339be"
}
```

---

## 3. json structured logging

### implementation

**file:** [app_python/app.py](../../app_python/app.py)

**key concepts:**

| concept | implementation |
|---------|----------------|
| `CustomJsonFormatter` | extends jsonlogger to add timestamp, level, logger fields |
| middleware | logs every request with timing, method, path, status |
| `extra={}` parameter | adds structured fields to log records |
| log level by status | 4xx+ uses warning, 5xx uses error |

### log format

```json
{
  "timestamp": "2026-03-19T20:58:37.281534+00:00",
  "level": "INFO",
  "logger": "app",
  "message": "HTTP request completed",
  "event": "request_end",
  "method": "GET",
  "path": "/health",
  "status_code": 200,
  "duration_ms": 0.27,
  "client_ip": "127.0.0.1"
}
```

### logged events

| event | description | fields |
|-------|-------------|--------|
| `startup` | application starts | host, port, python_version |
| `request_start` | http request received | method, path, client_ip, user_agent |
| `request_end` | http request completed | method, path, status_code, duration_ms |
| `error_404` | not found error | method, path, client_ip |
| `shutdown` | application stops | uptime_seconds |

### requirements update

**file:** [app_python/requirements.txt](../../app_python/requirements.txt)

added: `python-json-logger==3.2.1`

---

## 4. logql queries

### basic queries

```logql
# all logs from python app
{app="devops-python"}

# filter by text
{app="devops-python"} |= "health"

# parse json and filter
{app="devops-python"} | json | level="INFO"

# filter by status code
{app="devops-python"} | json | status_code>=400
```

### aggregation queries

```logql
# logs per second by app
sum by (app) (rate({app=~"devops-.*"} [1m]))

# count by log level
sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))

# error rate
rate({app="devops-python"} | json | level="ERROR" [5m])

# requests with high latency
{app="devops-python"} | json | duration_ms > 100
```

### testing queries via api

```bash
curl -s -G 'http://localhost:3100/loki/api/v1/query_range' \
  --data-urlencode 'query={app="devops-python"} | json' \
  --data-urlencode 'limit=3' | python3 -m json.tool

{
    "status": "success",
    "data": {
        "resultType": "streams",
        "result": [
            {
                "stream": {
                    "app": "devops-python",
                    "client_ip": "127.0.0.1",
                    "container": "devops-python",
                    "event": "request_start",
                    "job": "docker",
                    "level": "info",
                    "logger": "app",
                    "logging_job": "promtail",
                    "message": "HTTP request started",
                    "method": "GET",
                    "name": "app",
                    "path": "/health",
                    "query": "",
                    "service_name": "devops-python",
                    "timestamp": "2026-03-19T21:37:49.665286+00:00",
                    "user_agent": "Python-urllib/3.13"
                },
                "values": [
                    [
                        "1773956269665401004",
                        "{\"timestamp\": \"2026-03-19T21:37:49.665286+00:00\", \"level\": \"INFO\", \"name\": \"app\", \"message\": \"HTTP request started\", \"event\": \"request_start\", \"method\": \"GET\", \"path\": \"/health\", \"query\": \"\", \"client_ip\": \"127.0.0.1\", \"user_agent\": \"Python-urllib/3.13\", \"logger\": \"app\"}"
                    ]
                ]
            },
        ...
```

---

## 5. grafana dashboard

### configuration files

| file | purpose |
|------|---------|
| [grafana/provisioning/datasources/datasources.yml](../grafana/provisioning/datasources/datasources.yml) | loki data source |
| [grafana/provisioning/dashboards/dashboards.yml](../grafana/provisioning/dashboards/dashboards.yml) | dashboard provisioning config |
| [grafana/provisioning/dashboards/json/devops-logs-dashboard.json](../grafana/provisioning/dashboards/json/devops-logs-dashboard.json) | pre-built dashboard |

### dashboard panels

| panel | type | query |
|-------|------|-------|
| recent logs | logs | `{app=~"devops-.*"}` |
| request rate | time series | `sum by (app) (rate({app=~"devops-.*"} [1m]))` |
| error logs | logs | `{app=~"devops-.*"} | json | level="ERROR"` |
| log level distribution | stat | `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))` |

### access

1. open http://localhost:3000
2. login with admin/admin
3. navigate to explore → select loki
4. run queries or view dashboards

### dashboard screenshot 

[grafana dashboard with log panels](screenshots/grafana-dashboard.png)

---

## 6. production considerations

### security

| measure | implementation |
|---------|----------------|
| grafana auth | `GF_AUTH_ANONYMOUS_ENABLED=false` |
| admin password | via .env file (not committed) |
| read-only mounts | config files mounted `:ro` |
| docker socket | consider socket proxy for production |

### resource limits

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

### retention

- **period**: 7 days (168h)
- **implementation**: loki compactor
- **cleanup**: automatic via `retention_enabled: true`

---

## 7. testing

### generate traffic

```bash
for i in {1..20}; do curl http://localhost:8000/; done
for i in {1..10}; do curl http://localhost:8000/health; done
curl http://localhost:8000/nonexistent  # generates 404
```

### verify logs in loki

```bash
# check labels
curl -s 'http://localhost:3100/loki/api/v1/labels' | python3 -m json.tool

{
    "status": "success",
    "data": ["app", "container", "job", "level", "logging_job", "service_name"]
}

# check container logs
docker logs devops-python 2>&1 | head -5

{"timestamp": "2026-03-19T20:58:37.281534+00:00", "level": "INFO", "name": "app", "message": "HTTP request completed", "event": "request_end", "method": "GET", "path": "/health", "status_code": 200, "duration_ms": 0.27, "client_ip": "127.0.0.1", "logger": "app"}
```

---

## 8. challenges

### loki config field error

**problem**: loki 3.0 doesn't recognize `enforce_metric_name` field.

**solution**: removed the deprecated field from limits_config.

### promtail health check

**problem**: promtail container has no curl/wget for health checks.

**solution**: exposed port 9080 externally, health verified from host.

### python app health check

**problem**: python slim image has no curl.

**solution**: used python's urllib for health check:
```yaml
test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:5000/health')\" || exit 1"]
```
