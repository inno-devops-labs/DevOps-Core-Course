# Lab 6 — Advanced Ansible & CI/CD


---

## 1. Overview

- **Ansible version:** 2.16.3 (ansible-core)
- **Target VM OS:** Ubuntu 24.04 LTS (AWS EC2)
- **Docker:** 29.2.1
- **Docker Compose:** v5.1.0
- **Connection:** SSH with key-based authentication

### What Was Accomplished

- Refactored `common` and `docker` roles with blocks, rescue/always error handling, and a comprehensive tag strategy
- Migrated from `docker run` (via `community.docker.docker_container`) to Docker Compose for declarative container management
- Renamed `app_deploy` role to `web_app` for clarity and reusability
- Implemented role dependencies (`web_app` depends on `docker`)
- Built wipe logic with double-gating (variable + tag) for safe application removal
- Created a GitHub Actions CI/CD workflow with ansible-lint and automated deployment

### Updated Directory Structure

```
ansible/
├── inventory/
│   └── hosts.ini
├── roles/
│   ├── common/
│   │   ├── tasks/main.yml       # Refactored with blocks & tags
│   │   └── defaults/main.yml
│   ├── docker/
│   │   ├── tasks/main.yml       # Refactored with blocks & tags
│   │   ├── handlers/main.yml
│   │   └── defaults/main.yml
│   └── web_app/                  # Renamed from app_deploy
│       ├── tasks/
│       │   ├── main.yml          # Docker Compose deployment + wipe include
│       │   └── wipe.yml          # Wipe logic
│       ├── templates/
│       │   └── docker-compose.yml.j2
│       ├── handlers/main.yml
│       ├── defaults/main.yml
│       └── meta/main.yml        # Role dependencies
├── playbooks/
│   ├── site.yml
│   ├── provision.yml
│   └── deploy.yml
├── group_vars/
│   └── all.yml                  # Encrypted with Ansible Vault
└── ansible.cfg
```

---

## 2. Blocks & Tags

### Block Usage in `common` Role

The `common` role was refactored into two blocks:

1. **Package installation block** (`packages` tag) — groups apt cache update and package installation with a rescue block that runs `apt-get update --fix-missing` on failure, and an always block that logs completion to `/tmp/ansible_common_packages.log`.

2. **System configuration block** (`users` tag) — groups timezone and user-related configuration.

```yaml
- name: Install system packages
  block:
    - name: Update apt cache
      apt:
        update_cache: yes
        cache_valid_time: 3600

    - name: Install common packages
      apt:
        name: "{{ common_packages }}"
        state: present

  rescue:
    - name: Fix apt cache and retry
      command: apt-get update --fix-missing

    - name: Retry package installation
      apt:
        name: "{{ common_packages }}"
        state: present

  always:
    - name: Log package installation completion
      copy:
        content: "Package installation completed at {{ ansible_date_time.iso8601 }}\n"
        dest: /tmp/ansible_common_packages.log
        mode: "0644"

  become: true
  tags:
    - packages
```

### Block Usage in `docker` Role

The `docker` role was refactored into two blocks:

1. **Docker installation block** (`docker_install` tag) — groups all Docker setup tasks (prerequisites, GPG key, repository, package installation) with a rescue block that waits 10 seconds and retries on GPG/network failure, and an always block ensuring Docker service is enabled.

2. **Docker configuration block** (`docker_config` tag) — groups user group assignment and Python library installation.

### Tag Strategy

| Tag | Scope | Description |
|-----|-------|-------------|
| `common` | Role level | All common role tasks |
| `packages` | Block level | Package installation only |
| `users` | Block level | User/system configuration only |
| `docker` | Role level | All docker role tasks |
| `docker_install` | Block level | Docker installation only |
| `docker_config` | Block level | Docker configuration only |
| `web_app` | Role level | All web_app role tasks |
| `app_deploy` | Block level | Deployment tasks only |
| `compose` | Block level | Docker Compose tasks |
| `web_app_wipe` | Task level | Wipe logic only |

### Tag Listing Output

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

### Selective Execution with `--tags docker`

Only Docker tasks run; common role is skipped entirely:

