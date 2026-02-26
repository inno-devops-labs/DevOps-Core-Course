# Lab 05 — Ansible Fundamentals

## 1. Architecture Overview

**Ansible version:** 2.16+
**Control node OS:** Ubuntu 24.04 LTS (local machine)
**Target VM OS:** Ubuntu 24.04 LTS (Yandex Cloud, from Lab 4 Terraform code)
**Cloud provider:** Yandex Cloud, zone ru-central1-a

### Role structure

```
ansible/
├── inventory/
│   ├── hosts.ini          # Static inventory with VM IP
│   └── yandex.yml         # Dynamic inventory (Yandex Cloud plugin)
├── roles/
│   ├── common/            # Basic system setup
│   │   ├── tasks/main.yml
│   │   └── defaults/main.yml
│   ├── docker/            # Docker installation
│   │   ├── tasks/main.yml
│   │   ├── handlers/main.yml
│   │   └── defaults/main.yml
│   └── app_deploy/        # Run our Python app in Docker
│       ├── tasks/main.yml
│       ├── handlers/main.yml
│       └── defaults/main.yml
├── playbooks/
│   ├── site.yml           # All roles together
│   ├── provision.yml      # Only system setup
│   └── deploy.yml         # Only app deployment
├── group_vars/
│   └── all.yml            # Encrypted with Ansible Vault
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
- Update apt package cache (with cache_valid_time so it doesn't update every run)
- Install essential packages: python3-pip, curl, git, vim, htop, wget, unzip
- Set timezone to Europe/Moscow

**Variables (defaults/main.yml):**
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

**Handlers:** None needed (apt installs don't require a service restart)

**Dependencies:** None

---

### docker role

**Purpose:** Install Docker CE on Ubuntu following the official Docker installation steps.

**Tasks:**
1. Install prerequisites (ca-certificates, curl, gnupg)
2. Create /etc/apt/keyrings directory
3. Download Docker's official GPG key
4. Add Docker apt repository (uses `{{ ansible_distribution_release }}` fact so it works on different Ubuntu versions)
5. Install docker-ce, docker-ce-cli, containerd.io, buildx, compose plugin
6. Start and enable Docker service
7. Add `ubuntu` user to docker group (so we don't need sudo for docker commands)
8. Install python3-docker (needed for Ansible's docker modules to work)

**Variables (defaults/main.yml):**
```yaml
docker_user: ubuntu
```

**Handlers (handlers/main.yml):**
```yaml
- name: restart docker
  service:
    name: docker
    state: restarted
```
Triggered when Docker packages are installed/updated.

**Dependencies:** common role (apt cache must be updated first)

---

### app_deploy role

**Purpose:** Pull our Python app Docker image from Docker Hub and run it as a container.

**Tasks:**
1. Log in to Docker Hub (uses vault credentials, `no_log: true` so password never appears in logs)
2. Pull the Docker image
3. Remove old container if it exists
4. Start new container with port mapping and restart policy
5. Wait for port 5000 to be open
6. Verify `/health` endpoint returns 200

**Variables (defaults/main.yml):**
```yaml
app_port: 5000
app_restart_policy: unless-stopped
app_env_vars: {}
```

Variables from vault (group_vars/all.yml):
```yaml
dockerhub_username: blxxdclxud
dockerhub_password: <encrypted>
app_name: devops-info-service
docker_image: "{{ dockerhub_username }}/{{ app_name }}"
docker_image_tag: latest
app_port: 5000
app_container_name: "{{ app_name }}"
```

**Handlers (handlers/main.yml):**
```yaml
- name: restart app container
```
Triggered when container configuration changes.

**Dependencies:** docker role (Docker must be installed)

---

## 3. Idempotency Demonstration

### First run — `ansible-playbook playbooks/provision.yml`

```
PLAY [Provision web servers] **************************************************

TASK [Gathering Facts] ********************************************************
ok: [lab-vm]

TASK [common : Update apt cache] **********************************************
changed: [lab-vm]

TASK [common : Install common packages] ***************************************
changed: [lab-vm]

TASK [common : Set timezone] **************************************************
changed: [lab-vm]

TASK [docker : Install required packages for Docker repo] *********************
changed: [lab-vm]

TASK [docker : Create keyrings directory] *************************************
changed: [lab-vm]

TASK [docker : Add Docker GPG key] ********************************************
changed: [lab-vm]

TASK [docker : Add Docker repository] *****************************************
changed: [lab-vm]

TASK [docker : Install Docker packages] ***************************************
changed: [lab-vm]

TASK [docker : Ensure Docker service is started and enabled] ******************
changed: [lab-vm]

TASK [docker : Add user to docker group] **************************************
changed: [lab-vm]

TASK [docker : Install python3-docker for Ansible docker modules] *************
changed: [lab-vm]

RUNNING HANDLERS [docker] *****************************************************
TASK [docker : restart docker] ************************************************
changed: [lab-vm]

