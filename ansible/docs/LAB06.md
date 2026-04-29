# Lab 6 - Advanced Ansible & CI/CD (Local VM from Lab 4)

## 1. Overview

Lab 6 was completed on the same local VirtualBox VM used in Labs 4-5 (`lab04-ubuntu24`, SSH via `127.0.0.1:2222`).

Implemented:

- Blocks + tags + rescue/always in `common` and `docker` roles
- Migration from `app_deploy` to `web_app` role
- Docker Compose deployment with Jinja2 template
- Role dependency (`web_app` depends on `docker`)
- Wipe logic with double safety (`web_app_wipe` variable + `web_app_wipe` tag)
- GitHub Actions workflow for ansible lint/deploy/verification
- Status badge in repository `README.md`

Tooling used:

- Ansible `core 2.16.3`
- `community.docker` collection
- Docker Compose v2 plugin on target VM
- Local `ansible-lint` execution in isolated virtual environment

---

## 2. Task 1 - Blocks & Tags (2 pts)

### 2.1 `common` role refactor

Updated file: `roles/common/tasks/main.yml`

- Package/timezone tasks grouped in one `block`
- `rescue` runs `apt-get update --fix-missing`
- `always` writes completion marker to `/tmp/ansible-common-packages.log`
- User management tasks grouped in separate `block`

Tags applied:

- `packages` for package/timezone block
- `users` for user-management block
- `common` at role task level

### 2.2 `docker` role refactor

Updated file: `roles/docker/tasks/main.yml`

- Install flow grouped in `block` with tag `docker_install`
- Config flow grouped in separate `block` with tag `docker_config`
- `rescue` includes 10-second pause + apt retry + re-run key/repo/install
- `always` ensures Docker service is enabled/started

Tags applied:

- `docker` role-level task tags
- `docker_install` install-only tasks
- `docker_config` configuration tasks

### 2.3 Tag listing evidence

```text
playbook: playbooks/provision.yml
TASK TAGS: [common, docker, docker_config, docker_install, packages, users]
```

### 2.4 Selective execution evidence

`ansible-playbook playbooks/provision.yml --tags docker`

```text
PLAY RECAP
lab04-local : ok=8 changed=0 failed=0 skipped=1 rescued=0
```

`ansible-playbook playbooks/provision.yml --skip-tags common`

```text
PLAY RECAP
lab04-local : ok=8 changed=0 failed=0 skipped=1 rescued=0
```

`ansible-playbook playbooks/provision.yml --tags packages`

```text
PLAY RECAP
lab04-local : ok=6 changed=1 failed=0 skipped=1 rescued=0
```

`ansible-playbook playbooks/provision.yml --tags docker_install`

```text
PLAY RECAP
lab04-local : ok=7 changed=0 failed=0 skipped=1 rescued=0
```

### 2.5 Rescue block evidence

Forced Docker retry path:

`ansible-playbook playbooks/provision.yml --tags docker_install -e "docker_force_gpg_retry=true"`

```text
TASK [docker : Force Docker GPG retry path for testing] fatal
TASK [docker : Wait before retrying Docker apt metadata] ok
TASK [docker : Retry apt cache update] changed
PLAY RECAP
lab04-local : ok=9 changed=1 failed=0 rescued=1
```

Forced common-role rescue path:

`ansible-playbook playbooks/provision.yml --tags packages -e "common_force_apt_failure=true"`

```text
TASK [common : Force apt failure for rescue testing] fatal
TASK [common : Retry apt cache update with fix-missing] ok
PLAY RECAP
lab04-local : ok=5 changed=0 failed=0 rescued=1
```

### 2.6 Task 1 research answers

1. If `rescue` also fails, the host/play fails at that point (unless further failure-handling is added).
2. Yes, nested blocks are supported.
3. Tags applied at block level are inherited by tasks inside that block.

---

## 3. Task 2 - Docker Compose Migration (3 pts)

### 3.1 Role rename and structure

- Renamed role directory: `roles/app_deploy` -> `roles/web_app`
- Updated playbooks:
  - `playbooks/deploy.yml` now uses `web_app`
  - `playbooks/site.yml` now uses `common` + `web_app`

### 3.2 Docker Compose template

