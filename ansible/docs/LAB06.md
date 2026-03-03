# Lab 6: Advanced Ansible & CI/CD — Submission

**Name:** Ravwvil
**Date:** 2026-02-28
**Lab Points:** 10 + 2.5 bonus

---

## Task 1: Blocks & Tags (2 pts)

### 1.1 Block Refactoring Overview

All three roles (`common`, `docker`, `web_app`) were refactored to use Ansible blocks for:
- **Task grouping** — logically related tasks wrapped in blocks
- **Error handling** — rescue sections for failure recovery
- **Always blocks** — guaranteed cleanup/logging steps
- **Directive sharing** — `become: true` and `tags` applied at block level

### 1.2 Common Role Refactoring

**File:** `roles/common/tasks/main.yml`

Three blocks were created:

| Block | Tag | Purpose |
|-------|-----|---------|
| Install system packages | `packages` | apt cache update + package installation |
| Manage users | `users` | Application user creation + docker group |
| Configure system settings | `timezone` | System timezone configuration |

**Error handling:** The packages block includes a `rescue` section that runs `apt-get update --fix-missing` and retries installation. An `always` block logs completion to `/tmp/common_packages_done.log`.

### 1.3 Docker Role Refactoring

**File:** `roles/docker/tasks/main.yml`

Two blocks were created:

| Block | Tag | Purpose |
|-------|-----|---------|
| Install Docker CE | `docker_install` | Full Docker CE installation pipeline |
| Configure Docker | `docker_config` | User groups, Python packages |

**Error handling:** The installation block includes a `rescue` section that waits 10 seconds and retries (handles GPG key network timeouts). An `always` block ensures Docker service is enabled and started.

### 1.4 Web App Role (Formerly app_deploy)

**File:** `roles/web_app/tasks/main.yml`

Deployment tasks wrapped in a block with `rescue` that displays debug info on failure.

### 1.5 Tag Strategy

```
provision.yml
├── common (tag: common)
│   ├── packages (tag: packages)
│   ├── users (tag: users)
│   └── timezone (tag: timezone)
└── docker (tag: docker)
    ├── docker_install (tag: docker_install)
    └── docker_config (tag: docker_config)

deploy.yml
└── web_app
    ├── web_app_wipe (tag: web_app_wipe)
    ├── app_deploy (tag: app_deploy)
    └── compose (tag: compose)
```

### 1.6 Execution Examples

```bash
# Run only docker installation
ansible-playbook playbooks/provision.yml --tags "docker_install"

# Skip common role
ansible-playbook playbooks/provision.yml --skip-tags "common"

# Install packages only
ansible-playbook playbooks/provision.yml --tags "packages"

# List all available tags
ansible-playbook playbooks/provision.yml --list-tags
```

### 1.7 Research Answers

**Q: What happens if rescue block also fails?**
A: If the rescue block fails, the play fails entirely. Ansible does not provide a "rescue for rescue." The `always` block still runs regardless.

**Q: Can you have nested blocks?**
A: Yes, blocks can be nested. Inner blocks can have their own rescue/always sections, providing granular error handling.

**Q: How do tags inherit to tasks within blocks?**
A: Tags applied at the block level are inherited by all tasks within that block (including rescue and always sections). Tasks can also have their own additional tags.

---

## Task 2: Docker Compose (3 pts)

### 2.1 Role Rename

Renamed `app_deploy` → `web_app` for better specificity and to support multi-app deployment patterns. Updated all playbook references accordingly.

### 2.2 Docker Compose Template

**File:** `roles/web_app/templates/docker-compose.yml.j2`

```yaml
version: '{{ docker_compose_version | default("3.8") }}'

services:
  {{ app_name }}:
    image: {{ docker_image }}:{{ docker_tag }}
    container_name: {{ app_name }}
    restart: unless-stopped
    ports:
      - "{{ app_port }}:{{ app_internal_port }}"
    environment:
      HOST: "0.0.0.0"
      PORT: "{{ app_internal_port }}"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{{ app_internal_port }}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

**Variables supported:**
- `app_name` — service/container name
- `docker_image` — Docker Hub image
- `docker_tag` — image version tag
- `app_port` — host port
- `app_internal_port` — container port
- `app_env_vars` — additional environment variables (optional dict)

### 2.3 Role Dependencies

**File:** `roles/web_app/meta/main.yml`

```yaml
dependencies:
  - role: docker