PLAY RECAP ********************************************************************
lab-vm : ok=13  changed=12  unreachable=0  failed=0  skipped=0
```

Almost everything shows `changed` (yellow) because nothing was installed yet.

### Second run — `ansible-playbook playbooks/provision.yml`

```
PLAY [Provision web servers] **************************************************

TASK [Gathering Facts] ********************************************************
ok: [lab-vm]

TASK [common : Update apt cache] **********************************************
ok: [lab-vm]

TASK [common : Install common packages] ***************************************
ok: [lab-vm]

TASK [common : Set timezone] **************************************************
ok: [lab-vm]

TASK [docker : Install required packages for Docker repo] *********************
ok: [lab-vm]

TASK [docker : Create keyrings directory] *************************************
ok: [lab-vm]

TASK [docker : Add Docker GPG key] ********************************************
ok: [lab-vm]

TASK [docker : Add Docker repository] *****************************************
ok: [lab-vm]

TASK [docker : Install Docker packages] ***************************************
ok: [lab-vm]

TASK [docker : Ensure Docker service is started and enabled] ******************
ok: [lab-vm]

TASK [docker : Add user to docker group] **************************************
ok: [lab-vm]

TASK [docker : Install python3-docker for Ansible docker modules] *************
ok: [lab-vm]

PLAY RECAP ********************************************************************
lab-vm : ok=12  changed=0  unreachable=0  failed=0  skipped=0
```

Zero `changed` on the second run. The handler didn't even trigger because Docker packages weren't reinstalled.

### Analysis

**What changed on first run:** Everything, because the VM was a fresh Ubuntu with no extra software.

**What stayed ok on second run:**
- `apt` module checks if packages are already at `state: present` — if yes, it skips
- `file` module checks if directory already has correct permissions
- `get_url` checks if the file already exists with the same checksum
- `apt_repository` checks if the repo line is already in the sources
- `service` checks if Docker is already started and enabled
- `user` checks if ubuntu is already in the docker group

**What makes our roles idempotent:** We use Ansible's declarative modules (`apt`, `service`, `file`, `user`) instead of shell commands. These modules always check current state before making changes. If the state already matches what we want, they do nothing.

---

## 4. Ansible Vault Usage

### How credentials are stored

All sensitive data lives in `group_vars/all.yml`, which is encrypted with Ansible Vault. The file looks like this in git:

```
$ANSIBLE_VAULT;1.1;AES256
66386134653765386232383236303063623663373634373061653833613437326438663862383834
3564663330343232643665323839633039323438393562660a336439613066663462303933313831
...
```

It is completely unreadable without the vault password.

### Vault password management

The vault password is stored in `ansible/.vault_pass` (a plain text file with just the password). This file is in `.gitignore` so it never gets committed. The `ansible.cfg` points to it:

```ini
vault_password_file = .vault_pass
```

This way we don't have to type `--ask-vault-pass` every time.

### Commands used

```bash
# Encrypt the file (run this after creating/editing it as plaintext)
ansible-vault encrypt group_vars/all.yml

# View encrypted file to verify
ansible-vault view group_vars/all.yml

# Edit encrypted file
ansible-vault edit group_vars/all.yml
```

### Why Ansible Vault is necessary

If we committed our Docker Hub password to git, anyone with access to the repo could use our credentials. Ansible Vault encrypts the file with AES-256, so the encrypted version is safe to commit. The only thing that must stay secret is the vault password itself, which we keep out of git via `.gitignore`.

---

## 5. Deployment Verification

### Terminal output from `ansible-playbook playbooks/deploy.yml`

```
PLAY [Deploy application] *****************************************************

TASK [Gathering Facts] ********************************************************
ok: [lab-vm]

TASK [app_deploy : Log in to Docker Hub] **************************************
ok: [lab-vm]

TASK [app_deploy : Pull Docker image] *****************************************
changed: [lab-vm]

TASK [app_deploy : Remove old container if exists] ****************************
ok: [lab-vm]

TASK [app_deploy : Run application container] *********************************
changed: [lab-vm]

TASK [app_deploy : Wait for application to be ready] **************************
ok: [lab-vm]

TASK [app_deploy : Verify health endpoint] ************************************
ok: [lab-vm]

TASK [app_deploy : Print health check result] *********************************
ok: [lab-vm] => {
    "msg": "App is healthy: 200"
}

PLAY RECAP ********************************************************************
lab-vm : ok=8  changed=2  unreachable=0  failed=0  skipped=0
```

### Container status — `ansible webservers -a "docker ps"`

```
lab-vm | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                               COMMAND                  CREATED         STATUS         PORTS                    NAMES
a3f2c1d4e8b7   blxxdclxud/devops-info-service:latest   "python -m uvicorn a…"   2 minutes ago   Up 2 minutes   0.0.0.0:5000->5000/tcp   devops-info-service
```

### Health check — `curl http://<VM-IP>:5000/health`

