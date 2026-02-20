# Lab 05 — Ansible Fundamentals

## 1. Architecture Overview

**Ansible version:** 2.16+  
**Target VM:** Ubuntu 22.04 LTS (local VirtualBox VM from Lab 04, created via Pulumi)  
**Connection:** SSH via NAT port forwarding (`127.0.0.1:2223`, user `vagrant`)

### Role Structure

```
ansible/
├── ansible.cfg                # Ansible configuration
├── inventory/
│   └── hosts.ini              # Static inventory (VM connection details)
├── roles/
│   ├── common/                # System setup: apt update, essential packages
│   │   ├── tasks/main.yml
│   │   └── defaults/main.yml
│   ├── docker/                # Docker CE installation and configuration
│   │   ├── tasks/main.yml
│   │   ├── handlers/main.yml
│   │   └── defaults/main.yml
│   └── app_deploy/            # Application deployment via Docker
│       ├── tasks/main.yml
│       ├── handlers/main.yml
│       └── defaults/main.yml
├── playbooks/
│   ├── site.yml               # Master playbook (provision + deploy)
│   ├── provision.yml          # System provisioning (common + docker)
│   └── deploy.yml             # App deployment
├── group_vars/
│   └── all.yml                # Encrypted variables (Ansible Vault)
└── docs/
    └── LAB05.md               # This documentation
```

**Why roles instead of monolithic playbooks?**  
Roles provide reusability, modularity, and clear separation of concerns. Each role handles one specific responsibility (system setup, Docker, app deploy) and can be tested or reused independently.

---

## 2. Roles Documentation

### Role: `common`

- **Purpose:** Update apt cache and install essential system packages.
- **Variables:** `common_packages` — list of packages to install (python3-pip, curl, git, vim, htop, etc.).
- **Handlers:** None.
- **Dependencies:** None.

### Role: `docker`

- **Purpose:** Install Docker CE from the official repository, enable the service, and add user to the docker group.
- **Variables:** `docker_user` — user to add to the docker group (default: `vagrant`).
- **Handlers:** `restart docker` — triggered when Docker packages are installed or configuration changes.
- **Dependencies:** None (but should run after `common`).

### Role: `app_deploy`

- **Purpose:** Pull and run the Python application container from Docker Hub.
- **Variables:** `app_port`, `app_restart_policy` (defaults), plus vaulted variables: `dockerhub_username`, `dockerhub_password`, `docker_image`, `docker_image_tag`, `app_container_name`.
- **Handlers:** `restart app container` — restarts the application container if needed.
- **Dependencies:** Requires Docker to be installed (role `docker`).

---

## 3. Idempotency Demonstration

### First Run (`ansible-playbook playbooks/provision.yml`)

```
PLAY [Provision web servers] **************************************************

TASK [Gathering Facts] ********************************************************
ok: [myvm]

TASK [common : Update apt cache] **********************************************
changed: [myvm]

TASK [common : Install common packages] ***************************************
changed: [myvm]

TASK [docker : Add Docker GPG key] ********************************************
changed: [myvm]

TASK [docker : Add Docker repository] *****************************************
changed: [myvm]

TASK [docker : Install Docker CE packages] ************************************
changed: [myvm]

TASK [docker : Ensure Docker service is started and enabled] ******************
ok: [myvm]

TASK [docker : Add vagrant user to docker group] ******************************
ok: [myvm]

TASK [docker : Install python3-docker] ****************************************
ok: [myvm]

RUNNING HANDLER [docker : restart docker] *************************************
changed: [myvm]

PLAY RECAP ********************************************************************
myvm         : ok=12   changed=4    unreachable=0    failed=0    skipped=0
```

Many tasks show **"changed"** (yellow) — packages installed, Docker repo added, service started.

### Second Run (`ansible-playbook playbooks/provision.yml`)

```
PLAY [Provision web servers] **************************************************

TASK [Gathering Facts] ********************************************************
ok: [myvm]

TASK [common : Update apt cache] **********************************************
ok: [myvm]

TASK [common : Install common packages] ***************************************
ok: [myvm]

TASK [docker : Add Docker GPG key] ********************************************
ok: [myvm]

TASK [docker : Add Docker repository] *****************************************
ok: [myvm]

TASK [docker : Install Docker CE packages] ************************************
ok: [myvm]

TASK [docker : Ensure Docker service is started and enabled] ******************
ok: [myvm]

TASK [docker : Add vagrant user to docker group] ******************************
ok: [myvm]

TASK [docker : Install python3-docker] ****************************************
ok: [myvm]

PLAY RECAP ********************************************************************
myvm         : ok=11   changed=0    unreachable=0    failed=0    skipped=0
```

