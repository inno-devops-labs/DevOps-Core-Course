# Lab 6: Advanced Ansible & CI/CD — Submission

**Name:** DevOps Student  
**Date:** 2026-03-04  
**Lab Points:** 10 + 2.5 bonus  

[![Ansible Deploy Python](https://github.com/mpasgat/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/mpasgat/DevOps-Core-Course/actions/workflows/ansible-deploy.yml)
[![Ansible Deploy Java](https://github.com/mpasgat/DevOps-Core-Course/actions/workflows/ansible-deploy-java.yml/badge.svg)](https://github.com/mpasgat/DevOps-Core-Course/actions/workflows/ansible-deploy-java.yml)

---

## Task 1: Blocks & Tags (2 pts)

### Overview

Both the `common` and `docker` roles were refactored to use Ansible **blocks** for logical task grouping, **rescue** sections for error handling, and **always** sections for guaranteed cleanup/logging. Tags were applied at block level so they propagate to all contained tasks.

### `common` Role — `roles/common/tasks/main.yml`

Three blocks were created:

| Block | Tags | Purpose |
|-------|------|---------|
| Install common packages | `packages`, `common` | apt cache update + package install |
| Configure system timezone | `common` | timezone via community.general.timezone |
| Manage deployment users | `users`, `common` | create deploy group and user |

**Rescue block** (`packages` block): if apt cache update fails, runs `apt-get update --fix-missing` and retries installation.

**Always block** (all blocks): writes a completion log to `/tmp/ansible_common_*.log` for auditing.

### `docker` Role — `roles/docker/tasks/main.yml`

Two blocks were created:

| Block | Tags | Purpose |
|-------|------|---------|
| Install Docker engine | `docker`, `docker_install` | GPG key + apt repo + packages + Python SDK |
| Configure Docker | `docker`, `docker_config` | add user to docker group |

**Rescue block** (`docker_install` block): waits 10 seconds, re-downloads the GPG key with `force: true`, retries install — handles transient network/GPG failures.

**Always block** (`docker_install`): uses `ignore_errors: true` to ensure `docker` service is enabled even if some install step partially failed.

### Tag Strategy Summary

| Tag | Scope | Usage |
|-----|-------|-------|
| `common` | entire common role | `--tags common` |
| `packages` | apt installs | `--tags packages` |
| `users` | user/group management | `--tags users` |
| `docker` | entire docker role | `--tags docker` |
| `docker_install` | docker installation | `--tags docker_install` |
| `docker_config` | docker user/group config | `--tags docker_config` |
| `app_deploy` | compose deploy | `--tags app_deploy` |
| `compose` | compose deploy (alias) | `--tags compose` |
| `web_app_wipe` | wipe task | `--tags web_app_wipe` |

### Test Commands

```bash
# Run only tagged tasks
ansible-playbook playbooks/provision.yml --tags "docker"
ansible-playbook playbooks/provision.yml --skip-tags "common"
ansible-playbook playbooks/provision.yml --tags "packages"
ansible-playbook playbooks/provision.yml --tags "docker_install"

# List all available tags
ansible-playbook playbooks/provision.yml --list-tags
```

### Research Answers

**Q: What happens if rescue block also fails?**  
If the rescue block fails, Ansible marks the play as failed and stops execution (unless `ignore_errors: true` is set). The always block still runs regardless. This means critical failures in rescue do surface — they are not silently swallowed.

**Q: Can you have nested blocks?**  
Yes. Ansible supports nested blocks. The inner block can have its own `rescue`/`always` sections, and the outer block's `rescue` only catches errors not handled by the inner block.

**Q: How do tags inherit to tasks within blocks?**  
Tags applied at the block level are inherited by all tasks inside the block. Tasks can also have additional tags, but the block-level tags always apply. If you specify `--tags docker`, all tasks inside a block tagged `docker` will run.

---

## Task 2: Docker Compose (3 pts)

### Overview

The `app_deploy` role was renamed to `web_app`. The role now:
1. Uses a **Jinja2 template** (`docker-compose.yml.j2`) for the compose file
2. Declares a **role dependency** on `docker` via `meta/main.yml`
3. Uses `community.docker.docker_compose_v2` for idempotent deployment
4. Verifies the health endpoint after every deployment

### Role Rename

```bash
# In ansible/roles/
mv app_deploy web_app
```

All playbook references updated: `app_deploy` → `web_app`.

### Docker Compose Template — `roles/web_app/templates/docker-compose.yml.j2`

Variables used in the template:

| Variable | Default | Description |
|----------|---------|-------------|
| `app_name` | `devops-app` | service and container name |
| `docker_image` | `112005/devops-lab3-python` | Docker Hub image |
| `docker_tag` | `latest` | image tag |
| `app_port` | `5000` | host-side port |
| `app_internal_port` | `8080` | container-side port (gunicorn) |
| `app_restart_policy` | `unless-stopped` | restart behaviour |
| `app_env` | `{}` | extra environment variables |
| `docker_compose_version` | `3.8` | compose file version |

**Sample rendered output for Python app:**
```yaml
version: '3.8'

services:
  devops-python:
    image: 112005/devops-lab3-python:latest
    container_name: devops-python
    ports:
      - "5000:8080"
    environment:
      - APP_NAME=devops-python
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

### Role Dependencies — `roles/web_app/meta/main.yml`

```yaml
dependencies:
  - role: docker
```

This ensures that when only `web_app` is included in a playbook, Ansible automatically runs the `docker` role first to guarantee Docker is installed and running before attempting `docker_compose_v2` operations.

**Test:**
```bash
# Only web_app in playbook — docker role runs automatically first
ansible-playbook playbooks/deploy.yml
```

### Deployment Block

The `deploy` block in `roles/web_app/tasks/main.yml`:
1. Creates `/opt/<app_name>` directory
2. Templates `docker-compose.yml`
3. Calls `community.docker.docker_compose_v2` with `pull: always`
4. Waits for the port to open
5. Hits `/health` to confirm the app is alive
6. **Rescue** block logs failure details for debugging

### Variables Configuration

`group_vars/all.yml` (Vault-encrypted) contains: `dockerhub_username`, `dockerhub_password`.

Per-app variables live in `vars/app_python.yml` and `vars/app_java.yml`.

### Idempotency

Running the playbook twice in a row:
- 1st run: `changed` (pulls image, creates directory, starts container)
- 2nd run: `ok` (image unchanged, compose detects no diff)

```bash
ansible-playbook playbooks/deploy_python.yml   # changed
ansible-playbook playbooks/deploy_python.yml   # ok
```

### Research Answers

**Q: `restart: always` vs `restart: unless-stopped`?**  
`always` restarts the container even if it was manually stopped. `unless-stopped` respects a manual `docker stop` and does not auto-restart — better for controlled maintenance windows.

**Q: How do Docker Compose networks differ from Docker bridge networks?**  
Docker Compose automatically creates a project-scoped bridge network named `<project>_default`. Containers in the same Compose project communicate by service name (DNS). Plain `docker run` containers using the default bridge network cannot resolve each other by name unless `--link` (deprecated) or a custom network is used.

**Q: Can you reference Ansible Vault variables in the template?**  
Yes. Vault-decrypted variables are available in the Jinja2 template context just like any other variable. Ansible decrypts Vault content before running tasks, so `{{ dockerhub_password }}` in a template would render the plaintext value (use `no_log: true` on any task that would display it).

---

## Task 3: Wipe Logic (1 pt)

### Implementation

| Gate | Mechanism | Purpose |
|------|-----------|---------|
| Tag gate | `--tags web_app_wipe` in CLI | prevent accidental wipe during normal runs |
| Variable gate | `-e "web_app_wipe=true"` + `when: web_app_wipe \| bool` | explicit intent required |

**Default:** `web_app_wipe: false` in `roles/web_app/defaults/main.yml` — wipe tasks are skipped unless the variable is explicitly set.

**File:** `roles/web_app/tasks/wipe.yml` — stops containers via `docker_compose_v2`, removes the compose file, removes the project directory.

### Wipe + Main Tasks Ordering

`wipe.yml` is included at the **beginning** of `main.yml`. This allows clean-reinstall in a single command:
1. Wipe tasks run → old containers stopped, directory removed
2. Deploy tasks run → fresh compose file templated, container started

### Test Scenarios

**Scenario 1 — Normal deployment (wipe should NOT run)**
```bash
ansible-playbook playbooks/deploy_python.yml
# Result: app deployed, wipe tasks skipped (variable=false)
```

**Scenario 2 — Wipe only**
```bash
ansible-playbook playbooks/deploy_python.yml \
  -e "web_app_wipe=true" --tags web_app_wipe
# Result: containers removed, /opt/devops-python deleted, deploy skipped
```

**Scenario 3 — Clean reinstall (wipe → deploy)**
```bash
ansible-playbook playbooks/deploy_python.yml -e "web_app_wipe=true"
# Result: old deployment removed, fresh deployment created
```

**Scenario 4a — Tag specified but variable false (should NOT wipe)**
```bash
ansible-playbook playbooks/deploy_python.yml --tags web_app_wipe
# Result: include_tasks runs, when: web_app_wipe | bool is false → skip
```

**Scenario 4b — Variable true, tag specified (wipe only)**
```bash
ansible-playbook playbooks/deploy_python.yml \
  -e "web_app_wipe=true" --tags web_app_wipe
# Result: only wipe runs (deploy block is tagged app_deploy, not selected)
```

### Research Answers

1. **Why use both variable AND tag?**  
   The tag prevents the wipe from running during normal tag-less plays (edge case). The variable prevents accidental wipe if someone adds `web_app_wipe` to a global `--tags` list without realising it. Both must be true simultaneously — two independent safety latches.

2. **Difference from `never` tag?**  
   The `never` tag makes tasks completely invisible to `--list-tasks` and skips them even if you explicitly pass `--tags never`... unless `never` is in `--tags`. The double-gate approach used here is more explicit: operators must actively set a variable AND specify the tag. The `never` approach only has one gate (the tag). Also, `never`-tagged tasks cannot easily be used in the "wipe then deploy" scenario.

3. **Why must wipe logic come BEFORE deployment in main.yml?**  
   For clean-reinstall (`-e "web_app_wipe=true"` without `--tags`), all tasks run in order. If wipe were after deploy, the app would deploy first and then be immediately wiped, leaving nothing running.

4. **Clean reinstall vs rolling update?**  
   Clean reinstall is suited for major version upgrades, corrupted state, or configuration-breaking changes. Rolling updates (patch releases, config tweaks) are preferable for zero-downtime scenarios.

5. **Extending to wipe images and volumes?**  
   Add tasks before directory removal using `community.docker.docker_image` with `state: absent` and `docker_compose_v2` with `remove_volumes: true`.

---

## Task 4: CI/CD with GitHub Actions (3 pts)

### Workflow Architecture

```
Code Push (ansible/**) → Lint Job → Deploy Job → Verify
```

Two workflows cover both apps:
- `.github/workflows/ansible-deploy.yml` — Python app
- `.github/workflows/ansible-deploy-java.yml` — Java app (Bonus)

### Workflow: `ansible-deploy.yml`

**Triggers:**
- `push` to `master`/`main` when files under `ansible/**` change (excluding `ansible/docs/**`)
- `pull_request` to `master`/`main`
- `workflow_dispatch` (manual)

**Path filter** prevents CI running when only docs change.

**Jobs:**

| Job | Runner | Condition |
|-----|--------|-----------|
| `lint` | ubuntu-latest | always |
| `deploy` | ubuntu-latest | only on push (not PRs) |

**Lint job steps:**
1. Checkout code
2. Set up Python 3.12
3. `pip install ansible ansible-lint`
4. `ansible-galaxy collection install -r collections/requirements.yml`
5. `ansible-lint playbooks/*.yml`

**Deploy job steps:**
1. Checkout
2. Install Ansible + collections
3. Configure SSH (`~/.ssh/id_rsa` from secret, `ssh-keyscan` for known_hosts)
4. Write Vault password to `/tmp/vault_pass`
5. Run `ansible-playbook playbooks/deploy_python.yml`
6. **Always** clean up `/tmp/vault_pass` and `~/.ssh/id_rsa`
7. `curl` health check to verify app is live

### Required GitHub Secrets

| Secret | Value |
|--------|-------|
| `ANSIBLE_VAULT_PASSWORD` | Vault password used for `ansible-vault` |
| `SSH_PRIVATE_KEY` | Private key for SSH access to the VM |
| `VM_HOST` | VM IP address (e.g., `100.53.0.12`) |
| `VM_USER` | SSH username (e.g., `ubuntu`) |

Configure at: **Settings → Secrets and variables → Actions → New repository secret**

### Security Considerations

- SSH private key is written to disk only during the deploy job step and deleted in the `always` cleanup step
- Vault password uses the same `always` cleanup pattern
- `no_log: true` is set on the Docker Hub login task to prevent credential exposure in logs
- PR builds run lint only — no secrets exposed, no deployment triggered

### Research Answers

1. **Security implications of SSH keys in GitHub Secrets?**  
   GitHub Secrets are encrypted at rest and only exposed to allowed Actions. The risk is if a malicious PR could print the secret — GitHub prevents secrets from being accessed in PRs from forks, which mitigates the main attack vector. Rotation policy and least-privilege keys (deploy-only, specific host) reduce blast radius.

2. **Staging → Production pipeline?**  
   Add a `staging` environment in GitHub repo settings with required reviewers. Use separate inventory groups (`staging`, `production`) and separate workflows/jobs conditioned on branch (`release/**` → staging, tag `v*` → production).

3. **Rollbacks?**  
   Tag each deployment with a git SHA or version tag. Keep previous Docker images tagged by sha. Add a `rollback` job triggered manually or on failed health check that re-runs the playbook with `docker_tag: <previous_sha>`.

4. **Self-hosted vs GitHub-hosted runner security?**  
   Self-hosted runners run in your infrastructure — no SSH key in GitHub Secrets, direct filesystem access. Downside: the runner host itself becomes a security boundary. GitHub-hosted runners are ephemeral (clean VM each run) — better isolation but require SSH credentials in secrets.

---

## Bonus Part 1: Multi-App Deployment (1.5 pts)

### Architecture

```
ansible/
├── vars/
│   ├── app_python.yml   ← Python app variables
│   └── app_java.yml     ← Java app variables
├── roles/
│   └── web_app/         ← single reusable role
└── playbooks/
    ├── deploy_python.yml
    ├── deploy_java.yml
    └── deploy_all.yml
```

The **same `web_app` role** deploys both apps — role reusability in action.

### Variable Files

**`vars/app_python.yml`**
```yaml
app_name: devops-python
docker_image: "112005/devops-lab3-python"
app_port: 5000
app_internal_port: 8080   # gunicorn
compose_project_dir: "/opt/devops-python"
```

**`vars/app_java.yml`**
```yaml
app_name: devops-java
docker_image: "112005/devops-lab3-java"
app_port: 8001            # different host port!
app_internal_port: 8080   # Spring Boot default
compose_project_dir: "/opt/devops-java"
```

Port separation prevents host-side conflicts. Both containers map to their own `compose_project_dir`, so Compose projects are fully isolated.

### `deploy_all.yml`

Uses `include_role` with inline `vars` to invoke `web_app` twice in a single play. This also correctly handles wipe:

```bash
# Wipe both apps
ansible-playbook playbooks/deploy_all.yml \
  -e "web_app_wipe=true" --tags web_app_wipe

# Wipe only Python app
ansible-playbook playbooks/deploy_python.yml \
  -e "web_app_wipe=true" --tags web_app_wipe
```

Because `compose_project_dir` is different for each app, wipe only removes that app's directory.

### Test Commands

```bash
# Deploy both apps
ansible-playbook playbooks/deploy_all.yml

# Verify on target VM
ssh ubuntu@100.53.0.12 "docker ps"
curl http://100.53.0.12:5000/health    # Python
curl http://100.53.0.12:8001/health    # Java

# Independent deployment
ansible-playbook playbooks/deploy_python.yml  # only Python
ansible-playbook playbooks/deploy_java.yml    # only Java

# Independent wipe
ansible-playbook playbooks/deploy_python.yml \
  -e "web_app_wipe=true" --tags web_app_wipe
# Python gone, Java untouched
```

---

## Bonus Part 2: Multi-App CI/CD (1 pt)

### Workflow Strategy

Separate workflows for each app using **path filters** to ensure only the affected app is deployed when its configuration changes:

| Workflow | File | Trigger paths |
|----------|------|---------------|
| Python deploy | `ansible-deploy.yml` | `ansible/**` (broad — covers shared role changes) |
| Java deploy | `ansible-deploy-java.yml` | `ansible/vars/app_java.yml`, `ansible/playbooks/deploy_java.yml`, `ansible/roles/web_app/**` |

**Role-change scenario:** Changing `roles/web_app/tasks/main.yml` triggers **both** workflows because:
- `ansible-deploy.yml` watches `ansible/**`
- `ansible-deploy-java.yml` watches `ansible/roles/web_app/**`

Both apps are redeployed — correct behaviour since the shared role changed.

**App-only scenario:** Changing `vars/app_java.yml` triggers only `ansible-deploy-java.yml`. The Python app is unaffected.

### Status Badges

Both badges are in the root `README.md`:
```markdown
[![Ansible Deploy Python](https://github.com/mpasgat/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](...)
[![Ansible Deploy Java](https://github.com/mpasgat/DevOps-Core-Course/actions/workflows/ansible-deploy-java.yml/badge.svg)](...)
```

### Comparison: Separate workflows vs Matrix

| Criterion | Separate workflows | Matrix strategy |
|-----------|-------------------|-----------------|
| Independent triggering | ✅ path filters per workflow | ❌ single trigger for all |
| Separate failure visibility | ✅ badge per app | partial (matrix job names) |
| Code duplication | moderate | low |
| Independent secrets per app | possible | harder |
| Recommended for | production | prototyping |

Separate workflows chosen — better observability and independent triggering.

---

## Summary

| Task | Status | Notes |
|------|--------|-------|
| Blocks & Tags | ✅ | common + docker roles refactored |
| Docker Compose | ✅ | template, meta deps, v2 module |
| Wipe Logic | ✅ | double-gate: variable + tag |
| CI/CD | ✅ | lint + deploy + verify, cleanup |
| Documentation | ✅ | this file |
| Bonus: Multi-App | ✅ | Python + Java, same role |
| Bonus: Multi-App CI/CD | ✅ | separate workflows, path filters |

### Key Learnings

- **Blocks** make role intent readable and enable error recovery without extra playbooks
- **Role dependencies** (`meta/main.yml`) enforce provisioning order automatically, preventing "docker not installed" surprises
- **Docker Compose v2** module is idempotent — second run shows `ok` when nothing changed
- **Double-gate wipe** trades slight verbosity for a safety pattern that prevents accidental data loss
- **Path filters** in GitHub Actions cut CI costs significantly for monorepo setups
- Vault-encrypted `group_vars/all.yml` is auto-loaded; no `vars_files` needed in playbooks

### Total Time Spent

Approximately 4 hours (implementation + testing + documentation).