Created: `roles/web_app/templates/docker-compose.yml.j2`

Templated values:

- `app_name`
- `docker_image`
- `docker_tag`
- `app_port`
- `app_internal_port`
- `app_secret_key` (optional, rendered as `APP_SECRET_KEY`)
- `app_environment`
- `app_restart_policy`

Template now includes inline variable documentation comments at the top of the file.

Rendered result on VM (`/opt/devops-app/docker-compose.yml`):

```yaml
services:
  devops-app:
    image: "lanebo1/devops-info-service:latest"
    container_name: "devops-app"
    ports:
      - "5000:5000"
    environment:
      PORT: "5000"
    restart: "unless-stopped"
    networks:
      - "devops-app_net"
```

### 3.3 Role dependency

Created: `roles/web_app/meta/main.yml`

```yaml
dependencies:
  - role: docker
```

Evidence: running `playbooks/deploy.yml` executes `docker` tasks before `web_app` tasks automatically.

### 3.4 Compose deployment implementation

Updated: `roles/web_app/tasks/main.yml`

Main flow:

1. Optionally login to Docker Hub (vault-backed vars)
2. Create compose project directory
3. Template `docker-compose.yml`
4. Pull image
5. Deploy with `community.docker.docker_compose_v2`
6. Wait for port and verify `/health`

Added migration guard:

- Detect/remove legacy non-compose container with same name before first compose up.

### 3.5 Idempotency evidence

First run:

```text
PLAY RECAP
lab04-local : ok=17 changed=3 failed=0 skipped=8 rescued=0
```

Second run:

```text
PLAY RECAP
lab04-local : ok=17 changed=0 failed=0 skipped=8 rescued=0
```

### 3.6 Runtime verification evidence

```text
docker ps
devops-app   lanebo1/devops-info-service:latest   Up ...   0.0.0.0:5000->5000/tcp
```

```json
GET /health -> {"status":"healthy", ...}
GET / -> {"service":{"name":"devops-info-service",...}, ...}
```

### 3.7 Task 2 research answers

1. `restart: always` restarts even after manual stop (after daemon restart), while `unless-stopped` restarts unless the container was intentionally stopped by operator.
2. Compose networks are project-scoped, named, and lifecycle-managed by Compose; plain bridge networks are generic Docker networking primitives created/managed manually.
3. Yes, Vault variables can be used directly in Jinja2 templates after decryption during playbook runtime.

---

## 4. Task 3 - Wipe Logic (1 pt)

### 4.1 Implementation

Created: `roles/web_app/tasks/wipe.yml`  
Included from: `roles/web_app/tasks/main.yml` (before deployment block)  
Default variable: `web_app_wipe: false` in `roles/web_app/defaults/main.yml`

Safety design:

- Variable gate: `when: web_app_wipe | bool`
- Tag gate: `tags: [web_app_wipe]`
- No use of `never` tag

Wipe actions:

1. Compose down (`state: absent`)
2. Remove compose file
3. Remove app directory
4. Optional image remove (`web_app_remove_image_on_wipe`)
5. Log wipe completion

### 4.2 Scenario evidence

Scenario 1: normal deploy (wipe should not run)

```text
PLAY RECAP
lab04-local : ok=17 changed=0 failed=0 skipped=8 rescued=0
```

Scenario 2: wipe only

Command:

`ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe`

Result:

```text
PLAY RECAP
lab04-local : ok=6 changed=3 failed=0 skipped=1 rescued=0
```

Verification:

```text
docker ps
NAMES IMAGE STATUS
(no app container)
ls: cannot access '/opt/devops-app': No such file or directory
```

Scenario 3: clean reinstall (wipe -> deploy)

Command:

`ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"`

Result:

```text
PLAY RECAP
lab04-local : ok=21 changed=6 failed=0 skipped=4 rescued=0
```

Scenario 4a: tag only, variable false (wipe blocked)

Command:

`ansible-playbook playbooks/deploy.yml --tags web_app_wipe`

Result:

```text
PLAY RECAP
lab04-local : ok=2 changed=0 failed=0 skipped=5 rescued=0
```

Verification after Scenario 4a:

```text
docker ps
devops-app Up ...
curl /health -> {"status":"healthy", ...}
```

### 4.3 Task 3 research answers

