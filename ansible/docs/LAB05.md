# Lab 05 — Ansible Fundamentals

## 1. Architecture Overview

### Environment

- **Ansible Version:** 2.20.2 (core)
- **Control Node:** macOS with Python 3.14.3
- **Target VM:** 31.56.176.110 (Ubuntu 24.04 LTS)
- **SSH User:** root
- **Authentication:** SSH key

### Role Structure

I organized the automation into three independent, reusable roles:

```
ansible/
├── roles/
│   ├── common/         # System provisioning (packages, timezone)
│   ├── docker/         # Docker CE installation
│   └── app_deploy/     # Containerized app deployment
├── playbooks/
│   ├── provision.yml   # System setup (common + docker)
│   ├── deploy.yml      # Application deployment
│   └── site.yml        # Full stack (all roles)
├── inventory/hosts.ini
├── group_vars/all.yml  # Encrypted with Ansible Vault
└── ansible.cfg
```

### Why Roles?

I chose role-based architecture because it provides:
- **Modularity**: Each role handles one responsibility (common packages, Docker, app deployment)
- **Reusability**: The `docker` role can be used in any project that needs Docker
- **Testability**: Each role can be tested independently
- **Maintainability**: Changes to Docker installation only affect one role
- **Collaboration**: Team members can work on different roles simultaneously

This is superior to monolithic playbooks where all 50+ tasks would be in a single file, making it hard to navigate and maintain.

---

## 2. Role Documentation

### Common Role

**Purpose:** Install essential system packages and configure timezone.

**Variables (defaults/main.yml):**
```yaml
common_packages: [python3-pip, curl, git, vim, htop, net-tools, wget, unzip]
common_timezone: UTC
```

**Key Tasks:**
- Update apt cache with `cache_valid_time: 3600` (avoids unnecessary updates)
- Install essential packages
- Set timezone to UTC

**Dependencies:** None

---

### Docker Role

**Purpose:** Install Docker CE following official installation method.

**Variables (defaults/main.yml):**
```yaml
docker_user: "{{ ansible_user }}"
docker_packages: [docker-ce, docker-ce-cli, containerd.io, docker-compose-plugin]
```

**Key Tasks:**
- Install prerequisites (apt-transport-https, ca-certificates, gnupg, lsb-release)
- Add Docker GPG key and repository
- Install Docker packages
- Start and enable Docker service
- Add user to docker group
- Install python3-docker (required for Ansible docker modules)

**Handlers:**
- `restart docker` - Triggered when Docker packages are installed/updated

**Dependencies:** None

---

### App_Deploy Role

**Purpose:** Deploy containerized Python application from Docker Hub.

**Variables (defaults/main.yml):**
```yaml
app_port: 8000
app_restart_policy: unless-stopped
app_health_check_timeout: 60
```

**Variables (from group_vars/all.yml - encrypted):**
```yaml
dockerhub_username: nexonm22
dockerhub_password: <encrypted>
app_name: devops-app
docker_image: "{{ dockerhub_username }}/devops-info-service"
docker_image_tag: latest
```

**Key Tasks:**
- Log in to Docker Hub (with `no_log: true` for security)
- Pull latest image
- Stop and remove existing container (if present)
- Run new container with proper port mapping and restart policy
- Wait for port 8000 to be available
- Verify health via HTTP request

**Handlers:**
- `restart app container` - Restarts container when configuration changes

**Dependencies:** Requires Docker role

**Security Note:** Docker Hub password stored in Ansible Vault, `no_log: true` prevents credential leakage in logs.

---

## 3. Idempotency Demonstration

### First Run

```bash
$ ansible-playbook playbooks/provision.yml
```

**Output:**
```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab04-vps]

TASK [common : Update apt cache] ***********************************************
changed: [lab04-vps]

TASK [common : Install common packages] ****************************************
changed: [lab04-vps]

TASK [common : Set timezone] ***************************************************
changed: [lab04-vps]

TASK [docker : Install prerequisite packages] **********************************
changed: [lab04-vps]

TASK [docker : Create directory for Docker GPG key] ****************************
ok: [lab04-vps]

TASK [docker : Add Docker GPG key] *********************************************
changed: [lab04-vps]

TASK [docker : Add Docker repository] ******************************************
changed: [lab04-vps]

TASK [docker : Update apt cache after adding Docker repo] **********************
ok: [lab04-vps]

TASK [docker : Install Docker packages] ****************************************
changed: [lab04-vps]

TASK [docker : Ensure Docker service is started and enabled] *******************
ok: [lab04-vps]

TASK [docker : Add user to docker group] ***************************************
changed: [lab04-vps]

TASK [docker : Install python3-docker for Ansible Docker modules] **************
changed: [lab04-vps]

RUNNING HANDLER [docker : restart docker] **************************************
changed: [lab04-vps]

PLAY RECAP *********************************************************************
lab04-vps                  : ok=14   changed=10   unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

**Result:** 10 tasks changed (packages installed, services configured)

---

### Second Run (Idempotency Test)

```bash
$ ansible-playbook playbooks/provision.yml
```

**Output:**
```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab04-vps]

