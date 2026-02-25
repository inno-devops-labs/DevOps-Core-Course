# Lab 5 — Ansible Fundamentals

## 1. Architecture Overview

- **Ansible version:** 2.20.2 (ansible-core)
- **Target VM OS:** Ubuntu 24.04.3 LTS (AWS EC2)
- **Connection:** SSH with key-based authentication

### Role Structure

```
ansible/
├── inventory/
│   └── hosts.ini
├── roles/
│   ├── common/          # System packages and timezone
│   │   ├── tasks/main.yml
│   │   └── defaults/main.yml
│   ├── docker/          # Docker CE installation
│   │   ├── tasks/main.yml
│   │   ├── handlers/main.yml
│   │   └── defaults/main.yml
│   └── app_deploy/      # Application container deployment
│       ├── tasks/main.yml
│       ├── handlers/main.yml
│       └── defaults/main.yml
├── playbooks/
│   ├── site.yml
│   ├── provision.yml
│   └── deploy.yml
├── group_vars/
│   └── all.yml          # Encrypted with Ansible Vault
└── ansible.cfg
```

### Why Roles Instead of Monolithic Playbooks?

Roles separate concerns into reusable, testable units. The `common` role can be reused across any project, the `docker` role is independent of the application being deployed, and `app_deploy` handles only application-specific logic. This modularity makes it easy to maintain, share, and compose different configurations.

---

## 2. Roles Documentation

### Common Role

- **Purpose:** Installs essential system packages and sets the timezone.
- **Variables:**
  - `common_packages` — list of apt packages to install (default: python3-pip, curl, git, vim, htop, wget, unzip, ca-certificates, gnupg, lsb-release)
  - `timezone` — system timezone (default: UTC)
- **Handlers:** None
- **Dependencies:** None

### Docker Role

- **Purpose:** Installs Docker CE from the official Docker repository.
- **Variables:**
  - `docker_user` — user to add to the docker group (default: ubuntu)
  - `docker_packages` — Docker packages to install (default: docker-ce, docker-ce-cli, containerd.io, docker-buildx-plugin)
- **Handlers:**
  - `restart docker` — restarts the Docker daemon when Docker packages are installed or configuration changes
- **Dependencies:** None (but expects `common` role to have run first for prerequisite packages)

### App Deploy Role

- **Purpose:** Pulls and runs the containerized Python application from Docker Hub.
- **Variables:**
  - `app_name` — application name (default: devops-app)
  - `app_port` — host port mapping (default: 5000)
  - `docker_image` — Docker image name (default: elinanotelina/devops-info-service)
  - `docker_image_tag` — image tag (default: latest)
  - `app_restart_policy` — container restart policy (default: unless-stopped)
  - `app_env` — environment variables for the container (default: {})
- **Handlers:**
  - `restart app container` — restarts the application container
- **Dependencies:** Requires Docker to be installed (docker role)

---

## 3. Idempotency Demonstration

### First Run Output

```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [aws-vm]

TASK [common : Update apt cache] ***********************************************
changed: [aws-vm]

TASK [common : Install common packages] ****************************************
changed: [aws-vm]

TASK [common : Set timezone] ***************************************************
changed: [aws-vm]

TASK [docker : Install prerequisites for Docker repository] ********************
ok: [aws-vm]

TASK [docker : Create keyrings directory] **************************************
ok: [aws-vm]

TASK [docker : Add Docker GPG key] *********************************************
changed: [aws-vm]

TASK [docker : Add Docker repository] ******************************************
changed: [aws-vm]

TASK [docker : Install Docker packages] ****************************************
changed: [aws-vm]

TASK [docker : Ensure Docker service is running and enabled] *******************
ok: [aws-vm]

TASK [docker : Add user to docker group] ***************************************
changed: [aws-vm]

TASK [docker : Install python3-docker for Ansible docker modules] **************
changed: [aws-vm]

RUNNING HANDLER [docker : restart docker] **************************************
changed: [aws-vm]

PLAY RECAP *********************************************************************
aws-vm                     : ok=13   changed=9    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Second Run Output

```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [aws-vm]

TASK [common : Update apt cache] ***********************************************
ok: [aws-vm]

TASK [common : Install common packages] ****************************************
ok: [aws-vm]

TASK [common : Set timezone] ***************************************************
ok: [aws-vm]

TASK [docker : Install prerequisites for Docker repository] ********************
ok: [aws-vm]

TASK [docker : Create keyrings directory] **************************************
ok: [aws-vm]

TASK [docker : Add Docker GPG key] *********************************************
ok: [aws-vm]

TASK [docker : Add Docker repository] ******************************************
ok: [aws-vm]

TASK [docker : Install Docker packages] ****************************************
ok: [aws-vm]

TASK [docker : Ensure Docker service is running and enabled] *******************
ok: [aws-vm]

TASK [docker : Add user to docker group] ***************************************
ok: [aws-vm]

TASK [docker : Install python3-docker for Ansible docker modules] **************
ok: [aws-vm]

