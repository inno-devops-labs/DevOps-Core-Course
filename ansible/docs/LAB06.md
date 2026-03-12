## Overview

In Lab 6, I upgraded the Ansible setup from Lab 5 to a production-style layout:

- Refactored roles with `block`/`rescue`/`always`
- Added role and task tags for selective execution
- Migrated app deployment from single `docker run` style to Docker Compose
- Renamed role `app_deploy` -> `web_app`
- Added role dependency (`web_app` depends on `docker`)
- Implemented safe wipe logic with double gating (`web_app_wipe` variable + `web_app_wipe` tag)
- Added GitHub Actions workflow for lint + deployment + verification

Tech used: Ansible, Jinja2, Docker Compose v2 module, GitHub Actions, Ansible Vault.

---

## Blocks & Tags

### `common` role changes

File: `ansible/roles/common/tasks/main.yml`

- Package tasks are grouped in a block with tag `packages`.
- User management tasks are grouped in a block with tag `users`.
- `rescue` runs `apt-get update --fix-missing` and retries apt cache update.
- `always` writes completion logs to `/tmp/common-role.log`.
- `become: true` is applied once at block level.

### `docker` role changes

File: `ansible/roles/docker/tasks/main.yml`

- Docker installation tasks grouped under tag `docker_install`.
- Docker configuration tasks grouped under tag `docker_config`.
- `rescue` waits 10 seconds, refreshes apt cache, retries GPG/repo/install.
- `always` ensures Docker service is enabled and started.

### Tag strategy

- Role-level tags:
  - `common` role in `playbooks/provision.yml`
  - `docker` role in `playbooks/provision.yml`
  - `web_app`/`app_deploy` role in `playbooks/deploy.yml`
- Task-level tags:
  - `packages`, `users`, `docker_install`, `docker_config`, `compose`, `web_app_wipe`

### `--list-tags` evidence

```bash
ANSIBLE_LOCAL_TEMP=.ansible/tmp ansible-playbook playbooks/provision.yml --list-tags
```

Output:

```text
playbook: playbooks/provision.yml

  play #1 (webservers): Provision web servers    TAGS: []
      TASK TAGS: [common, docker, docker_config, docker_install, packages, users]
```

```bash
ANSIBLE_LOCAL_TEMP=.ansible/tmp ansible-playbook playbooks/deploy.yml --list-tags
```

Output:

```text
playbook: playbooks/deploy.yml

  play #1 (webservers): Deploy application    TAGS: []
      TASK TAGS: [app_deploy, compose, docker_config, docker_install, web_app, web_app_wipe]
```

---

## Docker Compose Migration

### Role rename

- Renamed directory: `ansible/roles/app_deploy` -> `ansible/roles/web_app`
- Updated playbook reference in `ansible/playbooks/deploy.yml`

### Compose template

File: `ansible/roles/web_app/templates/docker-compose.yml.j2`

- Dynamic service name/image/tag/ports via variables
- Dynamic environment block from `app_env`
- `restart: unless-stopped`
- Dedicated bridge network `web_app_net`

### Role dependency

File: `ansible/roles/web_app/meta/main.yml`

```yaml
dependencies:
  - role: docker
```

This guarantees Docker installation before Compose deployment.

### Deployment implementation

File: `ansible/roles/web_app/tasks/main.yml`

- Includes wipe tasks first
- Creates `/opt/{{ app_name }}` project directory
- Renders `docker-compose.yml`
- Deploys stack with `community.docker.docker_compose_v2`
- Waits for app port and checks `/health`
- Uses `rescue` to report deployment failure context

### Variables

File: `ansible/roles/web_app/defaults/main.yml`

- `web_app_name`, `web_app_docker_image`, `web_app_docker_tag`
- `web_app_port`, `web_app_internal_port`
- `web_app_compose_project_dir`, `web_app_docker_compose_version`
- `web_app_secret_key` (override with Vault)
- `web_app_env`
- `web_app_wipe` (default `false`)

The role keeps compatibility with legacy variable names (`app_name`, `docker_image`, etc.) through `default(...)`, so existing Vault values continue to work.

---

## Wipe Logic

### Implementation

Files:

- `ansible/roles/web_app/tasks/wipe.yml`
- `ansible/roles/web_app/tasks/main.yml`

Behavior:

- Wipe tasks are included at the beginning of role execution.
- Wipe block runs only when `web_app_wipe | bool` is `true`.
- Wipe is tagged with `web_app_wipe`.
- Wipe removes compose project, compose file, and app directory.

Double safety mechanism:

1. Variable gate: `-e "web_app_wipe=true"`
2. Tag gate: `--tags web_app_wipe`

Result: destructive cleanup is explicit and controlled.

### Test scenarios

1. Normal deploy (wipe should not run):

```bash
ansible-playbook playbooks/deploy.yml
```

2. Wipe only:

```bash
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe
```

3. Clean reinstall (wipe -> deploy):

