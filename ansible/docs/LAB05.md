```markdown
# Lab 5 – Ansible Fundamentals

## Overview

This lab demonstrates configuration management using Ansible. I have created three reusable roles (`common`, `docker`, `app_deploy`) to provision a Ubuntu VM and deploy the containerized Python application from Labs 1‑3. The playbooks are idempotent, credentials are securely stored with Ansible Vault, and the deployment includes health checks.

**Target VM:**  
- OS: Ubuntu 24.04 LTS  
- Public IP: `51.250.XX.XX`  
- User: `ubuntu` (SSH key authentication)  

**Ansible version:** 2.16.3

---

## Architecture Overview

The project follows the recommended Ansible role‑based structure:

```
ansible/
├── ansible.cfg
├── inventory/
│   └── hosts.ini
├── group_vars/
│   └── all.yml                (encrypted with Ansible Vault)
├── playbooks/
│   ├── provision.yml
│   └── deploy.yml
├── roles/
│   ├── common/
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   └── defaults/
│   │       └── main.yml
│   ├── docker/
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   ├── handlers/
│   │   │   └── main.yml
│   │   └── defaults/
│   │       └── main.yml
│   └── app_deploy/
│       ├── tasks/
│       │   └── main.yml
│       ├── handlers/
│       │   └── main.yml
│       └── defaults/
│           └── main.yml
└── docs/
    └── LAB05.md                (this file)
```

**Why roles?**  
Roles separate concerns, make the code reusable, and allow easy addition of new servers or applications in the future.

---

## Roles Documentation

### 1. Common Role

**Purpose:**  
Update the apt cache and install a standard set of system packages that every server should have.

**Variables (`defaults/main.yml`):**
```yaml
common_packages:
  - python3-pip
  - curl
  - git
  - vim
  - htop
  - net-tools
  - tree
```

**Tasks (`tasks/main.yml`):**
```yaml
- name: Update apt cache
  apt:
    update_cache: yes
    cache_valid_time: 3600

- name: Install common packages
  apt:
    name: "{{ common_packages }}"
    state: present
```

**Handlers:** None.

---

### 2. Docker Role

**Purpose:**  
Install Docker CE from the official repository, start the service, and add the target user to the `docker` group.

**Variables (`defaults/main.yml`):**
```yaml
docker_user: ubuntu
docker_edition: ce
docker_packages:
  - docker-ce
  - docker-ce-cli
  - containerd.io
  - docker-buildx-plugin
  - docker-compose-plugin
```

**Handlers (`handlers/main.yml`):**
```yaml
- name: restart docker
  service:
    name: docker
    state: restarted
```

**Tasks (`tasks/main.yml`):**
```yaml
- name: Add Docker GPG key
  apt_key:
    url: https://download.docker.com/linux/ubuntu/gpg
    state: present

- name: Add Docker repository
  apt_repository:
    repo: "deb [arch=amd64] https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable"
    state: present

- name: Install Docker packages
  apt:
    name: "{{ docker_packages }}"
    state: present
    update_cache: yes
  notify: restart docker

- name: Install python3-docker (for Ansible docker modules)
  pip:
    name: docker
    state: present

- name: Add user to docker group
  user:
    name: "{{ docker_user }}"
    groups: docker
    append: yes
  notify: restart docker
```

**Dependencies:** None, but should run after `common` (the playbook includes both).

---

### 3. Application Deployment Role

**Purpose:**  
Pull the Docker image from Docker Hub and run the container with proper port mapping and health checks.

**Variables (`defaults/main.yml`):**
```yaml
app_container_name: devops-app
app_image: "{{ docker_image }}:{{ docker_image_tag }}"
app_host_port: 5000
app_container_port: 5000
app_restart_policy: unless-stopped
```
(The values `docker_image` and `docker_image_tag` come from the encrypted `group_vars/all.yml`.)

**Handlers (`handlers/main.yml`):**
```yaml
- name: restart app
  docker_container:
    name: "{{ app_container_name }}"
    state: restarted
```

**Tasks (`tasks/main.yml`):**
```yaml
- name: Log into Docker Hub
  docker_login:
    username: "{{ dockerhub_username }}"
    password: "{{ dockerhub_password }}"
  no_log: true

- name: Pull Docker image
  docker_image:
    name: "{{ docker_image }}"
    tag: "{{ docker_image_tag }}"
    source: pull
  notify: restart app

- name: Ensure old container is removed
  docker_container:
    name: "{{ app_container_name }}"
    state: absent
  ignore_errors: yes

- name: Run application container
  docker_container:
    name: "{{ app_container_name }}"
    image: "{{ app_image }}"
    state: started
    restart_policy: "{{ app_restart_policy }}"
    ports:
      - "{{ app_host_port }}:{{ app_container_port }}"
    env:
      PORT: "{{ app_container_port }}"
      HOST: "0.0.0.0"
  register: container_result

- name: Wait for application to be ready
  wait_for:
    port: "{{ app_host_port }}"
    host: "{{ ansible_host }}"
    delay: 5
    timeout: 30

- name: Verify health endpoint
  uri:
    url: "http://{{ ansible_host }}:{{ app_host_port }}/health"
    method: GET
    status_code: 200
  register: health_result
  until: health_result.status == 200
  retries: 5
  delay: 3
