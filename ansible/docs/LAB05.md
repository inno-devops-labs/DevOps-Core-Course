# Lab 5 — Ansible Fundamentals

## 1. Architecture Overview

- **Ansible version:** 2.16+
- **Target VM OS:** Ubuntu 24.04 LTS (Yandex Cloud VM from Lab 4)
- **Control node:** WSL2 / Linux workstation
- **VM name:** lab04-vm-6d1e
- **VM public IP:** 93.77.180.16
- **SSH connection:** ssh ubuntu@93.77.180.16

### Role Structure

```
ansible/
├── ansible.cfg                 # Ansible configuration
├── inventory/
│   └── hosts.ini               # Static inventory with VM IP
├── roles/
│   ├── common/                 # System essentials
│   │   ├── tasks/main.yml
│   │   └── defaults/main.yml
│   ├── docker/                 # Docker CE installation
│   │   ├── tasks/main.yml
│   │   ├── handlers/main.yml
│   │   └── defaults/main.yml
│   └── app_deploy/             # Application deployment
│       ├── tasks/main.yml
│       ├── handlers/main.yml
│       └── defaults/main.yml
├── playbooks/
│   ├── site.yml                # Full provisioning + deployment
│   ├── provision.yml           # System provisioning only
│   └── deploy.yml              # App deployment only
├── group_vars/
│   ├── all.yml                 # Encrypted variables (Vault)
│   └── all.yml.example         # Example variables (unencrypted)
└── docs/
    └── LAB05.md                # This documentation
```

### Why Roles Instead of Monolithic Playbooks?

Roles provide a standardized, modular structure for organizing Ansible code. Instead of one large playbook with all tasks mixed together, roles separate concerns:
- **common** handles base system packages — reusable on any project
- **docker** handles Docker installation — can be shared across teams
- **app_deploy** handles application-specific deployment — swappable per project

This modularity means each role can be tested, maintained, and reused independently.

---

## 2. Roles Documentation

### 2.1 Common Role

| Field | Value |
|-------|-------|
| **Purpose** | Install essential system packages and configure timezone |
| **Key Variables** | `common_packages` (list of apt packages), `common_timezone` (default: UTC) |
| **Handlers** | None |
| **Dependencies** | None |

**Tasks performed:**
1. Update apt cache (with 1-hour cache validity)
2. Install essential packages (python3-pip, curl, git, vim, htop, wget, etc.)
3. Set system timezone

### 2.2 Docker Role

| Field | Value |
|-------|-------|
| **Purpose** | Install Docker CE from official repository |
| **Key Variables** | `docker_user` (user to add to docker group), `docker_packages` (Docker packages list), `docker_python_packages` (Python Docker library) |
| **Handlers** | `restart docker` — restarts Docker daemon when configuration changes |
| **Dependencies** | None (but runs after common role in provision playbook) |

**Tasks performed:**
1. Remove old Docker packages (if any)
2. Install prerequisites (ca-certificates, curl, gnupg)
3. Create keyrings directory
4. Add Docker official GPG key
5. Add Docker APT repository
6. Install Docker CE packages → triggers `restart docker` handler
7. Ensure Docker service is running and enabled
8. Add user to docker group
9. Install python3-docker for Ansible Docker modules

### 2.3 App Deploy Role

| Field | Value |
|-------|-------|
| **Purpose** | Deploy containerized Python app from Docker Hub |
| **Key Variables** | `app_name`, `app_port` (host: 5000), `app_container_port` (container: 8000), `app_restart_policy`, `docker_image`, `docker_image_tag`, `dockerhub_username`, `dockerhub_password` (from Vault) |
| **Handlers** | `restart app` — restarts the application container |
| **Dependencies** | Requires `docker` role to be applied first |