```bash
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"
```

4. Safety check (tag set, variable false):

```bash
ansible-playbook playbooks/deploy.yml --tags web_app_wipe
```

Expected: wipe block is skipped by `when` condition.

---

## CI/CD Integration

File: `.github/workflows/ansible-deploy.yml`

### Workflow architecture

- Trigger on pushes/PRs affecting `ansible/**`
- Excludes `ansible/docs/**`
- Job `lint`:
  - Installs `ansible`, `ansible-lint`, `community.docker`
  - Runs `ansible-lint playbooks/*.yml`
- Job `deploy` (push only):
  - Sets up SSH from GitHub Secrets
  - Builds runtime inventory file
  - Uses Vault password from secret
  - Runs `ansible-playbook playbooks/deploy.yml`
  - Verifies app and health endpoints via `curl`

### Required GitHub Secrets

- `ANSIBLE_VAULT_PASSWORD`
- `SSH_PRIVATE_KEY`
- `VM_HOST`
- `VM_USER`

### Badge

Added to root `README.md`:

![Ansible Deployment](https://github.com/sofiakulagina/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/sofiakulagina/DevOps-Core-Course/actions/workflows/ansible-deploy.yml)

---

## Testing Results

### Local syntax checks

```bash
ANSIBLE_LOCAL_TEMP=.ansible/tmp ansible-playbook playbooks/provision.yml --syntax-check
ANSIBLE_LOCAL_TEMP=.ansible/tmp ansible-playbook playbooks/deploy.yml --syntax-check
```

Both returned successful syntax validation (`playbook: ...`).

### Notes

- `ansible-lint` is configured in CI workflow.
- On this local machine, `ansible-lint` binary was not available (`command not found`), so lint validation is delegated to GitHub Actions.

### Runtime verification on target VM

Use these commands after deployment:

```bash
ssh <user>@<vm_ip> "docker ps"
ssh <user>@<vm_ip> "docker compose -f /opt/devops-app/docker-compose.yml ps"
curl -f http://<vm_ip>:8000
curl -f http://<vm_ip>:8000/health
```

---

## Challenges & Solutions

1. Sandbox blocked default Ansible temp path (`~/.ansible/tmp`) during local checks.
   - Solution: run checks with `ANSIBLE_LOCAL_TEMP=.ansible/tmp` inside repo.
2. Migration from container module to Compose module required variable and template redesign.
   - Solution: centralized runtime config in role defaults + Jinja2 compose template.
3. Safe cleanup needed to avoid accidental environment destruction.
   - Solution: double-gated wipe logic (`variable + tag`) plus default `web_app_wipe: false`.

---

## Research Answers

### Task 1 (Blocks & Tags)

1. What happens if `rescue` block also fails?
- The play fails; Ansible reports a failed task in `rescue`.

2. Can you have nested blocks?
- Yes. Nested blocks are valid and useful for focused error handling.

3. How do tags inherit within blocks?
- Tags set on a block are inherited by tasks in `block`, `rescue`, and `always` sections.

### Task 2 (Docker Compose)

1. `restart: always` vs `restart: unless-stopped`?
- `always`: restart even after manual stop (after daemon reboot).
- `unless-stopped`: restart automatically unless user intentionally stopped container.

2. Compose networks vs default Docker bridge?
- Compose creates project-scoped user-defined networks with built-in DNS/service discovery.
- Default bridge is global/shared and less isolated.

3. Can Ansible Vault variables be used in templates?
- Yes. Vault-decrypted variables are available to Jinja2 templates during playbook execution.

### Task 3 (Wipe Logic)

1. Why both variable and tag?
- Two independent confirmations reduce accidental destructive execution.

2. Difference from `never` tag?
- `never` is a static tag behavior.
- Variable+tag allows explicit runtime safety logic and clean reinstall flows.

3. Why wipe before deploy?
- Enables deterministic clean reinstall: remove old state first, then deploy fresh.

4. Clean reinstall vs rolling update?
- Clean reinstall for drifted/broken state reset.
- Rolling update for minimal downtime and state continuity.

5. How to extend wipe to images/volumes?
- Add `docker_compose_v2` cleanup options and dedicated tasks to prune project images/volumes with explicit additional guards.

### Task 4 (CI/CD)

1. Security implications of SSH keys in GitHub Secrets?
- If secrets leak (misconfiguration/log exposure), attackers can access infrastructure.
- Mitigate with least-privilege keys, key rotation, environment protection rules, and IP/host restrictions.

2. Staging -> production pipeline design?
- Use separate jobs/environments: deploy to staging, run smoke tests, require manual approval, then deploy to production.

3. What to add for rollbacks?
- Versioned image tags, release metadata, and workflow step to redeploy previous known-good tag.

4. Why can self-hosted runner improve security?
- Private network access without exposing SSH externally, tighter boundary control, and reduced secret distribution to public runner infrastructure.
