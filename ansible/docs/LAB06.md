# Lab 6: Advanced Ansible & CI/CD

[![Ansible Deployment (Python)](https://github.com/AEZuraa/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/AEZuraa/DevOps-Core-Course/actions/workflows/ansible-deploy.yml)
[![Ansible Deployment (Go Bonus)](https://github.com/AEZuraa/DevOps-Core-Course/actions/workflows/ansible-deploy-bonus.yml/badge.svg)](https://github.com/AEZuraa/DevOps-Core-Course/actions/workflows/ansible-deploy-bonus.yml)

---

## Task 1: Blocks & Tags (2 pts)

### Implementation

All three roles (`common`, `docker`, `web_app`) were refactored with Ansible blocks, rescue/always sections, and a comprehensive tag strategy.

### Common Role (`roles/common/tasks/main.yml`)

Two logical blocks with error handling:

**Block 1 — Package Installation** (tag: `packages`):

```yaml
- name: Install system packages
  block:
    - name: Update apt cache
    - name: Install common packages
  rescue:
    - name: Fix apt cache and retry (apt-get update --fix-missing)
    - name: Retry package installation
  always:
    - name: Log package installation completion (/tmp/ansible_common_packages.log)
  become: true
  tags: [packages, common]
```

**Block 2 — User & System Configuration** (tag: `users`):

```yaml
- name: Configure users and system
  block:
    - name: Set timezone
    - name: Ensure deploy group exists
    - name: Create deploy user
  always:
    - name: Log user configuration completion (/tmp/ansible_common_users.log)
  become: true
  tags: [users, common]
```

### Docker Role (`roles/docker/tasks/main.yml`)

**Block 1 — Docker Installation** (tag: `docker_install`):

```yaml
- name: Install Docker
  block:
    - name: Install prerequisites
    - name: Create keyrings directory
    - name: Add Docker GPG key
    - name: Add Docker repository
    - name: Install Docker packages
  rescue:
    - name: Wait 10 seconds before retry
    - name: Retry apt update after GPG key failure
    - name: Retry Docker installation
  always:
    - name: Ensure Docker service is enabled and started
  become: true
  tags: [docker_install, docker]
```

**Block 2 — Docker Configuration** (tag: `docker_config`):

```yaml
- name: Configure Docker
  block:
    - name: Add user to docker group
    - name: Install python3-docker for Ansible docker modules
  become: true
  tags: [docker_config, docker]
```

### Tag Strategy

| Tag | Scope | Purpose |
|-----|-------|---------|
| `common` | Entire common role | Run all common tasks |
| `packages` | Package installation block | Only install packages |
| `users` | User management block | Only configure users |
| `docker` | Entire docker role | Run all docker tasks |
| `docker_install` | Docker installation block | Only install Docker |
| `docker_config` | Docker configuration block | Only configure Docker |
| `web_app` | Entire web_app role | Run all app tasks |
| `app_deploy` | Deployment block | Only deploy application |
| `compose` | Deployment block | Alias for compose deployment |
| `web_app_wipe` | Wipe tasks | Only wipe application |

### Execution Examples

```bash
# Run only Docker installation
ansible-playbook playbooks/provision.yml --tags "docker_install"

# Skip common role entirely
ansible-playbook playbooks/provision.yml --skip-tags "common"

# Install packages only
ansible-playbook playbooks/provision.yml --tags "packages"

# List all available tags
ansible-playbook playbooks/site.yml --list-tags
```

### Evidence: --list-tags

```
$ ansible-playbook playbooks/site.yml --list-tags

playbook: playbooks/site.yml

  play #1 (webservers): Full infrastructure setup and deployment        TAGS: []
      TASK TAGS: [app_deploy, common, compose, docker, docker_config, docker_install, packages, users, web_app, web_app_wipe]
```

### Evidence: selective execution

```bash
ansible-playbook playbooks/provision.yml --tags "docker_install"
```

```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab04-vm]

TASK [docker : Install prerequisites for Docker repository] ********************
ok: [lab04-vm]

TASK [docker : Create keyrings directory] **************************************
ok: [lab04-vm]

TASK [docker : Add Docker GPG key] *********************************************
ok: [lab04-vm]

TASK [docker : Add Docker repository] ******************************************
ok: [lab04-vm]

TASK [docker : Install Docker packages] ****************************************
ok: [lab04-vm]

TASK [docker : Ensure Docker service is enabled and started] *******************
ok: [lab04-vm]

PLAY RECAP *********************************************************************
lab04-vm                   : ok=7    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

```bash
ansible-playbook playbooks/provision.yml --tags "packages"
```

```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab04-vm]

TASK [common : Update apt cache] ***********************************************
ok: [lab04-vm]

TASK [common : Install common packages] ****************************************
ok: [lab04-vm]

TASK [common : Log package installation completion] ****************************
changed: [lab04-vm]

PLAY RECAP *********************************************************************
lab04-vm                   : ok=4    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

```bash
ansible-playbook playbooks/provision.yml --skip-tags "common"
```

```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab04-vm]

TASK [docker : Install prerequisites for Docker repository] ********************
ok: [lab04-vm]

TASK [docker : Create keyrings directory] **************************************
ok: [lab04-vm]

TASK [docker : Add Docker GPG key] *********************************************
ok: [lab04-vm]

TASK [docker : Add Docker repository] ******************************************
ok: [lab04-vm]

TASK [docker : Install Docker packages] ****************************************
ok: [lab04-vm]

TASK [docker : Ensure Docker service is enabled and started] *******************
ok: [lab04-vm]

TASK [docker : Add user to docker group] ***************************************
ok: [lab04-vm]

TASK [docker : Install python3-docker for Ansible docker modules] **************
ok: [lab04-vm]

PLAY RECAP *********************************************************************
lab04-vm                   : ok=9    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Evidence: rescue block triggered

The rescue block in the `web_app` role was triggered when `docker compose up` failed due to a container name conflict (old container from previous lab still present):

```bash
ansible-playbook playbooks/deploy.yml
```

```
TASK [web_app : Deploy with docker compose] ************************************
fatal: [lab04-vm]: FAILED! => {"changed": false, "cmd": ["docker", "compose", "up", "-d",
"--remove-orphans"], "rc": 1, "stderr": " Container devops-app Error response from daemon:
Conflict. The container name \"/devops-app\" is already in use by container \"8999db58c415...\"
You have to remove (or rename) that container to be able to reuse that name."}

TASK [web_app : Handle deployment failure] *************************************
ok: [lab04-vm] => {
    "msg": "Deployment of devops-app failed. Check logs for details."
}

TASK [web_app : Show docker compose logs] **************************************
changed: [lab04-vm]

TASK [web_app : Display compose logs] ******************************************
ok: [lab04-vm] => {
    "compose_logs.stdout_lines": []
}

PLAY RECAP *********************************************************************
lab04-vm                   : ok=17   changed=1    unreachable=0    failed=0    skipped=5    rescued=1    ignored=1
```

The `rescued=1` counter confirms the rescue block handled the failure gracefully instead of aborting the play.

### Research Answers

**Q: What happens if rescue block also fails?**
A: The play fails and execution stops for the host. The always block still runs regardless. The rescue block failure is treated as a normal task failure.

**Q: Can you have nested blocks?**
A: Yes, blocks can be nested. However, only the outermost block can have rescue/always sections. Nested blocks are useful for grouping tasks with shared directives.

**Q: How do tags inherit to tasks within blocks?**
A: Tags applied at block level are automatically inherited by all tasks inside the block (including rescue/always). Tasks inside blocks can also have their own additional tags.

---

## Task 2: Docker Compose (3 pts)

### Role Rename

Renamed `app_deploy` → `web_app` for better semantics and multi-app readiness:

```bash
cd ansible/roles && mv app_deploy web_app
```

Updated all playbook references (`provision.yml`, `deploy.yml`, `site.yml`).

### Docker Compose Template

**File:** `roles/web_app/templates/docker-compose.yml.j2`

```yaml
---
services:
  {{ app_name }}:
    image: {{ docker_image }}:{{ docker_tag }}
    container_name: {{ app_name }}
    ports:
      - "{{ app_port }}:{{ app_internal_port }}"
    environment:
      HOST: "0.0.0.0"
      PORT: "{{ app_internal_port }}"
    restart: {{ app_restart_policy }}
    networks:
      - app_network

networks:
  app_network:
    driver: bridge
```

All values are Jinja2-templated and configurable via role defaults or external variables.

### Role Dependencies

**File:** `roles/web_app/meta/main.yml`

```yaml
dependencies:
  - role: docker
```

Running only the `web_app` role automatically triggers Docker installation first.

### Before / After Comparison

| Aspect | Before (app_deploy) | After (web_app) |
|--------|---------------------|-----------------|
| Deployment method | `docker run` via `docker_container` module | Docker Compose via template |
| Configuration | Inline in tasks | Templated `docker-compose.yml.j2` |
| Error handling | None | Block/rescue/always |
| Dependencies | Manual (must run docker role first) | Automatic via `meta/main.yml` |
| Multi-app support | No | Yes (same role, different variables) |
| Wipe logic | Not implemented | Variable + tag double-gating |
| Tags | None | `app_deploy`, `compose`, `web_app_wipe` |

### Variables

**Default values** (`roles/web_app/defaults/main.yml`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `app_name` | `devops-app` | Service and container name |
| `docker_image` | `aezuraa/devops-info-service` | Docker Hub image |
| `docker_tag` | `python` | Image version tag |
| `app_port` | `8000` | Host-exposed port |
| `app_internal_port` | `8080` | Container internal port |
| `app_restart_policy` | `unless-stopped` | Container restart policy |
| `compose_project_dir` | `/opt/{{ app_name }}` | Deploy directory on host |
| `web_app_wipe` | `false` | Wipe safety variable |

### Evidence: first run

```bash
ansible-playbook playbooks/deploy.yml
```

```
PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab04-vm]

TASK [docker : Install prerequisites for Docker repository] ********************
ok: [lab04-vm]

TASK [docker : Create keyrings directory] **************************************
ok: [lab04-vm]

TASK [docker : Add Docker GPG key] *********************************************
ok: [lab04-vm]

TASK [docker : Add Docker repository] ******************************************
ok: [lab04-vm]

TASK [docker : Install Docker packages] ****************************************
ok: [lab04-vm]

TASK [docker : Ensure Docker service is enabled and started] *******************
ok: [lab04-vm]

TASK [docker : Add user to docker group] ***************************************
ok: [lab04-vm]

TASK [docker : Install python3-docker for Ansible docker modules] **************
ok: [lab04-vm]

TASK [web_app : Include wipe tasks] ********************************************
included: roles/web_app/tasks/wipe.yml for lab04-vm

TASK [web_app : Stop and remove containers via docker compose] *****************
skipping: [lab04-vm]

TASK [web_app : Remove docker-compose file] ************************************
skipping: [lab04-vm]

TASK [web_app : Remove application directory] **********************************
skipping: [lab04-vm]

TASK [web_app : Remove Docker image] *******************************************
skipping: [lab04-vm]

TASK [web_app : Log wipe completion] *******************************************
skipping: [lab04-vm]

TASK [web_app : Create app directory] ******************************************
changed: [lab04-vm]

TASK [web_app : Template docker-compose file] **********************************
changed: [lab04-vm]

TASK [web_app : Log in to Docker Hub] ******************************************
fatal: [lab04-vm]: FAILED! => {... "no_log: true" ...}
...ignoring

TASK [web_app : Pull latest image] *********************************************
ok: [lab04-vm]

TASK [web_app : Deploy with docker compose] ************************************
changed: [lab04-vm]

TASK [web_app : Wait for application to be ready] ******************************
ok: [lab04-vm]

TASK [web_app : Verify health endpoint] ****************************************
ok: [lab04-vm]

TASK [web_app : Display health check result] ***********************************
ok: [lab04-vm] => {
    "health_check.json": {
        "status": "healthy",
        "timestamp": "2026-03-04T16:54:41.845057+00:00",
        "uptime_seconds": 9
    }
}

PLAY RECAP *********************************************************************
lab04-vm                   : ok=18   changed=3    unreachable=0    failed=0    skipped=5    rescued=0    ignored=1
```

First run: `changed=3` — directory created, compose file templated, containers started.

### Evidence: second run (idempotent)

```bash
ansible-playbook playbooks/deploy.yml
```

```
PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab04-vm]

TASK [docker : Install prerequisites for Docker repository] ********************
ok: [lab04-vm]

TASK [docker : Create keyrings directory] **************************************
ok: [lab04-vm]

TASK [docker : Add Docker GPG key] *********************************************
ok: [lab04-vm]

TASK [docker : Add Docker repository] ******************************************
ok: [lab04-vm]

TASK [docker : Install Docker packages] ****************************************
ok: [lab04-vm]

TASK [docker : Ensure Docker service is enabled and started] *******************
ok: [lab04-vm]

TASK [docker : Add user to docker group] ***************************************
ok: [lab04-vm]

TASK [docker : Install python3-docker for Ansible docker modules] **************
ok: [lab04-vm]

TASK [web_app : Include wipe tasks] ********************************************
included: roles/web_app/tasks/wipe.yml for lab04-vm

TASK [web_app : Stop and remove containers via docker compose] *****************
skipping: [lab04-vm]

TASK [web_app : Remove docker-compose file] ************************************
skipping: [lab04-vm]

TASK [web_app : Remove application directory] **********************************
skipping: [lab04-vm]

TASK [web_app : Remove Docker image] *******************************************
skipping: [lab04-vm]

TASK [web_app : Log wipe completion] *******************************************
skipping: [lab04-vm]

TASK [web_app : Create app directory] ******************************************
ok: [lab04-vm]

TASK [web_app : Template docker-compose file] **********************************
ok: [lab04-vm]

TASK [web_app : Log in to Docker Hub] ******************************************
fatal: [lab04-vm]: FAILED! => {... "no_log: true" ...}
...ignoring

TASK [web_app : Pull latest image] *********************************************
ok: [lab04-vm]

TASK [web_app : Deploy with docker compose] ************************************
ok: [lab04-vm]

TASK [web_app : Wait for application to be ready] ******************************
ok: [lab04-vm]

TASK [web_app : Verify health endpoint] ****************************************
ok: [lab04-vm]

TASK [web_app : Display health check result] ***********************************
ok: [lab04-vm] => {
    "health_check.json": {
        "status": "healthy",
        "timestamp": "2026-03-04T16:56:13.832102+00:00",
        "uptime_seconds": 101
    }
}

PLAY RECAP *********************************************************************
lab04-vm                   : ok=18   changed=0    unreachable=0    failed=0    skipped=5    rescued=0    ignored=1
```

Second run: `changed=0` — full idempotency confirmed. All tasks report `ok`, nothing changed.

### Evidence: VM verification

```
$ docker ps
CONTAINER ID   IMAGE                                STATUS         PORTS                                         NAMES
57a4e11ab0c8   aezuraa/devops-info-service:python   Up 3 minutes   0.0.0.0:8080->8080/tcp, [::]:8080->8080/tcp   devops-app

$ curl -s http://localhost:8080/ | python3 -m json.tool
{
    "service": {
        "description": "DevOps course info service",
        "framework": "Flask",
        "name": "devops-info-service",
        "version": "1.0.0"
    },
    "system": {
        "architecture": "x86_64",
        "cpu_count": 2,
        "hostname": "57a4e11ab0c8",
        "platform": "Linux",
        "python_version": "3.12.12"
    },
    "runtime": {
        "current_time": "2026-03-04T16:57:43.008174+00:00",
        "uptime_human": "3 minutes",
        "uptime_seconds": 190
    },
    "endpoints": ["/", "/health"]
}

$ curl -s http://localhost:8080/health | python3 -m json.tool
{
    "status": "healthy",
    "timestamp": "2026-03-04T16:57:43.062120+00:00",
    "uptime_seconds": 190
}
```

### Research Answers

**Q: What's the difference between `restart: always` and `restart: unless-stopped`?**
A: `always` restarts even after a `docker stop` command on daemon restart. `unless-stopped` does NOT restart if the container was explicitly stopped before the daemon restart. `unless-stopped` is safer for production — it respects manual stop actions.

**Q: How do Docker Compose networks differ from Docker bridge networks?**
A: Compose creates a dedicated bridge network per project with built-in DNS resolution (services can reference each other by name). Default Docker bridge networks don't provide automatic DNS and use legacy `--link` for inter-container communication.

**Q: Can you reference Ansible Vault variables in the template?**
A: Yes. Vault-encrypted variables are decrypted at playbook runtime and can be referenced in Jinja2 templates like any other variable (e.g., `{{ app_secret_key }}`).

---

## Task 3: Wipe Logic (1 pt)

### Implementation

Wipe logic uses **double-gating** — both a variable (`web_app_wipe: true`) and a tag (`--tags web_app_wipe`) must be active for wipe tasks to run.

**File:** `roles/web_app/tasks/wipe.yml`

```yaml
- name: Wipe web application
  block:
    - name: Stop and remove containers via docker compose
    - name: Remove docker-compose file
    - name: Remove application directory
    - name: Remove Docker image
    - name: Log wipe completion
  when: web_app_wipe | bool
  tags: [web_app_wipe]
```

**Included at the top of** `roles/web_app/tasks/main.yml` (before deploy block):

```yaml
- name: Include wipe tasks
  include_tasks: wipe.yml
  tags: [web_app_wipe]
```

### Test Scenarios

**Scenario 1: Normal deployment (wipe does NOT run)**

```bash
ansible-playbook playbooks/deploy.yml
```

```
TASK [web_app : Include wipe tasks] ********************************************
included: roles/web_app/tasks/wipe.yml for lab04-vm

TASK [web_app : Stop and remove containers via docker compose] *****************
skipping: [lab04-vm]

TASK [web_app : Remove docker-compose file] ************************************
skipping: [lab04-vm]

TASK [web_app : Remove application directory] **********************************
skipping: [lab04-vm]

TASK [web_app : Remove Docker image] *******************************************
skipping: [lab04-vm]

TASK [web_app : Log wipe completion] *******************************************
skipping: [lab04-vm]

...

PLAY RECAP *********************************************************************
lab04-vm                   : ok=18   changed=3    unreachable=0    failed=0    skipped=5    rescued=0    ignored=1
```

All wipe tasks **skipped** because `web_app_wipe` defaults to `false`. Deployment proceeds normally.

**Scenario 2: Wipe only**

```bash
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true" \
  --tags web_app_wipe
```

```
PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab04-vm]

TASK [web_app : Include wipe tasks] ********************************************
included: roles/web_app/tasks/wipe.yml for lab04-vm

TASK [web_app : Stop and remove containers via docker compose] *****************
changed: [lab04-vm]

TASK [web_app : Remove docker-compose file] ************************************
changed: [lab04-vm]

TASK [web_app : Remove application directory] **********************************
changed: [lab04-vm]

TASK [web_app : Remove Docker image] *******************************************
changed: [lab04-vm]

TASK [web_app : Log wipe completion] *******************************************
ok: [lab04-vm] => {
    "msg": "Application devops-app wiped successfully from /opt/devops-app"
}

PLAY RECAP *********************************************************************
lab04-vm                   : ok=7    changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

All wipe tasks **executed** (`changed=4`). Deployment tasks were NOT run because `--tags web_app_wipe` excluded them.

**VM verification after wipe:**

```
$ docker ps
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES

$ ls /opt
containerd
```

No containers running, no application directory — wipe successful.

**Scenario 3: Clean reinstallation (wipe → deploy)**

```bash
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true"
```

```
PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab04-vm]

...docker role tasks (ok)...

TASK [web_app : Include wipe tasks] ********************************************
included: roles/web_app/tasks/wipe.yml for lab04-vm

TASK [web_app : Stop and remove containers via docker compose] *****************
fatal: [lab04-vm]: FAILED! => {"msg": "Unable to change directory before execution."}
...ignoring

TASK [web_app : Remove docker-compose file] ************************************
ok: [lab04-vm]

TASK [web_app : Remove application directory] **********************************
ok: [lab04-vm]

TASK [web_app : Remove Docker image] *******************************************
fatal: [lab04-vm]: FAILED! => {"stderr": "No such image: aezuraa/devops-info-service:python"}
...ignoring

TASK [web_app : Log wipe completion] *******************************************
ok: [lab04-vm] => {
    "msg": "Application devops-app wiped successfully from /opt/devops-app"
}

TASK [web_app : Create app directory] ******************************************
changed: [lab04-vm]

TASK [web_app : Template docker-compose file] **********************************
changed: [lab04-vm]

...

TASK [web_app : Deploy with docker compose] ************************************
changed: [lab04-vm]

TASK [web_app : Display health check result] ***********************************
ok: [lab04-vm] => {
    "health_check.json": {
        "status": "healthy",
        "timestamp": "2026-03-04T17:00:49.660406+00:00",
        "uptime_seconds": 13
    }
}

PLAY RECAP *********************************************************************
lab04-vm                   : ok=23   changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=3
```

Wipe ran first (cleanup errors ignored gracefully for already-clean state), then deployment completed successfully with healthy app.

**Scenario 4: Safety check — tag without variable**

```bash
ansible-playbook playbooks/deploy.yml --tags web_app_wipe
```

```
PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab04-vm]

TASK [web_app : Include wipe tasks] ********************************************
included: roles/web_app/tasks/wipe.yml for lab04-vm

TASK [web_app : Stop and remove containers via docker compose] *****************
skipping: [lab04-vm]

TASK [web_app : Remove docker-compose file] ************************************
skipping: [lab04-vm]

TASK [web_app : Remove application directory] **********************************
skipping: [lab04-vm]

TASK [web_app : Remove Docker image] *******************************************
skipping: [lab04-vm]

TASK [web_app : Log wipe completion] *******************************************
skipping: [lab04-vm]

PLAY RECAP *********************************************************************
lab04-vm                   : ok=2    changed=0    unreachable=0    failed=0    skipped=5    rescued=0    ignored=0
```

Wipe tasks were **included** (tag matched) but **skipped** by `when: web_app_wipe | bool` because the variable defaults to `false`. Double-gating works as intended.

### Research Answers

**1. Why use both variable AND tag?**
Double safety: the variable prevents accidental wipe if tags are misconfigured, and the tag prevents wipe from running during normal deployments. Neither alone is sufficient — together they ensure wipe only happens when explicitly intended.

**2. What's the difference between `never` tag and this approach?**
The `never` tag makes tasks never run unless explicitly included with `--tags never`. This approach is more flexible: the variable allows runtime decisions (`-e "web_app_wipe=true"`) while the tag prevents execution during normal playbook runs. The `never` tag approach cannot support the "clean reinstall" scenario (wipe + deploy in one run).

**3. Why must wipe logic come BEFORE deployment in main.yml?**
For the clean reinstall scenario: old application must be removed before deploying the new one. This ensures a fresh state before the new deployment begins.

**4. When would you want clean reinstallation vs. rolling update?**
Clean reinstall is best when: changing major versions, debugging persistent state issues, switching application architecture, or fixing corrupted installations. Rolling updates are better for: zero-downtime deployments, minor version bumps, and frequent configuration changes.

**5. How would you extend this to wipe Docker images and volumes too?**
Add tasks for `docker rmi` (already included), `docker volume prune`, and `docker network prune` to the wipe block. Use `--volumes` flag with `docker compose down` to remove named volumes.

---

## Task 4: CI/CD (3 pts)

### Workflow Architecture

Two GitHub Actions workflows for independent deployment:

```
Code Push → Path Filter → Ansible Lint → Deploy via Ansible → Verify (curl)
```

### Workflow 1: Python App (`.github/workflows/ansible-deploy.yml`)

- **Trigger:** Push to `master`/`lab06` with changes in `ansible/**`
- **Job 1 — Lint:** Installs `ansible-lint`, validates playbooks and role files
- **Job 2 — Deploy:** Sets up SSH, decrypts vault, runs `deploy_python.yml`
- **Job 3 — Verify:** Curls `http://VM:8000` and `/health`

### Workflow 2: Go Bonus App (`.github/workflows/ansible-deploy-bonus.yml`)

- **Trigger:** Push to `master`/`lab06` with changes in bonus-specific paths
- Same job structure, deploys `deploy_bonus.yml` and verifies on port `8001`

### Path Filters

| File Changed | Python Workflow | Bonus Workflow |
|-------------|-----------------|----------------|
| `ansible/vars/app_python.yml` | Runs | Skipped |
| `ansible/vars/app_bonus.yml` | Skipped | Runs |
| `ansible/roles/web_app/**` | Runs | Runs |
| `ansible/playbooks/deploy_bonus.yml` | Skipped | Runs |

### Required GitHub Secrets

| Secret | Purpose |
|--------|---------|
| `ANSIBLE_VAULT_PASSWORD` | Decrypt vault-encrypted variables |
| `SSH_PRIVATE_KEY` | SSH access to target VM |
| `VM_HOST` | Target VM IP address |
| `VM_USER` | SSH username |

### Status Badges

Added to `ansible/docs/LAB06.md` (this report).

### Research Answers

**1. Security implications of storing SSH keys in GitHub Secrets?**
Secrets are encrypted at rest and masked in logs, but anyone with write access to the repo can create workflows that read them. Best practices: use deploy keys with minimal permissions, rotate regularly, prefer self-hosted runners for direct access.

**2. How to implement staging → production pipeline?**
Use separate inventory files (`inventory/staging.ini`, `inventory/production.ini`) and GitHub environments with required approvals. The staging job runs first; production requires manual approval after staging verification.

**3. What would you add to make rollbacks possible?**
Pin Docker image tags to specific versions (not `latest`). Store the previous tag in a file or variable. Create a rollback playbook that deploys the previous version. Use CalVer tags (`2026.02.27`) for traceability.

**4. How does self-hosted runner improve security?**
Self-hosted runners eliminate the need to expose SSH keys to GitHub infrastructure. The runner runs inside the trusted network with direct access to targets. No secrets leave the private environment.

---

## Task 5: Documentation

This file (`ansible/docs/LAB06.md`) serves as the complete documentation for Lab 6.

---

## Bonus Part 1: Multi-App Deployment (1.5 pts)

### Architecture

The `web_app` role is reused for both Python and Go applications with different variable files:

```
ansible/
├── vars/
│   ├── app_python.yml   # Python app: port 8000
│   └── app_bonus.yml    # Go app: port 8001
├── playbooks/
│   ├── deploy_python.yml    # Deploy Python only
│   ├── deploy_bonus.yml     # Deploy Go only
│   └── deploy_all.yml       # Deploy both apps
└── roles/
    └── web_app/             # Single role for all apps
```

### Variable Files

**Python App** (`vars/app_python.yml`):

| Variable | Value |
|----------|-------|
| `app_name` | `devops-python` |
| `docker_image` | `aezuraa/devops-info-service` |
| `docker_tag` | `python` |
| `app_port` | `8000` |
| `app_internal_port` | `8080` |

**Go Bonus App** (`vars/app_bonus.yml`):

| Variable | Value |
|----------|-------|
| `app_name` | `devops-go` |
| `docker_image` | `aezuraa/devops-info-service` |
| `docker_tag` | `go` |
| `app_port` | `8001` |
| `app_internal_port` | `8080` |

### Role Reusability

The `web_app` role is entirely parameterized — the same code handles both apps. Each app gets its own:
- Docker Compose project directory (`/opt/devops-python`, `/opt/devops-go`)
- Container name and network
- Host port mapping (8000 vs 8001)

### Deployment Commands

```bash
# Deploy Python only
ansible-playbook playbooks/deploy_python.yml

# Deploy Go only
ansible-playbook playbooks/deploy_bonus.yml

# Deploy both apps
ansible-playbook playbooks/deploy_all.yml

# Wipe only Python app (Go unaffected)
ansible-playbook playbooks/deploy_python.yml \
  -e "web_app_wipe=true" --tags web_app_wipe

# Wipe only Go app
ansible-playbook playbooks/deploy_bonus.yml \
  -e "web_app_wipe=true" --tags web_app_wipe
```

### Port Conflict Resolution

Apps use different host ports (8000, 8001) to run simultaneously. Both use internal port 8080, which is isolated within their respective Docker containers.

### Evidence: both apps deployed

**Deploy Python app:**

```bash
ansible-playbook playbooks/deploy_python.yml
```

```
PLAY [Deploy Python Application] ***********************************************

...

TASK [web_app : Create app directory] ******************************************
changed: [lab04-vm]

TASK [web_app : Template docker-compose file] **********************************
changed: [lab04-vm]

TASK [web_app : Deploy with docker compose] ************************************
changed: [lab04-vm]

TASK [web_app : Display health check result] ***********************************
ok: [lab04-vm] => {
    "health_check.json": {
        "status": "healthy",
        "timestamp": "2026-03-04T17:03:21.367388+00:00",
        "uptime_seconds": 12
    }
}

PLAY RECAP *********************************************************************
lab04-vm                   : ok=18   changed=3    unreachable=0    failed=0    skipped=5    rescued=0    ignored=1
```

**Deploy Go app:**

```bash
ansible-playbook playbooks/deploy_bonus.yml
```

```
PLAY [Deploy Go (Bonus) Application] *******************************************

...

TASK [web_app : Create app directory] ******************************************
changed: [lab04-vm]

TASK [web_app : Template docker-compose file] **********************************
changed: [lab04-vm]

TASK [web_app : Deploy with docker compose] ************************************
changed: [lab04-vm]

TASK [web_app : Display health check result] ***********************************
ok: [lab04-vm] => {
    "health_check.json": {
        "status": "healthy",
        "timestamp": "2026-03-04T17:04:55.481275349Z",
        "uptime_seconds": 11
    }
}

PLAY RECAP *********************************************************************
lab04-vm                   : ok=18   changed=3    unreachable=0    failed=0    skipped=5    rescued=0    ignored=1
```

**Deploy both apps together:**

```bash
ansible-playbook playbooks/deploy_all.yml
```

```
PLAY [Deploy All Applications] *************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab04-vm]

TASK [Deploy Python App] *******************************************************
included: web_app for lab04-vm

...

TASK [web_app : Display health check result] ***********************************
ok: [lab04-vm] => {
    "health_check.json": {
        "status": "healthy",
        "timestamp": "2026-03-04T17:11:02.150239+00:00",
        "uptime_seconds": 12
    }
}

TASK [Deploy Go (Bonus) App] ***************************************************
included: web_app for lab04-vm

...

TASK [web_app : Display health check result] ***********************************
ok: [lab04-vm] => {
    "health_check.json": {
        "status": "healthy",
        "timestamp": "2026-03-04T17:11:43.803111981Z",
        "uptime_seconds": 153
    }
}

PLAY RECAP *********************************************************************
lab04-vm                   : ok=29   changed=1    unreachable=0    failed=0    skipped=10   rescued=0    ignored=2
```

**VM verification — both apps running simultaneously:**

```
$ docker ps
CONTAINER ID   IMAGE                                STATUS          PORTS                                         NAMES
d6f0d29512da   aezuraa/devops-info-service:go       Up 24 seconds   0.0.0.0:8001->8080/tcp, [::]:8001->8080/tcp   devops-go
eed8d69ac7a1   aezuraa/devops-info-service:python   Up 2 minutes    0.0.0.0:8000->8080/tcp, [::]:8000->8080/tcp   devops-python

$ curl -s http://localhost:8000/health
{"status": "healthy", "timestamp": "2026-03-04T17:05:08.591651+00:00", "uptime_seconds": 119}

$ curl -s http://localhost:8001/health
{"status": "healthy", "timestamp": "2026-03-04T17:05:08.697947633Z", "uptime_seconds": 24}

$ curl -s http://localhost:8000/ | python3 -m json.tool
{
    "service": {
        "name": "devops-info-service",
        "framework": "Flask",
        ...
    }
}

$ curl -s http://localhost:8001/ | python3 -m json.tool
{
    "service": {
        "name": "devops-info-service",
        "framework": "Go net/http",
        ...
    }
}
```

Both apps are live: Python on `:8000` (Flask), Go on `:8001` (Go net/http).

### Evidence: independent wipe

**Wipe only Python (Go should survive):**

```bash
ansible-playbook playbooks/deploy_python.yml \
  -e "web_app_wipe=true" --tags web_app_wipe
```

```
PLAY [Deploy Python Application] ***********************************************

TASK [Gathering Facts] *********************************************************
ok: [lab04-vm]

TASK [web_app : Include wipe tasks] ********************************************
included: roles/web_app/tasks/wipe.yml for lab04-vm

TASK [web_app : Stop and remove containers via docker compose] *****************
changed: [lab04-vm]

TASK [web_app : Remove docker-compose file] ************************************
changed: [lab04-vm]

TASK [web_app : Remove application directory] **********************************
changed: [lab04-vm]

TASK [web_app : Remove Docker image] *******************************************
changed: [lab04-vm]

TASK [web_app : Log wipe completion] *******************************************
ok: [lab04-vm] => {
    "msg": "Application devops-python wiped successfully from /opt/devops-python"
}

PLAY RECAP *********************************************************************
lab04-vm                   : ok=7    changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

**VM verification after Python wipe:**

```
$ docker ps
CONTAINER ID   IMAGE                            STATUS              PORTS                                         NAMES
d6f0d29512da   aezuraa/devops-info-service:go   Up About a minute   0.0.0.0:8001->8080/tcp, [::]:8001->8080/tcp   devops-go

$ curl -s http://localhost:8001/health
{"status": "healthy", "timestamp": "2026-03-04T17:05:59.954314906Z", "uptime_seconds": 76}

$ curl -s --max-time 3 http://localhost:8000/
Connection refused — Python app is gone

$ ls /opt
containerd
devops-go
```

Python app wiped, Go app **unaffected** — independent lifecycle confirmed.

---

## Bonus Part 2: Multi-App CI/CD (1 pt)

### Implementation

Two separate GitHub Actions workflows (Approach A) for independent deployments:

1. **`ansible-deploy.yml`** — Triggered by Python-specific and shared Ansible file changes
2. **`ansible-deploy-bonus.yml`** — Triggered by Go-specific and shared Ansible file changes

### Path Filter Strategy

Changes to shared files (`roles/web_app/**`) trigger both workflows. Changes to app-specific files trigger only the relevant workflow. Documentation changes are excluded from all triggers.

### Testing Scenarios

| Change | Python Workflow | Bonus Workflow |
|--------|:---:|:---:|
| `vars/app_python.yml` | Runs | - |
| `vars/app_bonus.yml` | - | Runs |
| `roles/web_app/**` | Runs | Runs |
| `ansible/docs/**` | - | - |

---

## Summary

### What was accomplished

1. **Blocks & Tags** — All roles refactored with logical grouping, error recovery, and selective execution
2. **Docker Compose** — Migration from imperative `docker run` to declarative Compose templates
3. **Wipe Logic** — Safe cleanup with double-gating (variable + tag)
4. **CI/CD** — Automated lint → deploy → verify pipeline via GitHub Actions
5. **Multi-App** — Role reuse for Python and Go apps with independent lifecycle
6. **Multi-App CI/CD** — Independent deployment triggers via path filters

### Key Learnings

- Ansible blocks significantly improve error handling and code organization
- Docker Compose templates with Jinja2 enable flexible, multi-app deployments
- Double-gating (variable + tag) is essential for destructive operations
- Path filters in CI/CD prevent unnecessary deployments and reduce costs

### Final Directory Structure

```
ansible/
├── ansible.cfg
├── .vault_pass
├── docs/
│   ├── LAB05.md
│   └── LAB06.md
├── inventory/
│   ├── hosts.ini
│   └── group_vars/
│       └── all.yml (encrypted)
├── vars/
│   ├── app_python.yml
│   └── app_bonus.yml
├── playbooks/
│   ├── site.yml
│   ├── provision.yml
│   ├── deploy.yml
│   ├── deploy_python.yml
│   ├── deploy_bonus.yml
│   └── deploy_all.yml
└── roles/
    ├── common/
    │   ├── defaults/main.yml
    │   └── tasks/main.yml (blocks + tags + rescue)
    ├── docker/
    │   ├── defaults/main.yml
    │   ├── handlers/main.yml
    │   └── tasks/main.yml (blocks + tags + rescue)
    └── web_app/
        ├── defaults/main.yml
        ├── handlers/main.yml
        ├── meta/main.yml (docker dependency)
        ├── templates/docker-compose.yml.j2
        └── tasks/
            ├── main.yml (deploy with blocks)
            └── wipe.yml (double-gated cleanup)
```
