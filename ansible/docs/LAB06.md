# Lab 6: Advanced Ansible & CI/CD - Submission

**Student:** `Danil Fishchenko`  
**Date:** `2026-03-05`  
**Branch:** `lab06`  
**Repository:** `pepegx/DevOps-Core-Course`

---

## Overview

Lab 6 was implemented on top of Lab 5 and validated against a local Ubuntu 24.04 target container (`lab05-ubuntu2404`) via inventory `ansible/inventory/hosts.local-docker.ini`.

What was completed:
- Roles `common` and `docker` were refactored using `block`/`rescue`/`always` and tag strategy.
- Role `app_deploy` was renamed to `web_app`.
- Deployment was migrated from `community.docker.docker_container` to `community.docker.docker_compose_v2` with Jinja2 compose template.
- Safe wipe logic was added with variable + tag gating.
- GitHub Actions workflow for Ansible lint/deploy/verify was added.

Key implementation files:
- `ansible/roles/common/tasks/main.yml`
- `ansible/roles/docker/tasks/main.yml`
- `ansible/roles/web_app/tasks/main.yml`
- `ansible/roles/web_app/tasks/wipe.yml`
- `ansible/roles/web_app/templates/docker-compose.yml.j2`
- `ansible/roles/web_app/meta/main.yml`
- `.github/workflows/ansible-deploy.yml`

---

## Task 1: Blocks & Tags (2 pts)

### 1.1 Block usage and tag strategy

`roles/common/tasks/main.yml`:
- `packages` block:
  - apt update + package install in `block`
  - apt recovery in `rescue` (`apt-get update --fix-missing`)
  - completion log file in `always`
- `users` block:
  - user management loop (controlled by `common_users`)
- timezone task tagged as `common`

`roles/docker/tasks/main.yml`:
- `docker_install` block:
  - repository and package install steps
  - `rescue` with retry flow (pause + apt update + retry repo/key/install)
  - `always` to force Docker service enabled/running
- `docker_config` block:
  - daemon config + docker group users
  - `always` to enforce service state

Role-level tags in playbook:
- `common` role tag in `playbooks/provision.yml`
- `docker` role tag in `playbooks/provision.yml`

### 1.2 Evidence

`--list-tags` output:
```text
TASK TAGS: [common, docker, docker_config, docker_install, packages, users]
```

Selective run example (`--tags docker`):
```text
PLAY RECAP
lab05-ubuntu2404 : ok=11 changed=0 failed=0 rescued=0
```

Selective run example (`--tags docker_install`):
```text
PLAY RECAP
lab05-ubuntu2404 : ok=8 changed=0 failed=0 rescued=0
```

Selective run example (`--tags packages`):
```text
PLAY RECAP
lab05-ubuntu2404 : ok=4 changed=1 failed=0 rescued=0
```

`rescue` triggered (controlled negative test with invalid repo URL):
```text
TASK [docker : Configure Docker apt repository] ... FAILED
TASK [docker : Wait before retrying Docker repository setup]
TASK [docker : Retry apt cache update after repository failure]
TASK [docker : Retry Docker GPG key download]
TASK [docker : Retry Docker apt repository configuration] ... FAILED
PLAY RECAP ... failed=1 rescued=1
```

### 1.3 Research answers

1. What happens if `rescue` also fails?
- The play continues to treat the task block as failed. `rescue` is not a guaranteed recovery; it is a fallback path. If fallback fails, the host/play fails unless `ignore_errors` is used.

2. Can blocks be nested?
- Yes. Nested blocks are valid and useful for fine-grained recovery scopes.

3. How do tags inherit inside blocks?
- Tags on a block are inherited by tasks inside that block. Tags on role include are inherited by role tasks as well.

---

## Task 2: Docker Compose Migration (3 pts)

### 2.1 Migration details

Role rename:
- `ansible/roles/app_deploy` -> `ansible/roles/web_app`

