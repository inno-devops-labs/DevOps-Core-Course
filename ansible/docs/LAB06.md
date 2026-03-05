# LAB06 — Advanced Ansible & CI/CD

**Running from WSL when project is on `/mnt/c/...`:** Ansible ignores `ansible.cfg` (world-writable directory). Always pass inventory and roles path:

```bash
cd ansible   # from DevOps-Core-Course
export ANSIBLE_ROLES_PATH=roles
ansible-playbook -i inventory/hosts.ini playbooks/provision.yml --list-tags
```

Use **`-i inventory/hosts.ini`** (static inventory). Do not use `inventory/yandex.yml` for this lab unless you have the Yandex dynamic inventory plugin configured.

---

## 1. Overview

**Technologies:** Ansible 2.16+, Docker Compose v2, `community.docker.docker_compose_v2`, GitHub Actions.

**Accomplished:** Refactored **common** and **docker** roles with blocks, rescue/always, and tags. Replaced **app_deploy** with **web_app** role using Docker Compose (templated `docker-compose.yml.j2`). Implemented **wipe logic** (variable `web_app_wipe` + tag `web_app_wipe`). Added CI/CD workflow (ansible-lint, deploy, verify). Bonus: multi-app vars/playbooks and separate workflow for bonus app.

## 2. Blocks & Tags

**common role:** Block 1 (tag `packages`): apt update, install packages, timezone — rescue: apt-get update --fix-missing; always: log to `/tmp/ansible-common-complete.log`. Block 2 (tag `users`): ensure deploy user exists.

**docker role:** Block 1 (tag `docker_install`): install Docker — rescue: pause 10s and retry GPG key; always: ensure Docker service enabled. Block 2 (tag `docker_config`): add user to docker group, install python3-docker.

**Tag strategy:** `common`, `packages`, `users`, `docker`, `docker_install`, `docker_config`, `app_deploy`, `compose`, `web_app_wipe`.

**Selective execution:**

![Tags list](screenshots/lab06-list-tags.png)

![Execution with --tags docker](screenshots/lab06-tags-docker.png)

## 3. Docker Compose Migration

**Template:** `roles/web_app/templates/docker-compose.yml.j2` — variables: `app_name`, `docker_image`, `docker_tag`, `app_port`, `app_internal_port`, `app_env`, optional `app_secret_key`. Restart: `unless-stopped`.

**Role dependencies:** `roles/web_app/meta/main.yml` declares dependency on **docker** so Docker is installed before app deploy.

**Before:** app_deploy used `docker_container` (docker run). **After:** web_app uses `docker_compose_v2` with templated compose file in `compose_project_dir`.

![Docker Compose deploy success](screenshots/lab06-compose-deploy.png)

![Idempotency — second run](screenshots/lab06-compose-idempotency.png)

![Templated docker-compose.yml on VM](screenshots/lab06-compose-file.png)

## 4. Wipe Logic

**Implementation:** `roles/web_app/tasks/wipe.yml` — compose down, remove compose file, remove app dir, debug log. Included at top of `main.yml`. Runs only when `web_app_wipe | default(false) | bool` and tag `web_app_wipe` is used (or full play with variable set).

**Scenarios:** (1) Normal deploy — wipe skipped. (2) Wipe only: `-e "web_app_wipe=true" --tags web_app_wipe`. (3) Clean reinstall: `-e "web_app_wipe=true"` (wipe then deploy). (4a) Tag without variable — wipe skipped by `when`.

![Scenario 1 — normal deploy](screenshots/lab06-wipe-scenario1.png)

![Scenario 2 — wipe only](screenshots/lab06-wipe-scenario2.png)

![Scenario 3 — clean reinstall](screenshots/lab06-wipe-scenario3.png)

![Scenario 4a — wipe blocked](screenshots/lab06-wipe-scenario4a.png)

![App running after clean reinstall](screenshots/lab06-wipe-app-running.png)

## 5. CI/CD Integration

**Workflow:** `.github/workflows/ansible-deploy.yml`. Triggers: push/PR to `main`/`master` with changes in `ansible/**` or workflow file. Jobs: **lint** (ansible-lint), **deploy** (SSH, vault, playbook, curl verification on :8000 and /health).

**Secrets:** `ANSIBLE_VAULT_PASSWORD`, `SSH_PRIVATE_KEY`, `VM_HOST`.

![Successful workflow run](screenshots/lab06-cicd-workflow.png)

![ansible-lint passing](screenshots/lab06-cicd-lint.png)

![ansible-playbook execution](screenshots/lab06-cicd-deploy.png)

![Verification step](screenshots/lab06-cicd-verify.png)

![Status badge in README](screenshots/lab06-cicd-badge.png)

## 6. Testing Results

**Tags:** `--list-tags` shows all tags; runs with `--tags`/`--skip-tags` execute only selected tasks.

**Idempotency:** Second run of `deploy.yml` shows ok, no changes.

**Wipe:** All four scenarios (normal, wipe-only, clean reinstall, tag-only) produce expected behaviour.

**Application:** `curl http://<VM_IP>:8000` and `curl http://<VM_IP>:8000/health` return success after deploy.

![Application accessible](screenshots/lab06-app-accessible.png)

## 7. Challenges & Solutions

- **Compose module:** Used `community.docker.docker_compose_v2` (Compose v2) instead of deprecated `docker_compose`.
- **Wipe when dir missing:** Wipe tasks use `ignore_errors: true` so missing compose file or directory does not fail the play.
- **Group vars:** `group_vars/all.yml` (vault) holds `dockerhub_username`, `dockerhub_password`; ensure vars are set for deploy and deploy_all.

## 8. Research Answers

**Task 1:** If rescue block fails, the play fails. Nested blocks are allowed. Tags on a block apply to all tasks inside it.

**Task 3:** Variable + tag give double safety (default off + explicit tag). `never` tag excludes tasks; here we use a positive tag + `when`. Wipe before deploy allows one play to do clean reinstall. Clean reinstall for major/broken state; rolling update for zero-downtime. To wipe images/volumes: add tasks or compose `state: absent` with options, same variable/tag.

**Task 4:** SSH keys in Secrets are encrypted at rest; use deploy keys and rotate if leaked. Staging→production: separate workflows or environments with different inventories. Rollbacks: playbook with previous image tag or wipe + deploy old tag. Self-hosted runner avoids exposing SSH to GitHub-hosted runners.

---

## Bonus Part 1 — Multi-App

**Vars:** `vars/app_python.yml` (port 8000), `vars/app_bonus.yml` (port 8001). **Playbooks:** `deploy_python.yml`, `deploy_bonus.yml`, `deploy_all.yml`. Wipe is per-app via different `app_name`/`compose_project_dir`.

![Both apps deployed](screenshots/lab06-bonus-both-apps.png)

---

## Bonus Part 2 — Multi-App CI/CD

**Workflow:** `.github/workflows/ansible-deploy-bonus.yml` for bonus app only (path filters). Independent from main app workflow.

![Bonus workflow / badges](screenshots/lab06-bonus-cicd.png)
