# LAB06 Report - Advanced Ansible and CI/CD

## 1. Overview

Lab 6 is completed with the following outcomes:

- Refactored roles with `block`/`rescue`/`always` patterns.
- Added role and task tags for selective execution.
- Migrated app deployment from `docker_container` to Docker Compose template + module.
- Added `web_app` role dependency on `docker`.
- Implemented safe wipe flow using double-gating (`web_app_wipe` variable + `web_app_wipe` tag).
- Added GitHub Actions workflow for `ansible-lint` and deployment.
- Added workflow status badge to root `README.md`.

Modified key files:

- `ansible/roles/common/tasks/main.yml`
- `ansible/roles/docker/tasks/main.yml`
- `ansible/roles/web_app/tasks/main.yml`
- `ansible/roles/web_app/tasks/wipe.yml`
- `ansible/roles/web_app/templates/docker-compose.yml.j2`
- `ansible/roles/web_app/meta/main.yml`
- `ansible/playbooks/provision.yml`
- `ansible/playbooks/deploy.yml`
- `.github/workflows/ansible-deploy.yml`

## 2. Blocks and Tags

### common role

- `packages` block:
  - apt update and package installation are grouped in one block.
  - `rescue` retries apt with `apt-get update --fix-missing`.
  - `always` writes completion log to `/tmp/ansible-common-packages.log`.
- `users` block:
  - user creation and group assignment are grouped.
  - `always` writes completion log to `/tmp/ansible-common-users.log`.

Tags used:

- `common` at role/task level
- `packages`
- `users`

### docker role

- `docker_install` block:
  - prerequisites, key/repo setup, package install, Python Docker bindings.
  - `rescue` waits 10s, refreshes apt cache, retries GPG key download.
  - `always` ensures Docker service is enabled and started.
- `docker_config` block:
  - user group membership for Docker access.

Tags used:

- `docker` at role/task level
- `docker_install`
- `docker_config`

### Tag listing evidence

`ansible-playbook playbooks/provision.yml --list-tags`:

```text
TASK TAGS: [common, docker, docker_config, docker_install, packages, users]
```

`ansible-playbook playbooks/deploy.yml --list-tags`:

```text
TASK TAGS: [app_deploy, compose, docker, docker_config, docker_install, web_app, web_app_wipe]
```

## 3. Docker Compose Migration

### Before

- Role used:
  - `community.docker.docker_container`
  - direct container recreation flow

### After

- Role now uses Compose:
  - creates `compose_project_dir`
  - renders `docker-compose.yml` from Jinja template
  - deploys using `community.docker.docker_compose_v2`

Template file:

- `ansible/roles/web_app/templates/docker-compose.yml.j2`

Supported variables:

- `app_name`
- `docker_image`
- `docker_tag`
- `app_port`
- `app_internal_port`
- `app_env`
- `app_restart_policy`
- `docker_compose_version`

### Role dependency

`ansible/roles/web_app/meta/main.yml` includes:

- dependency on role `docker`

This guarantees Docker setup before Compose deployment when `web_app` runs.

## 4. Wipe Logic

Implemented in:

- `ansible/roles/web_app/tasks/wipe.yml`
- included from `ansible/roles/web_app/tasks/main.yml`

Behavior:

- runs only when:
  - `web_app_wipe | bool == true`
  - and `--tags web_app_wipe` is selected
- performs:
  - `docker_compose_v2 state: absent`
  - remove compose file
  - remove project directory
  - completion message

Defaults:

- `web_app_wipe: false`
- `web_app_wipe_remove_images: false`

Why this is safe:

- Tag alone is not enough.
- Variable alone is not enough (if running wipe-only flow).
- Operator must opt in explicitly.

## 5. CI/CD Integration

Added workflow:

- `.github/workflows/ansible-deploy.yml`

Pipeline:

1. `lint` job:
   - installs `ansible-core`, `ansible-lint`
   - installs `community.docker` collection from `ansible/requirements.yml`
   - runs `ansible-lint` on playbooks and roles
