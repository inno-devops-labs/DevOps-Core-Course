# LAB07 Report - Observability and Logging with Loki Stack

## 1. Architecture

Centralized logging stack:

- `app-python` (and optional `app-bonus`) emit stdout logs.
- `promtail` discovers Docker containers via `/var/run/docker.sock`.
- Promtail filters containers with label `logging=promtail` and pushes to Loki.
- `loki` stores logs with TSDB (`schema v13`) on local filesystem.
- `grafana` reads Loki and provides Explore + dashboard visualization.

```text
+----------------------+       +---------------------+
| app-python / bonus   | ----> | Promtail            |
| labels: logging, app | logs  | docker_sd + relabel |
+----------------------+       +----------+----------+
                                          |
                                          | push logs
                                          v
                                 +--------+--------+
                                 | Loki 3.0 (TSDB) |
                                 +--------+--------+
                                          |
                                          | query
                                          v
                                 +--------+--------+
                                 | Grafana 12.3.1  |
                                 +-----------------+
```

## 2. Setup Guide

### 2.1 Prepare environment

```bash
cd monitoring
cp .env.example .env
# edit .env and set:
# - GRAFANA_ADMIN_PASSWORD
# - APP_PYTHON_IMAGE (from your Lab 2 image)
```

### 2.2 Deploy

```bash
docker compose up -d
docker compose ps
```

Optional bonus app (if you completed Lab 1 bonus):

```bash
docker compose --profile bonus up -d
```

### 2.3 Verify endpoints

```bash
curl http://localhost:3100/ready
curl http://localhost:9080/ready
curl http://localhost:3000/api/health
```

Grafana URL: `http://localhost:3000`

- Anonymous access is disabled.
- Login with credentials from `.env`.
- Loki data source is auto-provisioned from `grafana/provisioning/datasources/loki.yml`.

## 3. Configuration

### Loki (`monitoring/loki/config.yml`)

Key decisions:

- `store: tsdb` + `schema: v13` for Loki 3.0 recommended storage path.
- `object_store: filesystem` for single-node lab environment.
- `retention_period: 168h` (7 days) under `limits_config`.
- `compactor.retention_enabled: true` for retention cleanup.

Snippet:

```yaml
schema_config:
  configs:
    - from: 2024-01-01
      store: tsdb
      object_store: filesystem
      schema: v13
limits_config:
  retention_period: 168h
```

### Promtail (`monitoring/promtail/config.yml`)

Key decisions:

- Docker service discovery (`docker_sd_configs`) via socket.
- Label filter to scrape only containers marked for logging.
- Relabel rules for `container`, `app`, `service`, `container_id` labels.

Snippet:

```yaml
docker_sd_configs:
  - host: unix:///var/run/docker.sock
    filters:
      - name: label
        values: ["logging=promtail"]
```

## 4. Application Logging

The Flask app was upgraded to structured JSON logging:

- Custom `JSONFormatter` outputs one JSON object per line.
- Request lifecycle logging:
  - `@app.before_request`: method/path/client/user-agent
  - `@app.after_request`: status_code + request context
- Error handlers log structured warning/error events.

Example log line:

```json
{"timestamp":"2026-03-12T11:10:20.123456+00:00","level":"INFO","logger":"devops-info-service","message":"request_completed","method":"GET","path":"/health","status_code":200,"client_ip":"172.20.0.1"}
```

## 5. Dashboard

Dashboard contains 4 required panels:

1. Logs Table
   - Query: `{app=~"devops-.*"}`
2. Request Rate (time series)
   - Query: `sum by (app) (rate({app=~"devops-.*"}[1m]))`
3. Error Logs
   - Query: `{app=~"devops-.*"} | json | level="ERROR"`
4. Log Level Distribution
   - Query: `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))`

Useful Explore queries used during testing:

```logql
{app="devops-python"}
{app="devops-python"} |= "ERROR"
{app="devops-python"} | json | method="GET"
```

## 6. Production Config

Implemented production-readiness baseline:

- Resource limits and reservations for Loki/Promtail/Grafana/apps in compose.
- Grafana anonymous authentication disabled.
- Admin password moved to `.env` (not committed; `.env` is gitignored).
- Healthchecks added for Loki and Grafana; Promtail and app readiness are validated via service status and queries.
- Retention policy configured for 7 days.

## 7. Testing

Traffic generation:

```bash
for i in {1..20}; do curl -s http://localhost:8000/ >/dev/null; done
for i in {1..20}; do curl -s http://localhost:8000/health >/dev/null; done
```

Compose/health:

```bash
docker compose ps
curl http://localhost:3100/ready
curl http://localhost:9080/targets
curl http://localhost:3000/api/health
```

Ansible bonus deployment:

```bash
cd ansible
ANSIBLE_HOME=/tmp/.ansible \
ANSIBLE_LOCAL_TEMP=/tmp/ansible-local-tmp \
ANSIBLE_REMOTE_TEMP=/tmp/ansible-local-tmp \
ANSIBLE_COLLECTIONS_PATH=$PWD/.ansible/collections \
ANSIBLE_ROLES_PATH=$PWD/roles \
../.venv/bin/ansible-playbook -i inventory/hosts.ini playbooks/deploy-monitoring.yml --syntax-check --vault-password-file ../.vault_pass

ANSIBLE_HOME=/tmp/.ansible \
ANSIBLE_LOCAL_TEMP=/tmp/ansible-local-tmp \
ANSIBLE_REMOTE_TEMP=/tmp/ansible-local-tmp \
ANSIBLE_COLLECTIONS_PATH=$PWD/.ansible/collections \
ANSIBLE_ROLES_PATH=$PWD/roles \
../.venv/bin/ansible-playbook -i inventory/hosts.ini playbooks/deploy-monitoring.yml --list-tags --vault-password-file ../.vault_pass
```

Idempotency check:

```bash
ANSIBLE_CONFIG=$PWD/ansible.cfg ansible-playbook playbooks/deploy-monitoring.yml --vault-password-file ../.vault_pass
ANSIBLE_CONFIG=$PWD/ansible.cfg ansible-playbook playbooks/deploy-monitoring.yml --vault-password-file ../.vault_pass
```

Expected: second run should report mostly `ok` with minimal/no `changed`.

## 8. Challenges

1. Compose security vs convenience
   - Promtail needs Docker socket access for discovery.
   - Mitigation: read-only mount and label-based target filtering.

2. Loki 3.0 TSDB migration details
   - Older examples often use boltdb-shipper.
   - Solution: use v13 + tsdb + compactor retention settings.

3. Grafana bootstrap
   - Manual data source setup is error-prone.
   - Solution: datasource provisioning file mounted at startup.

## Evidence Placeholders

Add screenshots before submission:

- `monitoring/docs/screenshots/explore-3-containers.png`
- `monitoring/docs/screenshots/json-logs.png`
- `monitoring/docs/screenshots/dashboard-4-panels.png`
- `monitoring/docs/screenshots/compose-healthy.png`
- `monitoring/docs/screenshots/grafana-login.png`