**Tasks performed:**
1. Log in to Docker Hub (credentials from Vault, `no_log: true`)
2. Pull Docker image (force pull for latest)
3. Stop existing container (ignore errors if not running)
4. Remove old container
5. Run new container with port mapping (5000:8000) and restart policy
6. Wait for application port to be ready (60s timeout)
7. Verify `/health` endpoint returns HTTP 200
8. Display health check result

---

## 3. Idempotency Demonstration

### First Run — `ansible-playbook playbooks/provision.yml`

<!-- Paste terminal output from first run here -->
```
PLAY [Provision web servers] **************************************************

TASK [common : Update apt cache] *************************************  changed
TASK [common : Install common packages] ******************************  changed
TASK [common : Set timezone] *****************************************  ok
TASK [docker : Remove old Docker packages] ***************************  ok
TASK [docker : Install prerequisites] ********************************  changed
TASK [docker : Create keyrings directory] ****************************  changed
TASK [docker : Add Docker official GPG key] **************************  changed
TASK [docker : Add Docker APT repository] ****************************  changed
TASK [docker : Install Docker packages] ******************************  changed
TASK [docker : Ensure Docker service is running and enabled] *********  ok
TASK [docker : Add user to docker group] *****************************  changed
TASK [docker : Install python3-docker] *******************************  changed

PLAY RECAP ****************************************************************
lab04-vm-6d1e   : ok=14   changed=9   unreachable=0   failed=0   skipped=0   rescued=0   ignored=0
```

**Analysis:** Most tasks show "changed" (yellow) because packages are being installed for the first time, GPG key and repository are being added, and the user is being added to the docker group.

### Second Run — `ansible-playbook playbooks/provision.yml`

<!-- Paste terminal output from second run here -->
```
PLAY [Provision web servers] **************************************************

TASK [common : Update apt cache] *************************************  ok
TASK [common : Install common packages] ******************************  ok
TASK [common : Set timezone] *****************************************  ok
TASK [docker : Remove old Docker packages] ***************************  ok
TASK [docker : Install prerequisites] ********************************  ok
TASK [docker : Create keyrings directory] ****************************  ok
TASK [docker : Add Docker official GPG key] **************************  ok
TASK [docker : Add Docker APT repository] ****************************  ok
TASK [docker : Install Docker packages] ******************************  ok
TASK [docker : Ensure Docker service is running and enabled] *********  ok
TASK [docker : Add user to docker group] *****************************  ok
TASK [docker : Install python3-docker] *******************************  ok

PLAY RECAP ****************************************************************
lab04-vm-6d1e   : ok=13   changed=0   unreachable=0   failed=0   skipped=0   rescued=0   ignored=0
```

**Analysis:** All tasks show "ok" (green) with **zero changes**. This proves idempotency:
- `apt` module checks if packages are already installed (`state: present`)
- `get_url` with `force: false` skips download if GPG key exists
- `apt_repository` checks if repo is already configured
- `service` confirms Docker is already running and enabled
- `user` module verifies group membership already exists

### What Makes Roles Idempotent?

- Using **declarative modules** (`apt`, `service`, `file`) instead of imperative `command`/`shell`
- Specifying **desired state** (`state: present`, `state: started`) — Ansible only acts if current state differs
- Using `cache_valid_time: 3600` — apt cache update skipped if refreshed within the hour
- Using `force: false` on `get_url` — GPG key not re-downloaded if file exists

---

## 4. Ansible Vault Usage

### How Credentials Are Stored

Sensitive data (Docker Hub username and access token) is stored in `group_vars/all.yml`, encrypted with Ansible Vault using AES-256.

### Vault Password Management

- Vault password is stored in `.vault_pass` file (added to `.gitignore`)
- `ansible.cfg` references `vault_password_file = .vault_pass` for automatic decryption
- Alternative: use `--ask-vault-pass` flag to enter password interactively

### Example of Encrypted File

```
$ANSIBLE_VAULT;1.1;AES256
61623739326536373830333030313438326562353836633235386663636366353433393764373363
3432383661363162653066626435653738323031333138640a613537636436373366353839353463
...
```

