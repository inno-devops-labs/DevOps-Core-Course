# Lab 05 — Ansible Fundamentals

## 1. Architecture Overview

**Ansible version:** 2.20.2 (ansible-core), Ansible package 13.3.0  
**Target VM OS:** Ubuntu 24.04 LTS (Yandex Cloud, provisioned via Pulumi in Lab 4)  
**Control node:** macOS (local machine)

### Role Structure

```
ansible/
├── inventory/
│   ├── hosts.ini              # Static inventory with VM IP
│   └── group_vars/
│       └── all.yml            # Encrypted variables (Vault)
├── roles/
│   ├── common/                # System packages & timezone
│   │   ├── tasks/main.yml
│   │   └── defaults/main.yml
│   ├── docker/                # Docker CE installation
│   │   ├── tasks/main.yml
│   │   ├── handlers/main.yml
│   │   └── defaults/main.yml
│   └── app_deploy/            # Container-based app deployment
│       ├── tasks/main.yml
│       ├── handlers/main.yml
│       └── defaults/main.yml
├── playbooks/
│   ├── site.yml               # Full setup (provision + deploy)
│   ├── provision.yml          # System provisioning only
│   └── deploy.yml             # App deployment only
├── ansible.cfg                # Ansible configuration
├── .vault_pass                # Vault password (gitignored)
└── docs/
    └── LAB05.md               # This file
```

### Why Roles Instead of Monolithic Playbooks?

Roles provide modular, reusable units of automation. Each role encapsulates a single responsibility — `common` handles base packages, `docker` handles Docker installation, and `app_deploy` handles the application lifecycle. This separation makes it easy to reuse the Docker role in other projects, test roles independently, and maintain clear ownership of each piece of configuration.

---

## 2. Roles Documentation

### 2.1 Common Role

**Purpose:** Installs essential system packages and sets the timezone on all managed hosts.

**Variables (defaults):**
| Variable | Default | Description |
|----------|---------|-------------|
| `common_packages` | `[python3-pip, curl, git, vim, htop, wget, unzip, ca-certificates, gnupg, lsb-release]` | Packages to install |
| `common_timezone` | `Europe/Moscow` | System timezone |

**Handlers:** None.  
**Dependencies:** None.

### 2.2 Docker Role

**Purpose:** Installs Docker CE from the official Docker repository, ensures the service is running and enabled, and adds the target user to the `docker` group.

**Variables (defaults):**
| Variable | Default | Description |
|----------|---------|-------------|
| `docker_user` | `ubuntu` | User to add to docker group |
| `docker_packages` | `[docker-ce, docker-ce-cli, containerd.io, docker-buildx-plugin, docker-compose-plugin]` | Docker packages |

**Handlers:**
- `Restart docker` — restarts the Docker daemon when configuration changes (triggered by package install).

**Dependencies:** Requires `common` role to be applied first (for `ca-certificates`, `gnupg`, `curl`).

### 2.3 App Deploy Role

**Purpose:** Pulls a Docker image from Docker Hub, removes any existing container, runs the new version, and verifies it is healthy.

**Variables (defaults):**
| Variable | Default | Description |
|----------|---------|-------------|
| `app_name` | `devops-app` | Application name |
| `app_port` | `8080` | Port to expose |
| `app_container_name` | `{{ app_name }}` | Container name |
| `app_restart_policy` | `unless-stopped` | Docker restart policy |
| `app_env_vars` | `{HOST: 0.0.0.0, PORT: 8080, DEBUG: False}` | Environment variables |

**Vault variables (inventory/group_vars/all.yml):**
| Variable | Description |
|----------|-------------|
| `dockerhub_username` | Docker Hub username |
| `dockerhub_password` | Docker Hub access token |
| `docker_image` | Image name (`aezuraa/devops-info-service`) |
| `docker_image_tag` | Image tag (`python`) |

**Handlers:**
- `Restart app container` — restarts the application container.

**Dependencies:** Requires `docker` role (Docker must be installed and running).

---

## 3. Idempotency Demonstration

### First Run — `ansible-playbook playbooks/provision.yml`

