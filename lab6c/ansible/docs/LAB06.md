# Lab 6 — Advanced Ansible & CI/CD

## 1. Overview

This lab extends Lab 5 with:
- **Blocks and tags** in common and docker roles
- **Docker Compose** for app deployment (replacing docker run)
- **Wipe logic** (variable + tag) for clean removal
- **GitHub Actions** workflow for automated deployment

## 2. Blocks & Tags

### Common Role
- **packages** block: apt update + install, with rescue (retry apt on failure), always (log completion)
- **users** block: ensure sudo group
- **common** tag: entire role

### Docker Role
- **docker_install** block: repo setup, package install; rescue (wait 10s, retry); always (ensure service enabled)
- **docker_config** block: docker group, add user
- **docker** tag: entire role

### Web App Role
- **app_deploy**, **compose** tags: deployment tasks
- **web_app_wipe** tag: wipe tasks only

### Execution Examples
```bash
ansible-playbook playbooks/provision.yml --tags "docker"
ansible-playbook playbooks/provision.yml --skip-tags "common"
ansible-playbook playbooks/provision.yml --tags "packages"
ansible-playbook playbooks/provision.yml --list-tags
```

## 3. Docker Compose Migration

- **Template:** `roles/web_app/templates/docker-compose.yml.j2`
- **Project dir:** `/opt/{{ app_name }}`
- **Role dependency:** `web_app` depends on `docker` (meta/main.yml)
- **Module:** `community.docker.docker_compose_v2` with `state: present`, `pull: always`

## 4. Wipe Logic

- **Variable:** `web_app_wipe: false` (default)
- **Tag:** `web_app_wipe`
- **Tasks:** `roles/web_app/tasks/wipe.yml` — compose down, remove file, remove dir

### Scenarios
1. **Normal deploy:** `ansible-playbook playbooks/deploy.yml` — wipe skipped
2. **Wipe only:** `ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe`
3. **Clean reinstall:** `ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"`
4. **Safety:** `--tags web_app_wipe` without variable — wipe skipped (when blocks it)

## 5. CI/CD Integration

- **Workflow:** `.github/workflows/ansible-deploy.yml`
- **Triggers:** push to `lab6c/ansible/**`
- **Jobs:** lint (ansible-lint), deploy (playbook + verify)
- **Secrets required:** `ANSIBLE_VAULT_PASSWORD`, `SSH_PRIVATE_KEY`, `VM_HOST`, `VM_USER`

## 6. Testing Results

### 6.1 Provision with tags
```bash
ansible-playbook playbooks/provision.yml --tags "docker"
```
```
PLAY RECAP *********************************************************************
lab5-vm                    : ok=9    changed=0    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0
```

### 6.2 List of tags
```bash
ansible-playbook playbooks/provision.yml --list-tags
```
```
playbook: playbooks/provision.yml
  play #1 (webservers): Provision web servers  TAGS: []
      TASK TAGS: [common, docker, docker_config, docker_install, packages, users]
```

### 6.3 Deploy
```bash
ansible-playbook playbooks/deploy.yml
```
```
PLAY RECAP *********************************************************************
lab5-vm                    : ok=16   changed=2    unreachable=0    failed=0    skipped=5    rescued=0    ignored=0
```

### 6.4 Wipe-only
```bash
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe
```
```
TASK [web_app : Log wipe completion] *******************************************
ok: [lab5-vm] => {"msg": "Application devops-info-python wiped successfully"}
PLAY RECAP *********************************************************************
lab5-vm                    : ok=6    changed=3    unreachable=0    failed=0    skipped=0
```

### 6.5 Clean reinstall
```bash
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"
```
```
PLAY RECAP *********************************************************************
lab5-vm                    : ok=20   changed=3    unreachable=0    failed=0    skipped=1    rescued=0    ignored=1
```

### 6.6 Health check
```bash
curl http://62.84.127.190:5000/health
```
```json
{"status":"healthy","timestamp":"2026-03-05T12:17:53.667273Z","uptime_seconds":60}
```

### 6.7 Idempotency (2nd deploy run)
```bash
ansible-playbook playbooks/deploy.yml
```
Second run: `changed=0` (all `ok`, no changes).

### 6.8 Scenario 4a — safety (--tags web_app_wipe without variable)
```bash
ansible-playbook playbooks/deploy.yml --tags web_app_wipe
```
Wipe tasks skipped (when blocks: `web_app_wipe` false by default). Deploy runs normally.

### 6.9 GitHub Actions
Add 4 secrets and push. Include screenshot of successful workflow in report.


## 7. Challenges & Solutions

- **Template `to_native` filter:** Ansible 2.16+ does not provide `to_native` in Jinja2 — replaced with `to_json`.
- **dpkg lock:** On a new VM, `unattended-upgrades` blocks apt; retry `provision` after updates complete succeeds.
- **Wipe on empty directory:** `docker_compose_v2 state: absent` fails if directory was already removed. Added `compose_dir_stat` check before `compose down`.

## 8. Research Answers

### Task 1 — Blocks & Tags
- **If rescue also fails?** Play will fail with error; can add `ignore_errors` or nested rescue.
- **Nested blocks?** Yes, a block can contain another block.
- **Tag inheritance?** Tags on block apply to all tasks inside.

### Task 2 — Docker Compose
- **restart: always vs unless-stopped?** `unless-stopped` does not restart container after manual stop.
- **Compose networks vs bridge?** Compose creates named networks; bridge is the default network.
- **Vault in template?** Yes, Vault variables are available when templating.

### Task 3 — Wipe Logic
- **Variable + tag?** Double safety: variable prevents accidental wipe; tag enables selective execution.
- **never tag vs our approach?** `never` disables task by tag; our approach requires both tag and variable.
- **Wipe before deploy?** Enables clean reinstall: wipe → deploy in one run.
- **Clean reinstall vs rolling update?** Reinstall = full replacement; rolling = phased update without downtime.
- **Extending wipe?** Can add `docker image prune` and `docker volume rm` to wipe.yml.

### Task 4 — CI/CD
- **SSH keys in Secrets?** Use short-lived keys; regular rotation; restrict scope.
- **Staging → production?** Separate inventory/playbooks, approval before prod, or environment protection.
- **Rollbacks?** Add tag/version to image, keep previous config, workflow for rollback.
- **Self-hosted vs GitHub-hosted?** Self-hosted gives direct network/VMs access; fewer SSH key exposure risks.