```
$ ansible-playbook playbooks/provision.yml --tags docker

PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [aws-vm]

TASK [docker : Install prerequisites for Docker repository] ********************
ok: [aws-vm]

TASK [docker : Create keyrings directory] **************************************
ok: [aws-vm]

TASK [docker : Add Docker GPG key] *********************************************
ok: [aws-vm]

TASK [docker : Add Docker repository] ******************************************
ok: [aws-vm]

TASK [docker : Install Docker packages] ****************************************
ok: [aws-vm]

TASK [docker : Ensure Docker service is enabled and started] *******************
ok: [aws-vm]

TASK [docker : Add user to docker group] ***************************************
ok: [aws-vm]

TASK [docker : Install python3-docker for Ansible docker modules] **************
ok: [aws-vm]

PLAY RECAP *********************************************************************
aws-vm                     : ok=9    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Selective Execution with `--tags docker_install`

Only Docker installation block tasks run (configuration block skipped):

```
$ ansible-playbook playbooks/provision.yml --tags docker_install

PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [aws-vm]

TASK [docker : Install prerequisites for Docker repository] ********************
ok: [aws-vm]

TASK [docker : Create keyrings directory] **************************************
ok: [aws-vm]

TASK [docker : Add Docker GPG key] *********************************************
ok: [aws-vm]

TASK [docker : Add Docker repository] ******************************************
ok: [aws-vm]

TASK [docker : Install Docker packages] ****************************************
ok: [aws-vm]

TASK [docker : Ensure Docker service is enabled and started] *******************
ok: [aws-vm]

PLAY RECAP *********************************************************************
aws-vm                     : ok=7    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Selective Execution with `--tags packages`

Only the packages block in the common role runs:

```
$ ansible-playbook playbooks/provision.yml --tags packages

PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [aws-vm]

TASK [common : Update apt cache] ***********************************************
ok: [aws-vm]

TASK [common : Install common packages] ****************************************
ok: [aws-vm]

TASK [common : Log package installation completion] ****************************
changed: [aws-vm]

PLAY RECAP *********************************************************************
aws-vm                     : ok=4    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Selective Execution with `--skip-tags common`

Common role is skipped, only Docker tasks execute:

```
$ ansible-playbook playbooks/provision.yml --skip-tags common

PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [aws-vm]

TASK [docker : Install prerequisites for Docker repository] ********************
ok: [aws-vm]

TASK [docker : Create keyrings directory] **************************************
ok: [aws-vm]

TASK [docker : Add Docker GPG key] *********************************************
ok: [aws-vm]

TASK [docker : Add Docker repository] ******************************************
ok: [aws-vm]

TASK [docker : Install Docker packages] ****************************************
ok: [aws-vm]

TASK [docker : Ensure Docker service is enabled and started] *******************
ok: [aws-vm]

TASK [docker : Add user to docker group] ***************************************
ok: [aws-vm]

TASK [docker : Install python3-docker for Ansible docker modules] **************
ok: [aws-vm]

PLAY RECAP *********************************************************************
aws-vm                     : ok=9    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Rescue Block Triggered (First Deploy with Container Conflict)

During the initial Docker Compose deployment, a conflict with the old Lab 5 container triggered the rescue block:

```
TASK [web_app : Deploy with docker compose] ************************************
fatal: [aws-vm]: FAILED! => {"changed": false, "msg": "non-zero return code",
  "stderr": "Container devops-app Error response from daemon: Conflict. The container
  name \"/devops-app\" is already in use..."}

TASK [web_app : Log deployment failure] ****************************************
ok: [aws-vm] => {
    "msg": "Deployment of devops-app failed. Check Docker logs with: docker compose
    -f /opt/devops-app/docker-compose.yml logs"
}

TASK [web_app : Show docker compose logs on failure] ***************************
changed: [aws-vm]

PLAY RECAP *********************************************************************
aws-vm                     : ok=16   changed=3    unreachable=0    failed=0    skipped=5    rescued=1    ignored=0
```

### Research Answers — Blocks & Tags

**Q: What happens if the rescue block also fails?**
The play fails for that host. Ansible does not have a "rescue of rescue" mechanism. The always block still executes regardless.

