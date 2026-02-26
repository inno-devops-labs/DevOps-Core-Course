# Lab 05 — Ansible Fundamentals

## 1. Architecture Overview

**Ansible version:** ansible-core 2.20.3
**Control node OS:** Ubuntu 24.04 LTS (local machine)
**Target VM OS:** Ubuntu 24.04 LTS (Yandex Cloud, recreated using Lab 4 Terraform code)
**Cloud provider:** Yandex Cloud, zone ru-central1-a, VM public IP: 89.169.131.155

### Role structure

```
ansible/
├── inventory/
│   ├── hosts.ini              # Static inventory
│   ├── group_vars/
│   │   └── all.yml            # Encrypted with Ansible Vault
│   ├── yandex.yml             # Dynamic inventory notes
│   └── yandex_inventory.py    # Dynamic inventory script (Yandex Cloud API)
├── roles/
│   ├── common/                # Basic system setup
│   │   ├── tasks/main.yml
│   │   └── defaults/main.yml
│   ├── docker/                # Docker installation
│   │   ├── tasks/main.yml
│   │   ├── handlers/main.yml
│   │   └── defaults/main.yml
│   └── app_deploy/            # Run our Python app in Docker
│       ├── tasks/main.yml
│       ├── handlers/main.yml
│       └── defaults/main.yml
├── playbooks/
│   ├── site.yml               # All roles together
│   ├── provision.yml          # System setup only
│   └── deploy.yml             # App deployment only
├── ansible.cfg
└── docs/
    └── LAB05.md
```

### Why roles instead of one big playbook?

Roles keep things organized. Each role does one specific job. If I need Docker on another project, I just copy the `docker` role. A monolithic playbook would be one huge file that is hard to read and impossible to reuse. Roles are the professional way to write Ansible.

---

## 2. Roles Documentation

### common role

**Purpose:** Basic server setup that any Ubuntu server needs before anything else.

**Tasks:**
- Update apt package cache (with `cache_valid_time=3600` so it does not update if it was updated less than an hour ago)
- Install essential packages: python3-pip, curl, git, vim, htop, wget, unzip
- Set timezone to Europe/Moscow

**Variables (`defaults/main.yml`):**
```yaml
common_packages:
  - python3-pip
  - curl
  - git
  - vim
  - htop
  - wget
  - unzip

common_timezone: "Europe/Moscow"
```

**Handlers:** None — apt installs do not require a service restart.

**Dependencies:** None.

---

### docker role

**Purpose:** Install Docker CE on Ubuntu following the official Docker installation steps, translated to Ansible tasks.

