# Lab 6: Advanced Ansible & CI/CD - Submission


## Overview

In this lab, I refactored my Ansible roles with blocks/tags, migrated deployment from container-run logic to Docker Compose, implemented double-gated wipe logic, and added a GitHub Actions deployment workflow.

## Task 1: Blocks & Tags

### What I implemented

- In `roles/common/tasks/main.yml`:
  - package tasks grouped in a block with `packages` and `common`
  - user tasks grouped in a block with `users` and `common`
  - rescue for apt update with `apt-get update --fix-missing`
  - always log files in `/tmp`

- In `roles/docker/tasks/main.yml`:
  - installation block tagged `docker_install` (+ `docker`)
  - config block tagged `docker_config` (+ `docker`)
  - rescue with retry flow (pause + apt cache retry)
  - always block to ensure Docker service is enabled/running

### Real console output

```bash
ANSIBLE_LOCAL_TEMP=./.ansible/tmp ansible-playbook playbooks/provision.yml --list-tags
```

```text
playbook: playbooks/provision.yml

  play #1 (webservers): Provision web servers	TAGS: []
      TASK TAGS: [common, docker, docker_config, docker_install, packages, users]
```

Selective execution commands (executed against `192.168.1.210`):

```bash
ansible-playbook playbooks/provision.yml --tags docker --check
```

```text
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [hehe]

TASK [docker : Update apt cache] ***********************************************
changed: [hehe]

TASK [docker : Install required dependencies] **********************************
ok: [hehe]

TASK [docker : Download Docker GPG key] ****************************************
changed: [hehe]

TASK [docker : Install Docker GPG key] *****************************************
ok: [hehe]

TASK [docker : Add Docker repository] ******************************************
changed: [hehe]

TASK [docker : Install Docker] *************************************************
ok: [hehe]

TASK [docker : Ensure Docker service is running] *******************************
ok: [hehe]

TASK [docker : Add devops user to docker group] ********************************
ok: [hehe]

TASK [docker : Create Docker config directory] *********************************
ok: [hehe]

TASK [docker : Verify Docker service enabled] **********************************
ok: [hehe]

PLAY RECAP *********************************************************************
hehe                       : ok=11   changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

```bash
ansible-playbook playbooks/provision.yml --skip-tags common --check
```

```text
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [hehe]

TASK [docker : Update apt cache] ***********************************************
changed: [hehe]

TASK [docker : Install required dependencies] **********************************
ok: [hehe]

TASK [docker : Download Docker GPG key] ****************************************
changed: [hehe]

TASK [docker : Install Docker GPG key] *****************************************
ok: [hehe]

TASK [docker : Add Docker repository] ******************************************
changed: [hehe]

TASK [docker : Install Docker] *************************************************
ok: [hehe]

TASK [docker : Ensure Docker service is running] *******************************
ok: [hehe]

TASK [docker : Add devops user to docker group] ********************************
ok: [hehe]

TASK [docker : Create Docker config directory] *********************************
ok: [hehe]

TASK [docker : Verify Docker service enabled] **********************************
ok: [hehe]

PLAY RECAP *********************************************************************
hehe                       : ok=11   changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

```bash
ansible-playbook playbooks/provision.yml --tags packages --check
```

```text
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [hehe]

TASK [common : Update apt cache] ***********************************************
changed: [hehe]

TASK [common : Install common packages] ****************************************
ok: [hehe]

TASK [common : Log package block completion] ***********************************
changed: [hehe]

PLAY RECAP *********************************************************************
hehe                       : ok=4    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

```bash
ansible-playbook playbooks/provision.yml --tags docker_install --check
```

```text
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [hehe]

TASK [docker : Update apt cache] ***********************************************
changed: [hehe]

TASK [docker : Install required dependencies] **********************************
ok: [hehe]

TASK [docker : Download Docker GPG key] ****************************************
changed: [hehe]

TASK [docker : Install Docker GPG key] *****************************************
ok: [hehe]

TASK [docker : Add Docker repository] ******************************************
changed: [hehe]

TASK [docker : Install Docker] *************************************************
ok: [hehe]

