# Lab 6: Advanced Ansible & CI/CD

## 1. Overview

- **Technologies:** Ansible 2.16+, Docker Compose v2, GitHub Actions, Jinja2
- **Changes from Lab 5:**
  - Roles refactored with blocks, rescue, always, and tags
  - `app_deploy` renamed to `web_app`
  - Deployment switched from `docker run` to Docker Compose
  - Wipe logic with variable + tag safety
  - Ansible CI/CD workflow (lint + deploy)
- **Structure:** Same `ansible/` layout; `web_app` uses `templates/docker-compose.yml.j2` and `tasks/wipe.yml`

---

## 2. Blocks & Tags

### common role
- **Block:** Package installation (apt cache, common packages) with tag `packages`
- **Rescue:** Retry `apt update` and package install on failure
- **Always:** Log completion to `/tmp/ansible_common_complete`
- **Tags:** `packages`, `common`

### docker role
- **Block 1 (docker_install):** Prerequisites, GPG key, repo, Docker packages
- **Rescue:** Wait 10s, retry apt update and Docker install
- **Always:** Ensure Docker service is enabled and started
- **Block 2 (docker_config):** Add user to docker group, install python3-docker
- **Tags:** `docker_install`, `docker_config`, `docker`

### web_app role
- **Tags:** `app_deploy`, `compose`, `web_app_wipe` (wipe tasks only)

### Example commands
```bash
ansible-playbook playbooks/provision.yml --tags "docker"
ansible-playbook playbooks/provision.yml --skip-tags "common"
ansible-playbook playbooks/provision.yml --tags "packages"
ansible-playbook playbooks/provision.yml --tags "docker_install"
ansible-playbook playbooks/provision.yml --list-tags
```

---

## 3. Docker Compose Migration

- **Template:** `roles/web_app/templates/docker-compose.yml.j2`
  - Uses Jinja2 for `app_name`, `docker_image`, `docker_tag`, `app_port`, `app_internal_port`, `app_environment`
  - Restart policy: `unless-stopped`
- **Role dependency:** `roles/web_app/meta/main.yml` declares dependency on `docker`
- **Tasks:** Create app dir, template compose file, `docker_login`, `docker_compose_v2` (state: present, pull: always)
- **App dir:** `/opt/{{ app_name }}` (e.g. `/opt/devops-info-service`)

---

## 4. Wipe Logic

- **Variable:** `web_app_wipe` (default: `false`)
- **Tag:** `web_app_wipe`
- **Location:** `roles/web_app/tasks/wipe.yml`, included at top of `main.yml`
- **Behavior:** Wipe runs only when `web_app_wipe | bool` is true and tasks with tag `web_app_wipe` are executed
- **Tasks:** `docker compose down`, remove compose file, remove app directory, debug log

### Test scenarios
| Scenario | Command | Result |
|----------|---------|--------|
| Normal deploy | `ansible-playbook deploy.yml` | Deploy only; wipe skipped |
| Wipe only | `ansible-playbook deploy.yml -e "web_app_wipe=true" --tags web_app_wipe` | Wipe only; deploy skipped |
| Clean reinstall | `ansible-playbook deploy.yml -e "web_app_wipe=true"` | Wipe then deploy |
| Tag only, var false | `ansible-playbook deploy.yml --tags web_app_wipe` | Wipe skipped (when blocks it) |

---

## 5. CI/CD Integration

- **Workflow:** `.github/workflows/ansible-deploy.yml`
- **Triggers:** Push/PR to `ansible/**` on master, lab05, lab06
- **Jobs:**
  1. **lint:** ansible-lint on playbooks (continue-on-error: true)
  2. **deploy:** Runs only on push to master/lab06; requires secrets
- **Secrets:** `ANSIBLE_VAULT_PASSWORD`, `SSH_PRIVATE_KEY`, `VM_HOST`, `VM_USER`
- **Deploy steps:** Install Ansible, setup SSH, create CI inventory, run `deploy.yml` with vault, verify `/health`
- **Verification:** `curl http://VM_HOST:5000/health` after deploy

### Badge
```markdown
[![Ansible Deployment](https://github.com/abdughafforzoda/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/abdughafforzoda/DevOps-Core-Course/actions/workflows/ansible-deploy.yml)
```

---

## 6. Testing

- **Idempotency:** Run `deploy.yml` twice; second run should show mostly `ok`, no changes.
- **Selective tags:** Use `--tags` and `--skip-tags` as in section 2.
- **Wipe tests:** Run all four scenarios in section 4 and verify.
- **CI:** Push changes to `ansible/`, confirm workflow runs and lint passes; deploy passes when secrets are set.

---

## 7. Challenges

- _(Add any issues and how you resolved them)_
- **Note:** `community.docker.docker_compose_v2` has no `state: restarted`; handler uses `docker compose restart` via `command` module.

---

## 8. Research Answers

1. **Variable + tag:** Variable ensures wipe is explicit; tag limits wipe to runs where wipe is intended. Prevents accidental wipe.
2. **`never` vs this approach:** `never` runs only when explicitly requested; our approach also requires the variable.
3. **Wipe before deploy:** Enables wipe → deploy in one run (clean reinstall).
4. **Clean reinstall vs rolling update:** Clean reinstall for major changes or corruption; rolling update for low-risk updates.
5. **Extending wipe:** Add tasks to remove images (`docker image prune`) and volumes (`docker volume rm`) after `compose down`.