**Q: Can you have nested blocks?**
Yes, blocks can be nested. An inner block can have its own rescue/always sections. However, deep nesting hurts readability — prefer flat structure.

**Q: How do tags inherit to tasks within blocks?**
Tags applied at the block level automatically propagate to all tasks inside the block (including rescue and always sections). Tasks can also have their own additional tags.

---

## 3. Docker Compose Migration

### Why Docker Compose?

| Aspect | `docker run` (Lab 5) | Docker Compose (Lab 6) |
|--------|----------------------|------------------------|
| Configuration | Imperative Ansible modules | Declarative YAML file |
| Multi-container | Manual coordination | Built-in dependencies |
| Environment vars | Passed via `env` dict | Defined in compose file |
| Updates | Stop, remove, recreate | `docker compose up -d` handles it |
| Portability | Ansible-specific | Standard Docker tooling |

### Role Rename: `app_deploy` → `web_app`

The role was renamed to be more descriptive and support future multi-app patterns. `web_app` clearly identifies the type of application, while `app_deploy` was a generic action name.

### Docker Compose Template

**File:** `roles/web_app/templates/docker-compose.yml.j2`

```yaml
services:
  {{ app_name }}:
    image: {{ docker_image }}:{{ docker_tag }}
    container_name: {{ app_name }}
    ports:
      - "{{ app_port }}:{{ app_internal_port }}"
    environment:
      APP_NAME: "{{ app_name }}"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{{ app_internal_port }}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

### Templated Output on Server

```yaml
# /opt/devops-app/docker-compose.yml
services:
  devops-app:
    image: elinanotelina/devops-info-service:latest
    container_name: devops-app
    ports:
      - "5000:5000"
    environment:
      APP_NAME: "devops-app"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

### Role Dependencies

**File:** `roles/web_app/meta/main.yml`

```yaml
dependencies:
  - role: docker
```

Running only `deploy.yml` (which references `web_app`) automatically runs `docker` role first:

```
TASK [docker : Install prerequisites for Docker repository] ********************
ok: [aws-vm]
...
TASK [docker : Install python3-docker for Ansible docker modules] **************
ok: [aws-vm]

TASK [web_app : Include wipe tasks] ********************************************
included: .../roles/web_app/tasks/wipe.yml for aws-vm
...
TASK [web_app : Deploy with docker compose] ************************************
changed: [aws-vm]
```

### Deployment Output

```
$ ansible-playbook playbooks/deploy.yml

PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [aws-vm]

TASK [docker : Install prerequisites for Docker repository] ********************
ok: [aws-vm]
...
TASK [docker : Ensure Docker service is enabled and started] *******************
ok: [aws-vm]
...
TASK [web_app : Include wipe tasks] ********************************************
included: .../roles/web_app/tasks/wipe.yml for aws-vm

TASK [web_app : Stop and remove containers via docker compose] *****************
skipping: [aws-vm]
...

TASK [web_app : Create application directory] **********************************
changed: [aws-vm]

TASK [web_app : Template docker-compose file] **********************************
changed: [aws-vm]

TASK [web_app : Pull latest Docker image] **************************************
ok: [aws-vm]

TASK [web_app : Deploy with docker compose] ************************************
changed: [aws-vm]

TASK [web_app : Wait for application to be ready] ******************************
ok: [aws-vm]

TASK [web_app : Verify health endpoint] ****************************************
ok: [aws-vm]

TASK [web_app : Display health check result] ***********************************
ok: [aws-vm] => {
    "health_check.json": {
        "status": "healthy",
        "timestamp": "2026-03-05T11:34:50.303760+00:00",
        "uptime_seconds": 4
    }
}

PLAY RECAP *********************************************************************
aws-vm                     : ok=17   changed=2    unreachable=0    failed=0    skipped=5    rescued=0    ignored=0
```

### Idempotency Verification

Second run shows near-zero changes:

```
$ ansible-playbook playbooks/deploy.yml   # Second run

PLAY RECAP *********************************************************************
aws-vm                     : ok=17   changed=1    unreachable=0    failed=0    skipped=5    rescued=0    ignored=0
```

