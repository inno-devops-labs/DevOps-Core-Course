# Lab 6: Advanced Ansible & CI/CD - Submission

---

## Task 1: Blocks & Tags

### `common` Role

`roles/common/tasks/main.yml` - tasks grouped into a single block:

- **block**: updates apt cache and installs packages
- **rescue**: runs `apt --fix-missing` and retries install on failure
- **always**: writes a completion log to `/tmp/common_packages_done.log`
- **tags**: `packages`, `common`

### `docker` Role

`roles/docker/tasks/main.yml` - split into two blocks:

**Install block** (`docker_install` tag):

- **block**: downloads GPG key, adds repo, installs Docker CE packages
- **rescue**: waits 10 s then retries `apt update` + install (handles network timeouts)
- **always**: ensures Docker service is started and enabled

**Config block** (`docker_config` tag):

- Adds user to docker group
- Installs `python3-docker`

### Tag Strategy

| Tag              | Scope                       |
| ---------------- | --------------------------- |
| `common`         | Entire common role          |
| `packages`       | Package installation tasks  |
| `docker`         | Entire docker role          |
| `docker_install` | Docker CE installation only |
| `docker_config`  | Docker post-install config  |
| `app_deploy`     | Full web_app deployment     |
| `compose`        | Docker Compose tasks        |
| `web_app_wipe`   | Wipe tasks (explicit only)  |

### Answers

**Q: What happens if the rescue block also fails?**
Ansible marks the task as failed and stops execution for that host (unless `ignore_errors: true` or `any_errors_fatal: false` is set).

**Q: Can you have nested blocks?**
Yes - blocks can be nested to any depth, each with their own rescue/always sections.

**Q: How do tags inherit to tasks within blocks?**
Tags applied to a block are inherited by all tasks inside it. Tasks can also have their own additional tags.

---

## Task 2: Docker Compose

### Role Rename

`app_deploy` → `web_app`:

```bash
cp -r ansible/roles/app_deploy ansible/roles/web_app
```

All playbook references updated: `deploy.yml` now uses `roles: [web_app]`.

### Template - `docker-compose.yml.j2`

Located at `roles/web_app/templates/docker-compose.yml.j2`.

Key variables injected by Jinja2:

| Variable                 | Default           | Purpose                  |
| ------------------------ | ----------------- | ------------------------ |
| `app_name`               | `devops-app`      | Service & container name |
| `docker_image`           | (DockerHub image) | Image to pull            |
| `docker_tag`             | `latest`          | Image tag                |
| `app_port`               | `8000`            | Host port                |
| `app_internal_port`      | `8000`            | Container port           |
| `app_secret_key`         | (Vault encrypted) | App secret env var       |
| `docker_compose_version` | `3.8`             | Compose file version     |

### Role Dependency - `meta/main.yml`

```yaml
dependencies:
  - role: docker
```

This means running `deploy.yml` (which uses only `web_app`) automatically runs the `docker` role first - no need to explicitly include it.

### Deployment Block

`roles/web_app/tasks/main.yml`:

1. Create `compose_project_dir` (e.g. `/opt/devops-app`)
2. Template `docker-compose.yml` into that directory
3. `community.docker.docker_compose_v2` with `state: present, pull: always`
4. Rescue block logs failure message on error

### Variables

`roles/web_app/defaults/main.yml` holds all defaults. Override sensitive values with Vault:

```bash
ansible-vault encrypt_string 'my-secret' --name 'app_secret_key'
```

### Idempotency

Running the playbook twice produces `ok` on the second run - Docker Compose only recreates containers when the configuration changes.

### Research Answers

**Q: `restart: always` vs `restart: unless-stopped`?**
`always` restarts even after a manual `docker stop`. `unless-stopped` respects manual stops and does not restart them after daemon restart.

**Q: Docker Compose networks vs bridge networks?**
Compose automatically creates an isolated bridge network per project. Plain `docker run` uses the default bridge, where containers can't resolve each other by name.

**Q: Can you reference Vault variables in templates?**
Yes - Ansible decrypts Vault variables before rendering templates, so `{{ app_secret_key }}` works normally.

---

## Task 3: Wipe Logic

### Design

The wipe is controlled by a **double safety gate**:

1. **Tag gate** - must explicitly pass `--tags web_app_wipe`
2. **Variable gate** - must pass `-e "web_app_wipe=true"`

Both must be true for any wipe task to execute preventing accidental data loss.

### Files

- `roles/web_app/tasks/wipe.yml` - wipe task file
- `roles/web_app/defaults/main.yml` - `web_app_wipe: false`
- `roles/web_app/tasks/main.yml` - includes wipe.yml **before** deploy block

### wipe.yml

1. `community.docker.docker_compose_v2 state: absent` - stops & removes containers
2. Remove `docker-compose.yml` file
3. Remove the entire app directory (`compose_project_dir`)
4. Debug message confirming completion