Dependency:
- `ansible/roles/web_app/meta/main.yml` includes:
```yaml
dependencies:
  - role: docker
```

Compose template:
- `ansible/roles/web_app/templates/docker-compose.yml.j2`
- Templated values:
  - `app_name`
  - `docker_image`
  - `docker_tag`
  - `app_port`
  - `app_internal_port`
  - `app_env`
  - `app_labels`

Deployment implementation:
- `compose_project_dir` creation
- `docker-compose.yml` rendering
- safe migration check for legacy non-compose container
- `community.docker.docker_compose_v2` execution
- health verification with `uri` + `assert`

Required variable coverage:
- `docker_compose_version` is defined in role defaults and group vars example.
- Compose V2 ignores top-level `version`, so this variable is kept as explicit schema metadata (rendered as a comment in template).

### 2.2 Before/after

Before (Lab 5):
- single-container deployment via `community.docker.docker_container`

After (Lab 6):
- declarative deployment via compose file and `docker_compose_v2`

### 2.3 Evidence

Idempotent deployment output (second and third run):
```text
PLAY RECAP
lab05-ubuntu2404 : ok=19 changed=0 failed=0 rescued=0
```

Rendered compose file on target:
```yaml
services:
  devops-info-service:
    image: "host.docker.internal:5001/devops-info-service:latest"
    container_name: "devops-info-service"
    restart: "unless-stopped"
    ports:
      - "5000:5000"
```

Runtime verification:
```text
docker ps -> devops-info-service Up ... 0.0.0.0:5000->5000/tcp
curl /health -> {"status":"healthy", ...}
```

### 2.4 Research answers

1. `restart: always` vs `restart: unless-stopped`
- `always`: container restarts even after manual stop if Docker daemon restarts.
- `unless-stopped`: restarts on failures/reboots, but respects intentional manual stop.

2. Compose network vs default bridge network
- Compose creates project-scoped network(s), deterministic service DNS names, and isolated stack-level communication.
- Default bridge is global and less structured for multi-service app stacks.

3. Can Vault vars be used in Jinja2 compose template?
- Yes. Vault-encrypted vars are decrypted by Ansible at runtime and can be rendered into templates.

---

## Task 3: Wipe Logic (1 pt)

### 3.1 Implementation

`roles/web_app/defaults/main.yml`:
- `web_app_wipe: false` (safe default)

`roles/web_app/tasks/wipe.yml`:
- compose `state: absent`
- compose file removal
- project directory removal
- completion log message
- gated by `when: web_app_wipe | bool`
- tagged with `web_app_wipe`

`roles/web_app/tasks/main.yml`:
- `include_tasks: wipe.yml` is placed before deployment block

### 3.2 Test scenarios and evidence

Scenario 1: normal deploy (wipe must not run)
- Verified in deploy outputs: wipe tasks are `skipping` when `web_app_wipe=false`.

Scenario 2: wipe-only
```bash
ansible-playbook ... -e web_app_wipe=true --tags web_app_wipe
```
Result:
```text
PLAY RECAP ... ok=6 changed=3 failed=0
```
Verification:
- `docker ps -a | grep devops-info-service || true` -> empty
- `/opt/devops-info-service` -> not found

Scenario 3: clean reinstall (wipe -> deploy)
```bash
ansible-playbook ... -e web_app_wipe=true
```
Result:
```text
PLAY RECAP ... ok=23 changed=3 failed=0
```
App health check passed after redeploy.

Scenario 4a: `--tags web_app_wipe` with default `web_app_wipe=false`
Result:
```text
PLAY RECAP ... ok=2 changed=0 skipped=4 failed=0
```
Wipe blocked by `when` condition. Because `--tags` limits execution scope, only
wipe-tagged tasks are selected; normal deploy tasks are not selected in this mode.

Scenario 4b: `--tags web_app_wipe` with `web_app_wipe=true`
Result:
```text
PLAY RECAP ... ok=6 changed=3 failed=0
```
Only wipe tasks executed.

