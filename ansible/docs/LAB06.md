# Lab 6: Advanced Ansible & CI/CD - Submission

**Name:** Egor Torshin
**Date:** 2026-03-04
**Lab Points:** 10 + 2.5 bonus

---

## Task 1: Blocks & Tags (2 pts)

### Block usage in common role

The `common` role was refactored into two blocks:

1. **`packages` block** — groups apt cache update and package installation with rescue/always:
   - `rescue`: runs `apt-get update --fix-missing` and retries installation
   - `always`: writes a timestamp log to `/tmp/common_packages_done.log`

2. **`users` block** — manages system user creation (deploy user + sudo group membership)

```yaml
# roles/common/tasks/main.yml (packages block)
- name: Install system packages
  block:
    - name: Update apt cache
      ...
    - name: Install common packages
      ...
  rescue:
    - name: Fix apt cache and retry
      ...
  always:
    - name: Log package installation completion
      ...
  become: true
  tags:
    - packages
```

### Block usage in docker role

The `docker` role was split into two blocks:

1. **`docker_install` block** — prerequisites, GPG key, repository, engine packages with rescue logic:
   - `rescue`: waits 10 seconds, retries apt update and package installation
   - `always`: ensures Docker service is enabled and started

2. **`docker_config` block** — Python Docker SDK and user group management

### Tag strategy

| Tag | Scope | Description |
|-----|-------|-------------|
| `packages` | common role | Package installation tasks only |
| `users` | common role | User management tasks only |
| `docker_install` | docker role | Docker Engine installation only |
| `docker_config` | docker role | Docker environment configuration only |
| `app_deploy` | web_app role | Application deployment tasks |
| `compose` | web_app role | Docker Compose operations |
| `web_app_wipe` | web_app role | Wipe/cleanup tasks |

### Execution examples

```bash
# Run only docker installation
ansible-playbook playbooks/provision.yml --tags "docker_install"

# Skip common role entirely
ansible-playbook playbooks/provision.yml --skip-tags "packages,users"

# List all available tags
ansible-playbook playbooks/provision.yml --list-tags

# Check mode with specific tag
ansible-playbook playbooks/provision.yml --tags "docker_install" --check
```

### Research answers

**Q: What happens if rescue block also fails?**
The play fails for that host. Ansible marks the host as failed and proceeds with remaining hosts (unless `any_errors_fatal: true`). The `always` block still executes regardless.

**Q: Can you have nested blocks?**
Yes, blocks can be nested inside other blocks. Inner blocks can have their own rescue/always sections.

**Q: How do tags inherit to tasks within blocks?**
Tags applied at block level are inherited by all tasks within the block. Tasks can also have additional tags of their own.

---

## Task 2: Docker Compose (3 pts)

### Role rename: app_deploy -> web_app

The `app_deploy` role was renamed to `web_app` for better specificity and to support potential multi-app deployments.

### Docker Compose template

`roles/web_app/templates/docker-compose.yml.j2`:

```yaml
---
version: "{{ docker_compose_version }}"

services:
  {{ app_name }}:
    image: {{ docker_image }}:{{ docker_tag }}
    container_name: {{ app_name }}
    ports:
      - "{{ app_port }}:{{ app_internal_port }}"
    environment:
      APP_NAME: "{{ app_name }}"
      APP_PORT: "{{ app_internal_port }}"
    restart: unless-stopped
```

All values are parameterized through Jinja2 variables defined in `roles/web_app/defaults/main.yml`.

### Role dependencies

`roles/web_app/meta/main.yml` declares `docker` as a dependency, ensuring Docker is always installed before deployment:

```yaml
---
dependencies:
  - role: docker
```

### Before/after comparison

| Aspect | Before (Lab 5) | After (Lab 6) |
|--------|----------------|----------------|
| Deployment method | `docker run` via `community.docker.docker_container` | Docker Compose via template |
| Configuration | Ansible module parameters | Declarative `docker-compose.yml` |
| Image management | Manual pull + container create | `docker compose pull && up -d` |
| Cleanup | Manual container stop/remove | `docker compose down` |
| Role name | `app_deploy` | `web_app` |
| Dependencies | Implicit (playbook order) | Explicit (meta/main.yml) |

### Variables

```yaml
app_name: devops-app
docker_image: egortorshin/devops-info-service
docker_tag: latest
app_port: 8000
app_internal_port: 8000
compose_project_dir: "/opt/{{ app_name }}"
docker_compose_version: "3.8"
```

### Research answers

**Q: What's the difference between `restart: always` and `restart: unless-stopped`?**
`always` restarts even after manual `docker stop`. `unless-stopped` respects manual stops — it restarts on daemon restart only if the container was running before the daemon stopped.

**Q: How do Docker Compose networks differ from Docker bridge networks?**
Docker Compose automatically creates an isolated bridge network per project. All services in the same compose file can reach each other by service name. Default Docker bridge requires manual `--link` or explicit network creation.

**Q: Can you reference Ansible Vault variables in the template?**
Yes. Vault-encrypted variables are decrypted at runtime and can be used in Jinja2 templates identically to plaintext variables.

---

## Task 3: Wipe Logic (1 pt)

### Implementation

Wipe logic uses a **double-gating** mechanism:

1. **Variable gate:** `web_app_wipe` (default: `false`) — controlled via `-e "web_app_wipe=true"`
2. **Tag gate:** `web_app_wipe` tag — must be explicitly included or run without tag filters

`roles/web_app/tasks/wipe.yml`:

```yaml
- name: Wipe web application
  block:
    - name: Stop and remove containers via Docker Compose
      ...
    - name: Remove Docker image
      ...
    - name: Remove application directory
      ...
    - name: Log wipe completion
      ...
  when: web_app_wipe | default(false) | bool
  tags:
    - web_app_wipe
```

