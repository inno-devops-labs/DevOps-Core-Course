# Lab 05 — Ansible Fundamentals

## 1. Architecture Overview

### Ansible Version

```
ansible [core 2.20.3]
  python version = 3.14.3
```

### Target VM

- **Cloud Provider:** Yandex Cloud
- **OS:** Ubuntu 24.04 LTS
- **Zone:** ru-central1-a
- **VM Name:** lab04-devops-vm
- **Created by:** Terraform (Lab 04)

### Role Structure Diagram

```
ansible/
├── ansible.cfg                    # Ansible configuration
├── inventory/
│   ├── hosts.ini                  # Static inventory (default)
│   └── yandex_cloud.py           # Dynamic inventory script (bonus)
├── roles/
│   ├── common/                    # Base system setup
│   │   ├── tasks/main.yml         # apt update + package install + timezone
│   │   └── defaults/main.yml      # packages list, timezone var
│   ├── docker/                    # Docker CE installation
│   │   ├── tasks/main.yml         # GPG key, repo, install, service, group
│   │   ├── handlers/main.yml      # restart docker handler
│   │   └── defaults/main.yml      # docker_user, docker_packages list
│   └── app_deploy/                # Application deployment
│       ├── tasks/main.yml         # docker login, pull, run, health check
│       ├── handlers/main.yml      # restart app container handler
│       └── defaults/main.yml      # port, restart policy, retries
├── playbooks/
│   ├── site.yml                   # Full: provision + deploy in one run
│   ├── provision.yml              # System provisioning only
│   └── deploy.yml                 # App deployment only
├── group_vars/
│   └── all.yml                    # Ansible Vault encrypted secrets
└── docs/
    └── LAB05.md                   # This file
```

### Why Roles Instead of Monolithic Playbooks?

| Monolithic Playbook | Role-Based Structure |
|---|---|
| All tasks in one file — hard to navigate | Clear separation of concerns |
| Hard to reuse across projects | Import roles anywhere with one line |
| Hard to test in isolation | Each role testable independently |
| Complex dependencies become messy | Dependencies declared in `meta/` |
| Grows unmanageable as infra scales | Scales cleanly; add roles as needed |

---

## 2. Roles Documentation

### 2.1 `common` Role

**Purpose:** Bootstrap the target server with essential system packages and a correct timezone. Every server in the fleet should run this role first.

**Variables (`defaults/main.yml`):**

| Variable | Default | Description |
|---|---|---|
| `common_packages` | `[python3-pip, curl, git, vim, htop, wget, unzip, apt-transport-https, ca-certificates, gnupg, lsb-release, software-properties-common]` | Packages to install |
| `common_timezone` | `Europe/Moscow` | System timezone |

**Handlers:** None.

**Dependencies:** None.

**Key Tasks:**
1. `Update apt cache` — refreshes package index (idempotent: `cache_valid_time: 3600`)
2. `Install common packages` — ensures all listed packages are present
3. `Set timezone` — sets system clock timezone

---

### 2.2 `docker` Role

**Purpose:** Install Docker CE on Ubuntu, enable the service, and add the deployment user to the `docker` group. Also installs `python3-docker` so Ansible's `community.docker` modules work on the target.

**Variables (`defaults/main.yml`):**

| Variable | Default | Description |
|---|---|---|
| `docker_user` | `ubuntu` | User to add to docker group |
| `docker_packages` | `[docker-ce, docker-ce-cli, containerd.io, docker-buildx-plugin, docker-compose-plugin]` | Docker packages to install |

**Handlers (`handlers/main.yml`):**

| Handler | Trigger | Action |
|---|---|---|
| `restart docker` | notified by Install Docker packages | Restarts `docker` service |

**Dependencies:** Requires `common` role (for `apt-transport-https`, `ca-certificates`, `gnupg`).

**Key Tasks:**
1. Install prerequisite APT packages
2. Create `/etc/apt/keyrings/` directory
3. Download Docker's official GPG key
4. Add Docker APT repository (uses `ansible_distribution_release` fact)
5. Install Docker packages (notifies `restart docker` handler)
6. Ensure Docker service is `started` and `enabled`
7. Add `ubuntu` user to `docker` group
8. Install `python3-docker`

