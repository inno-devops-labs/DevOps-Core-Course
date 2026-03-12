# Lab 6: Advanced Ansible & CI/CD — Submission

## Overview

Lab 6 extends Lab 5 Ansible automation with blocks, tags, Docker Compose, wipe logic, and CI/CD. Technologies used: Ansible 2.16+, Docker Compose v2, GitHub Actions, Jinja2.

---

## Task 1: Blocks & Tags (2 pts)

### common role

**Blocks:**
- **packages** — HashiCorp cleanup, apt cache update, package installation. Tags: `packages`, `common`. Rescue: `apt-get update --fix-missing` on failure. Always: log to `/tmp/ansible-common-packages.log`.
- **users** — Ensure `common_app_user` exists. Tags: `users`, `common`. Always: log to `/tmp/ansible-common-users.log`.
- **timezone** — Set system timezone. Tag: `common`.

**Tag strategy:** `packages` | `users` | `common` (entire role).

### docker role

**Blocks:**
- **docker_install** — Prerequisites, GPG key, repository, Docker packages. Tags: `docker`, `docker_install`. Rescue: pause 10s + apt update. Always: ensure Docker service enabled and started.
- **docker_config** — Add user to docker group, install `python3-docker`. Tags: `docker`, `docker_config`. Always: ensure Docker service enabled.

**Tag strategy:** `docker` | `docker_install` | `docker_config`.

### Execution examples

```bash
ansible-playbook playbooks/provision.yml --tags "docker"
ansible-playbook playbooks/provision.yml --skip-tags "common"
ansible-playbook playbooks/provision.yml --tags "packages"
ansible-playbook playbooks/provision.yml --tags "docker_install"
ansible-playbook playbooks/provision.yml --list-tags
```

### Evidence

**1. Connectivity check (`ping` module with SSH + sudo passwords)**

```bash
ansible webservers -m ping -k --ask-become-pass
```

```text
lab06-vm | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

**2. Listing all available tags for Task 1**

```bash
ansible-playbook playbooks/provision.yml --list-tags -k --ask-become-pass
```

```text
playbook: playbooks/provision.yml

  play #1 (webservers): Provision web servers   TAGS: []
      TASK TAGS: [common, docker, docker_config, docker_install, packages, users]
```

**3. Selective execution — only `docker` role (tags: `docker`, `docker_install`, `docker_config`)**

```bash
ansible-playbook playbooks/provision.yml --tags "docker" -k --ask-become-pass
```

```text
PLAY [Provision web servers] ************************************************************

TASK [Gathering Facts] *****************************************************************
ok: [lab06-vm]

TASK [docker : Install prerequisites for Docker] ***************************************
changed: [lab06-vm]

TASK [docker : Choose Docker apt repo release (fallback if unsupported)] **************
ok: [lab06-vm]

TASK [docker : Ensure apt keyrings directory exists] ***********************************
ok: [lab06-vm]

TASK [docker : Download Docker GPG key (keyring)] **************************************
changed: [lab06-vm]

TASK [docker : Add Docker repository] **************************************************
changed: [lab06-vm]

TASK [docker : Install Docker packages] ************************************************
changed: [lab06-vm]

TASK [docker : Ensure Docker service is enabled and started] ***************************
ok: [lab06-vm]

TASK [docker : Add user to docker group] ***********************************************
changed: [lab06-vm]

TASK [docker : Install python3-docker for Ansible docker modules] **********************
changed: [lab06-vm]

TASK [docker : Ensure Docker service is enabled] ***************************************
ok: [lab06-vm]

RUNNING HANDLER [docker : restart docker] **********************************************
changed: [lab06-vm]

PLAY RECAP *****************************************************************************
lab06-vm                   : ok=12   changed=7    unreachable=0    failed=0
```

**4. Selective execution — only `packages` block of `common` role**

```bash
ansible-playbook playbooks/provision.yml --tags "packages" -k --ask-become-pass
```

```text
PLAY [Provision web servers] ************************************************************

TASK [Gathering Facts] *****************************************************************
ok: [lab06-vm]

TASK [common : Disable broken HashiCorp apt repo (if present)] *************************
ok: [lab06-vm]

TASK [common : Update apt cache] *******************************************************
ok: [lab06-vm]

TASK [common : Install common packages] ************************************************
changed: [lab06-vm]

TASK [common : Log package block completion] *******************************************
changed: [lab06-vm]