```json
{"status": "ok"}
```

### Main endpoint — `curl http://<VM-IP>:5000/`

```json
{"message": "DevOps Info Service", "time": "..."}
```

---

## 6. Key Decisions

**Why use roles instead of plain playbooks?**
Roles split your code into focused, reusable pieces. If I need to install Docker on a different project, I just copy the docker role. A plain playbook would be one huge file where everything is mixed together, hard to read and impossible to reuse across projects.

**How do roles improve reusability?**
Each role is self-contained with its own variables, handlers, and tasks. You can share roles via Ansible Galaxy. Other playbooks can include just the roles they need. For example, `provision.yml` uses `common` and `docker`, while `deploy.yml` only uses `app_deploy`.

**What makes a task idempotent?**
Using Ansible's built-in modules instead of shell commands. Modules like `apt`, `service`, `file`, and `user` check the current state first. They only make a change if the current state is different from the desired state. Running `apt: name=docker-ce state=present` ten times has the same result as running it once.

**How do handlers improve efficiency?**
Handlers only run once at the end of a play, even if notified multiple times. If ten tasks all notify `restart docker`, Docker restarts only once. Without handlers, you would either restart too many times (wasting time) or forget to restart at all (breaking things).

**Why is Ansible Vault necessary?**
We need Docker Hub credentials to pull private images. Storing them as plaintext in the repo would be a security risk — anyone with read access to the repo gets the credentials. Vault encrypts them with AES-256 so the encrypted file is safe to commit. Only the vault password needs to stay secret, and we keep it out of git.

---

## 7. Challenges

- The VM from Lab 4 was already destroyed, so I recreated it using `terraform apply` from the existing Lab 4 code
- `ansible_distribution_release` fact is needed in the Docker repo line — this makes the playbook work on both Ubuntu 22.04 (jammy) and 24.04 (noble) without changing code
- `python3-docker` must be installed on the target VM for Ansible's docker modules to work; this is easy to miss
- `no_log: true` on the Docker Hub login task is required so the password never appears in Ansible output or CI logs

---

## Bonus: Dynamic Inventory with Yandex Cloud

### Why dynamic inventory?

With static inventory (`hosts.ini`), I have to manually update the IP every time I recreate the VM. With dynamic inventory, Ansible queries the Yandex Cloud API directly and automatically discovers running VMs. If the IP changes, nothing needs to be updated.

### Setup

**Install the collection:**
```bash
ansible-galaxy collection install yandex.cloud
pip install yandexcloud
```

**Configuration file:** `inventory/yandex.yml`
```yaml
plugin: yandex.cloud.yandex_compute
auth_kind: serviceaccountfile
service_account_file: /home/blxxdclxud/yc-key.json
folder_id: b1ga4ttr9f92otmhh4cc
filters:
  - status = "RUNNING"
compose:
  ansible_host: network_interfaces[0].primary_v4_address.one_to_one_nat.address
  ansible_user: "'ubuntu'"
keyed_groups:
  - key: labels.get("project", "ungrouped")
    prefix: ""
    separator: ""
groups:
  webservers: "'devops-lab04' in labels.get('project', '')"
```

### Authentication

Same service account key file used in Lab 4 Terraform (`/home/blxxdclxud/yc-key.json`). The key file is in `.gitignore` on both Terraform and Ansible sides.

### How cloud metadata maps to Ansible variables

| Ansible variable | Yandex Cloud field |
|---|---|
| `ansible_host` | `network_interfaces[0].primary_v4_address.one_to_one_nat.address` (public IP) |
| `ansible_user` | hardcoded to `ubuntu` (all our VMs use this) |
| host group `webservers` | VMs with label `project=devops-lab04` |

### Test — `ansible-inventory --graph -i inventory/yandex.yml`

```
@all:
  |--@ungrouped:
  |--@webservers:
  |  |--lab-vm
  |--@devops-lab04:
  |  |--lab-vm
```

### Test — `ansible all -i inventory/yandex.yml -m ping`

```
lab-vm | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

### Running playbooks with dynamic inventory

```bash
ansible-playbook -i inventory/yandex.yml playbooks/provision.yml
ansible-playbook -i inventory/yandex.yml playbooks/deploy.yml
```

### What happens when VM IP changes

With static inventory I would have to find the new IP and update `hosts.ini` manually. With the Yandex Cloud plugin, Ansible queries the API every time and always gets the current IP. I can destroy and recreate the VM and my playbooks still work with no changes.

### Benefits vs static inventory

| Feature | Static (hosts.ini) | Dynamic (yandex.yml) |
|---|---|---|
| IP management | Manual update | Automatic |
| New VMs | Must add manually | Auto-discovered |
| Scaling to 10+ VMs | Very tedious | Works instantly |
| Deleted VMs | Must remove manually | Disappear automatically |
| Source of truth | The file itself | The cloud API |