### 3.3 Research answers

1. Why variable + tag together?
- Two safety gates:
  - variable prevents accidental deletion during normal runs
  - tag enables explicit wipe-only mode

2. Difference from `never` tag
- `never` prevents execution unless explicitly requested via tags.
- Variable+tag approach additionally gives runtime policy control via vars and supports clean reinstall flow.

3. Why wipe before deploy in `main.yml`?
- Required for deterministic clean reinstall sequence: remove old state first, then apply desired state.

4. Clean reinstall vs rolling update
- Clean reinstall: broken state reset, incompatible volume/state, major migration.
- Rolling update: preserve uptime/state where possible.

5. Extending wipe to images/volumes
- Add optional booleans (`web_app_remove_images`, `web_app_remove_volumes`) and keep defaults `false`.
- Require explicit opt-in to avoid destructive behavior.

---

## Task 4: CI/CD with GitHub Actions (3 pts)

### 4.1 Workflow implementation

Created:
- `.github/workflows/ansible-deploy.yml` (Python app)
- `.github/workflows/ansible-deploy-bonus.yml` (Bonus app)

Pipeline stages:
1. `lint` (per app)
- runs on `ubuntu-latest`
- install ansible + ansible-lint with `python3 -m pip`
- install Galaxy collections
- run `ansible-lint` for target playbook + shared roles (`docker`, `web_app`)

2. `deploy` (per app)
- runs after lint
- runs on self-hosted runner: `[self-hosted, macOS, ARM64]`
- recreates local registry `lab05-registry` with published port `5001:5000`
- builds and pushes app image into local registry:
  - Python: `localhost:5001/devops-info-service:${PYTHON_APP_IMAGE_TAG}`
  - Bonus: `localhost:5001/devops-info-service-go:${BONUS_APP_IMAGE_TAG}`
- uses local target inventory `inventory/hosts.local-docker.ini`
- decrypts Vault via `ANSIBLE_VAULT_PASSWORD` (or fallback file on runner host)
- runs app-specific playbook:
  - Python workflow: `playbooks/deploy_python.yml`
  - Bonus workflow: `playbooks/deploy_bonus.yml`
- verifies `/` and `/health` with `docker exec lab05-ubuntu2404 curl ...`

Triggers:
- `push` on `main/master/lab06` with app-specific path filters
- `pull_request` with app-specific path filters
- `workflow_dispatch`

Path filter behavior:
- Python-only changes (`ansible/vars/app_python.yml`, `deploy_python.yml`) trigger only Python workflow.
- Bonus-only changes (`ansible/vars/app_bonus.yml`, `deploy_bonus.yml`) trigger only Bonus workflow.
- Shared role changes (`ansible/roles/web_app/**`, `ansible/roles/docker/**`) trigger both workflows.

### 4.2 Secrets required

- `ANSIBLE_VAULT_PASSWORD` (recommended)

Runner-local fallback:
- if secret is not set, deploy jobs can use `$HOME/.ansible_vault_pass_lab06` on self-hosted runner host.

### 4.3 Badge

Status badges added to root `README.md`:
```markdown
[![Ansible Python Deploy](https://github.com/pepegx/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](...)
[![Ansible Bonus Deploy](https://github.com/pepegx/DevOps-Core-Course/actions/workflows/ansible-deploy-bonus.yml/badge.svg)](...)
```

### 4.4 What was validated locally

Validated locally on `2026-03-05`:
- workflow YAML syntax
- playbook syntax checks
- real playbook execution on Docker-based target
- split app workflows with independent path filters

Reproducibility checks executed in this session:
- `playbooks/deploy.yml` with `vars/local_test.yml`: success; second run `changed=0`.
- `playbooks/deploy_python.yml` with `vars/local_multiapp_test.yml`: success, health passed.
- `playbooks/deploy_bonus.yml` with `vars/local_multiapp_test.yml`: success, health passed.
- `playbooks/deploy_all.yml` with `vars/local_multiapp_test.yml`: success and idempotent (`changed=0`).

