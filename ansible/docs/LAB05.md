# LAB 5 — Ansible Fundamentals Report

---

## 1. Architecture Overview

### Ansible Version

```
ansible --version
ansible [core 2.20.2]
  config file = /home/egrapa/prog/DevOps-Core-Course/ansible/ansible.cfg
  ansible python module location = /usr/lib/python3.14/site-packages/ansible
  executable location = /usr/bin/ansible
  python version = 3.14.3
```

### Control Node

* OS: Arch Linux
* Ansible installed locally
* SSH key authentication used

### Target VM

* Virtualization: KVM/QEMU (virt-manager)
* Network: libvirt NAT (192.168.122.x)
* OS: Ubuntu 25.10 (Questing Quokka)
* Python: `/usr/bin/python3.13`
* Access: SSH (key-based authentication)

---

## Infrastructure Overview

```
Host Machine (Arch Linux)
   │
   ├── Ansible (Control Node)
   │       └── SSH
   │
   └── KVM / QEMU VM (Ubuntu 25.10)
           └── Docker Engine
                  └── Python Application Container
```

---

## Project Structure

```
ansible/
├── inventory/
│   └── hosts.ini
├── inventory/group_vars/
│   └── all.yml (encrypted via Vault)
├── roles/
│   ├── common/
│   ├── docker/
│   └── app_deploy/
├── playbooks/
│   ├── provision.yml
│   ├── deploy.yml
│   └── site.yml
├── ansible.cfg
└── docs/
    └── LAB05.md
```

---

## Why Roles Instead of Monolithic Playbooks?

Roles allow:

* Separation of concerns
* Clear modular structure
* Reusability across projects
* Cleaner main playbooks
* Easier debugging and maintenance

Instead of putting all tasks in one large file, each responsibility is isolated.

---

# 2. Roles Documentation

---

## 2.1 Role: `common`

### Purpose

Prepare base Ubuntu system with required tools for further provisioning and automation.

### Tasks

* Update apt cache
* Install essential packages

### Variables (`defaults/main.yml`)

```yaml
common_packages:
  - python3-pip
  - curl
  - git
  - vim
  - htop
```

### Idempotency

* Uses `apt` with `state: present`
* Uses `cache_valid_time` to prevent unnecessary updates
* No imperative shell commands

### Handlers

None required.

---

## 2.2 Role: `docker`

### Purpose

Install and configure Docker Engine.

### Tasks

* Install required dependencies
* Add Docker GPG key
* Add Docker repository
* Install Docker packages
* Enable and start Docker service
* Add SSH user to docker group
* Install `python3-docker`

### Variables (`defaults/main.yml`)

```yaml
docker_user: yan
```

### Handler

```yaml
- name: restart docker
  service:
    name: docker
    state: restarted
```

Triggered when Docker packages change.

### Idempotency

* `apt_repository` ensures repo is added once
* `apt state=present`
* `service state=started`
* `user append=yes`

Second run produces zero changes.

---

## 2.3 Role: `app_deploy`

### Purpose

Deploy containerized Python application from Docker Hub.

### Tasks

* Login to Docker Hub (via Vault credentials)
* Pull latest image
* Run container
* Wait for port 5000
* Perform HTTP health check

### Variables (Vault — encrypted)

Stored in:

```
inventory/group_vars/all.yml
```

Decrypted content example:

```yaml
dockerhub_username: egrapa
dockerhub_password: <token>

app_name: devops-core-course-lab2
docker_image: "{{ dockerhub_username }}/{{ app_name }}"
docker_image_tag: latest
app_port: 5000
app_container_name: "{{ app_name }}"
```

### Security

* Credentials encrypted with Ansible Vault
* `no_log: true` on login task
* `.vault_pass` excluded from Git
* Only encrypted vault file committed

### Idempotency

* `docker_image source: pull`
* `docker_container state: started`
* Container recreated only if configuration changes

---

# 3. Idempotency Demonstration

## First Run

```
ansible-playbook playbooks/provision.yml
```

Observed:

* Docker repository added
* Packages installed
* Service started

Tasks show `changed`.

---

## Second Run

```
ansible-playbook playbooks/provision.yml
```

Observed:

* All tasks show `ok`
* No `changed`

This confirms idempotency.

---

## Why It Is Idempotent

* Declarative state (`state: present`, `state: started`)
* No shell commands used for state changes
* Ansible checks system state before applying changes

---

# 4. Ansible Vault Usage

Vault file:

```
inventory/group_vars/all.yml
```

Encrypted format:

```
$ANSIBLE_VAULT;1.1;AES256
6238656365...
```

### Vault Strategy

* Vault password provided via `--ask-vault-pass`
* `.vault_pass` not committed
* Encrypted file safely committed
* No plaintext secrets in repository

### Why Vault Is Important

* Prevents credential leakage
* Secure automation
* Enables safe version control

---

# 5. Deployment Verification

## Deployment

```
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

Application deployed successfully.

---

## Container Status

```
ansible webservers -a "docker ps"
```

Output shows:

```
egrapa/devops-app:latest   Up   0.0.0.0:5000->5000/tcp
```

---

## Health Check

```
curl http://192.168.122.221:5000/health
```

Response:

```
{"status":"ok"}
```

Application is accessible and running.

---

# 6. Key Decisions

### Why Use Roles?

To separate infrastructure concerns and maintain clean modular automation.

### How Do Roles Improve Reusability?

Each role can be reused independently across different projects.

### What Makes a Task Idempotent?

It declares a desired state and does nothing if the system already matches that state.

### How Do Handlers Improve Efficiency?

They run only when notified, preventing unnecessary service restarts.

### Why Is Ansible Vault Necessary?

To protect Docker Hub credentials from exposure in Git repositories.

---

# 7. Challenges Encountered

* Vault variables not being loaded due to incorrect group_vars location
* Ensuring correct ansible.cfg was used
* Docker Hub authentication token configuration
* Understanding Ansible variable precedence
* Ensuring idempotency of repository and Docker installation tasks