```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab04-vm]

TASK [common : Update apt cache] ***********************************************
changed: [lab04-vm]

TASK [common : Install common packages] ****************************************
changed: [lab04-vm]

TASK [common : Set timezone] ***************************************************
changed: [lab04-vm]

TASK [docker : Install prerequisites for Docker repository] ********************
ok: [lab04-vm]

TASK [docker : Create keyrings directory] **************************************
ok: [lab04-vm]

TASK [docker : Add Docker GPG key] *********************************************
changed: [lab04-vm]

TASK [docker : Add Docker repository] ******************************************
changed: [lab04-vm]

TASK [docker : Install Docker packages] ****************************************
changed: [lab04-vm]

TASK [docker : Ensure Docker service is running and enabled] *******************
ok: [lab04-vm]

TASK [docker : Add user to docker group] ***************************************
changed: [lab04-vm]

TASK [docker : Install python3-docker for Ansible docker modules] **************
changed: [lab04-vm]

RUNNING HANDLER [docker : Restart docker] **************************************
changed: [lab04-vm]

PLAY RECAP *********************************************************************
lab04-vm                   : ok=13   changed=9    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

**Analysis:** 9 out of 13 tasks show `changed` — the system was in a fresh state, so packages were installed, Docker was set up from scratch, and the handler fired because Docker packages were installed.

### Second Run — `ansible-playbook playbooks/provision.yml`

```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab04-vm]

TASK [common : Update apt cache] ***********************************************
ok: [lab04-vm]

TASK [common : Install common packages] ****************************************
ok: [lab04-vm]

TASK [common : Set timezone] ***************************************************
ok: [lab04-vm]

TASK [docker : Install prerequisites for Docker repository] ********************
ok: [lab04-vm]

TASK [docker : Create keyrings directory] **************************************
ok: [lab04-vm]

TASK [docker : Add Docker GPG key] *********************************************
ok: [lab04-vm]

TASK [docker : Add Docker repository] ******************************************
ok: [lab04-vm]

TASK [docker : Install Docker packages] ****************************************
ok: [lab04-vm]

TASK [docker : Ensure Docker service is running and enabled] *******************
ok: [lab04-vm]

TASK [docker : Add user to docker group] ***************************************
ok: [lab04-vm]

TASK [docker : Install python3-docker for Ansible docker modules] **************
ok: [lab04-vm]

PLAY RECAP *********************************************************************
lab04-vm                   : ok=12   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

**Analysis:** Every task shows `ok` — zero changes. The handler did NOT fire because no task notified it. This proves idempotency: the system is already in the desired state, so Ansible makes no modifications.

**What makes the roles idempotent:**
- `apt` module with `state: present` — only installs if package is missing
- `apt_key` with `state: present` — only adds the key if it doesn't exist
- `apt_repository` with `state: present` — only adds if not already configured
- `service` with `state: started` — no-op if already running
- `user` with `groups: docker, append: yes` — no-op if user is already in the group
- `cache_valid_time: 3600` — skips apt update if cache is fresh

---

## 4. Ansible Vault Usage

### How Credentials Are Stored

All sensitive data (Docker Hub username/password, app configuration) is stored in `ansible/inventory/group_vars/all.yml`, encrypted with Ansible Vault.

### Vault Password Management

The vault password is stored in `ansible/.vault_pass` (a plain text file with the password). This file is:
- Listed in `.gitignore` — never committed to Git
- Referenced in `ansible.cfg` via `vault_password_file = .vault_pass`
- Permissions set to `600` (owner-only read/write)

### Encrypted File Example

The file `inventory/group_vars/all.yml` looks like this after encryption:

```
$ANSIBLE_VAULT;1.1;AES256
66386530356432313261653635333338316539633935613031633638653464386337613334
61613837613930306265316637653637663162363833383234363633626566303033616365
...
```

This can be safely committed to Git — the content is AES-256 encrypted and cannot be read without the vault password.

### Why Ansible Vault Is Important

Without Vault, credentials would be stored in plaintext YAML files. Even in a private repository, this creates risk: credentials in Git history are permanent, team members may have excessive access, and accidental pushes to public repos would leak secrets. Vault ensures secrets are encrypted at rest and only decrypted during playbook execution.

---