The single `changed` is from the `docker compose up -d` command module (command modules always report changed). All declarative tasks (directory, template, pull) show `ok`.

### Application Verification

```
$ docker ps
CONTAINER ID   IMAGE                                      STATUS                    PORTS                    NAMES
72aba0caead8   elinanotelina/devops-info-service:latest   Up About a minute         0.0.0.0:5000->5000/tcp   devops-app

$ curl http://localhost:5000/health
{"status":"healthy","timestamp":"2026-03-05T11:38:20.626283+00:00","uptime_seconds":82}

$ curl http://localhost:5000
{"service":{"name":"devops-info-service","version":"1.0.0",...},"system":{"hostname":"72aba0caead8",...},...}
```

### Research Answers — Docker Compose

**Q: What's the difference between `restart: always` and `restart: unless-stopped`?**
`always` restarts the container on any exit and on Docker daemon restart. `unless-stopped` does the same except it does not restart containers that were manually stopped (via `docker stop`) when the daemon restarts. `unless-stopped` is preferred for deployments where manual stops should be respected.

**Q: How do Docker Compose networks differ from Docker bridge networks?**
Docker Compose creates a project-scoped bridge network (`<project>_default`) where services can reach each other by service name. Standard bridge networks require manual creation and `--network` flags. Compose networks also provide DNS-based service discovery automatically.

**Q: Can you reference Ansible Vault variables in the template?**
Yes. Vault-encrypted variables are decrypted in memory during playbook execution and can be used in Jinja2 templates like any other variable. The rendered file on the target contains the decrypted value.

---

## 4. Wipe Logic

### Implementation

Wipe logic uses **double safety gating**:
1. **Variable gate:** `web_app_wipe: false` (default in `defaults/main.yml`)
2. **Tag gate:** `web_app_wipe` tag (must be specified or included)

Both conditions must be met for wipe tasks to execute during a normal tagged run.

**File:** `roles/web_app/tasks/wipe.yml`

```yaml
---
- name: Wipe web application
  when: web_app_wipe | bool
  become: true
  tags:
    - web_app_wipe
  block:
    - name: Stop and remove containers via docker compose
      ansible.builtin.command:
        cmd: docker compose -f {{ web_app_compose_dir }}/docker-compose.yml down --remove-orphans
      changed_when: true
      failed_when: false

    - name: Remove docker-compose file
      ansible.builtin.file:
        path: "{{ web_app_compose_dir }}/docker-compose.yml"
        state: absent

    - name: Remove application directory
      ansible.builtin.file:
        path: "{{ web_app_compose_dir }}"
        state: absent

    - name: Remove Docker image (optional cleanup)
      ansible.builtin.command:
        cmd: docker rmi {{ web_app_docker_image }}:{{ web_app_docker_tag }}
      changed_when: true
      failed_when: false

    - name: Log wipe completion
      ansible.builtin.debug:
        msg: "Application {{ web_app_name }} wiped successfully from {{ web_app_compose_dir }}"
```

Wipe is included at the **beginning** of `main.yml` (before deployment tasks) to support the clean reinstallation use case.

### Test Results

#### Scenario 1: Normal Deployment (wipe does NOT run)

```
$ ansible-playbook playbooks/deploy.yml

TASK [web_app : Include wipe tasks] ********************************************
included: .../roles/web_app/tasks/wipe.yml for aws-vm

TASK [web_app : Stop and remove containers via docker compose] *****************
skipping: [aws-vm]

TASK [web_app : Remove docker-compose file] ************************************
skipping: [aws-vm]

TASK [web_app : Remove application directory] **********************************
skipping: [aws-vm]

TASK [web_app : Remove Docker image (optional cleanup)] ************************
skipping: [aws-vm]

TASK [web_app : Log wipe completion] *******************************************
skipping: [aws-vm]

TASK [web_app : Create application directory] **********************************
ok: [aws-vm]
...
TASK [web_app : Display health check result] ***********************************
ok: [aws-vm] => {"health_check.json": {"status": "healthy",...}}

PLAY RECAP *********************************************************************
aws-vm                     : ok=17   changed=2    unreachable=0    failed=0    skipped=5    rescued=0    ignored=0
```

