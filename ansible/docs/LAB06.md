# Lab 6: Advanced Ansible & CI/CD - Submission

**Name:** Leonid Merkulov
**Date:** 2026-03-11
**Lab Points:** 10 + 2.5 bonus

---

## Task 1: Blocks & Tags (2 pts)

### Implementation

Refactored all roles (`common`, `docker`) to use Ansible blocks with `rescue`/`always` sections and comprehensive tag strategy.

#### Common Role (`roles/common/tasks/main.yml`)

- **Packages block** (tag: `packages`): Groups apt cache update and package installation with error handling
  - `rescue`: Runs `apt-get update --fix-missing` and retries
  - `always`: Logs completion timestamp to `/tmp/ansible_common_packages.log`
- **Users block** (tag: `users`): System configuration (timezone)

#### Docker Role (`roles/docker/tasks/main.yml`)

- **Docker Install block** (tag: `docker_install`): All Docker installation steps (prerequisites, GPG key, repo, packages)
  - `rescue`: Waits 10 seconds, retries apt update and package installation (handles GPG key network timeouts)
  - `always`: Ensures Docker service is enabled and started regardless of outcome
- **Docker Config block** (tag: `docker_config`): User group membership and python3-docker installation

### Tag Strategy

| Tag | Scope | Description |
|-----|-------|-------------|
| `common` | Role level | All common role tasks |
| `packages` | Block level | Package installation only |
| `users` | Block level | User/system configuration |
| `docker` | Role level | All Docker tasks |
| `docker_install` | Block level | Docker installation only |
| `docker_config` | Block level | Docker configuration only |

### Execution Examples

```bash
# Run only docker installation
ansible-playbook playbooks/provision.yml --tags "docker_install"

# Skip common role
ansible-playbook playbooks/provision.yml --skip-tags "common"

# Install packages only across all roles
ansible-playbook playbooks/provision.yml --tags "packages"

# List all available tags
ansible-playbook playbooks/provision.yml --list-tags
```

### Research Answers

**Q: What happens if rescue block also fails?**
A: Ansible marks the task as failed and stops execution for that host. The `always` block still runs regardless, but the play is considered failed.

**Q: Can you have nested blocks?**
A: Yes, blocks can be nested. Inner blocks can have their own rescue/always sections. However, deep nesting reduces readability and should be avoided.

**Q: How do tags inherit to tasks within blocks?**
A: Tags applied at the block level automatically inherit to all tasks within the block (including rescue and always sections). Individual tasks can have additional tags.

---

## Task 2: Docker Compose (3 pts)

### Role Rename

Renamed `app_deploy` → `web_app` for better semantic clarity and multi-app support.

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
```

### Role Dependencies

**File:** `roles/web_app/meta/main.yml`

The `web_app` role declares `docker` as a dependency, ensuring Docker is automatically installed before any app deployment:

```yaml
dependencies:
  - role: docker