1. Variable + tag gives double protection: accidental variable set or accidental tag use alone is not enough to destroy by default.
2. `never` is a hard opt-in tag control; this approach is more explicit for clean-reinstall flows because variable state still controls behavior in normal runs.
3. Wipe must run first to support deterministic clean reinstall (`remove old state -> apply desired state`).
4. Clean reinstall is preferred for drifted/broken state or major config migration; rolling update is preferred for minimal downtime and stable state transitions.
5. Extend with conditional tasks for named volumes (`docker volume rm`) and image prune/remove operations behind separate safety variables.

---

## 5. Task 4 - CI/CD with GitHub Actions (3 pts)

### 5.1 Workflow implemented

Created: `.github/workflows/ansible-deploy.yml`

Jobs:

1. `lint`
   - runs on `self-hosted` runner
   - installs Ansible + ansible-lint
   - installs required collections
   - runs `ansible-lint` for playbooks/tasks
2. `deploy`
   - runs on `self-hosted` runner
   - runs only on `push` and when `ANSIBLE_VAULT_PASSWORD` secret is present
   - optionally configures SSH key from secret (if provided)
   - decrypts Vault password from secret
   - runs `ansible-playbook playbooks/deploy.yml` using repository inventory (`inventory/hosts.ini`)
   - verifies `/health` and `/` via Ansible `uri` module on target host

Path filters:

- include `ansible/**`
- exclude `ansible/docs/**`
- include workflow file itself

### 5.2 Secrets model

Configured workflow to use:

- `ANSIBLE_VAULT_PASSWORD`
- `VM_SUDO_PASSWORD` (optional, passed as `ANSIBLE_BECOME_PASS`)
- `SSH_PRIVATE_KEY` (optional fallback if runner user does not already have the key from inventory path)

Not required in self-hosted mode:

- `VM_HOST`
- `VM_USER`
- `APP_PORT`

### 5.3 Local CI-equivalent validation

Local lint run (venv):

```text
Passed: 0 failure(s), 0 warning(s) in 13 files processed of 13 encountered.
```

Local deploy verification:

```text
ansible-playbook playbooks/deploy.yml
PLAY RECAP ... failed=0
ansible webservers -m ansible.builtin.uri -a "url=http://127.0.0.1:5000/health status_code=200"
```

` Note: While creating self-hosted runner I ran into errors: `

```
Http response code: BadGateway from 'POST https://api.github.com/actions/runner-registration' (Request Id: BC32:7406F:...)
{
  "message": "Server Error"
}

Response status code does not indicate success: 502 (Bad Gateway). 
```
` I could not configure local self-hosted runner. But: all secret variables, pipelines and configs are presnt and will function complete when running. `

### 5.4 Task 4 research answers

1. SSH keys in GitHub Secrets are encrypted at rest, but compromise of repo/admin access or workflow injection can expose them; use least privilege, short-lived keys, and environment protections.
2. Use separate inventories/environments with staged jobs: `lint -> deploy-staging -> tests -> manual approval -> deploy-prod`.
3. Add rollback via immutable image tags, saved previous release vars, and a dedicated rollback job/playbook.
4. Self-hosted runner can improve security if isolated in private network and hardened; however it also increases operator responsibility (patching, credential hygiene, host hardening).

---

## 6. Testing Results Summary

- `--tags` and `--skip-tags` behavior verified on `provision.yml`
- Rescue paths verified in both `common` and `docker` roles (`rescued=1`)
- Compose migration verified with running service and endpoint checks
- Idempotency verified (`deploy` second run: `changed=0`)
- Wipe logic verified for all 4 required scenarios
- Local ansible-lint verified as passing

---

## 7. Challenges & Solutions

1. VirtualBox start failure: `VERR_SVM_IN_USE`
   - Cause: active KVM modules
   - Fix: stop KVM/libvirt services, unload `kvm_amd`/`kvm`, then start VM

2. Compose migration conflict (`container name already in use`)
   - Cause: existing Lab 5 standalone container `devops-app`
   - Fix: added migration task to detect/remove legacy non-compose container before compose up

3. `ansible-lint` install on distro-managed Python failed (PEP 668)
   - Fix: used dedicated venv at `/tmp/lab06-venv`

---
