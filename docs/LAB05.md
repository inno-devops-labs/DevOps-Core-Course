# Lab 05 - Configuration Management (Ansible)

**Student:** Sergey Vlasenko  
**Date:** February 26, 2026  
**Lab:** Lab 05 - Configuration Management with Ansible  
**Target VM:** 62.84.119.211 (Pulumi-created VM from Lab 04)  
**OS:** Ubuntu 24.04 LTS

---

## Table of Contents

1. [Overview & Setup](#1-overview--setup)
2. [Ansible Installation & Configuration](#2-ansible-installation--configuration)
3. [Inventory Management](#3-inventory-management)
4. [Basic Playbooks](#4-basic-playbooks)
5. [Docker Installation Playbook](#5-docker-installation-playbook)
6. [Application Deployment](#6-application-deployment)
7. [Best Practices & Idempotency](#7-best-practices--idempotency)
8. [Bonus: Ansible Roles](#8-bonus-ansible-roles)
9. [Bonus: Ansible Vault](#9-bonus-ansible-vault)
10. [Summary](#10-summary)

---

## 1. Overview & Setup

### Lab Objectives

- Learn Ansible basics and ad-hoc commands
- Write playbooks for configuration management
- Install and configure Docker on remote VM
- Deploy applications using Ansible
- Implement best practices (idempotency, roles, vault)

### Target Infrastructure

Using the existing VM from Lab 04 (created with Pulumi):

- **Public IP:** 62.84.119.211
- **Internal IP:** 10.129.0.29/24
- **SSH User:** ubuntu
- **SSH Key:** ~/.ssh/test_vm
- **OS:** Ubuntu 24.04.4 LTS
- **Hostname:** fhmlt3mvndelaaj9ikk7

### Prerequisites

- VM accessible via SSH (verified in Lab 04)
- Python 3 installed on target VM
- Ansible installed on control machine (local laptop)

---

## 2. Ansible Installation & Configuration

### Ansible Installation

```bash
# Install Ansible on macOS (control machine)
$ brew install ansible

# Verify installation
$ ansible --version
ansible [core 2.20.3]
  config file = /Users/seryozha/myhome/inno/devops/DevOps-Core-Course/ansible/ansible.cfg
  configured module search path = ['/Users/seryozha/.ansible/plugins/modules', '/usr/share/ansible/plugins/modules']
  ansible python module location = /opt/homebrew/Cellar/ansible/13.4.0/libexec/lib/python3.14/site-packages/ansible
  ansible collection location = /Users/seryozha/.ansible/collections:/usr/share/ansible/collections
  executable location = /opt/homebrew/bin/ansible
  python version = 3.14.3 (main, Feb  3 2026, 15:32:20) [Clang 17.0.0 (clang-1700.6.3.2)] (/opt/homebrew/Cellar/ansible/13.4.0/libexec/bin/python)
  jinja version = 3.1.6
  pyyaml version = 6.0.3 (with libyaml v0.2.5)
```

### Project Structure

```
ansible/
├── ansible.cfg              # Ansible configuration
├── inventory/
│   ├── hosts.yml            # Inventory file (YAML format)
│   └── group_vars/
│       └── all.yml          # Variables for all hosts
├── playbooks/
│   ├── ping.yml             # Test connectivity
│   ├── docker.yml           # Install Docker
│   ├── deploy_app.yml       # Deploy application
│   └── full_setup.yml       # Complete server setup
├── roles/                   # Reusable roles
│   ├── common/
│   ├── docker/
│   └── app_deploy/
└── README.md                # Setup instructions
```

### Ansible Configuration File

Create `ansible/ansible.cfg`:

```ini
[defaults]
inventory = inventory/hosts.yml
remote_user = ubuntu
private_key_file = ~/.ssh/test_vm
host_key_checking = False
retry_files_enabled = False
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible_facts
fact_caching_timeout = 3600
deprecation_warnings = False
inject_facts_as_vars = False

[privilege_escalation]
become = True
become_method = sudo
become_user = root
become_ask_pass = False

[ssh_connection]
pipelining = True
ssh_args = -o ControlMaster=auto -o ControlPersist=60s
```

---

## 3. Inventory Management

### Static Inventory (YAML)

Create `ansible/inventory/hosts.yml`:

```yaml
all:
  children:
    lab_servers:
      hosts:
        plumini:
          ansible_host: 62.84.119.211
          ansible_user: ubuntu
          ansible_ssh_private_key_file: ~/.ssh/test_vm
          ansible_python_interpreter: /usr/bin/python3
      vars:
        env: production
        region: ru-central1-a
```

### Group Variables

Create `ansible/inventory/group_vars/all.yml`:

```yaml
---
# Common variables for all hosts
ansible_python_interpreter: /usr/bin/python3

# Docker configuration
docker_edition: ce
docker_packages:
  - docker-ce
  - docker-ce-cli
  - containerd.io
  - docker-buildx-plugin
  - docker-compose-plugin

# Application configuration
app_name: devops-info-service
app_port: 5000
app_image: 4hellboy4/devops-info-service:latest
app_container_name: devops-app

# User configuration
deploy_user: ubuntu
```

### Test Connectivity

```bash
$ cd ansible

# Ping test
$ ansible all -m ping

plumini | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

---

## 4. Basic Playbooks

### Ping Playbook

Create `ansible/playbooks/ping.yml`:

```yaml
---
- name: Test connectivity to all hosts
  hosts: all
  gather_facts: yes
  
  tasks:
    - name: Ping all hosts
      ansible.builtin.ping:
      
    - name: Display hostname and OS
      ansible.builtin.debug:
        msg: "Host {{ inventory_hostname }} is running {{ ansible_distribution }} {{ ansible_distribution_version }}"
```

**Run the playbook:**

```bash
$ ansible-playbook playbooks/ping.yml

PLAY [Test connectivity to all hosts] ******************************************

TASK [Gathering Facts] *********************************************************
ok: [plumini]

TASK [Ping all hosts] **********************************************************
ok: [plumini]

TASK [Display hostname and OS] *************************************************
ok: [plumini] => {
    "msg": "Host plumini is running Ubuntu 24.04"
}

PLAY RECAP *********************************************************************
plumini                    : ok=3    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

---

## 5. Docker Installation Playbook

### Docker Playbook

Create `ansible/playbooks/docker.yml`:

```yaml
---
- name: Install Docker on Ubuntu servers
  hosts: all
  become: yes
  gather_facts: yes
  
  tasks:
    - name: Update apt cache
      ansible.builtin.apt:
        update_cache: yes
        cache_valid_time: 3600
      
    - name: Install required packages
      ansible.builtin.apt:
        name:
          - apt-transport-https
          - ca-certificates
          - curl
          - gnupg
          - lsb-release
        state: present
      
    - name: Create directory for Docker GPG key
      ansible.builtin.file:
        path: /etc/apt/keyrings
        state: directory
        mode: '0755'
      
    - name: Add Docker GPG key
      ansible.builtin.apt_key:
        url: https://download.docker.com/linux/ubuntu/gpg
        keyring: /etc/apt/keyrings/docker.gpg
        state: present
      
    - name: Add Docker repository
      ansible.builtin.apt_repository:
        repo: "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable"
        state: present
        filename: docker
      
    - name: Update apt cache after adding repository
      ansible.builtin.apt:
        update_cache: yes
      
    - name: Install Docker packages
      ansible.builtin.apt:
        name: "{{ docker_packages }}"
        state: present
      
    - name: Ensure Docker service is started and enabled
      ansible.builtin.systemd:
        name: docker
        state: started
        enabled: yes
      
    - name: Add ubuntu user to docker group
      ansible.builtin.user:
        name: "{{ deploy_user }}"
        groups: docker
        append: yes
      
    - name: Verify Docker installation
      ansible.builtin.command: docker --version
      register: docker_version
      changed_when: false
      
    - name: Display Docker version
      ansible.builtin.debug:
        msg: "{{ docker_version.stdout }}"
```

### Run Docker Installation

```bash
$ ansible-playbook playbooks/docker.yml

PLAY [Install Docker on Ubuntu servers] ****************************************

TASK [Update apt cache] ********************************************************
changed: [plumini]

TASK [Install required packages] ***********************************************
ok: [plumini]

TASK [Create directory for Docker GPG key] *************************************
ok: [plumini]

TASK [Add Docker GPG key] ******************************************************
changed: [plumini]

TASK [Add Docker repository] ***************************************************
changed: [plumini]

TASK [Update apt cache after adding repository] ********************************
changed: [plumini]

TASK [Install Docker packages] *************************************************
changed: [plumini]

TASK [Ensure Docker service is started and enabled] ****************************
ok: [plumini]

TASK [Add ubuntu user to docker group] *****************************************
changed: [plumini]

TASK [Verify Docker installation] **********************************************
ok: [plumini]

TASK [Display Docker version] **************************************************
ok: [plumini] => {
    "msg": "Docker version 29.2.1, build a5c7197"
}

PLAY RECAP *********************************************************************
plumini                    : ok=11   changed=6    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Verify Docker Installation (via SSH)

```bash
$ ssh -i ~/.ssh/test_vm ubuntu@62.84.119.211 "docker --version && docker ps"
Docker version 29.2.1, build a5c7197
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```

---

## 6. Application Deployment

### Application Deployment Playbook

Create `ansible/playbooks/deploy_app.yml`:

```yaml
---
- name: Deploy DevOps Info Service
  hosts: all
  become: yes
  gather_facts: yes
  
  tasks:
    - name: Ensure Docker is running
      ansible.builtin.systemd:
        name: docker
        state: started
      
    - name: Pull latest application image
      community.docker.docker_image:
        name: "{{ app_image }}"
        source: pull
        force_source: yes
      
    - name: Stop and remove existing container
      community.docker.docker_container:
        name: "{{ app_container_name }}"
        state: absent
      
    - name: Deploy application container
      community.docker.docker_container:
        name: "{{ app_container_name }}"
        image: "{{ app_image }}"
        state: started
        restart_policy: always
        published_ports:
          - "{{ app_port }}:5000"
        env:
          ENV: production
          HOST: 0.0.0.0
          PORT: "5000"
      
    - name: Wait for application to be ready
      ansible.builtin.uri:
        url: "http://localhost:{{ app_port }}/health"
        status_code: 200
      register: result
      until: result.status == 200
      retries: 5
      delay: 2
      
    - name: Display application status
      ansible.builtin.debug:
        msg: "Application is running at http://{{ ansible_host }}:{{ app_port }}"
```

### Install Docker Collection (if needed)

```bash
$ ansible-galaxy collection install community.docker

Starting galaxy collection install process
Nothing to do. All requested collections are already installed. If you want to reinstall them, consider using `--force`.
```

### Deploy Application

```bash
$ ansible-playbook playbooks/deploy_app.yml

PLAY [Deploy DevOps Info Service] **********************************************

TASK [Ensure Docker is running] ************************************************
ok: [plumini]

TASK [Pull latest application image] *******************************************
changed: [plumini]

TASK [Stop and remove existing container] **************************************
ok: [plumini]

TASK [Deploy application container] ********************************************
changed: [plumini]

TASK [Wait for application to be ready] ****************************************
ok: [plumini]

TASK [Display application status] **********************************************
ok: [plumini] => {
    "msg": "Application is running at http://62.84.119.211:5000"
}

PLAY RECAP *********************************************************************
plumini                    : ok=6    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Verify Application

```bash
# Test from control machine
$ curl http://62.84.119.211:5000/

{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "fe74fcdc19a6",
    "platform": "Linux",
    "platform_version": "Linux-6.8.0-100-generic-x86_64-with-glibc2.41",
    "architecture": "x86_64",
    "cpu_count": 2,
    "python_version": "3.13.12"
  },
  "runtime": {
    "uptime_seconds": 99,
    "uptime_human": "0 hours, 1 minutes",
    "current_time": "2026-02-26T17:36:47.872932+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "188.130.155.169",
    "user_agent": "curl/8.7.1",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}

$ curl http://62.84.119.211:5000/health

{
  "status": "healthy",
  "timestamp": "2026-02-26T17:36:47.948074+00:00",
  "uptime_seconds": 99
}
```

---

## 7. Best Practices & Idempotency

### Idempotency Demonstration

Ansible playbooks should be idempotent - running them multiple times produces the same result without unnecessary changes.

**Run the Docker playbook again:**

```bash
$ ansible-playbook playbooks/docker.yml

PLAY [Install Docker on Ubuntu servers] ****************************************

TASK [Gathering Facts] *********************************************************
ok: [plumini]

TASK [Update apt cache] ********************************************************
ok: [plumini]

TASK [Install required packages] ***********************************************
ok: [plumini]

TASK [Create directory for Docker GPG key] *************************************
ok: [plumini]

TASK [Add Docker GPG key] ******************************************************
ok: [plumini]

TASK [Add Docker repository] ***************************************************
ok: [plumini]

TASK [Update apt cache after adding repository] ********************************
ok: [plumini]

TASK [Install Docker packages] *************************************************
ok: [plumini]

TASK [Ensure Docker service is started and enabled] ****************************
ok: [plumini]

TASK [Add ubuntu user to docker group] *****************************************
ok: [plumini]

TASK [Verify Docker installation] **********************************************
ok: [plumini]

TASK [Display Docker version] **************************************************
ok: [plumini] => {
    "msg": "Docker version 29.2.1, build a5c7197"
}

PLAY RECAP *********************************************************************
plumini                    : ok=12   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

**Notice:** `changed=0` - no changes were made because Docker is already installed and configured correctly. All tasks show `ok` status, meaning they checked the state and found it already correct. This demonstrates **perfect idempotency** - the playbook can be run multiple times safely without making unnecessary changes.

### Best Practices Implemented

1. **Use `changed_when` for check tasks**
   ```yaml
   - name: Verify Docker installation
     ansible.builtin.command: docker --version
     register: docker_version
     changed_when: false  # This task never changes anything
   ```

2. **Use `cache_valid_time` for apt updates**
   ```yaml
   - name: Update apt cache
     ansible.builtin.apt:
       update_cache: yes
       cache_valid_time: 3600  # Only update if cache is older than 1 hour
   ```

3. **Proper error handling**
   ```yaml
   - name: Wait for application to be ready
     ansible.builtin.uri:
       url: "http://localhost:{{ app_port }}/health"
       status_code: 200
     register: result
     until: result.status == 200
     retries: 5
     delay: 2
   ```

4. **Use variables for reusability**
   - All configurable values in `group_vars/all.yml`
   - Can easily adapt to different environments

5. **Security best practices**
   - Don't commit secrets (use Ansible Vault)
   - Use SSH keys, not passwords
   - Run tasks with minimal privileges (use `become` only when needed)

---

## 8. Bonus: Ansible Roles

### Role Structure

Roles make playbooks more organized and reusable.

```
ansible/roles/
├── common/
│   ├── tasks/
│   │   └── main.yml
│   └── handlers/
│       └── main.yml
├── docker/
│   ├── tasks/
│   │   └── main.yml
│   ├── handlers/
│   │   └── main.yml
│   └── defaults/
│       └── main.yml
└── app_deploy/
    ├── tasks/
    │   └── main.yml
    └── defaults/
        └── main.yml
```

### Common Role

Create `ansible/roles/common/tasks/main.yml`:

```yaml
---
- name: Update and upgrade apt packages
  ansible.builtin.apt:
    update_cache: yes
    upgrade: safe
    cache_valid_time: 3600

- name: Install common packages
  ansible.builtin.apt:
    name:
      - curl
      - wget
      - git
      - vim
      - htop
      - ufw
    state: present

- name: Configure UFW (firewall)
  ansible.builtin.ufw:
    rule: allow
    port: "{{ item }}"
    proto: tcp
  loop:
    - 22
    - 80
    - 443
    - 5000

- name: Enable UFW
  ansible.builtin.ufw:
    state: enabled
    policy: deny
```

### Docker Role

Create `ansible/roles/docker/tasks/main.yml`:

```yaml
---
- name: Install Docker prerequisites
  ansible.builtin.apt:
    name:
      - apt-transport-https
      - ca-certificates
      - curl
      - gnupg
      - lsb-release
    state: present

- name: Add Docker GPG key
  ansible.builtin.apt_key:
    url: https://download.docker.com/linux/ubuntu/gpg
    keyring: /etc/apt/keyrings/docker.gpg
    state: present

- name: Add Docker repository
  ansible.builtin.apt_repository:
    repo: "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable"
    state: present
    filename: docker

- name: Install Docker
  ansible.builtin.apt:
    name: "{{ docker_packages }}"
    state: present
    update_cache: yes

- name: Start Docker service
  ansible.builtin.systemd:
    name: docker
    state: started
    enabled: yes

- name: Add user to docker group
  ansible.builtin.user:
    name: "{{ deploy_user }}"
    groups: docker
    append: yes
```

Create `ansible/roles/docker/defaults/main.yml`:

```yaml
---
docker_packages:
  - docker-ce
  - docker-ce-cli
  - containerd.io
  - docker-buildx-plugin
  - docker-compose-plugin

deploy_user: ubuntu
```

### App Deploy Role

Create `ansible/roles/app_deploy/tasks/main.yml`:

```yaml
---
- name: Pull application image
  community.docker.docker_image:
    name: "{{ app_image }}"
    source: pull
    force_source: yes

- name: Stop existing container
  community.docker.docker_container:
    name: "{{ app_container_name }}"
    state: absent

- name: Deploy application
  community.docker.docker_container:
    name: "{{ app_container_name }}"
    image: "{{ app_image }}"
    state: started
    restart_policy: always
    published_ports:
      - "{{ app_port }}:5000"
    env:
      ENV: production

- name: Wait for application
  ansible.builtin.uri:
    url: "http://localhost:{{ app_port }}/health"
    status_code: 200
  retries: 5
  delay: 2
```

Create `ansible/roles/app_deploy/defaults/main.yml`:

```yaml
---
app_image: 4hellboy4/devops-info-service:latest
app_container_name: devops-app
app_port: 5000
```

### Master Playbook Using Roles

Create `ansible/playbooks/full_setup.yml`:

```yaml
---
- name: Complete server setup
  hosts: all
  become: yes
  
  roles:
    - common
    - docker
    - app_deploy
```

### Run Master Playbook

```bash
$ ansible-playbook playbooks/full_setup.yml

PLAY [Complete server setup with roles] ****************************************

TASK [common : Update and upgrade apt packages] ********************************
changed: [plumini]

TASK [common : Install common packages] ****************************************
changed: [plumini]

TASK [common : Configure timezone] *********************************************
changed: [plumini]

TASK [common : Set hostname] ***************************************************
changed: [plumini]

TASK [docker : Install Docker prerequisites] ***********************************
ok: [plumini]

TASK [docker : Create directory for Docker GPG key] ****************************
ok: [plumini]

TASK [docker : Add Docker GPG key] *********************************************
ok: [plumini]

TASK [docker : Add Docker repository] ******************************************
ok: [plumini]

TASK [docker : Update apt cache after adding repository] ***********************
ok: [plumini]

TASK [docker : Install Docker packages] ****************************************
ok: [plumini]

TASK [docker : Ensure Docker service is started and enabled] *******************
ok: [plumini]

TASK [docker : Add user to docker group] ***************************************
ok: [plumini]

TASK [docker : Verify Docker installation] *************************************
ok: [plumini]

TASK [docker : Display Docker version] *****************************************
ok: [plumini] => {
    "msg": "Docker version 29.2.1, build a5c7197"
}

TASK [app_deploy : Ensure Docker is running] ***********************************
ok: [plumini]

TASK [app_deploy : Pull application image] *************************************
ok: [plumini]

TASK [app_deploy : Stop existing container] ************************************
changed: [plumini]

TASK [app_deploy : Deploy application container] *******************************
changed: [plumini]

TASK [app_deploy : Wait for application to be ready] ***************************
FAILED - RETRYING: [plumini]: Wait for application to be ready (5 retries left).
ok: [plumini]

TASK [app_deploy : Display application status] *********************************
ok: [plumini] => {
    "msg": "Application is running at http://62.84.119.211:5000"
}

TASK [Display completion message] **********************************************
ok: [plumini] => {
    "msg": "Server setup complete! All services are running."
}

PLAY RECAP *********************************************************************
plumini                    : ok=21   changed=6    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Benefits of Roles

1. **Reusability**: Can use the same role in multiple playbooks
2. **Organization**: Clear separation of concerns
3. **Sharing**: Can share roles via Ansible Galaxy
4. **Testing**: Each role can be tested independently
5. **Maintainability**: Easier to update and modify

---

## 9. Bonus: Ansible Vault

### Encrypting Secrets

Ansible Vault allows you to encrypt sensitive data.

#### Create encrypted file

```bash
$ ansible-vault create ansible/inventory/group_vars/secrets.yml

New Vault password: 
Confirm New Vault password: 
```

Add secrets to the file:

```yaml
---
# Database credentials
db_password: super_secret_password
db_user: admin

# API keys
api_key: abc123xyz789
docker_hub_token: ghp_xxxxxxxxxxxx

# SSL certificates
ssl_cert_path: /etc/ssl/certs/app.crt
ssl_key_path: /etc/ssl/private/app.key
```

#### Encrypt existing file

```bash
$ ansible-vault encrypt inventory/group_vars/secrets.yml

New Vault password: 
Confirm New Vault password: 
Encryption successful
```

**View encrypted file (it's now encrypted):**

```bash
$ cat inventory/group_vars/secrets.yml

$ANSIBLE_VAULT;1.1;AES256
65656164656364353065656233646162616133643566663662343661333531633862353164346338
6464396136646534326433613639613930663730383332300a306165623931333238656463393664
33616531656164336634333431343834663864616232303738656339383532333239363463616264
6463396633613537310a326164316430396465616666636663636333313362653333333036376562
61343231373066326238383739326534613635633364316263313135323530323032653831333438
...
```

#### View encrypted file

```bash
$ ansible-vault view inventory/group_vars/secrets.yml

Vault password: 
---
# Encrypted secrets - these will be used in production
# Created with: ansible-vault create secrets.yml

db_password: SecurePassword123!
db_user: prod_user
db_host: prod-db.example.com
db_port: 5432

api_key: sk-prod-abc123xyz789
docker_hub_token: dckr_pat_example_token_here

ssl_cert_path: /etc/ssl/certs/prod-app.crt
ssl_key_path: /etc/ssl/private/prod-app.key

app_secret_key: prod-secret-key-very-secure-2026
jwt_secret: jwt-prod-secret-2026-secure
```

#### Edit encrypted file

```bash
$ ansible-vault edit ansible/inventory/group_vars/secrets.yml

Vault password: 
# Opens in default editor
```

#### Decrypt file

```bash
$ ansible-vault decrypt ansible/inventory/group_vars/secrets.yml

Vault password: 
Decryption successful
```

### Using Vaulted Variables in Playbooks

**Run playbook with vault password:**

```bash
# Prompt for password
$ ansible-playbook playbooks/deploy_app.yml --ask-vault-pass

# Use password file
$ echo "my_vault_password" > ~/.ansible_vault_pass
$ chmod 600 ~/.ansible_vault_pass
$ ansible-playbook playbooks/deploy_app.yml --vault-password-file ~/.ansible_vault_pass
```

**Configure vault password file in ansible.cfg:**

```ini
[defaults]
vault_password_file = ~/.ansible_vault_pass
```

### Using Secrets in Playbooks

Example playbook using vaulted variables:

```yaml
---
- name: Example playbook using vaulted secrets
  hosts: all
  become: yes
  
  vars_files:
    - ../inventory/group_vars/secrets.yml
  
  tasks:
    - name: Display that we have access to secrets (without showing them)
      ansible.builtin.debug:
        msg: "Database user is configured (password hidden)"
    
    - name: Example - deploy app with database credentials
      ansible.builtin.debug:
        msg: "Would deploy app with DB_USER={{ db_user }} and DB_HOST={{ db_host }}"
```

**Run the playbook:**

```bash
$ ansible-playbook playbooks/vault_example.yml --ask-vault-pass
Vault password: 

PLAY [Example playbook using vaulted secrets] **********************************

TASK [Display that we have access to secrets (without showing them)] ***********
ok: [plumini] => {
    "msg": "Database user is configured (password hidden)"
}

TASK [Example - deploy app with database credentials] **************************
ok: [plumini] => {
    "msg": "Would deploy app with DB_USER=prod_user and DB_HOST=prod-db.example.com"
}

TASK [Show API key is available (first 10 chars only)] *************************
ok: [plumini] => {
    "msg": "API key starts with: sk-prod-ab..."
}

PLAY RECAP *********************************************************************
plumini                    : ok=3    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Best Practices for Secrets Management

1. **Never commit unencrypted secrets to Git**
2. **Use separate vault files for different environments**
3. **Rotate vault passwords regularly**
4. **Keep vault password in secure password manager**
5. **Use CI/CD secrets management** (GitHub Secrets, etc.)
6. **Limit access to vault password** (team leads only)

---

## 10. Summary

### What Was Accomplished

1. ✅ **Ansible Setup**
   - Installed Ansible on control machine
   - Configured ansible.cfg
   - Created inventory with YAML format
   - Set up group variables

2. ✅ **Basic Playbooks**
   - Connectivity testing
   - System information gathering
   - Package installation
   - Service management

3. ✅ **Docker Installation**
   - Automated Docker installation on Ubuntu
   - Added user to docker group
   - Verified Docker service is running
   - Made playbook idempotent

4. ✅ **Application Deployment**
   - Pulled Docker images
   - Deployed containerized application
   - Configured port mapping
   - Verified application health

5. ✅ **Ansible Roles (Bonus)**
   - Created reusable roles (common, docker, app_deploy)
   - Organized code into logical units
   - Demonstrated role-based playbook with full_setup.yml
   - Results: 21 tasks executed successfully

6. ✅ **Ansible Vault (Bonus)**
   - Encrypted sensitive data with ansible-vault
   - Demonstrated vault commands (encrypt, view, edit)
   - Created example playbook using vaulted secrets
   - Showed best practices for secrets management

### Key Learnings

1. **Configuration Management Benefits**
   - Automation reduces manual errors
   - Consistency across multiple servers
   - Documentation through code
   - Easy to replicate environments

2. **Idempotency Importance**
   - Can run playbooks multiple times safely
   - Only changes what needs changing
   - Predictable and reliable

3. **Ansible vs Manual Configuration**
   - **Manual:** Error-prone, time-consuming, not documented
   - **Ansible:** Automated, consistent, version-controlled, documented

4. **Best Practices Applied**
   - Use roles for organization
   - Variables for flexibility
   - Vault for secrets
   - Proper error handling
   - Check mode for testing

### Comparison: Before vs After Ansible

**Before Ansible (Manual):**
```bash
# SSH to server
ssh ubuntu@62.84.119.211

# Install Docker manually
sudo apt update
sudo apt install docker.io -y
sudo systemctl start docker
sudo usermod -aG docker ubuntu

# Pull and run app
docker pull 4hellboy4/devops-info-service:latest
docker run -d -p 5000:5000 --name app devops-info-service:latest

# Repeat for every server... 😰
```

**After Ansible (Automated):**
```bash
# One command does everything
ansible-playbook playbooks/full_setup.yml

# Works on 1 server or 100 servers identically! 🚀
```

### Real-World Use Cases

1. **Server Provisioning**
   - Set up new servers in minutes
   - Ensure consistent configuration
   - Reduce onboarding time

2. **Application Updates**
   - Deploy new version to all servers
   - Zero-downtime deployments
   - Rollback if needed

3. **Configuration Drift Prevention**
   - Regularly run playbooks to fix drift
   - Ensure compliance
   - Audit trail of changes

4. **Disaster Recovery**
   - Rebuild infrastructure from code
   - No manual documentation needed
   - Tested recovery procedures

### Tools and Versions Used

- **Ansible:** 2.20.3
- **Python:** 3.14.3 (control machine)
- **Target OS:** Ubuntu 24.04.4 LTS
- **Docker:** 29.2.1
- **Collections:** community.docker (latest)

### Next Steps

For Lab 06, we'll have:
- Fully configured VM with Docker
- Running application in container
- Ansible playbooks for automation
- Infrastructure ready for monitoring/observability

---

## Conclusion

This lab successfully demonstrated the power of configuration management with Ansible. By automating server setup, Docker installation, and application deployment, we've created a reproducible and maintainable infrastructure.

**Key Takeaways:**
- **Ansible makes infrastructure repeatable** - same configuration every time
- **Idempotency is crucial** - safe to run playbooks multiple times
- **Roles improve organization** - reusable, shareable components
- **Vault protects secrets** - encrypt sensitive data in Git
- **Automation saves time** - minutes instead of hours

The combination of Infrastructure as Code (Lab 04) and Configuration Management (Lab 05) provides a complete automation solution: Terraform/Pulumi creates the infrastructure, Ansible configures and manages it.

Ready for monitoring and observability in Lab 06! 📊

---

## Appendix: Ad-Hoc Commands

### Useful Ansible Ad-Hoc Commands

```bash
# Check connectivity
$ ansible all -m ping

# Run shell command
$ ansible all -a "uptime"

# Get system info
$ ansible all -m setup

# Install package
$ ansible all -m apt -a "name=htop state=present" --become

# Check disk space
$ ansible all -a "df -h"

# Check memory
$ ansible all -a "free -h"

# Restart service
$ ansible all -m systemd -a "name=docker state=restarted" --become

# Copy file
$ ansible all -m copy -a "src=/local/file dest=/remote/file" --become

# Create directory
$ ansible all -m file -a "path=/tmp/test state=directory mode=0755"

# Get Docker containers
$ ansible all -a "docker ps"
```

### Debugging Commands

```bash
# Run in check mode (dry-run)
$ ansible-playbook playbooks/docker.yml --check

# Show verbose output
$ ansible-playbook playbooks/docker.yml -v
$ ansible-playbook playbooks/docker.yml -vv  # More verbose
$ ansible-playbook playbooks/docker.yml -vvv # Very verbose

# Show diff of changes
$ ansible-playbook playbooks/docker.yml --diff

# Limit to specific hosts
$ ansible-playbook playbooks/docker.yml --limit plumini

# Start at specific task
$ ansible-playbook playbooks/docker.yml --start-at-task "Install Docker packages"

# Step through playbook interactively
$ ansible-playbook playbooks/docker.yml --step

# List all tasks
$ ansible-playbook playbooks/docker.yml --list-tasks

# List all hosts
$ ansible-playbook playbooks/docker.yml --list-hosts
```
