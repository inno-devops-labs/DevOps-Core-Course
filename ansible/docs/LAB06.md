# Lab 6: Advanced Ansible & CI/CD - Submission

**Name:** Arina Zimina
**Date:** 2026-03-04
**Lab Points:** 10 + bonus

---

## Task 1: Blocks & Tags (2 pts)

### Implementation

All three roles (`common`, `docker`, `web_app`) were refactored to use Ansible blocks with `rescue`/`always` sections and a comprehensive tag strategy.

#### `common` role

- **`packages` block**: groups apt mirror configuration, cache update, and package installation. `rescue` runs `apt-get update --fix-missing` if the block fails and retries. `always` logs completion to `/tmp/ansible_common_packages.log`.
- **`users` block**: groups timezone setup. `always` logs completion.
- Tags: `packages`, `users`, `common`.

#### `docker` role

- **`docker_install` block**: groups Docker GPG key, repo, cache update, and package installation. `rescue` waits 10 seconds and retries (handles transient network failures). `always` ensures Docker service is enabled and started.
- **`docker_config` block**: groups user group membership and python3-docker installation.
- Tags: `docker_install`, `docker_config`, `docker`.

#### `web_app` role

- **Deploy block** (`app_deploy`, `compose`): groups Docker Hub login, directory creation, template rendering, compose up, health check. `rescue` logs the error and fails with diagnostic info.
- **Wipe block** (`web_app_wipe`): gated by `when: web_app_wipe | bool` variable.

### Tag strategy

| Tag | Scope |
|-----|-------|
| `packages` | common role: package installation only |
| `users` | common role: user/system configuration |
| `common` | entire common role |
| `docker_install` | docker role: installation only |
| `docker_config` | docker role: configuration only |
| `docker` | entire docker role |
| `app_deploy` | web_app role: deployment tasks |
| `compose` | web_app role: docker compose tasks |
| `web_app_wipe` | web_app role: wipe/cleanup tasks |

### Evidence

```bash
# Selective execution with tags
ansible-playbook playbooks/provision.yml --tags "docker" --ask-vault-pass

# Skip common role
ansible-playbook playbooks/provision.yml --skip-tags "common" --ask-vault-pass

# List all tags
ansible-playbook playbooks/deploy.yml --list-tags
```

> **TODO**: Paste terminal outputs here after running on VM.

### Research Questions

**Q: What happens if rescue block also fails?**
A: The play fails entirely. Ansible reports the original error from the block AND the rescue error. The `always` section still executes regardless — it runs whether block succeeds, block fails, or rescue fails.

**Q: Can you have nested blocks?**
A: Yes, blocks can be nested. An inner block can have its own `rescue`/`always`. However, deep nesting hurts readability — prefer flat structure with separate blocks for each logical group.

**Q: How do tags inherit to tasks within blocks?**
A: Tags applied at the block level automatically propagate to every task inside that block (including `rescue` and `always`). Tasks can also have their own additional tags. When running `--tags`, a task runs if it matches any of its inherited or direct tags.

---

## Task 2: Docker Compose (3 pts)

### Migration from `docker run` to Docker Compose

The `app_deploy` role was renamed to `web_app` and completely rewritten to use Docker Compose via a Jinja2 template.

#### Before (Lab 5 — `app_deploy`)

- Used `community.docker.docker_container` module
- Stopped, removed, and re-created container on each run
- No declarative configuration file

#### After (Lab 6 — `web_app`)

- Uses a templated `docker-compose.yml.j2`
- Deploys with `docker compose up -d --force-recreate`
- Declarative — desired state is in a version-controlled template
- Easy to add services, volumes, networks in the future

### Template structure

```yaml
version: '3.8'
services:
  {{ app_name }}:
    image: {{ docker_image }}:{{ docker_tag }}
    container_name: {{ app_name }}
    ports:
      - "{{ app_port }}:{{ app_internal_port }}"
    restart: {{ app_restart_policy }}
```

### Role dependencies

