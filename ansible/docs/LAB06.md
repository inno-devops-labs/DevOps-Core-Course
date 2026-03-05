# Lab 06 - Advanced Ansible and CI/CD

## Status

- Main tasks (1-5): completed
- Bonus tasks: not implemented in this submission

## 1. Overview

In Lab 06, the Ansible automation from Lab 05 was upgraded to production-style role structure and deployment flow:

- Refactored roles to use `block` / `rescue` / `always`
- Added granular tags for selective execution
- Migrated app deployment from single-container style to Docker Compose
- Implemented wipe logic with double safety gating (`web_app_wipe` variable + `web_app_wipe` tag)
- Added CI/CD automation using GitHub Actions for lint + deploy + verification

**Technologies used:**

- Ansible core + roles/playbooks
- `community.docker` collection (`docker_compose_v2`, `docker_login`)
- Docker Engine + Compose v2 plugin
- GitHub Actions
- Ansible Vault

## 2. Blocks and Tags

### 2.1 Block usage by role

#### `roles/common/tasks/main.yml`

- Package tasks are grouped in a block tagged `common,packages`
- Recovery uses `rescue` with `apt-get update --fix-missing`
- `always` writes completion evidence to `/tmp/ansible-common-packages.log`
- User/timezone tasks are grouped separately and tagged `common,users`

#### `roles/docker/tasks/main.yml`

- Docker installation and repo setup grouped under `docker,docker_install`
- `rescue` waits 10 seconds and retries apt operations
- `always` ensures Docker service is enabled/running
- Docker user and Python bindings grouped under `docker,docker_config`

### 2.2 Tag strategy

- Role-level tags:
  - `common`
  - `docker`
  - `web_app`
- Functional tags:
  - `packages`, `users`
  - `docker_install`, `docker_config`
  - `app_deploy`, `compose`
  - `web_app_wipe`

### 2.3 Tagged execution evidence

From `lab06.md` command logs:

```bash
ansible-playbook playbooks/provision.yml --list-tags
TASK TAGS: [common, docker, docker_config, docker_install, packages, users]
```

```bash
ansible-playbook playbooks/provision.yml --tags "docker"
PLAY RECAP: ok=11 changed=7 failed=0
```

```bash
ansible-playbook playbooks/provision.yml --skip-tags "common"
PLAY RECAP: ok=9 changed=0 failed=0 skipped=1
```

```bash
ansible-playbook playbooks/provision.yml --tags "packages"
PLAY RECAP: ok=4 changed=2 failed=0
```

```bash
ansible-playbook playbooks/provision.yml --tags "docker_install" --check
PLAY RECAP: ok=7 changed=0 failed=0 skipped=1
```

## 3. Docker Compose Migration

### 3.1 Role rename and structure

- Deployment role is now `web_app` and used in `ansible/playbooks/deploy.yml`
- `roles/web_app/meta/main.yml` defines dependency on `docker` so Docker is installed first automatically

### 3.2 Compose template structure

File: `ansible/roles/web_app/templates/docker-compose.yml.j2`

- Parameterized with:
  - `app_name`
  - `docker_image`, `docker_tag`
  - `app_port`, `app_internal_port`
  - `app_host`, `app_env`, `app_secret_key`
- Restart policy: `unless-stopped`
- Template rendered to `{{ compose_project_dir }}/docker-compose.yml`

### 3.3 Deployment implementation

File: `ansible/roles/web_app/tasks/main.yml`

- Creates compose directory
- Renders template
- Optionally logs in to Docker Hub
- Runs `community.docker.docker_compose_v2` with `pull: always`, `state: present`
- Waits for TCP port and verifies `/health`
- Uses rescue/fail block for explicit failure reporting

### 3.4 Before vs after comparison

- **Before (Lab 05):** container lifecycle controlled via direct container module logic
- **After (Lab 06):** lifecycle defined declaratively in compose template and applied by Compose v2
- **Outcome:** cleaner app config, easier updates, better multi-service extensibility

### 3.5 Deployment evidence

From `lab06.md`:

```bash
ansible-playbook playbooks/deploy.yml
TASK [web_app : Deploy stack with docker compose v2] ... changed
TASK [web_app : Verify health endpoint] ... ok
PLAY RECAP: ok=16 changed=2 failed=0
```

External endpoint check:

```bash
curl http://51.250.89.15:5000/health
{"status":"healthy","timestamp":"2026-03-04T21:28:55.824186+00:00","uptime_seconds":160}
```

## 4. Wipe Logic

### 4.1 Implementation

Files:

- `ansible/roles/web_app/tasks/wipe.yml`
- `ansible/roles/web_app/tasks/main.yml`
- `ansible/roles/web_app/defaults/main.yml`

Key behavior:

- Wipe tasks are included first in `main.yml`
- Wipe is executed only when:
  - tag `web_app_wipe` is selected, and
  - `web_app_wipe | bool` is `true`
- Default is safe: `web_app_wipe: false`

Wipe steps:

1. `docker_compose_v2 state=absent` (with `ignore_errors: true`)
2. Remove rendered compose file
3. Remove compose directory
4. Report completion

### 4.2 Test scenarios and results

#### Scenario 1: Normal deploy (wipe skipped)

- Command: `ansible-playbook playbooks/deploy.yml`
- Result: wipe tasks included but skipped; deploy succeeds

#### Scenario 2: Wipe only

- Command: `ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe`
- Result from logs: wipe tasks executed, compose stack and project directory removed

#### Scenario 3: Clean reinstall (wipe then deploy)

- Command: `ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"`
- Result from logs: wipe block runs first, then compose deployment recreates app and health check passes

#### Scenario 4: Safety gating