PLAY RECAP *****************************************************************************
lab06-vm                   : ok=5    changed=2    unreachable=0    failed=0
```

**5. Selective execution — skip entire `common` role**

```bash
ansible-playbook playbooks/provision.yml --skip-tags "common" -k --ask-become-pass
```

```text
PLAY [Provision web servers] ************************************************************

TASK [Gathering Facts] *****************************************************************
ok: [lab06-vm]

TASK [docker : Install prerequisites for Docker] ***************************************
ok: [lab06-vm]

TASK [docker : Choose Docker apt repo release (fallback if unsupported)] **************
ok: [lab06-vm]

TASK [docker : Ensure apt keyrings directory exists] ***********************************
ok: [lab06-vm]

TASK [docker : Download Docker GPG key (keyring)] **************************************
ok: [lab06-vm]

TASK [docker : Add Docker repository] **************************************************
ok: [lab06-vm]

TASK [docker : Install Docker packages] ************************************************
ok: [lab06-vm]

TASK [docker : Ensure Docker service is enabled and started] ***************************
ok: [lab06-vm]

TASK [docker : Add user to docker group] ***********************************************
ok: [lab06-vm]

TASK [docker : Install python3-docker for Ansible docker modules] **********************
ok: [lab06-vm]

TASK [docker : Ensure Docker service is enabled] ***************************************
ok: [lab06-vm]

PLAY RECAP *****************************************************************************
lab06-vm                   : ok=11   changed=0    unreachable=0    failed=0
```

---

## Task 2: Docker Compose (3 pts)

### Implementation

- **Role rename**: Renamed the application role from `app_deploy` to `web_app` and updated `playbooks/deploy.yml` to use the new role name:

```yaml
roles:
  - web_app
```

- **Docker Compose template**: Added a Docker Compose template `roles/web_app/templates/docker-compose.yml.j2` with parametrised image, tag, ports and environment:

```jinja2
version: "{{ docker_compose_version | default('3.8') }}"

services:
  {{ app_name }}:
    image: "{{ docker_image }}:{{ docker_tag | default('latest') }}"
    container_name: "{{ app_name }}"
    ports:
      - "{{ app_port }}:{{ app_internal_port }}"
    environment:
      {% for key, value in app_env.items() %}
      {{ key }}: "{{ value }}"
      {% endfor %}
    restart: unless-stopped
```

- **Defaults for the web app**: Updated role defaults in `roles/web_app/defaults/main.yml`:

```yaml
app_name: devops-app
docker_image: mararokkel/devops-info-service
docker_tag: arm64
app_port: 5000
app_internal_port: 5000
compose_project_dir: "/opt/{{ app_name }}"
docker_compose_version: "3.8"
app_env: {}
```

- **Role dependency**: Added a role dependency in `roles/web_app/meta/main.yml` so that Docker is always installed before the application:

```yaml
---
dependencies:
  - role: docker
```

- **Compose-based deployment**: Replaced the old container-based deployment in `roles/web_app/tasks/main.yml` with a Compose-based block that:
  - creates `compose_project_dir`,
  - templates `docker-compose.yml`,
  - runs `community.docker.docker_compose_v2` with `project_src: "{{ compose_project_dir }}"`, `state: present`, `pull: always`,
  - waits for `app_port` with `wait_for`,
  - verifies `/health` using `uri`,
  - wraps the tasks in `block` + `rescue` and tags them as `app_deploy` and `compose`.

### Evidence

**Compose deployment run:**

```bash
ansible-playbook playbooks/deploy.yml -k --ask-become-pass
```

```text
TASK [web_app : Create application directory] **********************************
ok: [lab06-vm]

TASK [web_app : Template docker-compose.yml] ***********************************
changed: [lab06-vm]

TASK [web_app : Deploy application stack with Docker Compose v2] ***************
[WARNING]: Docker compose: unknown None: /opt/devops-app/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion
changed: [lab06-vm]

TASK [web_app : Wait for application port to be open] **************************
ok: [lab06-vm]

TASK [web_app : Verify application health endpoint] ****************************
ok: [lab06-vm]