2. `deploy` job (`push` only):
   - sets up SSH from `SSH_PRIVATE_KEY`
   - builds CI inventory from `VM_HOST` + `VM_USER`
   - writes vault pass from `ANSIBLE_VAULT_PASSWORD`
   - runs `ansible-playbook playbooks/deploy.yml`
   - verifies `/` and `/health` with `curl`

Path filters:

- triggers on `ansible/**` and workflow changes
- excludes `ansible/docs/**`

Status badge added:

- root `README.md` includes `ansible-deploy` badge.

## 6. Testing Results

### Completed local checks

Commands run:

```bash
cd ansible
ANSIBLE_ROLES_PATH=roles ansible-playbook -i inventory/hosts.ini playbooks/provision.yml --syntax-check
ANSIBLE_ROLES_PATH=roles ansible-playbook -i inventory/hosts.ini playbooks/provision.yml --list-tags
ANSIBLE_ROLES_PATH=roles ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml --syntax-check
ANSIBLE_ROLES_PATH=roles ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml --list-tags
```

Result:

- both playbooks pass syntax check.
- expected tags are visible for selective execution.

Environment note:

- repository directory is world-writable in this environment, so `ansible.cfg` is ignored by Ansible and direct env overrides were used.

### Recommended runtime checks on VM

```bash
ansible-playbook playbooks/provision.yml --tags docker
ansible-playbook playbooks/deploy.yml
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"
docker ps
curl http://127.0.0.1:5000/health
```

## 7. Challenges and Solutions

- Challenge: legacy deploy playbook still referenced `app_deploy`.
  - Solution: migrated playbook to `web_app` and added role dependency metadata.
- Challenge: deployment path still used `docker_container`.
  - Solution: switched to Compose template + `docker_compose_v2`.
- Challenge: dangerous wipe scenarios.
  - Solution: implemented variable + tag double-gating.
- Challenge: CI should not run on docs-only changes.
  - Solution: added workflow path filters with docs exclusion.

## 8. Research Answers

### Blocks/Tags

1. What happens if rescue also fails?
   - The play fails after rescue failure; `always` still runs.
2. Can blocks be nested?
   - Yes. Nested blocks are valid and inherit directives unless overridden.
3. How do tags inherit in blocks?
   - Tags on block propagate to child tasks; task-level tags add/override as needed.

### Docker Compose

1. `restart: always` vs `unless-stopped`:
   - `always`: restarts even after manual stop and daemon restart.
   - `unless-stopped`: restarts unless explicitly stopped by operator.
2. Compose networks vs default bridge:
   - Compose creates project-scoped networks with service-name DNS.
   - Default bridge is global and less isolated for multi-app stacks.
3. Can Vault vars be used in templates?
   - Yes. Vaulted variables resolve normally in Jinja templates at runtime.

### Wipe Logic

1. Why variable + tag?
   - Defense in depth: two independent opt-ins reduce accidental destructive actions.
2. Difference from `never` tag:
   - `never` blocks normal execution unless directly targeted, but does not encode intent via runtime variable.
3. Why wipe before deploy?
   - Enables clean reinstall flow (`wipe -> deploy`) in one run.
4. Clean reinstall vs rolling update:
   - Reinstall for drift/corruption cleanup; rolling update for lower downtime.
5. How to extend wipe for images/volumes?
   - add `remove_images: all` and `remove_volumes: true` (with additional safety flags).

### CI/CD

1. Security implications of SSH keys in GitHub Secrets:
   - Safer than plaintext in repo, but compromise of repo/admin access exposes secrets.
2. Staging -> production pipeline:
   - separate jobs/environments with approval gates and environment-specific inventories.
3. Rollbacks:
   - pin image tags, keep previous tag metadata, add manual `rollback` workflow input.
4. Why self-hosted runner can improve security:
   - no inbound SSH key distribution to third-party runner; deployment executes inside controlled network boundary.