**Tasks:**
1. Install prerequisites (ca-certificates, curl, gnupg)
2. Create `/etc/apt/keyrings` directory with correct permissions
3. Download Docker's official GPG key
4. Add Docker apt repository using `{{ ansible_distribution_release }}` fact (works on Ubuntu 22.04 and 24.04 without changes)
5. Install docker-ce, docker-ce-cli, containerd.io, docker-buildx-plugin, docker-compose-plugin
6. Start and enable Docker service
7. Add `ubuntu` user to docker group
8. Install python3-docker (required for Ansible's docker modules)

**Variables (`defaults/main.yml`):**
```yaml
docker_user: ubuntu
```

**Handlers (`handlers/main.yml`):**
```yaml
- name: restart docker
  service:
    name: docker
    state: restarted
```
Triggered when Docker packages are installed (via `notify: restart docker`).

**Dependencies:** common role (apt cache should be updated first).

---

### app_deploy role

**Purpose:** Pull the Python app Docker image from Docker Hub and run it as a container.

**Tasks:**
1. Log in to Docker Hub using vault credentials (`no_log: true` so password never appears in output)
2. Pull Docker image
3. Remove old container if it exists (idempotent cleanup)
4. Start new container with port mapping `5000:5000` and `restart_policy: unless-stopped`
5. Wait for port 5000 to open (confirms container started)
6. Verify `/health` endpoint returns HTTP 200

**Variables (`defaults/main.yml`):**
```yaml
app_port: 5000
app_restart_policy: unless-stopped
app_env_vars: {}
```

Variables from vault (`inventory/group_vars/all.yml`):
```yaml
dockerhub_username: blxxdclxud
dockerhub_password: <encrypted>
app_name: devops-info-service
docker_image: "{{ dockerhub_username }}/{{ app_name }}"
docker_image_tag: latest
app_port: 5000
app_container_name: "{{ app_name }}"
```

**Handlers (`handlers/main.yml`):**
```yaml
- name: restart app container
  community.docker.docker_container:
    name: "{{ app_container_name }}"
    state: started
    restart: yes
```

**Dependencies:** docker role.

---

## 3. Idempotency Demonstration

### First run — `ansible-playbook playbooks/provision.yml`

```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab-vm]

TASK [common : Update apt cache] ***********************************************
changed: [lab-vm]

TASK [common : Install common packages] ****************************************
changed: [lab-vm]

TASK [common : Set timezone] ***************************************************
changed: [lab-vm]

TASK [docker : Install required packages for Docker repo] **********************
ok: [lab-vm]

TASK [docker : Create keyrings directory] **************************************
ok: [lab-vm]

TASK [docker : Add Docker GPG key] *********************************************
changed: [lab-vm]

TASK [docker : Add Docker repository] ******************************************
changed: [lab-vm]

TASK [docker : Install Docker packages] ****************************************
changed: [lab-vm]

TASK [docker : Ensure Docker service is started and enabled] *******************
ok: [lab-vm]

TASK [docker : Add user to docker group] ***************************************
changed: [lab-vm]

TASK [docker : Install python3-docker for Ansible docker modules] **************
changed: [lab-vm]

RUNNING HANDLER [docker : restart docker] **************************************
changed: [lab-vm]

PLAY RECAP *********************************************************************
lab-vm                     : ok=13   changed=9    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

9 tasks changed on first run because everything was installed fresh. The handler ran once at the end to restart Docker after packages were installed.

### Second run — `ansible-playbook playbooks/provision.yml`

```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab-vm]

TASK [common : Update apt cache] ***********************************************
ok: [lab-vm]

TASK [common : Install common packages] ****************************************
ok: [lab-vm]

TASK [common : Set timezone] ***************************************************
ok: [lab-vm]

TASK [docker : Install required packages for Docker repo] **********************
ok: [lab-vm]

TASK [docker : Create keyrings directory] **************************************
ok: [lab-vm]

TASK [docker : Add Docker GPG key] *********************************************
ok: [lab-vm]

TASK [docker : Add Docker repository] ******************************************
ok: [lab-vm]

TASK [docker : Install Docker packages] ****************************************
ok: [lab-vm]

TASK [docker : Ensure Docker service is started and enabled] *******************
ok: [lab-vm]

TASK [docker : Add user to docker group] ***************************************
ok: [lab-vm]

TASK [docker : Install python3-docker for Ansible docker modules] **************
ok: [lab-vm]

PLAY RECAP *********************************************************************
lab-vm                     : ok=12   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

**changed=0 on second run.** The handler did not even trigger because no packages were reinstalled.

### Analysis

**What changed on first run:** Almost everything, because the VM was a fresh Ubuntu with no Docker or common packages.

**What stayed `ok` on second run:**
- `apt` module checks if each package is already at `state: present` — if yes, it does nothing
- `file` module checks if the directory already has the correct permissions
- `get_url` checks if the file already exists with the correct checksum
- `apt_repository` checks if the repo line is already in the sources list
- `service` checks if Docker is already started and enabled
- `user` checks if ubuntu is already in the docker group

**What makes our roles idempotent:** We use Ansible's declarative modules (`apt`, `service`, `file`, `user`, `get_url`, `apt_repository`) instead of `shell` or `command`. These modules always check current state before making a change. If the state already matches the desired state, they do nothing.

---

## 4. Ansible Vault Usage

### How credentials are stored

All sensitive data lives in `inventory/group_vars/all.yml`, which is encrypted with Ansible Vault. The file in git looks like this:

```
$ANSIBLE_VAULT;1.1;AES256
32386331623939663963666531666434613830323232613238396234643063373738613764303939
6235346663643761326237373864353263323335336336360a656439343563613939353830393938
...
```