```

### Deployment Flow

1. Create app directory (`/opt/{{ app_name }}`)
2. Template `docker-compose.yml` with Jinja2 variables
3. Pull latest Docker image via `docker compose pull`
4. Deploy with `docker compose up -d --force-recreate`
5. Wait for port availability
6. Verify health endpoint returns 200

### Before/After Comparison

| Aspect | Before (docker run) | After (Docker Compose) |
|--------|---------------------|----------------------|
| Config | Inline command args | Declarative YAML file |
| Updates | Stop, remove, recreate | `docker compose up -d` |
| Health | Manual curl check | Built-in healthcheck |
| Multi-app | Separate containers | Compose per service |

### Research Answers

**Q: `restart: always` vs `restart: unless-stopped`?**
A: `always` restarts even after manual `docker stop`; `unless-stopped` respects manual stops and only auto-restarts on crashes or daemon restart.

**Q: Docker Compose networks vs Docker bridge?**
A: Compose creates isolated networks per project with automatic DNS resolution between services. Default bridge requires manual `--link` or IP addressing.

**Q: Can you reference Ansible Vault variables in templates?**
A: Yes, Vault-encrypted variables are decrypted at runtime and can be used in Jinja2 templates like any other variable.

---

## Task 3: Wipe Logic (1 pt)

### Implementation

Wipe logic uses **double-gating** — both a variable (`web_app_wipe`) AND a tag (`web_app_wipe`) must be active.

**File:** `roles/web_app/tasks/wipe.yml`

Steps:
1. Stop and remove containers via `docker compose down`
2. Remove `docker-compose.yml`
3. Remove application directory
4. Remove Docker image (optional, with `ignore_errors`)
5. Log completion

**Default:** `web_app_wipe: false` in `roles/web_app/defaults/main.yml`

### Test Scenarios

| # | Command | Variable | Tag | Result |
|---|---------|----------|-----|--------|
| 1 | `ansible-playbook deploy.yml` | false | not specified | Normal deploy, wipe skipped |
| 2 | `deploy.yml -e "web_app_wipe=true" --tags web_app_wipe` | true | specified | Wipe only, no deploy |
| 3 | `deploy.yml -e "web_app_wipe=true"` | true | all tags run | Wipe then deploy (clean install) |
| 4 | `deploy.yml --tags web_app_wipe` | false | specified | Wipe blocked by `when` condition |

### Research Answers

1. **Why both variable AND tag?** Double safety: the variable prevents accidental wipe when running with `--tags`, and the tag prevents wipe during normal deployments. Neither alone can trigger wipe.

2. **`never` tag vs this approach?** The `never` tag only runs with explicit `--tags never`. Our approach allows the clean reinstall scenario (wipe + deploy in one run) which `never` tag cannot support.

3. **Why wipe BEFORE deployment in main.yml?** Enables clean reinstall: old app is removed first, then fresh deployment follows. Logical flow: remove old → install new.

4. **Clean reinstall vs rolling update?** Clean reinstall for breaking changes, major version upgrades, or corrupted state. Rolling update for minor changes where downtime is unacceptable.

5. **Extending to wipe images and volumes?** Add `docker image prune -af` and `docker volume rm` commands to the wipe block. Our implementation already includes image removal.

---

## Task 4: CI/CD (3 pts)

### Workflow Architecture

**File:** `.github/workflows/ansible-deploy.yml`

```
Push to ansible/** → Lint → Deploy → Verify
```

### Jobs

1. **Lint** (`ubuntu-latest`): Runs `ansible-lint` on all playbooks
2. **Deploy** (needs lint, only on master push): Executes Ansible playbook via SSH to target VM

### GitHub Secrets Required

| Secret | Purpose |
|--------|---------|
| `ANSIBLE_VAULT_PASSWORD` | Decrypt Vault-encrypted variables |
| `SSH_PRIVATE_KEY` | SSH access to target VM |
| `VM_HOST` | Target VM IP address |
| `VM_USER` | SSH username |

### Path Filters

Workflow only triggers on changes to `ansible/**` (excluding docs), preventing unnecessary runs for unrelated changes.

### Verification

Post-deployment step verifies the app responds on port 8000 with `curl -f`.

### Research Answers

1. **Security of SSH keys in GitHub Secrets:** Secrets are encrypted at rest and masked in logs. Risk: anyone with repo write access can exfiltrate via workflow. Mitigation: use environment protection rules, require approvals, use short-lived credentials.

2. **Staging → production pipeline:** Add separate environments in GitHub with approval gates. Deploy to staging first, run integration tests, then require manual approval for production.

3. **Rollbacks:** Tag Docker images with git SHA. On rollback, re-deploy the previous image tag. Keep last N images available. Use `docker_tag` variable to pin versions.

4. **Self-hosted vs GitHub-hosted:** Self-hosted has direct network access (no SSH needed), secrets stay local, faster execution. GitHub-hosted is easier to set up but requires exposing SSH credentials.

---

## Task 5: Documentation

This file serves as the complete documentation for Lab 6.

---

## Bonus Part 1: Multi-App Deployment (1.5 pts)

### Architecture

Reuse the same `web_app` role for both Python and Go applications with different variable files.

```
ansible/
├── vars/
│   ├── app_python.yml    # Python app config (port 8000)
│   └── app_bonus.yml     # Go app config (port 8001)
├── playbooks/
│   ├── deploy_python.yml  # Deploy Python only
│   ├── deploy_bonus.yml   # Deploy Go only
│   └── deploy_all.yml     # Deploy both apps
└── roles/
    └── web_app/           # Shared role
```

### Port Strategy

| App | Host Port | Container Port | Image |
|-----|-----------|---------------|-------|
| Python | 8000 | 8000 | merkulovlr05/devops-info |
| Go | 8001 | 8080 | merkulovlr05/devops-info-go |

### Role Reusability

The `web_app` role is parametrized — `app_name`, `docker_image`, `app_port`, and `compose_project_dir` are passed as variables. Each app gets its own Docker Compose project in `/opt/<app_name>/`.

### Independent Wipe

Wipe logic works per-app because `app_name` and `compose_project_dir` differ:

```bash
# Wipe only Python
ansible-playbook deploy_python.yml -e "web_app_wipe=true" --tags web_app_wipe

# Wipe only Go
ansible-playbook deploy_bonus.yml -e "web_app_wipe=true" --tags web_app_wipe
```

---

## Bonus Part 2: Multi-App CI/CD (1 pt)

### Separate Workflows

Two independent workflows with app-specific path filters:

| Workflow | Triggers On | Deploys |
|----------|-------------|---------|
| `ansible-deploy.yml` | `ansible/vars/app_python.yml`, role changes | Python app |
| `ansible-deploy-bonus.yml` | `ansible/vars/app_bonus.yml`, role changes | Go app |

### Path Filter Strategy

- Changes to `vars/app_python.yml` → only Python workflow runs
- Changes to `vars/app_bonus.yml` → only Go workflow runs
- Changes to `roles/web_app/**` → both workflows run (shared role)

### Matrix vs Separate Workflows

Chose **separate workflows** for:
- Independent triggering based on app-specific file changes
- Clearer logs and status per application
- Independent failure handling (one app failure doesn't block the other)

---

## Summary

### Files Modified/Created

| File | Action |
|------|--------|
| `roles/common/tasks/main.yml` | Refactored with blocks & tags |
| `roles/docker/tasks/main.yml` | Refactored with blocks & tags |
| `roles/app_deploy/` → `roles/web_app/` | Renamed |
| `roles/web_app/tasks/main.yml` | Docker Compose deployment |
| `roles/web_app/tasks/wipe.yml` | New: wipe logic |
| `roles/web_app/templates/docker-compose.yml.j2` | New: Compose template |
| `roles/web_app/meta/main.yml` | New: role dependencies |
| `roles/web_app/defaults/main.yml` | Updated with new variables |
| `playbooks/provision.yml` | Updated with tags |
| `playbooks/site.yml` | Updated for web_app role |
| `playbooks/deploy.yml` | Updated for web_app role |
| `playbooks/deploy_python.yml` | New: Python-specific deploy |
| `playbooks/deploy_bonus.yml` | New: Go-specific deploy |
| `playbooks/deploy_all.yml` | New: deploy both apps |
| `vars/app_python.yml` | New: Python app variables |
| `vars/app_bonus.yml` | New: Go app variables |
| `.github/workflows/ansible-deploy.yml` | New: Python CI/CD |
| `.github/workflows/ansible-deploy-bonus.yml` | New: Go CI/CD |
| `README.md` | Added status badges |

### Key Learnings

- Blocks provide clean error handling and logical task grouping
- Tags enable surgical execution of specific parts of playbooks
- Docker Compose with Jinja2 templates enables declarative, parametrized deployments
- Double-gated wipe logic prevents accidental data loss
- Role reusability with variable files scales to multi-app architectures
- Path filters in CI/CD prevent unnecessary workflow runs