Wipe is included at the **beginning** of `main.yml` (before deployment) to support the clean reinstallation scenario: wipe old -> deploy new.

### Test scenarios

**Scenario 1: Normal deployment (wipe does NOT run)**
```bash
ansible-playbook playbooks/deploy.yml
# Wipe tasks are skipped because web_app_wipe tag is not specified
```

**Scenario 2: Wipe only**
```bash
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true" \
  --tags web_app_wipe
```

**Scenario 3: Clean reinstallation**
```bash
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true"
# Wipe runs first, then deployment follows
```

**Scenario 4: Safety check — tag without variable**
```bash
ansible-playbook playbooks/deploy.yml --tags web_app_wipe
# when condition blocks execution since web_app_wipe defaults to false
```

### Research answers

**1. Why use both variable AND tag?**
Double safety: the variable prevents accidental execution if tags aren't filtered properly, and the tag prevents wipe from running during normal deployments even if someone accidentally sets the variable.

**2. What's the difference between `never` tag and this approach?**
The `never` tag completely excludes tasks unless explicitly included with `--tags never`. Our approach allows wipe to run as part of a full deployment (clean install scenario) when the variable is set, which `never` tag cannot support.

**3. Why must wipe logic come BEFORE deployment in main.yml?**
To support the clean reinstallation pattern: first remove the old deployment, then deploy fresh. If wipe came after deployment, you'd deploy and immediately destroy.

**4. When would you want clean reinstallation vs. rolling update?**
Clean reinstallation for major version upgrades, configuration changes that require fresh state, or debugging environment issues. Rolling updates for minor patches where downtime must be minimized.

**5. How would you extend this to wipe Docker images and volumes too?**
Add `docker compose down --volumes --rmi all` to remove volumes and images, or separate tasks with `docker volume prune -f` and `docker image prune -af`.

---

## Task 4: CI/CD (3 pts)

### Workflow architecture

`.github/workflows/ansible-deploy.yml` implements a two-stage pipeline:

1. **Lint stage** (`lint` job) — runs on every push and PR:
   - Installs Python 3.12, Ansible, ansible-lint
   - Runs `ansible-lint` on all playbooks

2. **Deploy stage** (`deploy` job) — runs only on push to main/master:
   - Sets up SSH to target VM using GitHub Secrets
   - Decrypts Vault secrets
   - Executes `ansible-playbook playbooks/deploy.yml`
   - Verifies deployment via HTTP health check

### Path filters

The workflow only triggers on changes to:
- `ansible/**` (excluding `ansible/docs/**`)
- `.github/workflows/ansible-deploy.yml`

This avoids unnecessary runs when documentation or unrelated code changes.

### Required GitHub Secrets

| Secret | Purpose |
|--------|---------|
| `ANSIBLE_VAULT_PASSWORD` | Decrypt Vault-encrypted variables |
| `SSH_PRIVATE_KEY` | SSH access to target VM |
| `VM_HOST` | Target VM IP address |

### Research answers

**1. Security implications of SSH keys in GitHub Secrets?**
GitHub encrypts secrets at rest and in transit. They're never exposed in logs. However, anyone with repo write access can create workflows that use secrets. Mitigate with branch protection rules and required reviews.

**2. Staging -> production pipeline?**
Add environments in GitHub Actions with required reviewers. Deploy to staging automatically, require manual approval for production. Use separate inventory files per environment.

**3. Rollback strategy?**
Tag Docker images with git SHA. On failure, redeploy the previous image tag. Keep the last N compose files as backups. Alternatively, use blue-green deployment with two compose projects.

**4. Self-hosted vs GitHub-hosted runner security?**
Self-hosted runners keep secrets and SSH keys within your infrastructure. GitHub-hosted runners expose your SSH keys to GitHub's infrastructure (encrypted, but still external). Self-hosted also avoids network exposure of target VMs.

---

## Task 5: Documentation

This file serves as the documentation for Lab 6.

### Project structure

```
ansible/
├── ansible.cfg
├── .vault_pass
├── inventory/
│   └── hosts.ini
├── group_vars/
│   └── all.yml              # Vault-encrypted variables
├── docs/
│   ├── LAB05.md
│   └── LAB06.md              # This file
├── playbooks/
│   ├── site.yml              # Imports provision + deploy
│   ├── provision.yml          # common + docker roles
│   └── deploy.yml            # web_app role
└── roles/
    ├── common/
    │   ├── defaults/main.yml  # Package list, deploy user
    │   ├── handlers/main.yml
    │   └── tasks/main.yml     # Blocks: packages, users
    ├── docker/
    │   ├── defaults/main.yml  # Docker packages, repo config
    │   ├── handlers/main.yml  # restart docker handler
    │   └── tasks/main.yml     # Blocks: docker_install, docker_config
    └── web_app/
        ├── defaults/main.yml  # App config, wipe flag
        ├── handlers/main.yml  # restart app handler
        ├── meta/main.yml      # Dependency: docker role
        ├── templates/
        │   └── docker-compose.yml.j2
        ├── files/
        │   └── app.py         # Application source (legacy)
        └── tasks/
            ├── main.yml       # Wipe include + deploy block
            └── wipe.yml       # Wipe logic
```

---

## Summary

- Refactored all roles with blocks, rescue/always, and comprehensive tag strategy
- Migrated from `docker run` to Docker Compose with Jinja2 templating
- Implemented double-gated wipe logic (variable + tag)
- Created CI/CD pipeline with linting and automated deployment
- All roles use explicit dependencies via meta/main.yml
