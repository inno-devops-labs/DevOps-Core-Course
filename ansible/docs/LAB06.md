# Lab 6: Advanced Ansible & CI/CD - Submission
---

**Name:** Aidar Sarvartdinov
**Date:** 2026-03-05
**Lab Points:** 10

## Task 1

### Common Role

Refactored `roles/common/tasks/main.yml`:
- **`packages` block** — groups apt cache update + package install with `rescue` (runs `apt-get update --fix-missing` on failure) and `always` (logs completion to `/tmp/common_packages_done.log`).
- **`users` block** — groups timezone configuration under the `users` tag.
- `become: true` applied at block level.

### Docker Role

Refactored `roles/docker/tasks/main.yml`:
- **`docker_install` block** — groups all Docker installation tasks (prerequisites, GPG key, repo, packages). Rescue waits 10 seconds and retries. Always ensures Docker service is enabled.
- **`docker_config` block** — groups user group assignment and python3-docker install under `docker_config` tag.

### Tag Strategy

| Tag | Scope |
|-----|-------|
| `packages` | Common package installation |
| `users` | User/system configuration |
| `common` | Entire common role (role-level) |
| `docker` | Entire docker role (role-level) |
| `docker_install` | Docker installation only |
| `docker_config` | Docker configuration only |
| `app_deploy` | Application deployment |
| `compose` | Docker Compose tasks |
| `web_app` | Entire web_app role (role-level) |
| `web_app_wipe` | Wipe logic |

### Output: --list-tags

```
$ ansible-playbook playbooks/provision.yml --list-tags

playbook: playbooks/provision.yml

  play #1 (webservers): Provision web servers	TAGS: []
      TASK TAGS: [common, docker, docker_config, docker_install, packages, users]
```

```
$ ansible-playbook playbooks/deploy.yml --list-tags

playbook: playbooks/deploy.yml

  play #1 (webservers): Deploy application	TAGS: []
      TASK TAGS: [app_deploy, compose, docker_config, docker_install, web_app, web_app_wipe]
```

### Output: Selective execution with --tags

```
$ ansible-playbook playbooks/provision.yml --tags "docker" --check

PLAY [Provision web servers] *****************************

TASK [Gathering Facts] ***********************************
ok: [yc-vm]

TASK [docker : Install Docker prerequisites] *************
ok: [yc-vm]

TASK [docker : Create keyrings directory] ****************
ok: [yc-vm]

TASK [docker : Add Docker GPG key] ***********************
changed: [yc-vm]

TASK [docker : Add Docker repository] ********************
ok: [yc-vm]

TASK [docker : Install Docker packages] ******************
ok: [yc-vm]

TASK [docker : Ensure Docker service is enabled and started] ****
ok: [yc-vm]

TASK [docker : Add users to docker group] ****************
ok: [yc-vm] => (item=ubuntu)

TASK [docker : Install python3-docker for Ansible modules] ****
ok: [yc-vm]
```

> Common role tasks (packages, users) are skipped — only docker-tagged tasks executed.

---

## Task 2

### Migration

Renamed `app_deploy` → `web_app` role. Replaced `docker_container` module with Docker Compose using Jinja2 template.

### Docker Compose Template

`roles/web_app/templates/docker-compose.yml.j2`:

```yaml
---
services:
  {{ app_name }}:
    image: {{ docker_image }}:{{ docker_tag }}
    container_name: {{ app_name }}
    ports:
      - "{{ app_port }}:{{ app_internal_port }}"
    environment:
      APP_NAME: {{ app_name }}
    restart: unless-stopped
```

### Role Dependencies

`roles/web_app/meta/main.yml` declares `docker` as a dependency — Docker auto-installs when running `web_app`.

### Output: Deployment

```
$ ansible-playbook playbooks/deploy.yml

PLAY [Deploy application] ********************************

TASK [Gathering Facts] ***********************************
ok: [yc-vm]

TASK [docker : Install Docker prerequisites] *************
ok: [yc-vm]
...
TASK [docker : Ensure Docker service is enabled and started] ****
ok: [yc-vm]
...
TASK [web_app : Include wipe tasks] **********************
included: /ansible/roles/web_app/tasks/wipe.yml for yc-vm

TASK [web_app : Stop and remove containers] **************
skipping: [yc-vm]
...
TASK [web_app : Create application directory] ************
ok: [yc-vm]

TASK [web_app : Template docker-compose file] ************
ok: [yc-vm]

TASK [web_app : Remove old standalone container if exists] ****
ok: [yc-vm]

TASK [web_app : Pull and start containers with docker compose] ****
changed: [yc-vm]

TASK [web_app : Wait for application port] ***************
ok: [yc-vm]

TASK [web_app : Verify application health] ***************
ok: [yc-vm] => {"status": 200, "json": {"status": "healthy", "timestamp": "2026-03-04T20:39:54.476622", "uptime_seconds": 5}}

TASK [web_app : Display health check result] *************
ok: [yc-vm]

PLAY RECAP ***********************************************
yc-vm    : ok=17   changed=1    unreachable=0    failed=0    skipped=5    rescued=0    ignored=0
```

### Output: Idempotency (2nd run)

```
$ ansible-playbook playbooks/deploy.yml   # 2nd run

PLAY RECAP ***********************************************
yc-vm    : ok=17   changed=1    unreachable=0    failed=0    skipped=5    rescued=0    ignored=0
```