All tasks show **"ok"** (green), zero "changed". This proves idempotency.

### Analysis

- **First run:** apt cache updated, packages installed, Docker GPG key added, Docker repo configured, Docker service started, user added to docker group — all new changes.
- **Second run:** All desired states already achieved. Ansible detects no drift, makes no changes.
- **What makes roles idempotent:** Using declarative modules like `apt: state=present`, `service: state=started`, `user: groups=docker append=yes` — they check current state before acting.

---

## 4. Ansible Vault Usage

Credentials are stored in `group_vars/all.yml`, encrypted with Ansible Vault.

**How credentials are stored:** The file contains DockerHub username and access token, encrypted at rest.

**Vault password management:** Password is entered interactively via `--ask-vault-pass`, or stored in `.vault_pass` (excluded from git via `.gitignore`).

**Encrypted file example:**
```
$ANSIBLE_VAULT;1.1;AES256
31396664316237616632386465333739343530653266616435656233653337656365656164346233
3632633136386562653139376639393739313962626461620a633563366631343438633739653732
...
```

**Why Ansible Vault is important:** It prevents plaintext secrets from being committed to version control. Credentials remain encrypted and are only decrypted in memory during playbook execution.

---

## 5. Deployment Verification

### Deploy Run (`ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass`)

```
PLAY [Deploy application] *****************************************************

TASK [Gathering Facts] ********************************************************
ok: [myvm]

TASK [app_deploy : Log in to Docker Hub] **************************************
changed: [myvm]

TASK [app_deploy : Pull Docker image] *****************************************
changed: [myvm]

TASK [app_deploy : Remove old container (if exists)] **************************
ok: [myvm]

TASK [app_deploy : Run application container] *********************************
changed: [myvm]

TASK [app_deploy : Wait for application to be ready] **************************
ok: [myvm]

TASK [app_deploy : Verify health endpoint] ************************************
ok: [myvm]

TASK [app_deploy : Show health check result] **********************************
ok: [myvm] => {
    "health_result.json": {
        "status": "healthy",
        "timestamp": "2026-02-20T20:14:30.313Z",
        "uptime_seconds": 3
    }
}

PLAY RECAP ********************************************************************
myvm         : ok=8    changed=3    unreachable=0    failed=0    skipped=0
```

### Container Status (`docker ps`)

```
CONTAINER ID   IMAGE                                         COMMAND          CREATED         STATUS         PORTS                    NAMES
4fdc191f5d76   vladimirzhidkov/devops-info-service:latest   "python app.py"  4 minutes ago   Up 4 minutes   0.0.0.0:5000->5000/tcp   devops-info-service
```

### Health Check

```
$ curl http://localhost:5000/health
{"status":"healthy","timestamp":"2026-02-20T20:18:43.889Z","uptime_seconds":257}
```

---

## 6. Key Decisions

- **Why use roles instead of plain playbooks?**  
  Roles separate concerns, making each component independently testable and reusable across projects.

- **How do roles improve reusability?**  
  A role like `docker` can be dropped into any project that needs Docker. Variables in `defaults/` allow customization without modifying role code.

- **What makes a task idempotent?**  
  Using declarative state-based modules (`state: present`, `state: started`) instead of imperative commands. Ansible checks current state before making changes.

- **How do handlers improve efficiency?**  
  Handlers only run when notified by a changed task, and only once at the end of the play. This prevents unnecessary service restarts.

- **Why is Ansible Vault necessary?**  
  Secrets (passwords, tokens) must not be stored in plaintext in version control. Vault encrypts them, allowing safe commits while keeping secrets accessible during execution.

---

## 7. Challenges

- Ansible does not run natively on Windows — used WSL2 as the control node.
- VM uses password-based SSH — required `sshpass` package and `ansible_password` in inventory.
- NAT port forwarding means using `127.0.0.1:2223` instead of a direct IP.