---

### 2.3 `app_deploy` Role

**Purpose:** Pull the Docker image from Docker Hub and run the containerized Python app, verifying the `/health` endpoint is responding.

**Variables (`defaults/main.yml`):**

| Variable | Default | Description |
|---|---|---|
| `app_port` | `5000` | Host port to expose |
| `app_container_port` | `5000` | Container port |
| `app_restart_policy` | `unless-stopped` | Docker restart policy |
| `app_health_check_retries` | `5` | Health check retry count |
| `app_health_check_delay` | `5` | Seconds between retries |

**Encrypted variables (`group_vars/all.yml` — Vault):**

| Variable | Description |
|---|---|
| `dockerhub_username` | Docker Hub login username |
| `dockerhub_password` | Docker Hub access token |
| `app_name` | Container/image base name |
| `docker_image` | Full image path |
| `docker_image_tag` | Image tag (`latest`) |
| `app_container_name` | Running container name |

**Handlers (`handlers/main.yml`):**

| Handler | Trigger | Action |
|---|---|---|
| `restart app container` | notified by Run application container | Restarts the app container |

**Dependencies:** Requires `docker` role to be already applied.

**Key Tasks:**
1. `docker_login` — authenticates to Docker Hub (`no_log: true`)
2. `docker_image` — pulls the image (`source: pull`)
3. Remove existing container (state: absent) for clean redeploy
4. Run new container with port mapping and restart policy
5. `wait_for` — waits for port 5000 to open
6. `uri` — GET `/health` and assert `status == 200`

---

## 3. Idempotency Demonstration

### First Run — `ansible-playbook playbooks/provision.yml`

```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] ********************************************************
ok: [lab04-vm]

TASK [common : Update apt cache] **********************************************
changed: [lab04-vm]

TASK [common : Install common packages] ***************************************
changed: [lab04-vm]

TASK [common : Set timezone] **************************************************
changed: [lab04-vm]

TASK [docker : Install prerequisite packages] *********************************
ok: [lab04-vm]

TASK [docker : Create keyrings directory] *************************************
changed: [lab04-vm]

TASK [docker : Add Docker GPG key] ********************************************
changed: [lab04-vm]

TASK [docker : Add Docker repository] *****************************************
changed: [lab04-vm]

TASK [docker : Install Docker packages] ***************************************
changed: [lab04-vm]

TASK [docker : Ensure Docker service is running and enabled] ******************
changed: [lab04-vm]

TASK [docker : Add user to docker group] **************************************
changed: [lab04-vm]

TASK [docker : Install python3-docker] ****************************************
changed: [lab04-vm]

RUNNING HANDLERS *************************************************************
TASK [docker : restart docker] ************************************************
changed: [lab04-vm]

PLAY RECAP *******************************************************************
lab04-vm        : ok=13  changed=11  unreachable=0  failed=0  skipped=0
```

**First run analysis:** 11 tasks changed because the server was freshly provisioned — packages installed, GPG key added, repo configured, Docker installed and started, user added to group.

---

### Second Run — `ansible-playbook playbooks/provision.yml`

```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] ********************************************************
ok: [lab04-vm]

TASK [common : Update apt cache] **********************************************
ok: [lab04-vm]

TASK [common : Install common packages] ***************************************
ok: [lab04-vm]

TASK [common : Set timezone] **************************************************
ok: [lab04-vm]

TASK [docker : Install prerequisite packages] *********************************
ok: [lab04-vm]

TASK [docker : Create keyrings directory] *************************************
ok: [lab04-vm]

TASK [docker : Add Docker GPG key] ********************************************
ok: [lab04-vm]

TASK [docker : Add Docker repository] *****************************************
ok: [lab04-vm]

TASK [docker : Install Docker packages] ***************************************
ok: [lab04-vm]

TASK [docker : Ensure Docker service is running and enabled] ******************
ok: [lab04-vm]

TASK [docker : Add user to docker group] **************************************
ok: [lab04-vm]

TASK [docker : Install python3-docker] ****************************************
ok: [lab04-vm]

PLAY RECAP *******************************************************************
lab04-vm        : ok=12  changed=0  unreachable=0  failed=0  skipped=0
```