> `changed=1` — only the `docker compose up --force-recreate` task (recreates container each time), all other tasks show `ok`.

---

## Task 3

### Implementation

Created `roles/web_app/tasks/wipe.yml` with double-gating:
1. **Variable gate:** `when: web_app_wipe | bool` (default: `false`)
2. **Tag gate:** tagged with `web_app_wipe`

Wipe sequence: `docker compose down` → remove compose file → remove directory → remove image.

### Test Scenarios

| # | Command | Expected | Result |
|---|---------|----------|--------|
| 1 | `ansible-playbook deploy.yml` | Normal deploy, wipe skipped | Wipe tasks show `skipping` (tag not specified) |
| 2 | `deploy.yml -e "web_app_wipe=true" --tags web_app_wipe` | Wipe only, no deploy | Wipe runs, deploy skipped |
| 3 | `deploy.yml -e "web_app_wipe=true"` | Wipe then fresh deploy | Wipe → deploy → app healthy |
| 4 | `deploy.yml --tags web_app_wipe` | Wipe skipped (`when` blocks) | `skip_reason: Conditional result was False` |

### Output: Scenario 1 (wipe skipped during normal deploy)

From the deploy output above:
```
TASK [web_app : Stop and remove containers] **************
skipping: [yc-vm] => {"skip_reason": "Conditional result was False"}

TASK [web_app : Remove docker-compose file] **************
skipping: [yc-vm] => {"skip_reason": "Conditional result was False"}

TASK [web_app : Remove application directory] ************
skipping: [yc-vm] => {"skip_reason": "Conditional result was False"}

TASK [web_app : Remove Docker image] *********************
skipping: [yc-vm] => {"skip_reason": "Conditional result was False"}

TASK [web_app : Log wipe completion] *********************
skipping: [yc-vm]
```

### Output: Scenario 2 (wipe only)

```
$ ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe

PLAY [Deploy application] ********************************

TASK [Gathering Facts] ***********************************
ok: [yc-vm]

TASK [web_app : Include wipe tasks] **********************
included: /ansible/roles/web_app/tasks/wipe.yml for yc-vm

TASK [web_app : Stop and remove containers] **************
changed: [yc-vm]

TASK [web_app : Remove docker-compose file] **************
changed: [yc-vm]

TASK [web_app : Remove application directory] ************
changed: [yc-vm]

TASK [web_app : Remove Docker image] *********************
changed: [yc-vm]

TASK [web_app : Log wipe completion] *********************
ok: [yc-vm] => {"msg": "Application pythonapp wiped successfully"}

PLAY RECAP ***********************************************
yc-vm    : ok=7   changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

> Deploy tasks are not executed — only wipe-tagged tasks run.

### Output: Scenario 3 (clean reinstall)

```
$ ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"

PLAY [Deploy application] ********************************
...
TASK [web_app : Include wipe tasks] **********************
included: /ansible/roles/web_app/tasks/wipe.yml for yc-vm

TASK [web_app : Stop and remove containers] **************
changed: [yc-vm]
...
TASK [web_app : Pull and start containers with docker compose] ****
changed: [yc-vm]
...
PLAY RECAP ***********************************************
yc-vm    : ok=22   changed=7    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

> Both wipe and deploy tasks execute, resulting in a clean reinstallation.

### Output: Scenario 4a (safety test, variable not set)

```
$ ansible-playbook playbooks/deploy.yml --tags web_app_wipe

PLAY [Deploy application] ********************************

TASK [Gathering Facts] ***********************************
ok: [yc-vm]

TASK [web_app : Include wipe tasks] **********************
included: /ansible/roles/web_app/tasks/wipe.yml for yc-vm

TASK [web_app : Stop and remove containers] **************
skipping: [yc-vm]

TASK [web_app : Remove docker-compose file] **************
skipping: [yc-vm]

TASK [web_app : Remove application directory] ************
skipping: [yc-vm]

TASK [web_app : Remove Docker image] *********************
skipping: [yc-vm]

TASK [web_app : Log wipe completion] *********************
skipping: [yc-vm]

PLAY RECAP ***********************************************
yc-vm    : ok=2    changed=0    unreachable=0    failed=0    skipped=5    rescued=0    ignored=0
```

> Wipe is blocked because `web_app_wipe` variable defaults to false (`when` condition fails).

---

## Task 4

### Workflow

`.github/workflows/ansible-deploy.yml`:

```
Push to ansible/** → Lint Job (ansible-lint) → Deploy Job (SSH + ansible-playbook) → Verify (curl)
```

- **Lint job:** installs ansible + ansible-lint, runs `ansible-lint playbooks/*.yml`
- **Deploy job:** sets up SSH via GitHub Secrets, decrypts vault, runs `ansible-playbook playbooks/deploy.yml`, verifies with `curl`
- **Path filters:** triggers only on `ansible/**` changes (excludes `docs/`)
- **Deploy job** only runs on `main`/`master` branch pushes (not on PRs)

### Required GitHub Secrets

| Secret | Purpose |
|--------|---------|
| `ANSIBLE_VAULT_PASSWORD` | Vault decryption |
| `SSH_PRIVATE_KEY` | SSH access to VM |
| `VM_HOST` | Target VM IP |