```

Running `deploy.yml` automatically installs Docker first if not present.

### 2.4 Before/After Comparison

| Aspect | Before (app_deploy) | After (web_app) |
|--------|---------------------|-----------------|
| Container management | Raw `docker run` via modules | Docker Compose declarative |
| Configuration | Ansible variables only | Templated docker-compose.yml |
| Multi-container | Not supported | Ready (add services to template) |
| Updates | Stop → Remove → Run | `docker compose up -d` |
| Dependencies | Manual role ordering | Automatic via `meta/main.yml` |
| Wipe logic | Not available | Built-in with safety gates |

### 2.5 Deployment Flow

1. Log in to Docker Hub
2. Create `/opt/<app_name>/` directory
3. Template `docker-compose.yml` to the directory
4. `docker compose pull` — pull latest image
5. `docker compose up -d --remove-orphans` — deploy
6. Wait for port to be available
7. Verify `/health` endpoint responds 200

### 2.6 Research Answers

**Q: What's the difference between `restart: always` and `restart: unless-stopped`?**
A: `always` restarts the container even after Docker daemon restart. `unless-stopped` does NOT restart if the container was manually stopped before Docker daemon restart.

**Q: How do Docker Compose networks differ from Docker bridge networks?**
A: Compose creates a project-scoped network automatically. All services in the same compose file can reach each other by service name. Default bridge network requires manual `--link` or explicit network creation.

**Q: Can you reference Ansible Vault variables in the template?**
A: Yes. Vault-encrypted variables are decrypted during playbook execution, so Jinja2 templates can reference them just like any other variable.

---

## Task 3: Wipe Logic (1 pt)

### 3.1 Implementation

**Double safety mechanism:**
1. **Variable gate:** `web_app_wipe: false` (default) — tasks have `when: web_app_wipe | bool`
2. **Tag gate:** `web_app_wipe` tag — tasks only run when this tag is selected

Both conditions must be met for wipe to execute.

### 3.2 Wipe Tasks

**File:** `roles/web_app/tasks/wipe.yml`

1. `docker compose down --remove-orphans` — stop and remove containers
2. Remove `docker-compose.yml` file
3. Remove application directory (`/opt/<app_name>`)
4. Remove Docker image (optional, saves disk)
5. Log wipe completion

### 3.3 Test Scenarios

**Scenario 1: Normal deployment (wipe does NOT run)**
```bash
ansible-playbook playbooks/deploy.yml
# Wipe tasks are skipped — tag not specified in command
```

**Scenario 2: Wipe only**
```bash
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true" --tags web_app_wipe
# Only wipe runs, deployment skipped
```

**Scenario 3: Clean reinstallation**
```bash
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true"
# Wipe runs first, then fresh deployment
```

**Scenario 4: Safety check (tag but no variable)**
```bash
ansible-playbook playbooks/deploy.yml --tags web_app_wipe
# Wipe tasks skipped by `when` condition (variable is false)
```

### 3.4 Research Answers

**1. Why use both variable AND tag?**
Double safety prevents accidental wipe. The tag prevents wipe from running during normal `deploy.yml` execution. The variable prevents wipe even if someone uses `--tags web_app_wipe` without explicitly setting the variable.

**2. What's the difference between `never` tag and this approach?**
The `never` tag means tasks never run unless `--tags never` is specified. Our approach is more flexible: we can combine wipe + deploy in one command (clean reinstall), which `never` tag cannot support elegantly.

**3. Why must wipe logic come BEFORE deployment in main.yml?**
For clean reinstallation: old app is removed first, then fresh deployment follows. If wipe came after, you'd deploy then immediately destroy.

**4. When would you want clean reinstallation vs. rolling update?**
Clean reinstall: corrupted state, major version change, config structure change. Rolling update: minor version bumps, zero-downtime requirements.

**5. How would you extend this to wipe Docker images and volumes too?**
Add `docker rmi` command (already included) and `docker volume prune -f` for volumes. Can also add `docker system prune` for full cleanup.

---

## Task 4: CI/CD (3 pts)

### 4.1 Workflow Architecture

**File:** `.github/workflows/ansible-deploy.yml`

```
Push to ansible/** → Lint → Deploy → Verify
```

**Jobs:**
1. **lint** — installs ansible-lint, validates syntax of all playbooks
2. **deploy** — configures SSH, sets up Vault password, runs ansible-playbook
3. **verify** — curls health endpoint on target VM

### 4.2 Path Filters

```yaml
on:
  push:
    paths:
      - 'ansible/**'
      - '.github/workflows/ansible-deploy.yml'
```

Changes to docs, app code, or terraform do NOT trigger the Ansible workflow.

### 4.3 Required GitHub Secrets

| Secret | Purpose |
|--------|---------|
| `ANSIBLE_VAULT_PASSWORD` | Decrypts vault-encrypted variables |
| `SSH_PRIVATE_KEY` | SSH access to target VM |
| `VM_HOST` | Target VM IP address |
| `VM_USER` | SSH username (e.g., ubuntu) |

### 4.4 Security Considerations

- SSH key stored as GitHub Secret (encrypted at rest)
- Vault password never committed to repository
- Cleanup step removes sensitive files after deployment
- `no_log: true` prevents Docker Hub password from appearing in logs

### 4.5 Status Badges

Added to `README.md`:
```markdown
[![Ansible Deployment](...badge...)](...workflow...)
[![Ansible Deploy Bonus](...badge...)](...workflow...)
```

### 4.6 Research Answers

**1. Security implications of storing SSH keys in GitHub Secrets?**
Secrets are encrypted at rest and masked in logs. Risk: anyone with write access to the repo can create workflows that use the secrets. Mitigation: use environment protection rules, require approvals for production deployments.

**2. How would you implement staging → production pipeline?**
Use GitHub environments (`staging`, `production`) with separate inventory files. Staging deploys automatically, production requires manual approval via environment protection rules.

**3. What would you add to make rollbacks possible?**
Pin Docker image tags (not `latest`). Keep previous `docker-compose.yml` as backup. Use `docker_tag` variable to target specific versions. Rollback = redeploy with previous tag.

**4. How does self-hosted runner improve security?**
SSH keys stay on the runner machine, never transit through GitHub. The runner has direct network access to the VM. No need to expose VM to the internet for SSH from GitHub-hosted runners.

---

## Task 5: Documentation

This file (`ansible/docs/LAB06.md`) serves as the documentation. All code files include inline comments explaining the implementation.

---

## Bonus Part 1: Multi-App Deployment (1.5 pts)

### Architecture

The `web_app` role is reused for both Python and Go applications with different variable files:

```
ansible/
├── vars/
│   ├── app_python.yml    # Python app: port 8000
│   └── app_bonus.yml     # Go app: port 8001
├── roles/
│   └── web_app/          # Shared role
└── playbooks/
    ├── deploy_python.yml # Deploy Python only
    ├── deploy_bonus.yml  # Deploy Go only
    └── deploy_all.yml    # Deploy both
```

### Variable Strategy

| Variable | Python App | Go App |
|----------|-----------|--------|
| `app_name` | devops-python | devops-go |
| `docker_image` | ravwvil/devops-info-service | ravwvil/devops-info-service-go |
| `app_port` | 8000 | 8001 |
| `app_internal_port` | 8000 | 8080 |
| `compose_project_dir` | /opt/devops-python | /opt/devops-go |

### Port Conflict Resolution

Each app uses a different host port (8000, 8001) mapping to its respective container port. Both can run simultaneously without conflict.

### Independent Operations

```bash
# Deploy only Python
ansible-playbook playbooks/deploy_python.yml

# Deploy only Go
ansible-playbook playbooks/deploy_bonus.yml

# Deploy both
ansible-playbook playbooks/deploy_all.yml

# Wipe only Python (Go unaffected)
ansible-playbook playbooks/deploy_python.yml \
  -e "web_app_wipe=true" --tags web_app_wipe
```

### Role Reusability Benefits

- Single role definition, multiple deployments
- Consistent deployment pattern across all apps
- Wipe logic works per-app (different `app_name` and `compose_project_dir`)
- Easy to add more apps: create a new vars file and playbook

---

## Bonus Part 2: Multi-App CI/CD (1 pt)

### Workflow Strategy: Separate Workflows

**Approach A (implemented):** One workflow per app with targeted path filters.

| Workflow | Triggers On | Deploys |
|----------|-------------|---------|
| `ansible-deploy.yml` | `ansible/**`, main ansible files | Python app |
| `ansible-deploy-bonus.yml` | `ansible/vars/app_bonus.yml`, `app_go/**` | Go app |

### Path Filter Logic

- **Python app change** → only `ansible-deploy.yml` runs
- **Go app change** → only `ansible-deploy-bonus.yml` runs
- **Role change** (`roles/web_app/**`) → both workflows run
- **Docs change** → neither workflow runs

### Test Scenarios

1. Change `ansible/vars/app_python.yml` → only Python workflow triggers
2. Change `ansible/vars/app_bonus.yml` → only Go workflow triggers
3. Change `ansible/roles/web_app/tasks/main.yml` → both workflows trigger

---

## Summary

### What Was Accomplished

1. **Blocks & Tags** — All roles refactored with structured blocks, rescue/always error handling, comprehensive tag strategy
2. **Docker Compose** — Migrated from raw `docker run` to templated Docker Compose deployments with role dependencies
3. **Wipe Logic** — Safe cleanup with double-gated (variable + tag) protection, 4 test scenarios verified
4. **CI/CD** — Automated GitHub Actions workflow with linting, deployment, and verification
5. **Multi-App** — Role reusability for Python + Go apps with independent deployment and wipe
6. **Multi-App CI/CD** — Separate workflows with targeted path filters

### Key Learnings

- Ansible blocks provide clean error handling similar to try/catch
- Tags enable flexible, selective role execution
- Docker Compose simplifies container management vs raw Docker commands
- Double-gating (variable + tag) prevents accidental destructive operations
- Role reusability is a powerful Ansible pattern for multi-app deployments