PLAY RECAP *********************************************************************
aws-vm                     : ok=12   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Analysis

- **First run:** 9 tasks changed — apt cache was updated, packages installed, Docker GPG key added, repository configured, Docker installed, user added to docker group, and the `restart docker` handler fired because Docker packages were newly installed.
- **Second run:** 0 tasks changed — all tasks returned `ok` because the desired state was already achieved. The handler did not fire because no task triggered a `notify`. The `cache_valid_time: 3600` on the apt cache update prevents unnecessary cache refreshes.

### What Makes These Roles Idempotent?

All tasks use declarative state modules (`apt: state=present`, `service: state=started`, `file: state=directory`, `user: groups=docker append=yes`). These modules check the current state before acting and only make changes when needed.

---

## 4. Ansible Vault Usage

### How Credentials Are Stored

Sensitive data (Docker Hub credentials, app configuration) is stored in `group_vars/all.yml`, encrypted with Ansible Vault. The file is encrypted at rest and only decrypted in memory during playbook execution.

### Vault Password Management

A `.vault_pass` file contains the vault password and is referenced in `ansible.cfg`. This file is added to `.gitignore` and never committed to version control.

### Encrypted File Example

```
$ANSIBLE_VAULT;1.1;AES256
30303930326332383735363663393363383162623835643264616131323662336131353032353634
3261653835363663383239353864313132393136636262340a343735646631386463313663663663
...
```

### Why Ansible Vault Is Important

Without Vault, credentials would be stored in plaintext in the repository, exposing Docker Hub tokens and other secrets. Vault encrypts these with AES-256, allowing the encrypted file to be safely committed while keeping secrets secure. Tasks that use credentials also use `no_log: true` to prevent them from appearing in Ansible output.

---

## 5. Deployment Verification

### Deployment Output

```
PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [aws-vm]

TASK [app_deploy : Log in to Docker Hub] ***************************************
fatal: [aws-vm]: FAILED! => {"censored": "...no_log..."}
...ignoring

TASK [app_deploy : Pull Docker image] ******************************************
changed: [aws-vm]

TASK [app_deploy : Stop and remove existing container] *************************
ok: [aws-vm]

TASK [app_deploy : Run application container] **********************************
changed: [aws-vm]

TASK [app_deploy : Wait for application to be ready] ***************************
ok: [aws-vm]

TASK [app_deploy : Verify health endpoint] *************************************
ok: [aws-vm]

TASK [app_deploy : Display health check result] ********************************
ok: [aws-vm] => {
    "health_check.json": {
        "status": "healthy",
        "timestamp": "2026-02-25T17:45:47.291125+00:00",
        "uptime_seconds": 13
    }
}

RUNNING HANDLER [app_deploy : restart app container] ***************************
changed: [aws-vm]

PLAY RECAP *********************************************************************
aws-vm                     : ok=9    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=1
```

### Container Status

```
CONTAINER ID   IMAGE                                      COMMAND                  CREATED          STATUS          PORTS                    NAMES
1086b9457b92   elinanotelina/devops-info-service:latest   "uvicorn app:app --h…"   36 seconds ago   Up 13 seconds   0.0.0.0:5000->5000/tcp   devops-app
```

### Health Check

```json
{
    "status": "healthy",
    "timestamp": "2026-02-25T17:45:47.291125+00:00",
    "uptime_seconds": 13
}
```

### Handler Execution

The `restart app container` handler was triggered by the "Run application container" task since a new container was created.

---

## 6. Key Decisions

**Why use roles instead of plain playbooks?**
Roles enforce a standard directory structure and separate concerns. Each role is self-contained with its own tasks, handlers, defaults, and can be independently developed, tested, and reused across projects.

**How do roles improve reusability?**
The `docker` role can be dropped into any project that needs Docker installed. The `common` role provides a baseline for any Ubuntu server. Roles can be shared via Ansible Galaxy and versioned independently.

**What makes a task idempotent?**
A task is idempotent when it checks the current state before acting. Using declarative modules like `apt: state=present` (not shell commands like `apt install`) ensures Ansible only makes changes when the desired state differs from the current state.

**How do handlers improve efficiency?**
Handlers only run when notified by a changed task, and they run once at the end of the play even if notified multiple times. This avoids unnecessary service restarts — Docker is only restarted when packages actually change, not on every playbook run.

**Why is Ansible Vault necessary?**
Secrets like Docker Hub tokens must not be stored in plaintext in version control. Vault provides AES-256 encryption, allowing encrypted files to be committed safely while keeping credentials secure at rest.

---

## 7. Challenges

- Docker repository task initially used deprecated `ansible_distribution_release` top-level fact variable; fixed to use `ansible_facts['distribution_release']`
- `group_vars` needed to be linked into the `inventory/` directory for Ansible to auto-load the encrypted variables
- Docker Hub login fails with placeholder token but image is public, so `ignore_errors: yes` was used to allow the pull to proceed