### 4.5 Research answers

1. Security implications of storing SSH keys in GitHub Secrets
- Secrets reduce accidental disclosure, but compromise risk still exists via workflow misconfiguration, malicious PR logic, or overprivileged credentials.
- Mitigations: least-privilege tokens/keys, environment protection rules, branch protections, and periodic rotation.

2. Staging -> production pipeline design
- Separate jobs/environments:
  - deploy staging on merge
  - run smoke/integration tests
  - manual approval gate
  - deploy production

3. Rollback additions
- Keep immutable image tags and deployed release metadata.
- Add rollback workflow input (`target_tag`) and previous-known-good deployment step.

4. Self-hosted vs GitHub-hosted security
- Self-hosted can keep network/internal access private and avoid exposing targets to public runners.
- Requires strong host hardening and runner lifecycle controls.

---

## Task 5: Documentation (1 pt)

This document is the Lab 6 submission file and includes:
- implementation details
- test evidence snippets
- research answers
- challenges and fixes

---

## Bonus Part 1: Multi-App Deployment (1.5 pts)

### B1.1 Implemented files

- `ansible/vars/app_python.yml`
- `ansible/vars/app_bonus.yml`
- `ansible/playbooks/deploy_python.yml`
- `ansible/playbooks/deploy_bonus.yml`
- `ansible/playbooks/deploy_all.yml`

Local validation helper:
- `ansible/vars/local_multiapp_test.yml` (local registry + no Docker Hub login)

### B1.2 Variable strategy and role reusability

- Same role `web_app` is reused for both applications.
- App-specific behavior comes only from variable files:
  - Python app: `app_name=devops-python`, `app_port=8000`, `app_internal_port=5000`
  - Bonus app: `app_name=devops-go`, `app_port=8001`, `app_internal_port=8080`
- Different `compose_project_dir` per app prevents collisions:
  - `/opt/devops-python`
  - `/opt/devops-go`

### B1.3 Local evidence

Local prerequisites (for deterministic replay, run from repository root):
```bash
docker rm -f lab05-registry >/dev/null 2>&1 || true
docker run -d --name lab05-registry -p 5001:5000 registry:2
docker build -t localhost:5001/devops-info-service:latest app_python
docker build -t localhost:5001/devops-info-service-go:latest app_go
docker push localhost:5001/devops-info-service:latest
docker push localhost:5001/devops-info-service-go:latest
```

Deploy both apps:
```text
$ ansible-playbook -i inventory/hosts.local-docker.ini playbooks/deploy_all.yml \
    --vault-password-file ~/.ansible_vault_pass_lab06 -e @vars/local_multiapp_test.yml
PLAY RECAP ... failed=0
```
(`changed` count depends on initial host state.)

Core deploy replay (`deploy.yml`):
```text
$ ansible-playbook -i inventory/hosts.local-docker.ini playbooks/deploy.yml \
    --vault-password-file ~/.ansible_vault_pass_lab06 -e @vars/local_test.yml
PLAY RECAP ... failed=0
```

Both endpoints healthy:
```text
curl http://127.0.0.1:8000/health -> {"status":"healthy", ...}
curl http://127.0.0.1:8001/health -> {"status":"healthy", ...}
```

Independent wipe (Python only):
```text
$ ansible-playbook -i inventory/hosts.local-docker.ini playbooks/deploy_python.yml \
    --vault-password-file ~/.ansible_vault_pass_lab06 \
    -e @vars/local_multiapp_test.yml -e web_app_wipe=true --tags web_app_wipe
PLAY RECAP ... failed=0
```

Wipe both:
```text
$ ansible-playbook -i inventory/hosts.local-docker.ini playbooks/deploy_all.yml \
    --vault-password-file ~/.ansible_vault_pass_lab06 \
    -e @vars/local_multiapp_test.yml -e web_app_wipe=true --tags web_app_wipe
PLAY RECAP ... failed=0
```

