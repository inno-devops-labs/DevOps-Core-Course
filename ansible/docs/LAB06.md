# Lab 6: Advanced Ansible & CI/CD - Submission

**Name:** Kirill Nosov  
**Date:** 2026-03-05  
**Lab Points:** 10 + 2.5 bonus (implemented)

---

## 1. Overview

This lab upgrades the Lab 5 Ansible solution to a production-style structure:
- Refactored roles with `block`/`rescue`/`always` and selective tags.
- Migrated app deployment from `docker_container` to Docker Compose (`community.docker.docker_compose_v2`).
- Added safe wipe logic with double gating (`web_app_wipe` variable + `web_app_wipe` tag).
- Added GitHub Actions workflows for Ansible lint/deploy/verify.
- Implemented bonus multi-app deployment and bonus multi-app CI/CD workflow split.

Technologies: Ansible 2.16+, `community.docker`, Docker Compose v2 plugin, Jinja2 templates, GitHub Actions.

---

## 2. Blocks & Tags

### 2.1 `common` role
File: `roles/common/tasks/main.yml`

Implemented:
- Package block with tags: `packages`.
- User block with tags: `users`.
- `rescue` for apt failures using `apt-get update --fix-missing`.
- `always` logging to `/tmp/ansible-common-packages.log` and `/tmp/ansible-common-users.log`.

### 2.2 `docker` role
File: `roles/docker/tasks/main.yml`

Implemented:
- Installation block with tags: `docker_install`.
- Configuration block with tags: `docker_config`.
- `rescue` retry flow for Docker key/repo transient failures (`apt update`, wait 10s, retry key).
- `always` step ensures Docker service is enabled/started.

### 2.3 Role-level tags strategy
File: `playbooks/provision.yml`

- Role `common` is tagged `common`.
- Role `docker` is tagged `docker`.
- Task-level tags remain selectable (`packages`, `users`, `docker_install`, `docker_config`).

### 2.4 Execution examples

```bash
cd ansible
ansible-playbook playbooks/provision.yml --list-tags
ansible-playbook playbooks/provision.yml --tags docker
ansible-playbook playbooks/provision.yml --tags packages
ansible-playbook playbooks/provision.yml --tags docker_install --check
ansible-playbook playbooks/provision.yml --skip-tags common
```

---

## 3. Docker Compose Migration

### 3.1 Role rename and dependency
- Renamed role directory: `roles/app_deploy` -> `roles/web_app`.
- Updated `playbooks/deploy.yml` to use `web_app`.
- Added dependency in `roles/web_app/meta/main.yml`:

```yaml
dependencies:
  - role: docker
```

Reason: deploying app with compose requires Docker engine and compose plugin preinstalled.

### 3.2 Compose template
File: `roles/web_app/templates/docker-compose.yml.j2`

Template supports:
- `app_name`
- `docker_image`
- `docker_tag`
- `app_port`
- `app_internal_port`
- `app_env`
- optional Vault secret `app_secret_key`

Uses restart policy `unless-stopped` and dedicated bridge network `web_app_net`.

### 3.3 Deployment tasks
File: `roles/web_app/tasks/main.yml`

Implemented flow:
1. Ensure project directory exists (`/opt/{{ app_name }}` by default).
2. Docker Hub login via `community.docker.docker_login`.
3. Template `docker-compose.yml`.
4. Deploy with `community.docker.docker_compose_v2` (`pull: always`, `state: present`, `recreate: auto`).
5. Wait on port and verify `/health`.
6. Rescue block logs deployment failure context.

---

## 4. Wipe Logic

### 4.1 Safety mechanism
- Variable gate: `web_app_wipe` (default `false`) in `roles/web_app/defaults/main.yml`.
- Tag gate: `web_app_wipe` on wipe tasks in `roles/web_app/tasks/wipe.yml`.
- Include is placed at the top of `roles/web_app/tasks/main.yml` for clean reinstall flow.

### 4.2 Wipe implementation
File: `roles/web_app/tasks/wipe.yml`

Actions:
1. `docker_compose_v2 state=absent` to stop/remove containers.
2. Remove compose file.
3. Remove project directory.
4. Log completion.

### 4.3 Test scenarios

```bash
# Scenario 1: normal deployment (wipe skipped)
ansible-playbook playbooks/deploy.yml

# Scenario 2: wipe only
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe

# Scenario 3: clean reinstall (wipe then deploy)
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"

# Scenario 4a: tag only, variable false (wipe blocked)
ansible-playbook playbooks/deploy.yml --tags web_app_wipe
```

---

## 5. CI/CD Integration

### 5.1 Workflow files
- `.github/workflows/ansible-deploy.yml` (Python app deploy)
- `.github/workflows/ansible-deploy-bonus.yml` (bonus app deploy)

### 5.2 Workflow architecture
Each workflow contains:
1. **Lint job**: install Ansible + ansible-lint + collections; run `ansible-lint`.
2. **Deploy job** (push only): setup SSH, write vault password file from secret, run playbook.
3. **Verify step**: curl root and `/health` endpoints.