All wipe tasks skipped (variable is false), deployment proceeds normally.

#### Scenario 2: Wipe Only (remove existing deployment)

```
$ ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe

TASK [web_app : Include wipe tasks] ********************************************
included: .../roles/web_app/tasks/wipe.yml for aws-vm

TASK [web_app : Stop and remove containers via docker compose] *****************
changed: [aws-vm]

TASK [web_app : Remove docker-compose file] ************************************
changed: [aws-vm]

TASK [web_app : Remove application directory] **********************************
changed: [aws-vm]

TASK [web_app : Remove Docker image (optional cleanup)] ************************
changed: [aws-vm]

TASK [web_app : Log wipe completion] *******************************************
ok: [aws-vm] => {
    "msg": "Application devops-app wiped successfully from /opt/devops-app"
}

PLAY RECAP *********************************************************************
aws-vm                     : ok=7    changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

Verification after wipe:

```
$ docker ps
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES

$ ls /opt/
containerd
```

App removed, directory gone, no containers running.

#### Scenario 3: Clean Reinstallation (wipe → deploy)

```
$ ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"

TASK [web_app : Stop and remove containers via docker compose] *****************
...ignoring    # Already clean from previous wipe

TASK [web_app : Remove docker-compose file] ************************************
ok: [aws-vm]

TASK [web_app : Remove application directory] **********************************
ok: [aws-vm]

TASK [web_app : Log wipe completion] *******************************************
ok: [aws-vm] => {"msg": "Application devops-app wiped successfully from /opt/devops-app"}

TASK [web_app : Create application directory] **********************************
changed: [aws-vm]

TASK [web_app : Template docker-compose file] **********************************
changed: [aws-vm]

TASK [web_app : Pull latest Docker image] **************************************
changed: [aws-vm]

TASK [web_app : Deploy with docker compose] ************************************
changed: [aws-vm]

TASK [web_app : Wait for application to be ready] ******************************
ok: [aws-vm]

TASK [web_app : Verify health endpoint] ****************************************
ok: [aws-vm]

TASK [web_app : Display health check result] ***********************************
ok: [aws-vm] => {
    "health_check.json": {
        "status": "healthy",
        "timestamp": "2026-03-05T11:37:03.014246+00:00",
        "uptime_seconds": 4
    }
}

PLAY RECAP *********************************************************************
aws-vm                     : ok=22   changed=6    unreachable=0    failed=0    skipped=0    rescued=0    ignored=2
```

Wipe tasks ran first (cleaning up), then deployment tasks ran (fresh install). Application is healthy after clean reinstall.

#### Scenario 4a: Safety Check — Tag Specified but Variable False

```
$ ansible-playbook playbooks/deploy.yml --tags web_app_wipe

TASK [web_app : Include wipe tasks] ********************************************
included: .../roles/web_app/tasks/wipe.yml for aws-vm

TASK [web_app : Stop and remove containers via docker compose] *****************
skipping: [aws-vm]

TASK [web_app : Remove docker-compose file] ************************************
skipping: [aws-vm]

TASK [web_app : Remove application directory] **********************************
skipping: [aws-vm]

TASK [web_app : Remove Docker image (optional cleanup)] ************************
skipping: [aws-vm]

TASK [web_app : Log wipe completion] *******************************************
skipping: [aws-vm]