It is completely unreadable without the vault password.

### Vault password management

The vault password is stored in `ansible/.vault_pass` (plain text file). This file is in `.gitignore` so it never gets committed. The `ansible.cfg` points to it automatically:

```ini
vault_password_file = .vault_pass
```

### Commands used

```bash
# Encrypt the file after writing plaintext
ansible-vault encrypt inventory/group_vars/all.yml --vault-password-file .vault_pass --encrypt-vault-id default

# View encrypted file to verify content
ansible-vault view inventory/group_vars/all.yml --vault-password-file .vault_pass

# Edit encrypted file
ansible-vault edit inventory/group_vars/all.yml
```

### Proof of encryption (ansible-vault view output)

```
---
# Docker Hub credentials
dockerhub_username: blxxdclxud
dockerhub_password: dckr_pat_***************************

# Application configuration
app_name: devops-info-service
docker_image: "{{ dockerhub_username }}/{{ app_name }}"
docker_image_tag: latest
app_port: 5000
app_container_name: "{{ app_name }}"
```

### Why Ansible Vault is necessary

If we committed the Docker Hub password to git, anyone with access to the repo could pull our images without permission. Vault encrypts with AES-256, so the encrypted file is safe to commit. The only secret that must be kept out of git is the vault password file itself (`.vault_pass`), which is in `.gitignore`.

---

## 5. Deployment Verification

### Terminal output from `ansible-playbook playbooks/deploy.yml`

```
PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab-vm]

TASK [app_deploy : Log in to Docker Hub] ***************************************
ok: [lab-vm]

TASK [app_deploy : Pull Docker image] ******************************************
changed: [lab-vm]

TASK [app_deploy : Remove old container if exists] *****************************
ok: [lab-vm]

TASK [app_deploy : Run application container] **********************************
changed: [lab-vm]

TASK [app_deploy : Wait for application to be ready] ***************************
ok: [lab-vm]

TASK [app_deploy : Verify health endpoint] *************************************
ok: [lab-vm]

TASK [app_deploy : Print health check result] **********************************
ok: [lab-vm] => {
    "msg": "App is healthy: 200"
}

PLAY RECAP *********************************************************************
lab-vm                     : ok=8    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Container status — `ansible webservers -a "docker ps"`

```
lab-vm | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                                   COMMAND                  CREATED          STATUS                    PORTS                    NAMES
7708f3ef9215   blxxdclxud/devops-info-service:latest   "python -m uvicorn a…"   22 seconds ago   Up 20 seconds (healthy)   0.0.0.0:5000->5000/tcp   devops-info-service
```

### Health check — `curl http://89.169.131.155:5000/health`

```json
{"status":"healthy","timestamp":"2026-02-26T20:56:39.121836Z","uptime_seconds":19}
```

### Main endpoint — `curl http://89.169.131.155:5000/`

```json
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"7708f3ef9215","platform":"Linux","platform_version":"Linux-6.8.0-100-generic-x86_64-with-glibc2.41","architecture":"x86_64","cpu_count":2,"python_version":"3.13.12"},"runtime":{"uptime_seconds":20,"uptime_human":"0 hours, 0 minutes","current_time":"2026-02-26T20:56:39.536715Z","timezone":"UTC"},"request":{"client_ip":"80.136.142.219","user_agent":"curl/8.5.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}
```

---

## 6. Key Decisions

**Why use roles instead of plain playbooks?**
Roles split code into focused, reusable pieces. If I need to install Docker on a different project, I just copy the `docker` role. A plain playbook would be one huge file where everything is mixed together, making it hard to read and impossible to reuse across projects.

**How do roles improve reusability?**
Each role is self-contained with its own variables, handlers, and tasks. Other playbooks can include just the roles they need. For example, `provision.yml` uses `common` and `docker`, while `deploy.yml` only uses `app_deploy`. You can share roles via Ansible Galaxy.

**What makes a task idempotent?**
Using Ansible's built-in modules instead of shell commands. Modules like `apt`, `service`, `file`, and `user` check the current state first. They only make a change if the current state is different from the desired state. Running `apt: name=docker-ce state=present` ten times has the same result as running it once.

