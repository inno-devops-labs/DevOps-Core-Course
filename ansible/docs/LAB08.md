# Lab 8 Bonus: Ansible Prometheus Automation

This document describes the Lab 8 bonus automation added on top of the Lab 7 monitoring role.

## Scope

The role now provisions:
- Loki
- Promtail
- Grafana
- Prometheus
- Loki and Prometheus Grafana datasources
- Lab 7 logs dashboard
- Lab 8 metrics dashboard

## Files Added or Updated

- `ansible/roles/monitoring/defaults/main.yml`
- `ansible/roles/monitoring/tasks/setup.yml`
- `ansible/roles/monitoring/tasks/deploy.yml`
- `ansible/roles/monitoring/templates/docker-compose.yml.j2`
- `ansible/roles/monitoring/templates/grafana-datasource.yml.j2`
- `ansible/roles/monitoring/templates/prometheus.yml.j2`
- `ansible/roles/monitoring/files/lab08-metrics-dashboard.json`

## New Variables

Added defaults:
- `monitoring_prometheus_version`
- `monitoring_prometheus_port`
- `monitoring_prometheus_retention_time`
- `monitoring_prometheus_retention_size`
- `monitoring_prometheus_scrape_interval`
- `monitoring_prometheus_targets`
- `monitoring_grafana_metrics_enabled`
- `monitoring_metrics_dashboard_title`

Resource defaults were also updated to reflect the Lab 8 production profile:
- Grafana: `0.5 CPU`, `512M`
- Python app: `0.5 CPU`, `256M`
- Go app: `0.5 CPU`, `256M`
- Prometheus: `1 CPU`, `1G`

## Rendering Flow

`setup.yml` now:
- creates `{{ monitoring_project_dir }}/prometheus`
- renders `prometheus/prometheus.yml`
- renders the compose file with Prometheus included
- renders the shared datasource file with both Loki and Prometheus
- copies `lab08-metrics-dashboard.json` into Grafana's dashboards directory

`deploy.yml` now verifies:
- Prometheus port is reachable
- `/-/healthy` returns `200`
- `api/v1/query?query=up` returns `200`
- Grafana admin auth succeeds on `/api/user`
- when a reused `grafana-data` volume still contains an older admin password, the role resets user id `1` to `monitoring_grafana_admin_password` before datasource checks
- Grafana exposes datasource UID `prometheus`

## Grafana Persistence Note

Grafana stores its SQLite state inside the persistent `grafana-data` volume. In local reruns, that means changing `GF_SECURITY_ADMIN_PASSWORD` in Compose or `monitoring_grafana_admin_password` in Ansible is not always enough by itself to make the API checks pass.

To keep the bonus playbook reproducible on reruns, `deploy.yml` now:
- probes `http://127.0.0.1:3000/api/user` with the configured admin credentials
- runs `docker exec grafana grafana cli admin reset-admin-password --user-id 1 <password>` only when the probe returns `401`
- continues with datasource verification only after the configured password works again

## Local Validation

The current host did not have a ready `ansible-playbook` binary or the old Lab 5 Docker target container, so a temporary Ansible runtime was created in `/tmp`.

Validation steps performed on `2026-03-19`:

```bash
python3 -m venv /tmp/lab07-ansible-venv
/tmp/lab07-ansible-venv/bin/pip install ansible-core
HOME=/tmp /tmp/lab07-ansible-venv/bin/ansible-galaxy collection install \
  -r ansible/collections/requirements.yml \
  -p /tmp/lab07-ansible-collections

docker tag devops-info-service:lab08 localhost:5001/devops-info-service:latest
docker tag devops-info-service-go:lab08 localhost:5001/devops-info-service-go:latest
docker push localhost:5001/devops-info-service:latest
docker push localhost:5001/devops-info-service-go:latest

HOME=/tmp \
ANSIBLE_COLLECTIONS_PATH=/tmp/lab07-ansible-collections \
ANSIBLE_ROLES_PATH=/Users/pepega/Developer/learning/DevOps-Core-Course/ansible/roles \
/tmp/lab07-ansible-venv/bin/ansible-playbook \
  -i ansible/inventory/hosts.local-docker.ini \
  ansible/playbooks/deploy-monitoring.yml \
  --syntax-check

HOME=/tmp \
ANSIBLE_COLLECTIONS_PATH=/tmp/lab07-ansible-collections \
ANSIBLE_ROLES_PATH=/Users/pepega/Developer/learning/DevOps-Core-Course/ansible/roles \
/tmp/lab07-ansible-venv/bin/ansible-playbook \
  -i ansible/inventory/hosts.local-docker.ini \
  ansible/playbooks/deploy-monitoring.yml \
  -e @ansible/vars/local_monitoring_test.yml
```

Result:
- `playbook: ansible/playbooks/deploy-monitoring.yml`
- first full run completed successfully with `failed=0`
- second full run completed successfully with `changed=0 failed=0`
- after intentionally setting a stale Grafana admin password in the persisted volume, the next run completed successfully with `changed=1 failed=0` and restored the configured credentials

This confirms the bonus playbook is syntactically valid, deploys the full Lab 8 stack end-to-end on the local Docker target, remains reproducible with persistent Grafana state, and is idempotent on the second run.