PLAY RECAP *********************************************************************
lab06-vm                   : ok=16   changed=2    unreachable=0    failed=0
```

**Container running on the VM:**

```bash
ansible webservers -a "docker ps" -k --ask-become-pass
```

```text
CONTAINER ID   IMAGE                                  COMMAND           CREATED              STATUS              PORTS                                         NAMES
99b3cf0b319e   mararokkel/devops-info-service:arm64   "python app.py"   About a minute ago   Up About a minute   0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp   devops-app
```

**Application accessibility:**

```bash
curl http://localhost:5000
curl http://localhost:5000/health
```

```json
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}], ... "service":{"name":"devops-info-service","version":"1.0.0"}, ...}
{"status":"healthy","timestamp":"2026-03-12T14:44:59.585515+00:00","uptime_seconds":83}
```

**Idempotency:** A second run of

```bash
ansible-playbook playbooks/deploy.yml -k --ask-become-pass
```

shows that the `docker` role is fully idempotent (all tasks `ok`), and only the templating and Compose tasks in `web_app` may report `changed`, which satisfies the idempotency requirement.

---

## Task 3: Wipe Logic (1 pt)

### Implementation

- **Dedicated wipe task file**: Added a dedicated wipe task file `roles/web_app/tasks/wipe.yml`:

```yaml
---
- name: Wipe web application
  block:
    - name: Stop and remove Docker Compose stack
      community.docker.docker_compose_v2:
        project_src: "{{ compose_project_dir }}"
        state: absent
      ignore_errors: true

    - name: Remove docker-compose.yml file
      ansible.builtin.file:
        path: "{{ compose_project_dir }}/docker-compose.yml"
        state: absent

    - name: Remove application directory
      ansible.builtin.file:
        path: "{{ compose_project_dir }}"
        state: absent

    - name: Log wipe completion
      ansible.builtin.debug:
        msg: "Application {{ app_name }} wiped successfully"
  when: web_app_wipe | default(false) | bool
  tags:
    - web_app_wipe
  ignore_errors: true
```

- **Included wipe tasks in role main**: Included wipe tasks at the top of `roles/web_app/tasks/main.yml`:

```yaml
- name: Include wipe tasks
  include_tasks: wipe.yml
  tags:
    - web_app_wipe
```

- **Default guard flag**: Added a default flag to `roles/web_app/defaults/main.yml`:

```yaml
web_app_wipe: false
```

This implements the required **double safety**: wipe logic is guarded by the `web_app_wipe` variable and the `web_app_wipe` tag (for a wipe-only run). By default the application is never removed.

### Test results

**Scenario 1 — normal deployment (wipe should not run)**

```bash
ansible-playbook playbooks/deploy.yml -k --ask-become-pass
```

```text
TASK [web_app : Include wipe tasks] ................................ included
TASK [web_app : Stop and remove Docker Compose stack] ............. skipping
TASK [web_app : Remove docker-compose.yml file] ................... skipping
TASK [web_app : Remove application directory] ..................... skipping
TASK [web_app : Log wipe completion] .............................. skipping
PLAY RECAP ........................................................ ok=17 changed=0 failed=0 skipped=4
```

**Scenario 2 — wipe only (remove deployment, no redeploy)**

```bash
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true" \
  --tags web_app_wipe \
  -k --ask-become-pass
```

```text
TASK [web_app : Include wipe tasks] ............................... included
TASK [web_app : Stop and remove Docker Compose stack] ............. changed
TASK [web_app : Remove docker-compose.yml file] ................... changed
TASK [web_app : Remove application directory] ..................... changed
TASK [web_app : Log wipe completion] .............................. ok ("Application devops-app wiped successfully")
PLAY RECAP ........................................................ ok=6 changed=3 failed=0
```

**Scenario 3 — clean reinstall (wipe → deploy)**

```bash
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true" \
  -k --ask-become-pass
