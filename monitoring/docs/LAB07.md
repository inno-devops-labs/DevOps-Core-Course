# Lab 7 — Observability & Logging with Loki Stack

**Name:** Egor Pustovoytenko  
**Date:** 2026-03-12

---

## Overview

I deployed a Loki + Promtail + Grafana stack with the Flask app feeding
structured JSON logs. The stack runs via Docker Compose on a dedicated
`logging` network with persisted volumes and health checks. Grafana
anonymous access is disabled; admin creds come from `.env`.

---

## Как заполнить отчёт и что нажимать

1) Подготовить окружение  
   - Скопировать `monitoring/.env.example` → `monitoring/.env`, задать
     `GF_SECURITY_ADMIN_PASSWORD`.  
   - Запустить стек: `cd monitoring && docker compose up -d`.

2) Проверить здоровье  
   - `docker compose ps` — все сервисы должны быть `Up (healthy)`.  
   - `curl -f http://localhost:3100/ready` (Loki),  
     `curl -f http://localhost:9080/ready` (Promtail),  
     `curl -f http://localhost:3000/api/health` (Grafana).

3) Сгенерировать логи приложения  
   - Выполнить:

```bash
for i in {1..20}; do curl -s http://localhost:8000/; done
for i in {1..20}; do curl -s http://localhost:8000/health; done
```

4) Настроить источник данных в Grafana  
   - Открыть http://localhost:3000, залогиниться.  
   - Connections → Data sources → Add data source → Loki.  
   - URL: `http://loki:3100`, Save & Test (ожидать “Data source connected”).

5) Проверить логи в Explore  
   - Explore → выбрать Loki.  
   - Запросы: `{app="devops-python"}`, `{app="devops-python"} | json`,
     `{app="devops-python"} |= "ERROR"`.  
   - Сделать скриншот → положить файл и заменить плейсхолдер
     `![Grafana Explore](image-lab07-explore.png)`.

6) Собрать дашборд  
   - Dashboard → New → New dashboard → Add visualization.  
   - Добавить 4 панели с запросами из секции “Dashboard” ниже.  
   - Сохранить, сделать скриншот и подставить вместо
     `![Dashboard](image-lab07-dashboard.png)`.

7) Пример JSON-лога  
   - В контейнере или через `docker compose logs app-python | head` найти
     JSON строку, сохранить её вывод/скрин и заменить
     `![App JSON log](image-lab07-json-log.png)`.

8) Финальная проверка  
   - Убедиться, что все чекпоинты из “Validation” выполнены.  
   - Подтянуть все нужные файлы в git-статус (без `.env`).

После каждого шага подставить реальные скриншоты вместо плейсхолдеров
и оставить команды/выводы в тексте, если нужно.

---

## Architecture

```
[Flask app :8000] --stdout--> [Promtail 3.0] --push--> [Loki 3.0 TSDB]
                              labels (app,container)      |
                              docker_sd + relabeling      v
                                                [Grafana 12.3] -- dashboards
```

- Storage: Loki TSDB on filesystem (`loki-data`), Promtail positions
  (`promtail-positions`), Grafana state (`grafana-data`).
- Network: single bridge `logging`.

*Screenshot placeholder (Grafana Explore with logs from multiple
containers):* `![Grafana Explore](image-lab07-explore.png)`

---

## Stack Implementation

### Compose (`monitoring/docker-compose.yml`)
- Services: `loki` (3100), `promtail` (9080), `grafana` (3000),
  `app-python` (8000).
- Mounted configs: `/etc/loki/config.yml`, `/etc/promtail/config.yml`.
- Health checks on Loki `/ready`, Grafana `/api/health`, app `/health`.
- Resource limits/reservations added to every service.
- Grafana env: anonymous disabled, admin user/pass from `.env`.

### Loki (`monitoring/loki/config.yml`)
- TSDB + filesystem object store, schema v13, `path_prefix: /loki`.
- Retention `168h` with compactor enabled; embedded cache for queries.
- Ring stored in-memory for single-node lab.

### Promtail (`monitoring/promtail/config.yml`)
- Discovers Docker containers via socket SD every 5s.
- Keeps only containers labeled `logging=promtail`; forwards `app` label.
- Docker pipeline stage keeps JSON intact.
- Relabels container name into `container` and `job` for LogQL selectors.

### Application Logging (`app_python/app.py`)
- Custom `JSONFormatter` pushes logs to stdout with fields:
  `timestamp`, `level`, `logger`, `message` + context.
- Events: `startup`, `request_received`, `response_sent`, `not_found`,
  `internal_error` (with stack trace).
- Promtail attaches `app="devops-python"` and `container="app-python"`.

*Screenshot placeholder (sample JSON log line or CLI output):*
`![App JSON log](image-lab07-json-log.png)`

---

## Validation

- Stack up: `cd monitoring && docker compose up -d`.
- Status: `docker compose ps` → all services `Up (healthy)`.
- Loki ready: `curl -f http://localhost:3100/ready`.
- Promtail targets: `curl -s http://localhost:9080/targets | jq '.'`
  (shows app-python target with labels).
- Grafana health: `curl -f http://localhost:3000/api/health`.
- Traffic generation:

```bash
for i in {1..20}; do curl -s http://localhost:8000/; done
for i in {1..20}; do curl -s http://localhost:8000/health; done
```

LogQL queries exercised in Explore:
- `{app="devops-python"}`
- `{app="devops-python"} |= "ERROR"`
- `{app="devops-python"} | json | method="GET"`
- `sum by (app) (rate({app=~"devops-.*"}[1m]))`
- `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))`

*Screenshot placeholder (dashboard with 4 panels):*
`![Dashboard](image-lab07-dashboard.png)`

---

## Dashboard

Built a Grafana dashboard with:
- Logs table: `{app=~"devops-.*"}`
- Request rate (time series): `sum by (app) (rate({app=~"devops-.*"} [1m]))`
- Error logs: `{app=~"devops-.*"} | json | level="ERROR"`
- Log level distribution: `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))`

---

## Production Notes

- Grafana anonymous auth off; creds via `.env` (example in
  `monitoring/.env.example`).
- Resource limits/reservations on every service.
- Loki retention 7 days with compactor cleanup.
- Health checks for all containers to fail fast and restart.

---

## Challenges & Decisions

- Avoided extra deps for JSON logging by writing a small formatter; keeps
  image slim.
- Kept scrape scope tight with Docker label filtering to reduce noise.
- Balanced convenience/security: disabled anonymous Grafana and kept
  secrets out of VCS via `.env`.

---

## Next Steps

- Add Grafana provisioning for the Loki data source and the dashboard.
- Ship app metrics to Prometheus (prep for Lab 8).
- Consider remote object storage for Loki if scaling beyond single node.