- 4a tag only (`--tags web_app_wipe` with default variable false): wipe blocked by `when`
- 4b var + tag (`-e "web_app_wipe=true" --tags web_app_wipe`): wipe allowed, deployment excluded by tag selection

## 5. CI/CD Integration

### 5.1 Workflow architecture

File: `.github/workflows/ansible-deploy.yml`

Jobs:

1. `lint`
2. `deploy` (depends on `lint`)

Pipeline flow:

1. Checkout
2. Install Ansible + `ansible-lint` (+ `community.docker`)
3. Lint playbooks
4. Setup SSH access to VM
5. Generate CI inventory from GitHub Secrets
6. Decrypt Vault password at runtime
7. Run `ansible-playbook playbooks/deploy.yml --tags app_deploy`
8. Verify app endpoint via `curl`

### 5.2 Trigger setup

- Manual: `workflow_dispatch`
- Push branches: `main`, `master`, `lab06`
- PR path filters: `ansible/**`, workflow file, excluding `ansible/docs/**`

### 5.3 Secrets used

- `ANSIBLE_VAULT_PASSWORD`
- `SSH_PRIVATE_KEY`
- `VM_HOST`
- `VM_USER`

### 5.4 CI/CD evidence

- Workflow file includes lint + deploy + verification stages
- Root `README.md` contains workflow status badge:
  - `Ansible Deployment` badge linked to Actions workflow

## 6. Testing Results

### 6.1 Provisioning/tag tests

- `--list-tags` confirmed tag map
- `--tags docker` ran only Docker role tasks
- `--skip-tags common` excluded common role tasks
- `--tags packages` executed only package block
- `--tags docker_install --check` validated installation path in check mode

### 6.2 Deploy/idempotency tests

- Compose deployment succeeded and `/health` returned HTTP 200
- Subsequent runs show mostly `ok` with limited `changed`, indicating idempotent behavior
- Wipe-only and clean-reinstall paths both executed correctly

### 6.3 Accessibility verification

- Remote health endpoint check returned expected JSON payload from running app

## 7. Challenges and Solutions

1. Docker apt/repo/network reliability during installation
- **Solution:** used `rescue` retry path in docker role (pause + apt retry)

2. Avoiding accidental destructive wipe
- **Solution:** double gating with both tag and variable, default variable set to `false`

3. Safe cleanup when target is already clean
- **Solution:** `ignore_errors: true` for compose removal task

4. Compose warning about obsolete `version` key
- **Solution:** deployment still succeeds; warning documented and can be resolved by removing version key in future cleanup

5. CI targeting dynamic VM details
- **Solution:** generated temporary inventory file in workflow from Secrets values

## 8. Research Answers

### 8.1 Task 1 research

1. **What happens if rescue block also fails?**
- The play fails at that point unless `ignore_errors` is used on the failing rescue task.

2. **Can you have nested blocks?**
- Yes. Blocks can be nested, but readability and debugging usually improve when nesting is shallow.

3. **How do tags inherit to tasks within blocks?**
- Tags applied to a block are inherited by all tasks inside that block (unless additional tags are set at task level).

### 8.2 Task 2 research

1. **`restart: always` vs `restart: unless-stopped`**
- `always` restarts container even after manual stop and daemon restart; `unless-stopped` restarts except when user intentionally stopped it.

2. **Compose networks vs bridge networks**
- Compose auto-manages project-scoped networks and service DNS naming; raw bridge networks are lower-level and require more manual setup.

3. **Can Vault variables be used in templates?**
- Yes. Vault-encrypted variables are decrypted at runtime and can be referenced directly in Jinja2 templates.

### 8.3 Task 3 research

1. **Why both variable and tag?**
- Defense-in-depth: prevents accidental wipe from either an unintended tag run or an unintended variable override alone.

2. **Difference from `never` tag**
- `never` prevents execution unless explicitly requested by tag; variable+tag gating adds runtime policy control and clearer intent.

3. **Why wipe before deploy in `main.yml`?**
- Supports clean reinstall flow: remove old state first, then install fresh state in a single run.

4. **When use clean reinstall vs rolling update?**
- Clean reinstall: corrupted state, major config reset, deterministic baseline needed.
- Rolling update: minimize downtime and keep service continuity.

5. **How to extend wipe to images/volumes?**
- Add guarded tasks for `docker image rm` / volume prune operations with separate boolean toggles (e.g., `web_app_wipe_images`, `web_app_wipe_volumes`).

### 8.4 Task 4 research

1. **Security implications of SSH key in GitHub Secrets**
- Safer than plaintext in repo, but still high impact if leaked; requires tight repo access control, environment protection, and key rotation.

2. **How to build staging -> production pipeline**
- Use separate jobs/environments with approvals: deploy to staging, run tests/smoke checks, then gated promotion to production.

3. **What to add for rollbacks**
- Keep versioned tags/artifacts, store release metadata, add `workflow_dispatch` rollback job with target version input.

4. **How self-hosted runner can improve security**
- Credentials and network paths remain inside controlled infrastructure; avoids exposing direct SSH access from public runners.

## 9. File Reference Summary

Primary Lab 06 files implemented/documented:

- `ansible/roles/common/tasks/main.yml`
- `ansible/roles/docker/tasks/main.yml`
- `ansible/roles/web_app/tasks/main.yml`
- `ansible/roles/web_app/tasks/wipe.yml`
- `ansible/roles/web_app/templates/docker-compose.yml.j2`
- `ansible/roles/web_app/defaults/main.yml`
- `ansible/roles/web_app/meta/main.yml`
- `.github/workflows/ansible-deploy.yml`
- `README.md` (workflow badge)