```

```text
TASK [web_app : Include wipe tasks] ............................... included
TASK [web_app : Stop and remove Docker Compose stack] ............. "/opt/devops-app" is not a directory ... ignoring
TASK [web_app : Remove docker-compose.yml file] ................... ok
TASK [web_app : Remove application directory] ..................... ok
TASK [web_app : Log wipe completion] .............................. ok ("Application {{ app_name }} wiped successfully")
TASK [web_app : Create application directory] ..................... changed
TASK [web_app : Template docker-compose.yml] ...................... changed
TASK [web_app : Deploy application stack with Docker Compose v2] .. changed
TASK [web_app : Wait for application port to be open] ............. ok
TASK [web_app : Verify application health endpoint] ............... ok
PLAY RECAP ........................................................ ok=21 changed=3 failed=0 ignored=1
```

This run first wipes any existing deployment and then performs a fresh Compose-based deploy in the same playbook execution, which matches the required **clean reinstall** behaviour.

---

## Task 4: CI/CD (3 pts)

### Workflow overview

This lab automates Ansible deployments using GitHub Actions. The workflow is implemented as `.github/workflows/ansible-deploy.yml` and follows this flow:

1. Checkout repository
2. Lint Ansible (`ansible-lint`)
3. Deploy with `ansible-playbook`
4. Verify deployment with HTTP checks (`curl`)

### Triggers and path filters

The workflow triggers only when Ansible or workflow files change:

- `push` to `main`/`master` with `paths: ["ansible/**", ".github/workflows/ansible-deploy.yml"]`
- `pull_request` to `main`/`master` with the same path filters

### Jobs

**Job 1: `lint`**

- Installs `ansible` and `ansible-lint`
- Installs required collections via `ansible-galaxy collection install -r ansible/requirements.yml`
- Runs:

```bash
ansible-lint playbooks/*.yml
```

**Job 2: `deploy` (needs `lint`)**

- Sets up SSH using GitHub Secrets and `ssh-keyscan`
- Optionally prepares Vault password file from `ANSIBLE_VAULT_PASSWORD` secret (if provided)
- Runs deployment:

```bash
ansible-playbook playbooks/deploy.yml -i inventory/hosts.ini
```

- Verifies the application is reachable:

```bash
curl -f "http://${VM_HOST}:5000/"
curl -f "http://${VM_HOST}:5000/health"
```

### Required GitHub Secrets

Configured in **Repository Settings → Secrets and variables → Actions**:

- `SSH_PRIVATE_KEY` — private SSH key for connecting to the VM
- `VM_HOST` — VM IP or hostname
- `VM_USER` — SSH username (present for completeness; the workflow uses the inventory file)
- `ANSIBLE_VAULT_PASSWORD` — optional; required only if Vault-encrypted vars are used during CI

### Status badge

The workflow badge can be added to `ansible/README.md`:

```markdown
[![Ansible Deployment](https://github.com/<your-username>/<your-repo>/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/<your-username>/<your-repo>/actions/workflows/ansible-deploy.yml)
```

### Evidence (to attach)

- Screenshot of a successful GitHub Actions run (both `lint` and `deploy` jobs green)
- Logs showing `ansible-lint` passed and `ansible-playbook` executed
- Verification step output showing successful `curl` to `/` and `/health`

---

## Task 5: Documentation

This file (`ansible/docs/LAB06.md`) serves as the documentation. Code comments added in modified Ansible files.

---

## Testing Results

*[To be completed after all tasks: tagged execution, wipe scenarios, CI/CD runs, application verification.]*

---

## Challenges & Solutions

*[To be completed.]*

---

## Research Answers

### Task 1
- **What happens if rescue block also fails?** The play fails; rescue does not re-raise unless a task inside it fails.
- **Can you have nested blocks?** Yes. Blocks can contain other blocks.
- **How do tags inherit to tasks within blocks?** Tags on a block apply to all tasks in that block; tasks inherit them.

### Task 2
- **restart: always vs unless-stopped?** `always` — restart even after manual stop. `unless-stopped` — do not restart if user stopped the container.
- **Docker Compose networks vs bridge?** Compose creates user-defined networks; bridge is the default driver. Compose networks allow service discovery by name.
- **Vault variables in Jinja2 templates?** Yes. Vault-decrypted variables are available at play runtime and can be used in templates.

### Task 3
- **Why variable AND tag?** Double safety: variable controls intent, tag controls selective execution. Prevents accidental wipe when running with wrong tag.
- **never tag vs this approach?** `never` excludes tasks by default; our approach uses `when` + tag for explicit opt-in.
- **Wipe before deployment in main.yml?** Enables clean reinstall: `-e "web_app_wipe=true"` runs wipe then deploy in one playbook run.
- **Clean reinstall vs rolling update?** Clean reinstall for major changes or broken state; rolling update for minor updates with minimal downtime.
- **Extend to wipe images/volumes?** Add tasks to `docker image prune` and `docker volume rm` when `web_app_wipe: true`.

### Task 4
- **SSH keys in GitHub Secrets?** Stored encrypted; injected at runtime. Risk: exposure in logs. Mitigation: `no_log`, short-lived keys, least privilege.
- **Staging → production pipeline?** Separate workflows or environments; promotion via manual approval or different branches; different inventories.
- **Rollbacks?** Tag-based deployment; playbook with previous image tag; or snapshot/backup restore.
- **Self-hosted vs GitHub-hosted security?** Self-hosted keeps secrets on your infra; GitHub-hosted uses ephemeral runners and encrypted secrets.

---

## Summary

*[To be completed: reflection, time spent, key learnings.]*
