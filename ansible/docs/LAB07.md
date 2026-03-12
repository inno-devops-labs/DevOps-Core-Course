# Lab 7 Bonus: Ansible Monitoring Role

This document describes the bonus automation added for Lab 7.

Implemented files:
- `ansible/playbooks/deploy-monitoring.yml`
- `ansible/roles/monitoring/defaults/main.yml`
- `ansible/roles/monitoring/tasks/setup.yml`
- `ansible/roles/monitoring/tasks/deploy.yml`
- `ansible/roles/monitoring/templates/docker-compose.yml.j2`
- `ansible/roles/monitoring/templates/loki-config.yml.j2`
- `ansible/roles/monitoring/templates/promtail-config.yml.j2`
- `ansible/roles/monitoring/templates/grafana-datasource.yml.j2`
- `ansible/roles/monitoring/templates/grafana-dashboards.yml.j2`
- `ansible/roles/monitoring/templates/lab07-logs-dashboard.json.j2`

Role behavior:
- creates `/opt/monitoring`
- renders Loki, Promtail, Grafana provisioning, and dashboard files
- deploys the stack with `community.docker.docker_compose_v2`
- waits for Loki, Promtail, Grafana, and application ports
- verifies Loki `/ready`, Promtail `/targets`, Grafana `/api/health`, app `/health`
- verifies Grafana datasource UID `loki` through the Grafana HTTP API

Useful commands:

```bash
cd ansible
ansible-galaxy collection install -r collections/requirements.yml
ansible-playbook -i inventory/hosts.local-docker.ini playbooks/deploy-monitoring.yml \
  -e @vars/local_monitoring_test.yml
ansible-playbook -i inventory/hosts.local-docker.ini playbooks/deploy-monitoring.yml \
  -e @vars/local_monitoring_test.yml
```

Expected result on second run:
- no template drift
- no Compose changes
- readiness checks still pass

## Verified bonus run

Verification was executed on `2026-03-12` against a fresh local target container named `lab05-ubuntu2404` with:
- local registry: `lab05-registry`
- control node command: `/tmp/lab07-ansible-venv/bin/ansible-playbook`
- inventory: `ansible/inventory/hosts.local-docker.ini`
- extra vars: `ansible/vars/local_monitoring_test.yml`
- full captured logs: `ansible/docs/first-run.output.txt`, `ansible/docs/second-run.output.txt`

First run command:

```bash
HOME=/tmp ANSIBLE_ROLES_PATH=/Users/pepega/Developer/learning/DevOps-Core-Course/ansible/roles \
ANSIBLE_COLLECTIONS_PATH=/tmp/lab07-ansible-collections \
/tmp/lab07-ansible-venv/bin/ansible-playbook \
  -i ansible/inventory/hosts.local-docker.ini \
  /tmp/lab07-deploy-monitoring.yml \
  -e @ansible/vars/local_monitoring_test.yml
```

Actual first run output excerpt:

```text
TASK [monitoring : Ensure monitoring directory structure exists] ***************
changed: [lab05-ubuntu2404] => (item=/opt/monitoring)
changed: [lab05-ubuntu2404] => (item=/opt/monitoring/loki)
changed: [lab05-ubuntu2404] => (item=/opt/monitoring/promtail)
changed: [lab05-ubuntu2404] => (item=/opt/monitoring/grafana)
changed: [lab05-ubuntu2404] => (item=/opt/monitoring/grafana/provisioning)
changed: [lab05-ubuntu2404] => (item=/opt/monitoring/grafana/provisioning/datasources)
changed: [lab05-ubuntu2404] => (item=/opt/monitoring/grafana/provisioning/dashboards)
changed: [lab05-ubuntu2404] => (item=/opt/monitoring/grafana/dashboards)

TASK [monitoring : Render monitoring docker compose file] **********************
changed: [lab05-ubuntu2404]

TASK [monitoring : Render Loki configuration] **********************************
changed: [lab05-ubuntu2404]

TASK [monitoring : Render Promtail configuration] ******************************
changed: [lab05-ubuntu2404]

TASK [monitoring : Render Grafana datasource provisioning] *********************
changed: [lab05-ubuntu2404]

TASK [monitoring : Render Grafana dashboard provisioning] **********************
changed: [lab05-ubuntu2404]

TASK [monitoring : Render Grafana dashboard JSON] ******************************
changed: [lab05-ubuntu2404]

TASK [monitoring : Deploy monitoring stack] ************************************
changed: [lab05-ubuntu2404]

TASK [monitoring : Wait for monitoring ports to become available] **************
ok: [lab05-ubuntu2404] => (item={'port': 3100, 'enabled': True})
ok: [lab05-ubuntu2404] => (item={'port': 9080, 'enabled': True})
ok: [lab05-ubuntu2404] => (item={'port': 3000, 'enabled': True})
ok: [lab05-ubuntu2404] => (item={'port': 8000, 'enabled': True})
ok: [lab05-ubuntu2404] => (item={'port': 8001, 'enabled': True})

TASK [monitoring : Verify Loki datasource is provisioned in Grafana] ***********
ok: [lab05-ubuntu2404]

PLAY RECAP *********************************************************************
lab05-ubuntu2404           : ok=30   changed=17   unreachable=0    failed=0    skipped=3    rescued=0    ignored=0
```