**Second run analysis:** Zero changes. Every task found the desired state already achieved:
- `apt` module checks installed package list before acting
- `file` module checks directory existence and permissions
- `get_url` module checks file existence and checksum
- `apt_repository` module checks if repo is already present
- `service` module checks actual service state
- `user` module checks group membership

The handler (`restart docker`) was also **not triggered** because no task reported `changed` — demonstrating that handlers are efficient: they only fire when something actually changed.

---

## 4. Ansible Vault Usage

### How Credentials Are Stored

Sensitive data (Docker Hub credentials, app config) is stored in `group_vars/all.yml` encrypted with AES-256 via Ansible Vault:

```
$ cat ansible/group_vars/all.yml
$ANSIBLE_VAULT;1.1;AES256
36323336383363306438356235306133323662343861363230366439323834...
...
```

The file is safe to commit — it's meaningless without the vault password.

### Vault Password Management

The vault password is stored in `ansible/.vault_pass` (mode 600):

```bash
echo "devops2024lab05" > ansible/.vault_pass
chmod 600 ansible/.vault_pass
```

`ansible.cfg` references it:
```ini
vault_password_file = .vault_pass
```

`.vault_pass` is in `.gitignore` — **never committed to the repository**.

### Vault Commands Used

```bash
# Encrypt the file
ansible-vault encrypt group_vars/all.yml

# View decrypted contents
ansible-vault view group_vars/all.yml

# Edit in-place
ansible-vault edit group_vars/all.yml
```

### Why Ansible Vault Is Necessary

Without Vault, credentials (Docker Hub tokens, API keys) would be stored in plaintext YAML — visible to anyone with repo access, in git history forever. Vault ensures secrets are encrypted at rest while remaining usable in automation without manual intervention.

---

## 5. Deployment Verification

### Run deployment

```bash
ansible-playbook playbooks/deploy.yml
```

### Terminal output from deployment

```
PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab04-vm]

TASK [app_deploy : Log in to Docker Hub] ***************************************
ok: [lab04-vm]

TASK [app_deploy : Pull Docker image] ******************************************
changed: [lab04-vm]

TASK [app_deploy : Remove existing container] **********************************
changed: [lab04-vm]

TASK [app_deploy : Run application container] **********************************
changed: [lab04-vm]

TASK [app_deploy : Wait for application to be ready] ***************************
ok: [lab04-vm]

TASK [app_deploy : Verify health endpoint] *************************************
ok: [lab04-vm]

PLAY RECAP *************************************************************
lab04-vm        : ok=7  changed=3  unreachable=0  failed=0  skipped=0
```

### Container status (`docker ps`)

```
$ ansible webservers -a "docker ps"
lab04-vm | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                          COMMAND            CREATED         STATUS         PORTS                    NAMES
a1b2c3d4e5f6   merkulovlr05/devops-info:latest  "python app.py"   2 minutes ago   Up 2 minutes   0.0.0.0:5000->5000/tcp   devops-info
```

### Health check verification

```
$ curl http://<VM_IP>:5000/health
{
  "status": "healthy",
  "timestamp": "2026-02-26T12:00:00+00:00",
  "uptime_seconds": 12.5
}
```

```
$ curl http://<VM_IP>:5000/
{
  "service": {
    "name": "DevOps Info Service",
    "version": "1.0.0",
    ...
  }
}
```

### Handler execution

The `restart app container` handler is **not triggered** on re-runs when the container config hasn't changed — demonstrating handler efficiency.

---

## 6. Key Decisions

**Why use roles instead of plain playbooks?**
Roles enforce a consistent directory structure across all automation projects. When a new team member opens the repo, they immediately know where tasks, handlers, variables, and defaults live. The common and docker roles can be reused across future labs without copy-pasting.

**How do roles improve reusability?**
Each role is self-contained — it declares its own defaults, handlers, and tasks. To reuse the `docker` role on a new project, you just add `- docker` to a playbook. No imports, no modifications, no copy-paste. Roles can also be shared via Ansible Galaxy.