PLAY RECAP *********************************************************************
aws-vm                     : ok=2    changed=0    unreachable=0    failed=0    skipped=5    rescued=0    ignored=0
```

All wipe tasks skipped because `web_app_wipe` variable defaults to `false` — the `when` condition blocks execution even though the tag matched.

### Research Answers — Wipe Logic

**1. Why use both variable AND tag?**
Double safety prevents accidental data loss. The tag prevents wipe from running during normal `deploy.yml` execution (deployment tags don't include `web_app_wipe`). The variable prevents wipe even if someone specifies the tag — they must also explicitly set `web_app_wipe=true`. Neither alone is sufficient.

**2. What's the difference between `never` tag and this approach?**
The `never` tag is a special Ansible tag that causes tasks to never run unless explicitly included with `--tags never`. This approach is more flexible: the wipe tasks are included naturally when all tags run (e.g., clean reinstall scenario) but gated by a variable. With `never` tag, you could not do a clean reinstall in a single playbook run.

**3. Why must wipe logic come BEFORE deployment in main.yml?**
For the clean reinstallation use case (`-e "web_app_wipe=true"` without `--tags`), wipe runs first to remove the old installation, then deployment tasks create a fresh install. If wipe came after deployment, you'd deploy then immediately destroy.

**4. When would you want clean reinstallation vs. rolling update?**
Clean reinstallation when: changing fundamental configuration (ports, volumes), debugging persistent state issues, major version upgrades, or recovering from corruption. Rolling update when: minor updates, zero-downtime required, or preserving application state.

**5. How would you extend this to wipe Docker images and volumes too?**
Add tasks: `docker volume prune -f` to remove dangling volumes, `docker image prune -a -f` for all unused images, or target specific volumes with `docker volume rm <name>`. The current implementation already removes the Docker image via `docker rmi`.

---

## 5. CI/CD Integration

### Workflow Architecture

```
Push to ansible/** → Ansible Lint → Deploy with Ansible → Verify Deployment
```

### Workflow File

**File:** `.github/workflows/ansible-deploy.yml`

```yaml
name: Ansible Deployment

on:
  push:
    branches: [ master, lab6 ]
    paths:
      - 'ansible/**'
      - '!ansible/docs/**'
      - '.github/workflows/ansible-deploy.yml'
  pull_request:
    branches: [ master, lab6 ]
    paths:
      - 'ansible/**'

jobs:
  lint:
    name: Ansible Lint
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install ansible ansible-lint

      - name: Create vault password file
        run: |
          echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > ansible/.vault_pass
          chmod 600 ansible/.vault_pass

      - name: Run ansible-lint
        run: |
          cd ansible
          ansible-lint playbooks/*.yml

      - name: Remove vault password file
        if: always()
        run: rm -f ansible/.vault_pass

  deploy:
    name: Deploy Application
    needs: lint
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install Ansible
        run: pip install ansible

      - name: Setup SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          ssh-keyscan -H ${{ secrets.VM_HOST }} >> ~/.ssh/known_hosts

      - name: Create vault password file
        run: |
          echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > ansible/.vault_pass
          chmod 600 ansible/.vault_pass

      - name: Deploy with Ansible
        run: |
          cd ansible
          ansible-playbook playbooks/deploy.yml \
            -i inventory/hosts.ini \
            -e "ansible_ssh_private_key_file=~/.ssh/id_rsa"

      - name: Remove vault password file
        if: always()
        run: rm -f ansible/.vault_pass

      - name: Verify Deployment
        run: |
          sleep 10
          curl -f http://${{ secrets.VM_HOST }}:5000 || exit 1
          curl -f http://${{ secrets.VM_HOST }}:5000/health || exit 1
```

### Required GitHub Secrets

| Secret | Purpose |
|--------|---------|
| `SSH_PRIVATE_KEY` | SSH private key for EC2 access |
| `VM_HOST` | Target EC2 IP address (52.91.90.128) |
| `ANSIBLE_VAULT_PASSWORD` | Password to decrypt Ansible Vault files |


### Path Filters

The workflow only triggers on changes to `ansible/**`, excluding documentation (`!ansible/docs/**`). The workflow file itself is also included to catch pipeline changes. This prevents unnecessary CI/CD runs when unrelated code changes.

### Status Badge

Added to root `README.md`:

```markdown
[![Ansible Deployment](https://github.com/elinanotelina/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/elinanotelina/DevOps-Core-Course/actions/workflows/ansible-deploy.yml)
```

### CI/CD Run Evidence

The workflow is configured and validated locally. Workflow run logs will be available in the GitHub Actions tab after the branch is merged to `master`. The workflow triggers on pushes to `ansible/**` (excluding `ansible/docs/**`), runs `ansible-lint` on all playbooks, then connects to the EC2 instance via SSH and runs `ansible-playbook playbooks/deploy.yml`, followed by a `curl` health check verification.

### Research Answers — CI/CD

**1. What are the security implications of storing SSH keys in GitHub Secrets?**
GitHub Secrets are encrypted at rest and only exposed to workflows as environment variables. Risks include: secrets leaked in logs if `echo`ed, accessible to anyone with write access to the repo, and compromised if a workflow runs malicious code. Mitigations: use short-lived keys, limit secret access to specific environments, rotate keys regularly, and never print secrets in logs.

**2. How would you implement a staging → production deployment pipeline?**
Use GitHub environments with protection rules. The `staging` environment deploys on every push; the `production` environment requires manual approval. Use separate inventory files (`hosts_staging.ini`, `hosts_prod.ini`) and environment-specific variables. The workflow would have `deploy-staging` and `deploy-production` jobs with the production job gated by environment approval.

**3. What would you add to make rollbacks possible?**
Tag Docker images with the git SHA or a semantic version instead of only `latest`. Store the previous deployment's image tag in a state file. Add a rollback job that deploys the previous known-good image tag. Alternatively, use blue-green deployment with two compose files and switch traffic at the load balancer.

**4. How does self-hosted runner improve security compared to GitHub-hosted?**
Self-hosted runners run inside your infrastructure, so secrets never leave your network. No SSH keys need to be stored in GitHub — the runner already has access to the target. Network traffic stays internal. However, self-hosted runners require maintenance and must be hardened against supply-chain attacks in Actions workflows.

---

## 6. Testing Results

### Full Test Summary

| Test | Result | Details |
|------|------|---------|
| Tag listing (`--list-tags`) | Pass | 6 tags on provision, 6 on deploy |
| Selective execution (`--tags docker`) |  Pass | Only docker tasks ran |
| Skip tags (`--skip-tags common`) | Pass | Common role entirely skipped |
| Rescue block triggered |  Pass | Container conflict handled gracefully |
| Docker Compose deployment |  Pass | Container running, health check passed |
| Idempotency (2nd run) |  Pass | 1 changed (command module), rest ok |
| Wipe Scenario 1: Normal deploy |  Pass | Wipe tasks skipped, app deployed |
| Wipe Scenario 2: Wipe only |  Pass | App removed, directory cleaned |
| Wipe Scenario 3: Clean reinstall |  Pass | Wipe → fresh deploy, app healthy |
| Wipe Scenario 4a: Tag without variable |  Pass | Wipe blocked by `when` condition |
| Health endpoint |  Pass | `{"status":"healthy"}` returned |
| Application root endpoint |  Pass | Service info JSON returned |

### Application Accessibility

```
$ curl http://localhost:5000/health
{
    "status": "healthy",
    "timestamp": "2026-03-05T11:39:11.416708+00:00",
    "uptime_seconds": 133
}

$ curl http://localhost:5000
{
    "service": {
        "name": "devops-info-service",
        "version": "1.0.0",
        "description": "DevOps course info service",
        "framework": "FastAPI"
    },
    "system": {
        "hostname": "72aba0caead8",
        "platform": "Linux",
        "architecture": "x86_64",
        "python_version": "3.13.12"
    },
    ...
}
```

---

## 7. Challenges & Solutions

**1. Container name conflict during Docker Compose migration.**
The old Lab 5 container (`devops-app`) was still running via `docker run`. Docker Compose tried to create a container with the same name and failed. Solution: the rescue block caught the error and logged diagnostics. The old container was removed, and the subsequent clean deploy succeeded.

**2. `version` attribute deprecation in Docker Compose.**
Docker Compose v2+ treats the `version` key as obsolete and emits a warning. Removed the `version` field from the Jinja2 template to produce clean output.

**3. Idempotency with command modules.**
The `docker compose up -d` command always reports `changed` because Ansible's `command` module cannot determine if the state actually changed. This is an acceptable trade-off — all declarative tasks (file, template, apt) correctly report idempotent state.

**4. SSH key permissions on Windows.**
`key.pem` had overly permissive ACLs on Windows, causing SSH to reject it. Fixed with `icacls key.pem /inheritance:r /grant:r "$env:USERNAME:R"`.

---