All steps use `ignore_errors: true` so a partially-deployed app (missing compose file) doesn't abort the wipe.

### Include in main.yml

```yaml
- name: Include wipe tasks
  ansible.builtin.include_tasks: wipe.yml
  tags:
    - web_app_wipe
```

Placed **before** the deploy block so the flow is: wipe → deploy (clean reinstall).

### Test Scenarios

**Scenario 1 - Normal deploy (wipe does NOT run):**

```bash
ansible-playbook playbooks/deploy.yml
# wipe tasks are skipped because --tags web_app_wipe is not passed
```

**Scenario 2 - Wipe only:**

```bash
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true" \
  --tags web_app_wipe
# app removed, deploy block skipped (tag filter)
```

**Scenario 3 - Clean reinstall:**

```bash
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true"
# wipe runs first, then full deploy runs
```

**Scenario 4 - Tag present but variable false (should NOT wipe):**

```bash
ansible-playbook playbooks/deploy.yml --tags web_app_wipe
# when: web_app_wipe | bool → false → wipe skipped
```

### Research Answers

**Q: Why use both variable AND tag?**
Either alone is insufficient. A tag alone could be accidentally passed. A variable alone has no way to skip deployment tasks in the same run. Together they provide both safety and flexibility.

**Q: What's the difference from the `never` tag?**
The `never` tag makes tasks completely invisible to normal runs but they still execute if explicitly tagged. Our approach adds a `when` condition so even if the tag is passed accidentally (e.g. `--tags all`), the variable gate stops execution.

**Q: Why must wipe come before deploy?**
For clean reinstall: wipe removes old app → deploy installs fresh. If deploy ran first, the old containers would conflict with the new ones.

**Q: When clean reinstall vs rolling update?**
Rolling update for zero-downtime production changes. Clean reinstall for breaking config changes, volume cleanup, or debugging environment drift.

---

## Task 4: CI/CD with GitHub Actions

### Workflow File

`.github/workflows/ansible-deploy.yml`

### Trigger

```yaml
on:
  push:
    branches: [main, master]
    paths:
      - "ansible/**"
      - "!ansible/docs/**"
      - ".github/workflows/ansible-deploy.yml"
  pull_request:
    branches: [main, master]
    paths:
      - "ansible/**"
```

Path filters ensure the workflow only runs when Ansible code changes - not on unrelated commits.

### Jobs

**`lint` job (runs on every push/PR):**

1. Checkout code
2. Install `ansible` + `ansible-lint`
3. Run `ansible-lint playbooks/*.yml`

**`deploy` job (runs on push only, after lint passes):**

1. Checkout code
2. Install Ansible + `community.docker` collection
3. Write SSH private key from secret → `~/.ssh/id_ed25519`
4. `ssh-keyscan` target host → `known_hosts`
5. Write vault password from secret → `ansible/.vault_pass`
6. `ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass`
7. Clean up vault password file (`if: always()`)
8. `curl` health check against `VM_HOST:8000`

### Required GitHub Secrets

| Secret                   | Purpose                           |
| ------------------------ | --------------------------------- |
| `SSH_PRIVATE_KEY`        | Private key to SSH into target VM |
| `VM_HOST`                | Target VM IP / hostname           |
| `ANSIBLE_VAULT_PASSWORD` | Vault decryption password         |

Add these at: **Settings → Secrets and variables → Actions → New repository secret**

### Status Badge

Added to `README.md`:

```markdown
[![Ansible Deployment](https://github.com/polinaminie/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/polinaminie/DevOps-Core-Course/actions/workflows/ansible-deploy.yml)
```

### Research Answers

**Q: Security implications of SSH keys in GitHub Secrets?**
Secrets are encrypted at rest and never exposed in logs. However, anyone with write access to the repo can create a workflow that exfiltrates them. Use least-privilege keys scoped to deploy only, and rotate regularly.

**Q: Staging → production pipeline?**
Add a `staging` environment job that deploys first, followed by a manual approval gate (`environment: production` with required reviewers), then the production deploy job.

**Q: How to make rollbacks possible?**
Tag Docker images with Git SHA (`docker_tag: ${{ github.sha }}`). To roll back, re-run the previous workflow run or add a rollback job that re-deploys the last known-good tag.

**Q: Self-hosted runner security advantage?**
The runner lives inside your network - no SSH key in secrets, no inbound firewall rule needed. GitHub-hosted runners must reach your VM over the internet, increasing attack surface.

---

## Task 5: Documentation

This file serves as the documentation for Lab 6. All Ansible files have inline comments explaining:

- Why blocks are structured the way they are
- Variable purpose and default values
- Safety mechanisms in wipe logic
- Step-by-step workflow comments in the CI/CD YAML

---