### B1.4 Trade-offs

- Separate playbooks are easier to reason about and map directly to CI triggers.
- `deploy_all.yml` provides one-command rollout for both apps.
- Wipe logic remains safe due variable+tag gating and per-app `compose_project_dir`.

---

## Bonus Part 2: Multi-App CI/CD (1 pt)

### B2.1 Implemented workflows

- `.github/workflows/ansible-deploy.yml` (Python app)
- `.github/workflows/ansible-deploy-bonus.yml` (Bonus app)

### B2.2 Triggering logic

Python workflow watches:
- `ansible/vars/app_python.yml`
- `ansible/playbooks/deploy_python.yml`
- shared role/config paths

Bonus workflow watches:
- `ansible/vars/app_bonus.yml`
- `ansible/playbooks/deploy_bonus.yml`
- shared role/config paths

Shared role updates trigger both workflows by design.

### B2.3 Deployment steps

Both workflows:
- lint only required app playbook + shared roles;
- rebuild and publish target image to local registry before deploy;
- deploy only the target app playbook via local Docker inventory;
- use `web_app_pull_policy=missing` for deterministic idempotent checks in this lab setup;
- verify the target app endpoint (`8000` for Python, `8001` for Bonus by default).

### B2.4 Required CI secrets/vars

Secrets:
- `ANSIBLE_VAULT_PASSWORD`

Repository Variables (optional overrides):
- `PYTHON_APP_PORT` (default `8000`)
- `BONUS_APP_PORT` (default `8001`)
- `PYTHON_APP_IMAGE_TAG` (default `latest`)
- `BONUS_APP_IMAGE_TAG` (default `latest`)

### B2.5 Remote evidence status

Workflows were executed successfully in GitHub Actions after migration to self-hosted deploy jobs.

---

## Challenges & Solutions

1. Recursive defaults in role variables
- Problem: backward-compat aliases created recursion (`app_internal_port` and `app_container_port`, same for image tags).
- Fix: switched to non-recursive defaults.

2. Migration conflict from old container to compose container
- Problem: legacy standalone container had same name and blocked compose create.
- Fix: inspect existing container and remove only if it is non-compose managed.

3. Undefined Docker Hub credentials in default deploy flow
- Problem: `dockerhub_username/password` could be absent and `docker_login` failed before deploy.
- Fix:
  - login task now uses safe defaults (`default('')`);
  - login runs only when credentials are present;
  - deploy continues without registry login when login is disabled or creds are absent.

4. Local nested-Docker instability (`overlay invalid argument` / registry errors)
- Problem: Docker daemon config updates were not guaranteed to apply before compose tasks.
- Fix:
  - added `meta: flush_handlers` in `docker` role;
  - added runtime storage-driver check (`docker info`) with conditional Docker restart;
  - added cleanup of stale stopped compose container before `compose up`.

5. CI deploy depended on pre-existing local images on self-hosted runner
- Problem: deploy could fail if local registry/image cache state was different.
- Fix: workflows now recreate local registry and build+push target image before deploy.

---

## Testing Results Summary

- Task 1 tags/selective execution: validated
- Task 1 rescue: validated (`rescued=1` in controlled test)
- Task 2 compose migration: validated
- Task 2 idempotency: validated (`changed=0` on repeated deploy)
- Task 3 wipe scenarios: validated (1, 2, 3, 4a, 4b)
- Task 4 workflows: validated locally and executed in GitHub Actions
- Bonus Part 1 (multi-app deploy/wipe/idempotency): reproduced locally after fixes
- Bonus Part 2 (split workflows + path filters): validated by workflow runs

---

## Summary

- Lab 6 core requirements are implemented.
- Bonus Part 1 and Bonus Part 2 are implemented.
- Core and bonus deploy flows are reproducible locally on Ubuntu 24.04 Docker target.
- CI workflows are aligned with current implementation (self-hosted local inventory flow).