`roles/web_app/meta/main.yml` declares `docker` as a dependency, so running `deploy.yml` automatically provisions Docker first.

### Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `app_name` | `devops-app` | Container and service name |
| `docker_image` | from vault | Docker Hub image |
| `docker_tag` | `latest` | Image version |
| `app_port` | `8000` | Host port |
| `app_internal_port` | `8000` | Container port |
| `compose_project_dir` | `/opt/{{ app_name }}` | Directory for compose file |
| `web_app_wipe` | `false` | Wipe control flag |

### Evidence

```bash
# Full deployment
ansible-playbook playbooks/deploy.yml --ask-vault-pass

# Idempotency (second run)
ansible-playbook playbooks/deploy.yml --ask-vault-pass

# Verify
ssh ubuntu@<VM_IP> "docker ps"
curl http://<VM_IP>:8000/health
```

> **TODO**: Paste terminal outputs and verify idempotency.

### Research Questions

**Q: What's the difference between `restart: always` and `restart: unless-stopped`?**
A: `always` restarts the container on any exit and on Docker daemon startup. `unless-stopped` does the same but does NOT restart containers that were manually stopped (with `docker stop`) when the daemon restarts. `unless-stopped` is preferred for deployments — it respects intentional stops.

**Q: How do Docker Compose networks differ from Docker bridge networks?**
A: Docker Compose automatically creates a dedicated bridge network per project. Containers within the same compose project can reach each other by service name (built-in DNS). Manual `docker run` uses the default bridge where containers communicate only by IP unless you create and attach a custom network.

**Q: Can you reference Ansible Vault variables in the template?**
A: Yes. Vault-encrypted variables are decrypted in memory during playbook execution. Jinja2 templates render with the decrypted values, so `{{ dockerhub_password }}` in a template would contain the plaintext. Be careful not to expose secrets in files on disk.

---

## Task 3: Wipe Logic (1 pt)

### Implementation

Wipe logic uses a **double-gating** mechanism:

1. **Variable gate**: `web_app_wipe: false` in `defaults/main.yml` — `when: web_app_wipe | bool` condition
2. **Tag gate**: `tags: [web_app_wipe]` — tasks only run when this tag is selected or all tags run

### Wipe tasks (`roles/web_app/tasks/wipe.yml`)

1. `docker compose down --remove-orphans` (stop and remove containers)
2. Remove `docker-compose.yml` file
3. Remove application directory (`/opt/<app_name>`)
4. Optionally remove Docker image
5. Log success message

### Test Scenarios

**Scenario 1: Normal deployment (wipe does NOT run)**
```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
# Wipe tasks are skipped because web_app_wipe=false
```

**Scenario 2: Wipe only**
```bash
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true" \
  --tags web_app_wipe --ask-vault-pass
# Only wipe runs; deployment is skipped (tag not matched)
```

**Scenario 3: Clean reinstall (wipe + deploy)**
```bash
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true" --ask-vault-pass
# Wipe runs first, then fresh deployment
```

**Scenario 4: Safety — tag without variable**
```bash
ansible-playbook playbooks/deploy.yml --tags web_app_wipe --ask-vault-pass
# Wipe tasks skipped by when condition (web_app_wipe=false)
```

> **TODO**: Paste terminal outputs for all 4 scenarios.

### Research Questions