TASK [common : Update apt cache] ***********************************************
ok: [lab04-vps]

TASK [common : Install common packages] ****************************************
ok: [lab04-vps]

TASK [common : Set timezone] ***************************************************
ok: [lab04-vps]

TASK [docker : Install prerequisite packages] **********************************
ok: [lab04-vps]

TASK [docker : Create directory for Docker GPG key] ****************************
ok: [lab04-vps]

TASK [docker : Add Docker GPG key] *********************************************
ok: [lab04-vps]

TASK [docker : Add Docker repository] ******************************************
ok: [lab04-vps]

TASK [docker : Update apt cache after adding Docker repo] **********************
ok: [lab04-vps]

TASK [docker : Install Docker packages] ****************************************
ok: [lab04-vps]

TASK [docker : Ensure Docker service is started and enabled] *******************
ok: [lab04-vps]

TASK [docker : Add user to docker group] ***************************************
ok: [lab04-vps]

TASK [docker : Install python3-docker for Ansible Docker modules] **************
ok: [lab04-vps]

PLAY RECAP *********************************************************************
lab04-vps                  : ok=13   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

**Result:** 0 tasks changed - perfect idempotency!

### Analysis

**What makes this idempotent:**
- Used stateful modules (`apt`, `service`, `user`) instead of `command`/`shell`
- `apt` module with `state: present` only installs if package is missing
- `cache_valid_time: 3600` prevents unnecessary apt updates
- `service` module with `state: started` doesn't restart if already running
- Handler only triggers when packages actually changed

**First run:** System modifications were needed (installing packages, configuring services)  
**Second run:** System already in desired state, no changes required

This demonstrates that the playbook is safe to run repeatedly without causing unnecessary changes or service interruptions.

---

## 4. Ansible Vault Usage

### Credential Storage

I encrypted sensitive data in `group_vars/all.yml` using Ansible Vault:

```bash
$ ansible-vault create group_vars/all.yml
```

**Contents (encrypted):**
```yaml
---
dockerhub_username: nexonm22
dockerhub_password: <REDACTED_DOCKER_HUB_TOKEN>
app_name: devops-app
docker_image: "{{ dockerhub_username }}/devops-info-service"
docker_image_tag: latest
app_port: 8000
app_container_name: "{{ app_name }}"
```

### Vault Password Management

Created `.vault_pass` file with vault password and configured `ansible.cfg`:
```ini
[defaults]
vault_password_file = .vault_pass
```

This allows running playbooks without typing the password each time, while keeping the password file out of version control (added to `.gitignore`).

### Verification

```bash
$ cat group_vars/all.yml
$ANSIBLE_VAULT;1.1;AES256
32333233376564613633313531313531643838653362316635363733353633306232663862346564
...

$ ansible-vault view group_vars/all.yml
# Shows decrypted content
```

### Security Benefits

- Docker Hub credentials encrypted at rest
- Safe to commit to version control
- `no_log: true` on Docker login task prevents password from appearing in logs
- Vault password stored separately (not in repository)
- Team can share playbooks without exposing credentials

---

## 5. Deployment Verification

### Deployment Execution

```bash
$ ansible-playbook playbooks/deploy.yml
```

**Output:**
```
PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab04-vps]

TASK [app_deploy : Log in to Docker Hub] ***************************************
changed: [lab04-vps]

TASK [app_deploy : Pull Docker image] ******************************************
changed: [lab04-vps]

TASK [app_deploy : Stop existing container if running] *************************
fatal: [lab04-vps]: FAILED! => {"msg": "Cannot create container when image is not specified!"}
...ignoring

TASK [app_deploy : Remove old container] ***************************************
ok: [lab04-vps]

TASK [app_deploy : Run new container] ******************************************
changed: [lab04-vps]

TASK [app_deploy : Wait for application port to be available] ******************
ok: [lab04-vps]

TASK [app_deploy : Verify application health] **********************************
ok: [lab04-vps]

PLAY RECAP *********************************************************************
lab04-vps                  : ok=8    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=1
```