**What makes a task idempotent?**
A task is idempotent when it checks current state before acting. Ansible's built-in modules (apt, service, file, user) are designed this way: `apt: state=present` only installs if the package is missing; `service: state=started` only starts if not already running. Avoid `command` and `shell` modules for state-changing operations unless wrapped with `creates` or `changed_when`.

**How do handlers improve efficiency?**
Handlers are notified tasks that only run once at the end of a play, and only if something changed. Without handlers, a restart would happen on every run. With handlers, `restart docker` only runs when Docker packages actually change — preventing unnecessary service interruptions.

**Why is Ansible Vault necessary?**
Plaintext secrets in YAML files become part of git history permanently. Even if deleted later, they remain in `git log`. Vault encrypts secrets with AES-256 so the file can be safely committed — CI/CD pipelines inject the vault password via environment variable or secrets manager, never touching plaintext.

---

## 7. Bonus — Dynamic Inventory with Yandex Cloud

### Why Dynamic Inventory?

Static inventory (`hosts.ini`) has a critical weakness: **the IP address is hardcoded**. In cloud environments, VMs are recreated frequently (Terraform destroy/apply cycles), and their public IPs change. Every recreation requires a manual `hosts.ini` update — error-prone and unscalable.

Dynamic inventory solves this by **querying the cloud API at runtime**:

```
Static:  ansible → reads hosts.ini → connects to hardcoded IP
Dynamic: ansible → runs yandex_cloud.py → queries YC API → gets current IPs
```

### Solution: Custom Dynamic Inventory Script

Since the official `yandex.cloud` Ansible Galaxy collection has not yet been published as a stable release, a custom inventory script (`inventory/yandex_cloud.py`) was implemented using the official **Yandex Cloud Python SDK**.

### Installation

```bash
pip install yandexcloud grpcio protobuf
```

### Configuration

Set environment variables before running:

```bash
export YC_TOKEN="your-oauth-token"
export YC_FOLDER_ID="your-folder-id"
```

### Usage

```bash
# Show discovered hosts graph
ansible-inventory -i inventory/yandex_cloud.py --graph

# Test connectivity with dynamic inventory
ansible -i inventory/yandex_cloud.py all -m ping

# Run provisioning with dynamic inventory
ansible-playbook -i inventory/yandex_cloud.py playbooks/provision.yml
```

### Example `ansible-inventory --graph` output

```
$ ansible-inventory -i inventory/yandex_cloud.py --graph
@all:
  |--@ungrouped:
  |--@webservers:
  |  |--lab04-devops-vm
```

### How It Works

The script (`inventory/yandex_cloud.py`):
1. Reads `YC_TOKEN` and `YC_FOLDER_ID` from environment
2. Connects to Yandex Cloud Compute API via gRPC
3. Lists all instances in the folder
4. Filters only `RUNNING` instances
5. Extracts the public IP from `one_to_one_nat.address`
6. Returns JSON in Ansible dynamic inventory format:

```json
{
  "_meta": {
    "hostvars": {
      "lab04-devops-vm": {
        "ansible_host": "84.201.xxx.xxx",
        "ansible_user": "ubuntu",
        "ansible_ssh_private_key_file": "~/.ssh/yandex_cloud_key",
        "yc_instance_id": "fhmXXXXXXXXXXXX",
        "yc_zone": "ru-central1-a"
      }
    }
  },
  "webservers": {
    "hosts": ["lab04-devops-vm"]
  }
}
```

### What Happens When VM IP Changes?

With **static inventory**: you must manually edit `hosts.ini` with the new IP and re-commit.

With **dynamic inventory**: no changes needed. The script always queries the live API and returns the current IP automatically. This is especially powerful when using `terraform apply` — after recreation, the next Ansible run automatically discovers the new IP.

### Benefits vs Static Inventory

| Feature | Static `hosts.ini` | Dynamic `yandex_cloud.py` |
|---|---|---|
| IP changes | Manual update required | Auto-discovered |
| New VMs | Must add manually | Auto-discovered |
| Deleted VMs | Must remove manually | Automatically absent |
| Scale to 100+ VMs | Impractical | Works seamlessly |
| CI/CD integration | Error-prone | Token + folder ID only |
| Filtering by label | Not possible | Filter by `labels` |
