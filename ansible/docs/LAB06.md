# Lab 6: Advanced Ansible & CI/CD — Submission

---

## Overview

This lab enhances the Ansible automation from Lab 5 with:

- **Blocks and tags** in `common` and `docker` roles for grouped tasks, error handling (rescue/always), and selective execution.
- **Docker Compose** deployment: the former `app_deploy` role was renamed to `web_app`, and deployment now uses a templated `docker-compose.yml.j2` and `docker compose up -d` on the target host.
- **Wipe logic** with double gating: variable `web_app_wipe` and tag `web_app_wipe`, so wipe runs only when explicitly requested.
- **CI/CD** via GitHub Actions: workflow runs `ansible-lint` on push/PR to `ansible/**`, and optionally runs the deploy playbook when vault password and VM secrets are configured.

**Technologies:** Ansible 2.16+, Docker Compose (plugin), Jinja2 templates, GitHub Actions.

---

## Task 1: Blocks & Tags 

### Block usage

**common role (`roles/common/tasks/main.yml`):**

- **Packages block:** apt cache update, install `common_packages`, set timezone.  
  - **Rescue:** on failure, run `apt-get update --fix-missing`.  
  - **Always:** write `/tmp/ansible-common-packages.log`.  
  - **Tags:** `packages`, `common`.  
  - **Become:** at block level.

- **Users block:** create users from `common_users` list (when non-empty).  
  - **Always:** write `/tmp/ansible-common-users.log`.  
  - **Tags:** `users`, `common`.

**docker role (`roles/docker/tasks/main.yml`):**

- **Install block:** dependencies, keyring dir, GPG key, Docker repo, Docker packages.  
  - **Rescue:** pause 10s, retry apt update and GPG key (for network timeouts).  
  - **Always:** ensure Docker service is started and enabled.  
  - **Tags:** `docker`, `docker_install`.

- **Config block:** add users to docker group, add `ansible_user` to docker group, install `python3-docker`.  
  - **Always:** ensure Docker service is enabled.  
  - **Tags:** `docker`, `docker_config`.

### Tag strategy

- **packages** — common package installation.  
- **users** — common user management.  
- **common** — entire common role.  
- **docker** — entire docker role.  
- **docker_install** — Docker installation only.  
- **docker_config** — Docker configuration only.  
- **app_deploy**, **compose** — web_app deployment.  
- **web_app_wipe** — wipe tasks only.

### Execution examples

```bash
# Run only docker-related tasks
ansible-playbook playbooks/provision.yml --tags "docker"

# Skip common role
ansible-playbook playbooks/provision.yml --skip-tags "common"

# Packages only (across roles)
ansible-playbook playbooks/provision.yml --tags "packages"

# List all tags
ansible-playbook playbooks/provision.yml --list-tags
```

### Research answers

- **If rescue block fails:** the play fails; rescue does not nest. Use a simple retry in rescue (e.g. apt update --fix-missing or GPG retry) to avoid complex chains.
- **Nested blocks:** Yes, Ansible allows nested blocks; keep nesting shallow for readability.
- **Tags on blocks:** Tags on a block apply to all tasks in that block (and rescue/always). Tasks inherit the block’s tags.

---

## Task 2: Docker Compose Migration 

### Rename and structure

- **Rename:** `roles/app_deploy` → `roles/web_app`.  
- **Playbook:** `playbooks/deploy.yml` now uses role `web_app` instead of `app_deploy`.

### Template structure

**File:** `roles/web_app/templates/docker-compose.yml.j2`

- Uses variables: `app_name`, `docker_image`, `docker_tag`, `app_port`, `app_internal_port`, `app_env` (optional).
- Single service, port mapping, optional `environment` from `app_env`, `restart: unless-stopped`.

### Role dependencies

**File:** `roles/web_app/meta/main.yml`

- `dependencies: [ { role: docker } ]` so Docker (and Docker Compose plugin) is installed before `web_app` runs.

### Deployment flow

1. Create `compose_project_dir` (e.g. `/opt/devops-app`).  
2. Template `docker-compose.yml` into that directory.  
3. Run `docker compose pull && docker compose up -d` in that directory (idempotent).  
4. Wait for port and verify `/health`.

### Variables (defaults and group_vars)

- **Defaults** (`roles/web_app/defaults/main.yml`): `app_name`, `docker_image`, `docker_tag`, `app_port`, `app_internal_port`, `compose_project_dir`, `app_restart_policy`, `app_env`, `web_app_wipe`.  
- **Secrets:** use group_vars (Vault) for Docker Hub credentials and app-specific overrides as in Lab 5.

### Before/after

- **Before (Lab 5):** `app_deploy` used `docker_login`, `docker_image` (pull), `docker_container` (run) with inline options.  
- **After:** `web_app` uses a single templated Compose file and `docker compose up -d`; same behavior, declarative and easier to extend (e.g. multi-container later).

---

## Task 3: Wipe Logic 

### Implementation

- **File:** `roles/web_app/tasks/wipe.yml`  
  - One block: Docker Compose down in `compose_project_dir`, remove `docker-compose.yml`, remove `compose_project_dir`, debug “wiped successfully”.  
  - **When:** `web_app_wipe | default(false) | bool`.  
  - **Tags:** `web_app_wipe`.  
  - **ignore_errors: true** on file/container removal so already-absent state does not fail.

- **Inclusion:** In `roles/web_app/tasks/main.yml`, first task is `include_tasks: wipe.yml` with tags `web_app_wipe`, so wipe runs before deployment when requested.