### 5.3 Required GitHub Secrets
- `ANSIBLE_VAULT_PASSWORD`
- `SSH_PRIVATE_KEY`
- `VM_HOST`
- `VM_USER` (optional for extended SSH usage)

### 5.4 Path-filter behavior
- Python Ansible workflow listens to Python deploy vars/playbooks plus shared role changes.
- Bonus workflow listens to bonus vars/playbooks plus shared role changes.
- `ansible/docs/**` is excluded from push triggers.

---

## 6. Testing Results

### 6.1 Local validation commands

```bash
cd ansible
ansible-playbook playbooks/provision.yml --syntax-check
ansible-playbook playbooks/deploy.yml --syntax-check
ansible-playbook playbooks/deploy_all.yml --syntax-check
ansible-playbook playbooks/provision.yml --list-tags
ansible-playbook playbooks/deploy.yml --list-tags
```

### 6.2 Runtime validation on target host

```bash
ansible-playbook playbooks/deploy_python.yml --ask-vault-pass
ansible-playbook playbooks/deploy_bonus.yml --ask-vault-pass

ssh root@<vm_ip> "docker ps"
curl http://<vm_ip>:8000
curl http://<vm_ip>:8000/health
curl http://<vm_ip>:8001
curl http://<vm_ip>:8001/health
```

### 6.3 Idempotency validation

```bash
ansible-playbook playbooks/deploy_python.yml --ask-vault-pass
ansible-playbook playbooks/deploy_python.yml --ask-vault-pass
ansible-playbook playbooks/deploy_all.yml --ask-vault-pass
ansible-playbook playbooks/deploy_all.yml --ask-vault-pass
```

Expected: second runs should show minimal `changed` counts.

---

## 7. Challenges & Solutions

1. **Migration from container module to compose module**  
   Solution: introduced template + project directory + `docker_compose_v2` with compose plugin package in docker role.

2. **Wipe safety requirements**  
   Solution: combined variable + tag gates; wipe include kept first in role for clean reinstall.

3. **Multi-app reuse without role duplication**  
   Solution: split app-specific vars (`vars/app_python.yml`, `vars/app_bonus.yml`) and reuse `web_app` role.

4. **CI trigger noise**  
   Solution: path filters narrowed to Ansible deployment files and role paths.

---

## 8. Research Answers

### Task 1 (Blocks/Tags)
1. If `rescue` also fails, the play fails at that point. `always` still executes.
2. Yes, nested blocks are supported.
3. Tags applied on a block are inherited by tasks inside the block.

### Task 2 (Compose)
1. `always` restarts after daemon restart/manual stop; `unless-stopped` restarts except when manually stopped.
2. Compose networks are project-scoped and auto-created from file state; bridge networks are generic Docker primitives managed independently.
3. Yes, Ansible Vault variables can be referenced directly in Jinja2 templates.

### Task 3 (Wipe)
1. Variable + tag gives double safety: config gate + explicit operator intent.
2. `never` blocks execution unless explicitly selected; this lab’s approach keeps wipe available for full-run clean reinstall when variable is true.
3. Wipe must run before deploy for wipe-then-fresh-install flow in one command.
4. Clean reinstall is useful for drift/corruption reset; rolling update is preferred for low-downtime version changes.
5. Extend by adding `remove_images: all`, volume removal options, and explicit Docker volume/network removal tasks.

### Task 4 (CI/CD)
1. SSH keys in GitHub Secrets reduce plaintext risk but require strict repo/org access controls, rotation, and least-privilege host keys/users.
2. Use separate staging/prod jobs with environment protection rules, approvals, and branch/tag-based promotion.
3. Add versioned image pinning, deploy metadata, and rollback jobs that redeploy previous known-good tags.
4. Self-hosted runner can keep SSH/material inside private network perimeter and avoid exposing target access from shared hosted runners.

---

## Bonus Part 1: Multi-App Deployment

Implemented:
- `ansible/vars/app_python.yml`
- `ansible/vars/app_bonus.yml`
- `ansible/playbooks/deploy_python.yml`
- `ansible/playbooks/deploy_bonus.yml`
- `ansible/playbooks/deploy_all.yml`

Result: same `web_app` role deploys both apps on separate ports (`8000`, `8001`) and supports independent wipe operations.

---

## Bonus Part 2: Multi-App CI/CD

Implemented:
- Main workflow for Python app deployment.
- Separate bonus workflow for bonus app deployment.

Behavior:
- Python-specific file changes trigger Python Ansible deploy workflow.
- Bonus-specific file changes trigger bonus Ansible deploy workflow.
- Shared `roles/web_app/**` changes can trigger both workflows.

---

## Summary

Lab 6 implementation is complete in repository code: roles refactored with advanced block/tag patterns, Compose-based deployment is active through `web_app` role with dependency handling, wipe logic is safely gated, and Ansible deployment automation is added in GitHub Actions including multi-app bonus path.