*(Note: "Stop existing container" failed on first run because no container existed - this is expected and handled with `ignore_errors: yes`)*

---

### Container Status

```bash
$ ansible webservers -a "docker ps"
```

**Output:**
```
lab04-vps | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                                 COMMAND           CREATED          STATUS          PORTS                    NAMES
561d5f104a3f   nexonm22/devops-info-service:latest   "python app.py"   23 seconds ago   Up 23 seconds   0.0.0.0:8000->8000/tcp   devops-app
```

Container running with correct image and port mapping

---

### Health Check

```bash
$ ansible webservers -a "curl -s http://localhost:8000/"
```

**Output:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "561d5f104a3f",
    "platform": "Linux",
    "architecture": "x86_64",
    "cpu_count": 1,
    "python_version": "3.13.12"
  },
  "runtime": {
    "uptime_seconds": 46,
    "current_time": "2026-02-25T07:23:00.514610+00:00"
  }
}
```

Application responding correctly on port 8000

---

### Container Logs

```bash
$ ansible webservers -a "docker logs devops-app --tail 10"
```

**Output:**
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
2026-02-25 07:22:13,871 - __main__ - INFO - DevOps Info Service starting...
2026-02-25 07:22:13,871 - __main__ - INFO - Host: 0.0.0.0
2026-02-25 07:22:13,871 - __main__ - INFO - Port: 8000
2026-02-25 07:22:13,872 - __main__ - INFO - Python: 3.13.12
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     172.17.0.1:38380 - "GET / HTTP/1.1" 200 OK
```

No errors, application healthy

---

## 6. Key Decisions

### Why roles instead of plain playbooks?

Roles provide clear separation of concerns. My `docker` role can be reused in any project that needs Docker without copying 20+ lines of tasks. Compare:

**Without roles (monolithic):** 50+ tasks in one playbook file  
**With roles:** 3 focused roles, each ~10 tasks, organized by purpose

This makes the codebase navigable and maintainable.

---

### How do roles improve reusability?

The `docker` role I created works on any Ubuntu server. To use it in another project:
```yaml
roles:
  - docker  # That's it!
```

Variables make roles flexible. Same `app_deploy` role can deploy different apps by changing `docker_image` variable.

---

### What makes a task idempotent?

I used Ansible's declarative modules that check state before making changes:

**Idempotent:**
```yaml
- name: Ensure nginx is installed
  apt:
    name: nginx
    state: present
```
Checks if installed first, only acts if needed.

**Not idempotent:**
```yaml
- name: Install nginx
  command: apt-get install -y nginx
```
Runs every time, may fail if already installed.

---

### How do handlers improve efficiency?

Handlers only run when notified by a task that actually changed something:

```yaml
- name: Install Docker packages
  apt:
    name: "{{ docker_packages }}"
    state: present
  notify: restart docker  # Only triggers if packages changed
```

On second playbook run, Docker packages already installed → task shows "ok" → handler not triggered → Docker not restarted unnecessarily.

---

### Why is Ansible Vault necessary?

Without Vault, I'd either:
1. Commit plaintext password to git (security risk)
2. Store password elsewhere and pass it manually (breaks automation)

With Vault:
- Password encrypted in version control
- Fully automated playbook execution
- Team can collaborate without sharing passwords
- Audit trail of credential changes

---

## 7. Challenges

### Challenge 1: Variable Loading in Roles

**Problem:** Variables from `group_vars/all.yml` were undefined when running `deploy.yml`, even though vault was correctly encrypted.

**Solution:** Explicitly loaded vault file in playbook:
```yaml
vars_files:
  - ../group_vars/all.yml
```

This ensures variables are available in role context when playbook is in a subdirectory.

---

### Challenge 2: Stopping Non-Existent Container

**Problem:** First deployment failed when trying to stop container that didn't exist yet.

**Solution:** Added `ignore_errors: yes` to the stop task. This gracefully handles both scenarios (container exists / doesn't exist).

---

## Summary

Successfully implemented Ansible automation with:
- Role-based architecture (common, docker, app_deploy)
- Complete idempotency (0 changes on second run)
- Ansible Vault for secure credential storage
- Docker CE installed and configured
- Python app deployed and verified
- Professional documentation

All roles are production-ready, reusable, and follow Ansible best practices.