TASK [docker : Ensure Docker service is running] *******************************
ok: [hehe]

PLAY RECAP *********************************************************************
hehe                       : ok=8    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Research answers

1. If a rescue block also fails, the play still fails after rescue processing.  
2. Yes, nested blocks are supported in Ansible.  
3. Tags applied on a block are inherited by tasks inside that block.

---

## Task 2: Docker Compose Migration

### Role migration

I replaced the old `app_deploy` role with a new `web_app` role:
- `roles/web_app/defaults/main.yml`
- `roles/web_app/meta/main.yml`
- `roles/web_app/templates/docker-compose.yml.j2`
- `roles/web_app/tasks/main.yml`
- `roles/web_app/tasks/wipe.yml`

I updated `playbooks/deploy.yml` to use `web_app`.

### Docker Compose template

Path: `roles/web_app/templates/docker-compose.yml.j2`

It supports:
- `app_name`, `docker_image`, `docker_tag`
- `app_port`, `app_internal_port`
- environment map `app_env`
- restart policy

### Role dependency

Path: `roles/web_app/meta/main.yml`

```yaml
dependencies:
  - role: docker
```

This ensures Docker role runs before web app role.

### Tags in deploy role

From `playbooks/deploy.yml --list-tags`:

```text
playbook: playbooks/deploy.yml

  play #1 (webservers): Deploy application	TAGS: []
      TASK TAGS: [app_deploy, compose, docker, docker_config, docker_install, web_app_wipe]
```

### Deploy run (first run)

```text
PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [hehe]

TASK [docker : Add devops user to docker group] ********************************
ok: [hehe]

TASK [docker : Create Docker config directory] *********************************
ok: [hehe]

TASK [docker : Verify Docker service enabled] **********************************
ok: [hehe]

TASK [web_app : Include wipe tasks] ********************************************
included: /opt/devops-app/roles/web_app/tasks/wipe.yml for hehe

TASK [web_app : Stop and remove containers with docker compose] ****************
skipping: [hehe]

TASK [web_app : Remove docker-compose file] ************************************
skipping: [hehe]

TASK [web_app : Remove application directory] **********************************
skipping: [hehe]

TASK [web_app : Log wipe completion] *******************************************
skipping: [hehe]

TASK [web_app : Create application directory] **********************************
changed: [hehe]

TASK [web_app : Template docker compose file] **********************************
changed: [hehe]

TASK [web_app : Pull and start services] ***************************************
changed: [hehe]

TASK [web_app : Wait for application port] *************************************
ok: [hehe]

PLAY RECAP *********************************************************************
hehe                       : ok=9    changed=2    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0
```

### Idempotency (second run)

```text
PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [hehe]

TASK [docker : Add devops user to docker group] ********************************
ok: [hehe]

TASK [docker : Create Docker config directory] *********************************
ok: [hehe]

TASK [docker : Verify Docker service enabled] **********************************
ok: [hehe]

TASK [web_app : Include wipe tasks] ********************************************
included: /opt/devops-app/roles/web_app/tasks/wipe.yml for hehe

TASK [web_app : Stop and remove containers with docker compose] ****************
skipping: [hehe]

TASK [web_app : Remove docker-compose file] ************************************
skipping: [hehe]

TASK [web_app : Remove application directory] **********************************
skipping: [hehe]

TASK [web_app : Log wipe completion] *******************************************
skipping: [hehe]

TASK [web_app : Create application directory] **********************************
ok: [hehe]

TASK [web_app : Template docker compose file] **********************************
ok: [hehe]

TASK [web_app : Pull and start services] ***************************************
ok: [hehe]

TASK [web_app : Wait for application port] *************************************
ok: [hehe]

PLAY RECAP *********************************************************************
hehe                       : ok=9    changed=0    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0
```

Second run: `changed=0` — fully idempotent.

---

## Task 3: Wipe Logic

### Implementation

I implemented double-gated wipe logic:

- variable gate:
  - `web_app_wipe: false` by default in `roles/web_app/defaults/main.yml`
- tag gate:
  - wipe tasks tagged `web_app_wipe`

