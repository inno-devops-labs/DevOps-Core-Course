# Lab 5 — Ansible Fundamentals — Documentation

## 1. Architecture Overview

- **Ansible version:** 2.16+ (verify with `ansible --version`)
- **Target VM:** Ubuntu 24.04 LTS, created by Terraform (Lab 4) on AWS EC2
- **Role structure:**
  - `common` — base system (apt cache, packages, timezone)
  - `docker` — Docker CE install, service, user in docker group
  - `app_deploy` — Docker Hub login, pull image, run container, health check

Roles are used instead of monolithic playbooks to keep tasks reusable, testable, and easy to maintain. Each role has a single responsibility and can be shared or reused across playbooks (e.g. `provision.yml` vs `deploy.yml`).

---

## 2. Roles Documentation

### common
- **Purpose:** Update apt cache, install common packages (python3-pip, curl, git, vim, htop, etc.), set timezone.
- **Variables:** `common_packages` (list), `common_timezone` (default: UTC).
- **Handlers:** None.
- **Dependencies:** None. Uses `community.general.timezone` (install collections from `requirements.yml`).

### docker
- **Purpose:** Install Docker CE from official repo (GPG key, repo, packages), ensure service is running and enabled, add remote user to docker group, install python3-docker for Ansible docker modules.
- **Variables:** `docker_apt_release_channel` (stable), `docker_users` (optional list).
- **Handlers:** `restart docker` — restarts Docker service (notified when repo/key/packages change).
- **Dependencies:** None. Assumes `common` has run (apt available).

### app_deploy
- **Purpose:** Log in to Docker Hub (vaulted credentials), pull image, stop/remove existing container, run new container with port mapping and restart policy, wait for port, verify `/health`.
- **Variables:** From vault/group_vars: `dockerhub_username`, `dockerhub_password`, `app_name`, `docker_image`, `docker_image_tag`, `app_port`, `app_container_name`, `app_restart_policy`, `app_env`. Defaults: `app_port` 5000, `app_restart_policy` unless-stopped.
- **Handlers:** `restart app container` — restarts the app container.
- **Dependencies:** Requires `docker` role (Docker installed and user in docker group).

---

## 3. Idempotency Demonstration

- **First run:** Many tasks show **changed** (yellow): apt update, package installs, Docker repo/key/packages, service start, user group, container create.
- **Second run:** Same playbook should show **ok** (green) for almost all tasks and **0 changed**. This shows idempotency: state is already as desired.

Tasks are idempotent because:
- `apt` uses `state: present` (no change if already installed).
- `service` uses `state: started` and `enabled: yes` (no change if already running).
- `docker_container` uses `state: started` with same image/ports; Ansible compares desired vs current.
- `docker_image` with `source: pull` only pulls if the image is missing or different.

**First run** (excerpt): `changed=9` — apt update, common packages, timezone, Docker GPG/repo/packages, docker group, python3-docker, handler restart docker.

**Second run** (excerpt): `changed=0` — all tasks reported `ok`; no handler fired. This confirms idempotency.

---

## 4. Ansible Vault Usage

- **Storage:** Sensitive data (Docker Hub username/password, app overrides) are in `group_vars/all.yml`, encrypted with `ansible-vault create group_vars/all.yml` (or `ansible-vault encrypt group_vars/all.yml`).
- **Password:** The committed `group_vars/all.yml` is encrypted. Run `ansible-vault edit group_vars/all.yml` to replace placeholder credentials with your Docker Hub username and access token, then run playbooks with `--ask-vault-pass`. Optionally use a password file (e.g. `.vault_pass`) and `--vault-password-file`; do not commit the password file (it is in `.gitignore`).
- **Example:** Encrypted file starts with `$ANSIBLE_VAULT;1.1;AES256...`. Verify with: `ansible-vault view group_vars/all.yml`.
- **Why:** Credentials stay in repo without being stored in plain text; only someone with the vault password can run plays that need them.

---

## 5. Deployment Verification

After running `ansible-playbook playbooks/deploy.yml --ask-vault-pass` (or `--vault-password-file`):

### VM and endpoints

| Host      | Ansible host  | VM public IP     |
|-----------|---------------|-------------------|
| lab04-vm  | webservers    | **54.204.251.43** |

### Container status (`ansible webservers -a "docker ps"`)

```
CONTAINER ID   IMAGE                                         COMMAND           CREATED         STATUS         PORTS                    NAMES
72c2984ba62a   pickpusha/devops-info-service-python:latest   "python app.py"   ...             Up 8 minutes   0.0.0.0:5000->5000/tcp   devops-info-service-python
```

### Endpoint responses

**Health — `GET http://54.204.251.43:5000/health`**

```json
{"status":"healthy","timestamp":"2026-02-24T12:00:40.060Z","uptime_seconds":503}
```

**Root — `GET http://54.204.251.43:5000/`**

```json
{
  "endpoints": [
    {"description": "Service information", "method": "GET", "path": "/"},
    {"description": "Health check", "method": "GET", "path": "/health"}
  ],
  "request": {
    "client_ip": "31.58.137.228",
    "method": "GET",
    "path": "/",
    "user_agent": "curl/8.5.0"
  },
  "runtime": {
    "current_time": "2026-02-24T12:00:41.796Z",
    "timezone": "UTC",
    "uptime_human": "0 hours, 8 minutes",
    "uptime_seconds": 505
  },
  "service": {
    "description": "DevOps course info service",
    "framework": "Flask",
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "system": {
    "architecture": "x86_64",
    "cpu_count": 1,
    "hostname": "72c2984ba62a",
    "platform": "Linux",
    "platform_version": "Linux-6.17.0-1007-aws-x86_64-with-glibc2.41",
    "python_version": "3.13.12"
  }
}
```

- **Deploy playbook:** Completed successfully — Docker login, image pull, container run, wait_for port, and health check all succeeded. Handler "restart app container" ran.
- **Health check (playbook):** `Health check OK: {'status': 'healthy', 'timestamp': '...', 'uptime_seconds': ...}`

---

## 6. Key Decisions

- **Why roles instead of plain playbooks?** Roles group related tasks, defaults, and handlers into reusable units, making playbooks short and clear and allowing the same role to be used in multiple playbooks (e.g. provision vs full site).
- **How do roles improve reusability?** The same role can be applied to different hosts or playbooks; variables in `defaults/` and `group_vars` allow customization without changing the role code.
- **What makes a task idempotent?** Using declarative modules (`apt`, `service`, `docker_container`, `file`) with a desired state so that re-running the task leaves the system unchanged when already in that state.
- **How do handlers improve efficiency?** Handlers run once at the end of the play when notified, so multiple tasks can notify “restart docker” without restarting Docker more than once.
- **Why is Ansible Vault necessary?** To store secrets (e.g. Docker Hub credentials) in the same repo as playbooks without exposing them in plain text, so automation remains safe and auditable.

---

## 7. Challenges

- Group vars loading: Ansible loads `group_vars` from next to the inventory file, so `inventory/group_vars/all.yml` is used when inventory is `inventory/hosts.ini`; the same encrypted content is kept in `group_vars/all.yml` for consistency.
- Vault credentials: Docker Hub credentials are read from `docker-creds` (local, in `.gitignore`) and encrypted into the vault so playbooks can run without committing secrets.

---