## 5. Deployment Verification

### Deploy Playbook Run — `ansible-playbook playbooks/deploy.yml`

```
PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab04-vm]

TASK [app_deploy : Log in to Docker Hub] ***************************************
ok: [lab04-vm]

TASK [app_deploy : Pull Docker image] ******************************************
ok: [lab04-vm]

TASK [app_deploy : Stop and remove existing container] *************************
ok: [lab04-vm]

TASK [app_deploy : Run application container] **********************************
changed: [lab04-vm]

TASK [app_deploy : Wait for application to be ready] ***************************
ok: [lab04-vm]

TASK [app_deploy : Verify health endpoint] *************************************
ok: [lab04-vm]

TASK [app_deploy : Display health check result] ********************************
ok: [lab04-vm] => {
    "health_check.json": {
        "status": "healthy",
        "timestamp": "2026-02-23T14:53:11.642430+00:00",
        "uptime_seconds": 9
    }
}

PLAY RECAP *********************************************************************
lab04-vm                   : ok=8    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Container Status — `docker ps`

```
CONTAINER ID   IMAGE                                COMMAND           CREATED          STATUS          PORTS                    NAMES
8999db58c415   aezuraa/devops-info-service:python   "python app.py"   45 seconds ago   Up 22 seconds   0.0.0.0:8080->8080/tcp   devops-app
```

### Health Check Verification

```bash
$ curl http://84.201.130.19:8080/health
{"status":"healthy","timestamp":"2026-02-23T14:54:49.625553+00:00","uptime_seconds":84}
```

### Handler Execution

The `Restart app container` handler fired during the first deployment because the `Run application container` task was `changed`. On subsequent runs with no container changes, it would not fire.

---

## 6. Key Decisions

**Why use roles instead of plain playbooks?**  
Roles enforce a standard directory structure that separates concerns — tasks, handlers, defaults, and files each live in their own location. This makes it trivial to reuse the `docker` role in any project that needs Docker, without copying and pasting task blocks between playbooks.

**How do roles improve reusability?**  
Each role is self-contained with its own variables, handlers, and tasks. The `docker` role can be dropped into any Ansible project to install Docker on Ubuntu. The `app_deploy` role can be parameterized for any Docker-based application — just override the image name, port, and credentials.

**What makes a task idempotent?**  
A task is idempotent when it checks the current state before acting. Ansible modules like `apt`, `service`, and `user` are inherently idempotent — they compare the desired state (`state: present`, `state: started`) against reality and only make changes when there's a difference. Using `command` or `shell` modules breaks idempotency unless you add `creates`/`removes` guards.

**How do handlers improve efficiency?**  
Handlers only run when notified by a changed task, and they run only once at the end of the play regardless of how many tasks notify them. This prevents unnecessary service restarts — Docker is only restarted when its packages are actually installed or updated, not on every playbook run.

**Why is Ansible Vault necessary?**  
Vault encrypts sensitive data (passwords, API tokens) so they can be stored alongside code in version control. Without Vault, you'd need to manage secrets outside of Git (environment variables, external secret managers), which complicates reproducibility. Vault strikes a balance between security and simplicity for team-sized projects.

---

## 7. Challenges

- **Yandex Cloud completion file:** The `yandex-cloud/completion.zsh.inc` file (~9MB) was freezing terminal startup. Disabled it in `.zshrc`.
- **Port mapping:** The lab template suggests port 5000, but our app from Labs 1-3 runs on port 8080. Updated all port references and added a security group rule for port 8080.
- **Docker image tag:** CI/CD pipeline from Lab 3 publishes the image as `aezuraa/devops-info-service:python`, not `:latest`. Configured the correct tag in vault variables.
- **VM recreation:** The Yandex Cloud VM from Lab 4 was shut down. Recreated it using the existing Pulumi configuration (`pulumi up`) before running Ansible.
- **group_vars path:** Ansible 2.20 requires `group_vars/` to be inside the inventory directory (adjacent to `hosts.ini`), not at the project root. Moved accordingly.
- **Deprecation warning:** `ansible_distribution_release` auto-injected fact is deprecated in 2.20+. Replaced with `ansible_facts['distribution_release']`.