The file is safely committed to Git — it cannot be read without the vault password.

### Why Ansible Vault Is Important

- **Security:** Credentials never appear in plaintext in version control
- **Compliance:** Meets security best practices for secret management
- **Convenience:** Encrypted files can be committed to Git alongside code
- **Access control:** Only team members with the vault password can decrypt
- **Audit trail:** Changes to secrets are tracked in Git history

---

## 5. Deployment Verification

### Deployment Run — `ansible-playbook playbooks/deploy.yml`

<!-- Paste terminal output here -->
```
PLAY [Deploy application] *****************************************************

TASK [app_deploy : Log in to Docker Hub] *****************************  ok
TASK [app_deploy : Pull Docker image] ********************************  ok
TASK [app_deploy : Inspect existing container] ***********************  ok
TASK [app_deploy : Stop existing container] **************************  skipped
TASK [app_deploy : Remove old container] *****************************  ok
TASK [app_deploy : Run application container] ************************* changed
TASK [app_deploy : Wait for application to be ready] *****************  ok
TASK [app_deploy : Verify health endpoint] ****************************  ok
TASK [app_deploy : Display health check result] ***********************  ok

PLAY RECAP ****************************************************************
lab04-vm-6d1e   : ok=9   changed=1   unreachable=0   failed=0   skipped=1   rescued=0   ignored=0
```

### Container Status — `docker ps`

<!-- Paste docker ps output here -->
```
CONTAINER ID   IMAGE                                STATUS         PORTS                    NAMES
97f64688f227   ravwvil/devops-info-service:latest   Up 4 minutes (healthy)   0.0.0.0:5000->8000/tcp   devops-info-service
```

### Health Check Verification

<!-- Paste curl outputs here -->
```bash
$ curl http://93.77.180.16:5000/health
{"status":"healthy","timestamp":"2026-02-26T20:51:38.357823+00:00","uptime_seconds":11}

$ curl http://93.77.180.16:5000/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"97f64688f227","platform":"Linux","architecture":"x86_64"},"runtime":{"timezone":"UTC"}}
```

### Handler Execution

The `restart docker` handler fires on first provision when Docker packages are installed. On subsequent runs, packages are already present, so the handler does not trigger — demonstrating efficient handler-based service management.

---

## 6. Key Decisions

### Why use roles instead of plain playbooks?
Roles enforce a standardized directory structure that separates tasks, handlers, defaults, and templates. This makes code reusable across projects and easier to maintain as complexity grows.

### How do roles improve reusability?
Each role is self-contained with its own variables, tasks, and handlers. The `docker` role, for example, can be dropped into any project that needs Docker — no copy-paste or modification required.

### What makes a task idempotent?
A task is idempotent when it checks the current state before making changes. Ansible's declarative modules (`apt`, `service`, `file`) compare desired state vs actual state and only act when they differ.

### How do handlers improve efficiency?
Handlers run only once at the end of a play, even if notified multiple times. This prevents unnecessary service restarts — Docker restarts only once after all installation tasks complete, not after each individual package.

### Why is Ansible Vault necessary?
Without Vault, credentials would be stored in plaintext YAML files visible to anyone with repository access. Vault encrypts secrets with AES-256, allowing safe storage in Git while restricting access to those with the vault password.

---

## 7. Challenges

- **Port mapping:** The Python app listens on port 8000 inside the container, but Lab 4's security group opens port 5000 — solved by mapping `5000:8000` in the container configuration.
- **GPG key installation:** The `apt_key` module is deprecated in newer Ansible versions — used `get_url` to download the key to `/etc/apt/keyrings/` instead, following Docker's official installation guide.
- **Idempotency of apt cache:** Without `cache_valid_time`, `update_cache: yes` always shows "changed" — adding `cache_valid_time: 3600` makes it idempotent.
