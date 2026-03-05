# Lab 6: Advanced Ansible and CI/CD

---

## 1. Overview

In this lab I upgraded my Ansible setup from basic role execution to a safer deployment pipeline:

- Refactored `common` and `docker` roles with blocks, tags, rescue, and always
- Migrated deployment from raw `docker_container` to a templated Docker Compose flow
- Renamed role `app_deploy` to `web_app`
- Added role dependency so `docker` is installed automatically before app deployment
- Added wipe logic with double protection: `web_app_wipe=true` + `--tags web_app_wipe`
- Added GitHub Actions workflow for lint + deploy + HTTP verification
- Added workflow badge to root README

Technologies used: Ansible, `community.docker`, Docker Compose v2, GitHub Actions, Ansible Vault.

---

## 2. Blocks and Tags

### What changed

`roles/common/tasks/main.yml`:
- `packages` block with apt update/install/timezone
- rescue path for apt cache refresh
- always path writing `/tmp/common-role.log`
- `users` block for deployment user management

`roles/docker/tasks/main.yml`:
- `docker_install` block for Docker repo and package install
- rescue path: wait, refresh apt metadata, retry key/repo/install
- always path: enforce Docker service enabled and started
- `docker_config` block for docker group membership

Playbook-level role tags:
- `common` on `common` role
- `docker` on `docker` role

### Tag strategy

- `common` for whole common role
- `packages`, `users` for sub-areas of common role
- `docker` for whole docker role
- `docker_install`, `docker_config` for install/config split
- `web_app`, `app_deploy`, `compose`, `web_app_wipe` for application role and flows

### Evidence

`ansible-playbook playbooks/provision.yml --list-tags`

```text
TASK TAGS: [common, docker, docker_config, docker_install, packages, users]
```

`ansible-playbook playbooks/provision.yml --tags docker_install --check`

```text
TASK [docker : Install Docker packages] ... FAILED
TASK [docker : Wait before Docker repository retry] ... skipping
TASK [docker : Refresh apt metadata before retry] ... changed
...
PLAY RECAP ... rescued=1
```

This run confirmed selective tag execution and rescue behavior.

---

## 3. Docker Compose Migration

### Role rename

- Renamed directory: `roles/app_deploy` -> `roles/web_app`
- Updated `playbooks/deploy.yml` to use role `web_app`

### Template and deployment flow

Created `roles/web_app/templates/docker-compose.yml.j2` with:
- templated service name, image, ports, environment, restart policy
- dedicated per-app network

Created compose deployment in `roles/web_app/tasks/main.yml`:
- ensure project dir
- render template
- deploy with `community.docker.docker_compose_v2`
- wait for port and validate `/health`

Rendered file on VM:

```yaml
version: "3.8"
services:
  devops-info-service:
    image: hikariatama/devops-info-service-python:lab02
    container_name: devops-info-service
    pull_policy: always
    ports:
      - "5000:5000"
    environment:
      PORT: "5000"
    restart: unless-stopped
```

### Role dependency

Created `roles/web_app/meta/main.yml`:

```yaml
dependencies:
  - role: docker
```

So running `deploy.yml` with `web_app` automatically executes Docker role first.

### Before/after comparison

- Before: imperative container lifecycle with `docker_container`
- After: declarative compose file + `docker_compose_v2`

This made configuration easier to read, easier to re-run, and easier to wipe safely.

---

## 4. Wipe Logic

### Implementation

`roles/web_app/defaults/main.yml`:
- `web_app_wipe: false` by default

`roles/web_app/tasks/wipe.yml`:
- checks compose file presence
- runs compose down (`state: absent`)
- removes compose file and project directory
- prints completion message
- all gated by `when: web_app_wipe | bool` and tag `web_app_wipe`

`roles/web_app/tasks/main.yml`:
- includes wipe tasks first
- then normal deployment block

### Why this is safe

Wipe tasks do not run accidentally because both are required:
1. explicit variable: `-e "web_app_wipe=true"`
2. explicit tag for wipe-only run: `--tags web_app_wipe`

---

## 5. CI/CD Integration

Created `.github/workflows/ansible-deploy.yml`.

Pipeline:
1. `lint` job:
   - checkout
   - install ansible + ansible-lint + collections
   - run ansible-lint with vault-aware fallback behavior
2. `deploy` job (push only):
   - setup SSH from secrets
   - run `ansible-playbook playbooks/deploy.yml`
   - verify `/` and `/health` via curl

Path filter behavior:
- triggers on `ansible/**`
- excludes `ansible/docs/**`
- includes workflow file changes

Required secrets:
- `ANSIBLE_VAULT_PASSWORD`
- `SSH_PRIVATE_KEY`
- `VM_HOST`

Badge added in root `README.md`:

```markdown
[![Ansible Deployment](https://github.com/hikariatama/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](...)
```

---

## 6. Testing Results

Environment:
- local QEMU VM from `local_vm/qemu/deploy.sh`
- ansible executed from `.venv-lab5`

### Validation commands