Second run command:

```bash
HOME=/tmp ANSIBLE_ROLES_PATH=/Users/pepega/Developer/learning/DevOps-Core-Course/ansible/roles \
ANSIBLE_COLLECTIONS_PATH=/tmp/lab07-ansible-collections \
/tmp/lab07-ansible-venv/bin/ansible-playbook \
  -i ansible/inventory/hosts.local-docker.ini \
  /tmp/lab07-deploy-monitoring.yml \
  -e @ansible/vars/local_monitoring_test.yml
```

Actual second run output excerpt:

```text
TASK [monitoring : Ensure monitoring directory structure exists] ***************
ok: [lab05-ubuntu2404] => (item=/opt/monitoring)
ok: [lab05-ubuntu2404] => (item=/opt/monitoring/loki)
ok: [lab05-ubuntu2404] => (item=/opt/monitoring/promtail)
ok: [lab05-ubuntu2404] => (item=/opt/monitoring/grafana)
ok: [lab05-ubuntu2404] => (item=/opt/monitoring/grafana/provisioning)
ok: [lab05-ubuntu2404] => (item=/opt/monitoring/grafana/provisioning/datasources)
ok: [lab05-ubuntu2404] => (item=/opt/monitoring/grafana/provisioning/dashboards)
ok: [lab05-ubuntu2404] => (item=/opt/monitoring/grafana/dashboards)

TASK [monitoring : Render monitoring docker compose file] **********************
ok: [lab05-ubuntu2404]

TASK [monitoring : Render Loki configuration] **********************************
ok: [lab05-ubuntu2404]

TASK [monitoring : Render Promtail configuration] ******************************
ok: [lab05-ubuntu2404]

TASK [monitoring : Render Grafana datasource provisioning] *********************
ok: [lab05-ubuntu2404]

TASK [monitoring : Render Grafana dashboard provisioning] **********************
ok: [lab05-ubuntu2404]

TASK [monitoring : Render Grafana dashboard JSON] ******************************
ok: [lab05-ubuntu2404]

TASK [monitoring : Deploy monitoring stack] ************************************
ok: [lab05-ubuntu2404]

TASK [monitoring : Wait for monitoring ports to become available] **************
ok: [lab05-ubuntu2404] => (item={'port': 3100, 'enabled': True})
ok: [lab05-ubuntu2404] => (item={'port': 9080, 'enabled': True})
ok: [lab05-ubuntu2404] => (item={'port': 3000, 'enabled': True})
ok: [lab05-ubuntu2404] => (item={'port': 8000, 'enabled': True})
ok: [lab05-ubuntu2404] => (item={'port': 8001, 'enabled': True})

TASK [monitoring : Verify Loki datasource is provisioned in Grafana] ***********
ok: [lab05-ubuntu2404]

PLAY RECAP *********************************************************************
lab05-ubuntu2404           : ok=29   changed=0    unreachable=0    failed=0    skipped=3    rescued=0    ignored=0
```

Result:
- first run deployed and configured the stack successfully
- second run was idempotent with `changed=0`