**How do handlers improve efficiency?**
Handlers only run once at the end of a play, even if notified multiple times. If ten tasks all notify `restart docker`, Docker restarts only once. Without handlers, you would either restart too many times or forget to restart at all.

**Why is Ansible Vault necessary?**
We need Docker Hub credentials to pull the private image. Storing them as plaintext in the repo is a security risk. Vault encrypts with AES-256 so the encrypted file is safe to commit. Only the vault password needs to stay secret, and we keep it out of git via `.gitignore`.

---

## 7. Challenges

- The VM from Lab 4 was already destroyed, so it was recreated with `terraform apply` from existing Lab 4 code
- `ansible_distribution_release` Ansible fact is needed in the Docker repo string to work on different Ubuntu versions automatically
- `python3-docker` must be installed on the target VM for Ansible docker modules to work — easy to forget
- `no_log: true` on the Docker Hub login task is required to prevent the password appearing in Ansible output
- `ansible-core 2.20.3` has a regression where `group_vars` must be placed relative to the inventory file (in `inventory/group_vars/`), not just in the project root
- The official `yandex.cloud` Ansible collection is not yet available on Ansible Galaxy for ansible-core 2.20.x, so dynamic inventory was implemented using a custom Python script with the `yandexcloud` SDK

---

## Bonus: Dynamic Inventory with Yandex Cloud

### Why dynamic inventory?

With static inventory, the VM IP must be updated manually every time the VM is recreated. With dynamic inventory, Ansible queries the Yandex Cloud API directly and always gets the current IP. If the VM is destroyed and recreated with a new IP, playbooks still work with no changes.

### Setup

**Install the Yandex Cloud Python SDK:**
```bash
pip install --break-system-packages yandexcloud grpcio
```

**Inventory script:** `inventory/yandex_inventory.py`

The script:
1. Loads the service account key (same JSON key used in Lab 4 Terraform)
2. Calls the Yandex Compute API to list all instances in the folder
3. Filters only RUNNING instances
4. For each instance, extracts the public NAT IP
5. Groups VMs with label `project=devops-lab04` into the `webservers` group
6. Returns JSON in the Ansible dynamic inventory format

### Authentication

Same service account key file used in Lab 4 Terraform (`/home/blxxdclxud/yc-key.json`). The key file is in `.gitignore` on both Terraform and Ansible sides.

### How cloud metadata maps to Ansible variables

| Ansible variable | Yandex Cloud field |
|---|---|
| `ansible_host` | `network_interfaces[0].primary_v4_address.one_to_one_nat.address` |
| `ansible_user` | hardcoded `ubuntu` (all VMs use this user) |
| host group `webservers` | VMs with label `project=devops-lab04` |

### Test — `ansible-inventory -i inventory/yandex_inventory.py --graph`

```
@all:
  |--@ungrouped:
  |--@webservers:
  |  |--lab-vm
```

### Test — `ansible all -i inventory/yandex_inventory.py -m ping`

```
lab-vm | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3.12"
    },
    "changed": false,
    "ping": "pong"
}
```

### Run provision with dynamic inventory

```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab-vm]

TASK [common : Update apt cache] ***********************************************
ok: [lab-vm]

TASK [common : Install common packages] ****************************************
ok: [lab-vm]

...

PLAY RECAP *********************************************************************
lab-vm                     : ok=12   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### What happens when VM IP changes

With static inventory (`hosts.ini`) I would have to find the new IP and update it manually. With the dynamic inventory script, Ansible queries the API every run and always gets the current IP automatically. Destroy and recreate the VM, playbooks still work with zero changes.

### Benefits vs static inventory

| Feature | Static (hosts.ini) | Dynamic (yandex_inventory.py) |
|---|---|---|
| IP management | Manual update | Automatic |
| New VMs | Must add manually | Auto-discovered |
| Scaling to 10+ VMs | Very tedious | Works instantly |
| Deleted VMs | Must remove manually | Disappear automatically |
| Source of truth | The file itself | The cloud API |