**Q: Why use both variable AND tag?**
A: Double safety. The tag prevents wipe from running during normal `ansible-playbook deploy.yml` (tags don't match). The variable prevents wipe if someone runs `--tags web_app_wipe` without setting the variable. Both must be true for wipe to execute — two independent locks.

**Q: What's the difference between `never` tag and this approach?**
A: The `never` tag is a special Ansible tag that excludes tasks unless `--tags never` is explicitly given. Our approach uses a custom tag + variable, which is more flexible: you can combine wipe with deployment tags for clean-reinstall scenarios. `never` tag can't be combined with deployment — it's all-or-nothing.

**Q: Why must wipe logic come BEFORE deployment in main.yml?**
A: For the clean-reinstall scenario (`-e "web_app_wipe=true"` without `--tags`). Tasks execute top-to-bottom: wipe removes the old app, then deployment installs fresh. If wipe came after, we'd deploy and then immediately destroy.

**Q: When would you want clean reinstallation vs. rolling update?**
A: Clean reinstall for major version changes, corrupted state, configuration schema changes, or debugging. Rolling update for minor patches and config tweaks — faster, no downtime.

**Q: How would you extend this to wipe Docker images and volumes too?**
A: Add `docker rmi` for images (already included), add `docker volume prune -f` or remove specific volumes with `docker volume rm`. Add `docker compose down -v` to remove named volumes defined in compose.

---

## Task 4: CI/CD (3 pts)

### Workflow architecture

File: `.github/workflows/ansible-deploy.yml`

```
Push to ansible/** → Lint job (ansible-lint) → Deploy job (ansible-playbook) → Verify (curl)
```

### Jobs

1. **`lint`** — runs on `ubuntu-latest`, installs ansible + ansible-lint, lints all playbooks
2. **`deploy`** — needs lint to pass, installs ansible and collections, sets up SSH, runs playbook with vault password, verifies deployment with curl

### Path filters

```yaml
paths:
  - 'ansible/**'
  - '!ansible/docs/**'        # skip docs-only changes
  - '.github/workflows/ansible-deploy.yml'
```

### Required GitHub Secrets

| Secret | Purpose |
|--------|---------|
| `ANSIBLE_VAULT_PASSWORD` | Decrypt `group_vars/all.yml` |
| `SSH_PRIVATE_KEY` | SSH to target VM |
| `VM_HOST` | Target VM IP address |

### Status badge

Added to `ansible/README.md`:

```
[![Ansible Deployment](https://github.com/Arino4kaMyr/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)]
```

> **TODO**: Configure GitHub Secrets in repo settings, push code, paste screenshot of passing workflow.

### Research Questions

**Q: What are the security implications of storing SSH keys in GitHub Secrets?**
A: GitHub Secrets are encrypted at rest and only exposed to workflows during execution. Risks: anyone with write access to the repo can create workflows that read secrets; secrets may leak in logs if echoed. Mitigation: use deploy keys (read-only), limit repo access, never echo secrets in workflow steps.

**Q: How would you implement staging -> production pipeline?**
A: Use separate inventory files (`hosts_staging.ini`, `hosts_production.ini`) and separate jobs. Staging deploys first, runs integration tests, then production deploys only if staging succeeds. Use GitHub environments with required reviewers for production.

**Q: What would you add to make rollbacks possible?**
A: Pin Docker image tags (not `latest`) with version numbers. Keep previous docker-compose.yml as a backup. On rollback, deploy with the previous tag. Alternatively, use blue-green deployment — keep old container running on a different port until new one is verified.

**Q: How does self-hosted runner improve security?**
A: Self-hosted runner runs inside your infrastructure — SSH keys never leave the network. No secrets stored in GitHub (runner already has access). Faster execution (no SSH overhead). Downside: you must maintain the runner and secure the VM it runs on.

---

## Task 5: Documentation

This file serves as the complete Lab 6 documentation.

---

## Summary

### What was accomplished

- Refactored all roles with blocks (rescue/always) and tags for selective execution
- Migrated from `docker run` to Docker Compose with Jinja2 templates
- Implemented role dependencies (web_app depends on docker)
- Added double-gated wipe logic (variable + tag)
- Created CI/CD workflow with linting, deployment, and verification
- Added status badge to README

### Key learnings

- Blocks enable error handling in Ansible (similar to try/catch)
- Tags allow running subsets of tasks without modifying playbooks
- Docker Compose templates make deployments declarative and reproducible
- Double-gating (variable + tag) prevents accidental destructive operations
- CI/CD with path filters avoids unnecessary deployments

> **TODO**: Add total time spent.