```bash
source .venv-lab5/bin/activate
cd ansible
ANSIBLE_VAULT_PASSWORD_FILE=.vault_pass ansible-lint -x var-naming,name playbooks/*.yml roles/*/tasks/*.yml roles/*/handlers/*.yml
ansible-playbook playbooks/provision.yml --syntax-check
ansible-playbook playbooks/deploy.yml --syntax-check --vault-password-file .vault_pass
ansible webservers -m ping --vault-password-file .vault_pass
```

Results:
- lint passed (with explicit rule exclusions for legacy naming/import style)
- syntax checks passed
- ping passed (`pong`)

### Wipe scenarios

Scenario 1, normal deployment:

```bash
ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass
```

Observed:
- wipe include loaded
- wipe tasks skipped (`web_app_wipe=false`)
- deployment tasks executed

Scenario 2, wipe only:

```bash
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe --vault-password-file .vault_pass
```

Observed:

```text
TASK [web_app : Report wipe completion] => "Application devops-info-service wiped successfully"
PLAY RECAP ... failed=0
```

Scenario 3, clean reinstall:

```bash
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --vault-password-file .vault_pass
```

Observed:
- wipe runs first
- compose deployment runs after wipe
- health check passes

Scenario 4a, safety check:

```bash
ansible-playbook playbooks/deploy.yml --tags web_app_wipe --vault-password-file .vault_pass
```

Observed:

```text
TASK [web_app : Check if compose project exists] ... skipping
TASK [web_app : Report wipe completion] ... skipping
PLAY RECAP ... failed=0 skipped=5
```

### Application verification

```bash
curl -fsS http://127.0.0.1:5000/health
```

Output:

```json
{"status":"healthy","timestamp":"2026-03-05T15:32:01.009821+00:00","uptime_seconds":18}
```

Container status:

```text
NAMES                 IMAGE                                          STATUS
devops-info-service   hikariatama/devops-info-service-python:lab02   Up 20 seconds
```

Idempotency check on compose path:

```bash
ansible-playbook playbooks/deploy.yml --tags compose --vault-password-file .vault_pass
```

Second run recap:

```text
PLAY RECAP ... changed=0 failed=0
```

---

## 7. Challenges and Solutions

1. Apt lock race on fresh VM  
Cloud-init and apt sometimes held `/var/lib/apt/lists/lock`.  
Solution: Docker install rescue path retries after short wait and metadata refresh.

2. Intermittent Docker registry pull EOF  
One compose run failed pulling image with transient EOF.  
Solution: re-run deployment. Existing rescue/debug output made failure obvious.

3. Encrypted vars with lint in CI  
Linting encrypted `group_vars/all.yml` requires vault context.  
Solution: workflow supports vault-aware lint path and fallback lint path for PRs without vault secret.

---

## 8. Research Answers

### Blocks and tags

1. What if rescue also fails?  
The task fails and play continues based on Ansible failure strategy. `always` still executes.

2. Can blocks be nested?  
Yes. Nested blocks are valid and useful for finer error handling boundaries.

3. How do tags inherit in blocks?  
Tags on a block are inherited by tasks inside the block.

### Docker Compose

4. `restart: always` vs `unless-stopped`  
`always` restarts even after manual stop and daemon restart. `unless-stopped` respects manual stops.

5. Compose networks vs default bridge  
Compose creates project-scoped networks with automatic service DNS. Plain bridge is generic and less app-scoped.

6. Can Vault vars be used in templates?  
Yes. Decrypted Vault values are regular Ansible vars at runtime and can be rendered in Jinja templates.

7. `docker_compose_v2` state options  
`present` ensures stack exists and is up. `absent` removes stack resources managed by compose.

8. `recreate` behavior  
`auto` recreates when config/image changes. `always` forces recreation every run. `never` avoids recreation.

### Wipe logic

9. Why variable and tag together?  
It is a double safety guard. Variable protects accidental tagged runs, tag protects accidental variable-only full runs.

10. Difference from `never` tag  
`never` blocks execution unless explicitly requested but gives no variable safety gate. Variable+tag gives explicit policy control.

11. Why wipe before deploy?  
Supports deterministic clean reinstall in one command.

12. Clean reinstall vs rolling update  
Clean reinstall is better after drift, broken state, or major config changes. Rolling update is better for availability.

13. How to extend wipe to volumes/images  
Add optional flags and compose/image prune steps behind extra gates, for example `web_app_wipe_volumes`, `web_app_wipe_images`.

### CI/CD

14. Security implications of SSH key in secrets  
Compromise of CI context can expose deployment credentials. Scope, rotation, and least privilege are required.

15. Staging to production pipeline  
Use separate jobs/environments with required approvals and promotion gates from staging verification to production deploy.

16. Rollback support  
Use immutable image tags, deployment metadata, and rollback workflow that redeploys previous known-good tag.

17. Why self-hosted can be more secure  
Credentials stay inside controlled infrastructure and traffic can stay internal, reducing external exposure.

---

## Summary

Lab 6 core requirements are implemented with local verification:
- advanced role structure with blocks/tags/rescue/always
- compose-based deployment with role dependency
- safe wipe logic with tested scenarios
- CI workflow for lint, deploy, and verification

The deployment stack is now easier to operate and safer to recover.