- **Default:** `roles/web_app/defaults/main.yml`: `web_app_wipe: false`.

### Variable + tag (double safety)

- Wipe runs only if **both** are true: variable `web_app_wipe=true` and (for “wipe only”) tag `web_app_wipe` can be used to run only wipe tasks.  
- Normal deploy: no extra vars, no wipe tag → wipe block skipped.  
- Wipe only: `-e "web_app_wipe=true" --tags web_app_wipe`.  
- Clean reinstall: `-e "web_app_wipe=true"` (no tag filter) → wipe runs first, then deploy.

### Test scenarios

1. **Normal deployment:** `ansible-playbook playbooks/deploy.yml` — wipe skipped, app deployed.  
2. **Wipe only:** `-e "web_app_wipe=true" --tags web_app_wipe` — only wipe runs; app and dir removed.  
3. **Clean reinstall:** `-e "web_app_wipe=true"` — wipe then deploy; fresh install.  
4. **Safety:** `--tags web_app_wipe` without `web_app_wipe=true` — when condition false, wipe block skipped.

---

## Task 4: CI/CD Integration

### Workflow

**File:** `.github/workflows/ansible-deploy.yml`

- **Trigger:** push/PR to `main` or `master` with changes under `ansible/**` or the workflow file.
- **Jobs:**  
  - **lint:** Ubuntu, Python 3.12, install Ansible and ansible-lint, run `ansible-lint playbooks/*.yml` in `ansible/`.  
  - **deploy:** runs only on push and when `ANSIBLE_VAULT_PASSWORD` is set; checks out repo, installs Ansible, sets up SSH from `SSH_PRIVATE_KEY`, runs `ansible-playbook playbooks/deploy.yml` with vault password file, then verification step (curl to `VM_HOST:8000` and `:8000/health`).

### Secrets (for deploy)

- `ANSIBLE_VAULT_PASSWORD` — Vault password.  
- `SSH_PRIVATE_KEY` — SSH key for the target VM.  
- `VM_HOST` — Target VM hostname or IP (for SSH and curl).

### Evidence

- Workflow run: Actions tab shows “Ansible Deployment” and lint/deploy jobs.  
- Lint: logs show `ansible-lint playbooks/*.yml` success.  
- Deploy: when secrets are set and VM is reachable, deploy step and verification step succeed.  
- Optional: add status badge to README:  
  `[![Ansible Deployment](https://github.com/USER/REPO/actions/workflows/ansible-deploy.yml/badge.svg)](...)`

---

## Task 5: Documentation

This file (`ansible/docs/LAB06.md`) serves as the Lab 6 documentation. Code comments were added in:

- `roles/common/tasks/main.yml` (blocks, tags).  
- `roles/docker/tasks/main.yml` (blocks, rescue, always, tags).  
- `roles/web_app/tasks/main.yml` and `wipe.yml` (wipe flow, tags).  
- `roles/web_app/templates/docker-compose.yml.j2` (variables).  
- `roles/web_app/defaults/main.yml` (wipe usage).  
- `.github/workflows/ansible-deploy.yml` (trigger and steps).

---

## Testing Results

- **Tags:** `ansible-playbook playbooks/provision.yml --list-tags` shows all role and block tags.  
- **Selective run:** `--tags "docker"` / `--skip-tags "common"` run only the intended tasks.  
- **Docker Compose:** First deploy shows “changed” for directory, template, and compose up; second run is idempotent (ok, no unnecessary changes).  
- **Wipe:** Scenarios 1–4 above behave as described.  
- **Application:** After deploy, `curl http://<VM>:8000` and `curl http://<VM>:8000/health` return expected responses when the app and port are correct.

---

## Challenges & Solutions

- **Rescue in common:** Used `apt-get update --fix-missing` via `command` in rescue instead of only `apt` with cache_valid_time 0, to match lab hint.  
- **Docker Compose from Ansible:** Avoided requiring `community.docker.docker_compose_v2` on the controller by templating the Compose file and running `docker compose pull && docker compose up -d` with the `command` module on the target; works with standard Docker Compose plugin on the host.  
- **Idempotency for compose up:** `changed_when` based on stdout containing “Creating”, “Starting”, “Pulling”, or “Recreating” so only real changes are reported.  
- **CI deploy:** Deploy job is conditional on `secrets.ANSIBLE_VAULT_PASSWORD != ''` and verification uses `|| true` so the workflow does not fail when VM is not configured or not reachable from GitHub.

---

## Research Answers (summary)

- **restart: always vs unless-stopped:** `always` restarts even after manual `docker stop`; `unless-stopped` does not restart after manual stop until reboot or next deploy.  
- **Compose networks vs bridge:** Compose can define named networks and driver options; default bridge is per-compose-project; custom networks allow isolation and DNS between services.  
- **Vault in templates:** Yes; variables resolved on the controller can be Vault-encrypted; the templated file on the host will contain decrypted values, so restrict permissions and use Vault only for values that are safe to appear on the host.  
- **Why variable and tag for wipe:** Variable prevents accidental wipe from a playbook that includes the role; tag prevents wipe from running unless the operator explicitly requests it; together they avoid mistakes.  
- **Wipe before deploy in main.yml:** So that a single run with `web_app_wipe=true` does wipe-then-deploy (clean reinstall) without a second playbook run.  
- **GitHub Secrets for SSH:** Keys are encrypted at rest and not logged; rotation and least-privilege keys are recommended; use deploy keys or short-lived credentials where possible.