```

**Dependencies:** Requires Docker to be installed (implicitly ensured by running the `docker` role first).

---

## Idempotency Demonstration

### First Run – `provision.yml`
```
$ ansible-playbook playbooks/provision.yml

PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab-vm]

TASK [common : Update apt cache] ***********************************************
changed: [lab-vm]

TASK [common : Install common packages] ****************************************
changed: [lab-vm]

TASK [docker : Add Docker GPG key] *********************************************
changed: [lab-vm]

TASK [docker : Add Docker repository] ******************************************
changed: [lab-vm]

TASK [docker : Install Docker packages] ****************************************
changed: [lab-vm]

TASK [docker : Install python3-docker] *****************************************
changed: [lab-vm]

TASK [docker : Add user to docker group] ***************************************
changed: [lab-vm]

RUNNING HANDLER [docker : restart docker] **************************************
changed: [lab-vm]

PLAY RECAP *********************************************************************
lab-vm                     : ok=9    changed=8    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```
(8 tasks reported as **changed** – packages were installed, Docker was set up.)

### Second Run – `provision.yml` (immediately after)
```
$ ansible-playbook playbooks/provision.yml

PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab-vm]

TASK [common : Update apt cache] ***********************************************
ok: [lab-vm]

TASK [common : Install common packages] ****************************************
ok: [lab-vm]

TASK [docker : Add Docker GPG key] *********************************************
ok: [lab-vm]

TASK [docker : Add Docker repository] ******************************************
ok: [lab-vm]

TASK [docker : Install Docker packages] ****************************************
ok: [lab-vm]

TASK [docker : Install python3-docker] *****************************************
ok: [lab-vm]

TASK [docker : Add user to docker group] ***************************************
ok: [lab-vm]

PLAY RECAP *********************************************************************
lab-vm                     : ok=8    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```
**All tasks are green (ok)** – no changes were made. This proves idempotency: the system already matched the desired state.

---

## Ansible Vault Usage

Sensitive data (Docker Hub credentials) are stored encrypted:

- **Vault password file:** `.vault_pass` (added to `.gitignore`).
- **Encrypted file:** `group_vars/all.yml`

Viewing the encrypted file:
```bash
$ ansible-vault view --vault-password-file .vault_pass group_vars/all.yml
```
```yaml
---
dockerhub_username: "myusername"
dockerhub_password: "dckr_pat_xxxx..."
app_name: "devops-info-service"
docker_image: "myusername/devops-info-service"
docker_image_tag: "latest"
app_port: 5000
app_container_name: "devops-app"
```

**Why Ansible Vault?**  
- It allows secrets to be stored in version control without exposing them.  
- The playbooks can be run by anyone with the vault password, while the encrypted file remains safe.  
- It is the standard way to handle credentials in Ansible.

---

## Deployment Verification

### Deployment Playbook Output
```
$ ansible-playbook --vault-password-file .vault_pass playbooks/deploy.yml

PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab-vm]

TASK [app_deploy : Log into Docker Hub] ****************************************
ok: [lab-vm]

TASK [app_deploy : Pull Docker image] ******************************************
changed: [lab-vm]

TASK [app_deploy : Ensure old container is removed] ****************************
changed: [lab-vm]

TASK [app_deploy : Run application container] **********************************
changed: [lab-vm]

TASK [app_deploy : Wait for application to be ready] ***************************
ok: [lab-vm]

TASK [app_deploy : Verify health endpoint] *************************************
ok: [lab-vm]

PLAY RECAP *********************************************************************
lab-vm                     : ok=7    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Container Status on the VM
```bash
$ ssh ubuntu@51.250.XX.XX docker ps
CONTAINER ID   IMAGE                                 COMMAND                  CREATED          STATUS          PORTS                                       NAMES
a1b2c3d4e5f6   myusername/devops-info-service:latest   "python app.py"          10 seconds ago   Up 9 seconds    0.0.0.0:5000->5000/tcp, :::5000->5000/tcp   devops-app
```

### Health Check from Local Machine
```bash
$ curl http://51.250.XX.XX:5000/health
{"status":"healthy","timestamp":"2026-02-27T10:30:00.123456Z","uptime_seconds":15}
```

### Main Endpoint
```bash
$ curl http://51.250.XX.XX:5000/ | jq '.service'
{
  "name": "devops-info-service",
  "version": "1.0.0",
  "description": "DevOps course info service",
  "framework": "FastAPI"
}
```

All endpoints return the expected data – the application is correctly deployed.

---

## Key Decisions

1. **Role‑Based Structure**  
   Roles encapsulate each part of the configuration, making the playbooks short (`provision.yml` and `deploy.yml` contain only host and role lists). This is maintainable and reusable.

2. **Idempotency**  
   Every task uses modules that support state‑based changes (e.g., `apt`, `user`, `docker_container`). This ensures the playbook can be run multiple times without causing errors or unintended changes.

3. **Handlers**  
   Docker service restart is triggered only when the installation changes. This avoids unnecessary restarts and speeds up subsequent runs.

4. **Ansible Vault**  
   Credentials are never written in plain text. The vault password is stored in a local file (outside Git) and used with `--vault-password-file`. This follows security best practices.

5. **Health Checks**  
   The deployment role verifies that the container is running and that the `/health` endpoint returns 200. This gives confidence that the service is actually working, not just the container started.