Wipe steps in `roles/web_app/tasks/wipe.yml`:
1. Compose down (`state: absent`)
2. remove compose file
3. remove project directory
4. log wipe completion

Wipe is included first in `roles/web_app/tasks/main.yml`, so clean reinstall flow is:
`wipe -> deploy`.

### Why both variable + tag?

It gives double safety:
- tag alone is not enough if variable stays false
- variable alone is not enough unless wipe-tagged tasks are selected in explicit wipe-only runs

### `never` vs this approach

`never` hard-disables tasks unless explicitly requested by tag.  
This lab requires variable + tag safety logic without `never`, which I implemented.

---

## Task 4: CI/CD Integration

### Workflow created

Path: `.github/workflows/ansible-deploy.yml`

Implemented jobs:
- `lint`:
  - checkout
  - setup python 3.12
  - install `ansible`, `ansible-lint`, `community.docker`
  - run `ansible-lint playbooks/*.yml`
- `deploy` (on push):
  - checkout + python
  - setup SSH from secrets
  - run `ansible-playbook playbooks/deploy.yml`
  - verify endpoint via curl

### Secrets expected by workflow

- `ANSIBLE_VAULT_PASSWORD`
- `SSH_PRIVATE_KEY`
- `VM_HOST`

### Status badge

Badge:
```markdown
[![Ansible Deployment](../../actions/workflows/ansible-deploy.yml/badge.svg)](../../actions/workflows/ansible-deploy.yml)
```

---

## Task 5: Testing Results

### Commands I ran

```bash
ANSIBLE_LOCAL_TEMP=./.ansible/tmp ansible-playbook playbooks/provision.yml --list-tags
ANSIBLE_LOCAL_TEMP=./.ansible/tmp ansible-playbook playbooks/deploy.yml --list-tags
ANSIBLE_LOCAL_TEMP=./.ansible/tmp ansible-playbook playbooks/provision.yml --syntax-check
ANSIBLE_LOCAL_TEMP=./.ansible/tmp ansible-playbook playbooks/deploy.yml --syntax-check
```

### Real outputs

```text
playbook: playbooks/provision.yml

  play #1 (webservers): Provision web servers	TAGS: []
      TASK TAGS: [common, docker, docker_config, docker_install, packages, users]

playbook: playbooks/deploy.yml

  play #1 (webservers): Deploy application	TAGS: []
      TASK TAGS: [app_deploy, compose, docker, docker_config, docker_install, web_app_wipe]

playbook: playbooks/provision.yml
playbook: playbooks/deploy.yml
```

### App running on 192.168.1.210:8000

```bash
curl http://192.168.1.210:8000
```

```json
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"172.18.0.1","method":"GET","path":"/","user_agent":"curl/8.14.1"},"runtime":{"current_time":"2026-05-12T09:03:46.062212+00:00","timezone":"UTC","uptime_human":"0 hours, 0 minutes","uptime_seconds":33},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":1,"hostname":"cd825625fb71","platform":"Linux","platform_version":"#1 SMP PREEMPT_DYNAMIC Debian 6.12.73-1 (2026-02-17)","python_version":"3.12.12"}}
```

### docker ps on remote host

```text
CONTAINER ID   IMAGE                 COMMAND           CREATED         STATUS         PORTS                                                   NAMES
cd825625fb71   cacucoh/testiks:1.0   "python app.py"   2 minutes ago   Up 2 minutes   8000/tcp, 0.0.0.0:8000->5000/tcp, [::]:8000->5000/tcp   devops-app
```

---

## Challenges & Solutions

1. **Ansible temp permission issue in local environment**
   - issue: Ansible could not write to `~/.ansible/tmp`
   - fix: used `ANSIBLE_LOCAL_TEMP=./.ansible/tmp`

2. **VM clock drift**
   - issue: VM system clock was behind actual date, causing Docker TLS certificate validation to fail when pulling images
   - fix: corrected VM date via `date -s` before running deploy

3. **ansible-lint missing**
   - issue: system package not installed
   - fix: created local `.venv` and installed `ansible-lint`
   - note: lint reports many pre-existing style issues outside this lab scope
