# Lab 5: Ansible Fundamentals

**Author:** ellilin
**Date:** 2026-02-25
**Tools:** Ansible 2.20, Docker, AWS EC2

## Overview

This lab demonstrates the fundamentals of Ansible for configuration management and application deployment. We provision an AWS EC2 instance with Docker and deploy a containerized Python Flask application (`ellilin/devops-info-python`) using Ansible roles and playbooks.

## Learning Objectives

- Set up Ansible inventory and configuration
- Create and use Ansible roles for modular configuration management
- Implement Ansible Vault for secure credential management
- Deploy Docker containers using Ansible modules
- Demonstrate playbook idempotency

## Prerequisites

- AWS EC2 instance running Ubuntu 24.04
- SSH key access to the EC2 instance
- Ansible 2.20+ installed locally
- Docker Hub account (for pulling container images)

## Project Structure

```
ansible/
├── ansible.cfg              # Ansible configuration
├── .vault_pass              # Vault password file
├── group_vars/
│   └── all.yml             # Encrypted variables (Vault)
├── inventory/
│   └── hosts.ini           # Inventory file
├── playbooks/
│   ├── provision.yml       # System provisioning playbook
│   └── deploy.yml          # Application deployment playbook
└── roles/
    ├── common/             # Common system configuration
    │   └── tasks/main.yml
    ├── docker/             # Docker installation
    │   ├── tasks/main.yml
    │   └── handlers/main.yml
    └── app_deploy/         # Application deployment
        └── tasks/main.yml
```

## Implementation

### 1. Ansible Configuration

**File:** `ansible.cfg`

```ini
[defaults]
inventory = inventory/hosts.ini
roles_path = roles
host_key_checking = False
remote_user = ubuntu
retry_files_enabled = False
vault_password_file = .vault_pass
```

### 2. Inventory Configuration

**File:** `inventory/hosts.ini`

```ini
[webservers]
lab04-vm ansible_host=3.92.6.53 ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/keys/labsuser.pem
```

### 3. Ansible Vault - Encrypted Variables

**File:** `group_vars/all.yml` (encrypted)

Encrypted using:
```bash
ansible-vault encrypt group_vars/all.yml
```

Variables stored:
- Docker Hub credentials
- Application configuration (image name, port, container name)
- Health check settings

View decrypted contents:
```bash
ansible-vault view group_vars/all.yml
```

```yaml
---
# Docker Hub credentials
dockerhub_username: ellilin
dockerhub_password: access-token

# Application configuration
app_name: devops-info-python
docker_image: ellilin/devops-info-python
docker_image_tag: latest
app_port: 5000
app_container_name: devops-app
app_env_vars: {}
app_restart_policy: unless-stopped
app_health_check_retries: 10
app_health_check_delay: 3
```

### 4. Roles Implementation

#### Common Role

**File:** `roles/common/tasks/main.yml`

```yaml
---
- name: Update apt cache
  apt:
    update_cache: yes
    cache_valid_time: 3600

- name: Install common packages
  apt:
    name: "{{ common_packages }}"
    state: present

- name: Set timezone
  timezone:
    name: "{{ common_timezone }}"
```

#### Docker Role

**File:** `roles/docker/tasks/main.yml`

```yaml
---
- name: Update apt cache
  apt:
    update_cache: yes

- name: Install dependencies
  apt:
    name:
      - ca-certificates
      - curl
      - gnupg
      - lsb-release
    state: present

- name: Add Docker GPG key
  apt_key:
    url: https://download.docker.com/linux/ubuntu/gpg
    state: present

- name: Add Docker repository
  apt_repository:
    repo: "deb [arch={{ 'amd64' if ansible_architecture == 'x86_64' else 'arm64' }}] https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable"
    state: present

- name: Update apt cache after adding Docker repo
  apt:
    update_cache: yes

- name: Install Docker packages
  apt:
    name:
      - docker-ce
      - docker-ce-cli
      - containerd.io
      - docker-buildx-plugin
      - docker-compose-plugin
    state: present
  notify: restart docker

- name: Ensure Docker service is running and enabled
  service:
    name: docker
    state: started
    enabled: yes

- name: Add user to docker group
  user:
    name: "{{ ansible_user }}"
    groups: docker
    append: yes

- name: Install python3-docker
  apt:
    name: python3-docker
    state: present
```

**File:** `roles/docker/handlers/main.yml`

```yaml
---
- name: restart docker
  service:
    name: docker
    state: restarted
```

#### App Deploy Role

**File:** `roles/app_deploy/tasks/main.yml`

```yaml
---
- name: Pull Docker image (public, no login required)
  docker_image:
    name: "{{ docker_image }}:{{ docker_image_tag }}"
    source: pull
    state: present

- name: Stop existing container
  docker_container:
    name: "{{ app_container_name }}"
    state: stopped
  failed_when: false

- name: Remove existing container
  docker_container:
    name: "{{ app_container_name }}"
    state: absent
  failed_when: false

- name: Run new container
  docker_container:
    name: "{{ app_container_name }}"
    image: "{{ docker_image }}:{{ docker_image_tag }}"
    state: started
    ports:
      - "{{ app_port }}:{{ app_port }}"
    env: "{{ app_env_vars }}"
    restart_policy: "{{ app_restart_policy }}"

- name: Wait for application port to be available
  wait_for:
    port: "{{ app_port }}"
    delay: "{{ app_health_check_delay }}"
    timeout: 60

- name: Verify health endpoint
  uri:
    url: "http://localhost:{{ app_port }}/health"
    method: GET
    status_code: [200, 404]
    timeout: 30
  register: health_check
  until: health_check.status in [200, 404]
  retries: "{{ app_health_check_retries }}"
  delay: "{{ app_health_check_delay }}"
  failed_when: false
  changed_when: false
```

### 5. Playbooks

#### Provision Playbook

**File:** `playbooks/provision.yml`

```yaml
---
- name: Provision web servers
  hosts: webservers
  become: yes
  vars_files:
    - ../group_vars/all.yml

  roles:
    - common
    - docker
```

#### Deploy Playbook

**File:** `playbooks/deploy.yml`

```yaml
---
- name: Deploy application
  hosts: webservers
  become: yes
  vars_files:
    - ../group_vars/all.yml

  roles:
    - app_deploy
```

## Execution and Results

### Initial Provisioning

```bash
$ ansible-playbook playbooks/provision.yml

PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab04-vm]

TASK [common : Update apt cache] ***********************************************
ok: [lab04-vm]

TASK [common : Install common packages] ****************************************
changed: [lab04-vm]

TASK [common : Set timezone] ***************************************************
changed: [lab04-vm]

TASK [docker : Update apt cache] ***********************************************
ok: [lab04-vm]

TASK [docker : Install dependencies] *******************************************
changed: [lab04-vm]

TASK [docker : Add Docker GPG key] *********************************************
changed: [lab04-vm]

TASK [docker : Add Docker repository] ******************************************
changed: [lab04-vm]

TASK [docker : Update apt cache after adding Docker repo] **********************
changed: [lab04-vm]

TASK [docker : Install Docker packages] ****************************************
changed: [lab04-vm]

TASK [docker : Ensure Docker service is running and enabled] *******************
ok: [lab04-vm]

TASK [docker : Add user to docker group] ***************************************
changed: [lab04-vm]

TASK [docker : Install python3-docker] *****************************************
changed: [lab04-vm]

RUNNING HANDLER [docker : restart docker] **************************************
changed: [lab04-vm]

PLAY RECAP *********************************************************************
lab04-vm                   : ok=14   changed=9    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Idempotency Test - Provisioning

Running the same playbook again shows idempotency (only apt cache update occurs):

```bash
$ ansible-playbook playbooks/provision.yml

PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab04-vm]

TASK [common : Update apt cache] ***********************************************
ok: [lab04-vm]

TASK [common : Install common packages] ****************************************
ok: [lab04-vm]

TASK [common : Set timezone] ***************************************************
ok: [lab04-vm]

TASK [docker : Update apt cache] ***********************************************
ok: [lab04-vm]

TASK [docker : Install dependencies] *******************************************
ok: [lab04-vm]

TASK [docker : Add Docker GPG key] *********************************************
ok: [lab04-vm]

TASK [docker : Add Docker repository] ******************************************
ok: [lab04-vm]

TASK [docker : Update apt cache after adding Docker repo] **********************
changed: [lab04-vm]

TASK [docker : Install Docker packages] ****************************************
ok: [lab04-vm]

TASK [docker : Ensure Docker service is running and enabled] *******************
ok: [lab04-vm]

TASK [docker : Add user to docker group] ***************************************
ok: [lab04-vm]

TASK [docker : Install python3-docker] *****************************************
ok: [lab04-vm]

PLAY RECAP *********************************************************************
lab04-vm                   : ok=13   changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Application Deployment

```bash
$ ansible-playbook playbooks/deploy.yml

PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab04-vm]

TASK [app_deploy : Pull Docker image (public, no login required)] **************
changed: [lab04-vm]

TASK [app_deploy : Stop existing container] ************************************
ok: [lab04-vm]

TASK [app_deploy : Remove existing container] **********************************
ok: [lab04-vm]

TASK [app_deploy : Run new container] ******************************************
changed: [lab04-vm]

TASK [app_deploy : Wait for application port to be available] ******************
ok: [lab04-vm]

TASK [app_deploy : Verify health endpoint] *************************************
ok: [lab04-vm]

PLAY RECAP *********************************************************************
lab04-vm                   : ok=7    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Application Verification

**Check container status:**

```bash
$ ansible webservers -m shell -a "docker ps --filter name=devops-app"

lab04-vm | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                               COMMAND           CREATED          STATUS                    PORTS                    NAMES
385d1dbd5a3c   ellilin/devops-info-python:latest   "python app.py"   24 seconds ago   Up 23 seconds (healthy)   0.0.0.0:5000->5000/tcp   devops-app
```

**Test health endpoint:**

```bash
$ curl http://3.92.6.53:5000/health

{"status":"healthy","timestamp":"2026-02-25T17:07:06.897704+00:00","uptime_seconds":38}
```

**Test main application endpoint:**

```bash
$ curl http://3.92.6.53:5000/

{
  "endpoints": [
    {"description": "Service information", "method": "GET", "path": "/"},
    {"description": "Health check", "method": "GET", "path": "/health"}
  ],
  "request": {
    "client_ip": "141.105.143.51",
    "method": "GET",
    "path": "/",
    "user_agent": "curl/8.7.1"
  },
  "runtime": {
    "current_time": "2026-02-25T17:15:44.781042+00:00",
    "timezone": "UTC",
    "uptime_human": "2 minutes",
    "uptime_seconds": 120
  },
  "service": {
    "description": "DevOps course info service",
    "framework": "Flask",
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "system": {
    "architecture": "x86_64",
    "cpu_count": 1,
    "hostname": "40b8830eb0fe",
    "platform": "Linux",
    "platform_version": "#7~24.04.1-Ubuntu SMP Thu Jan 22 21:04:49 UTC 2026",
    "python_version": "3.13.12"
  }
}
```

### Idempotency Test - Deployment

```bash
$ ansible-playbook playbooks/deploy.yml

PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab04-vm]

TASK [app_deploy : Pull Docker image (public, no login required)] **************
ok: [lab04-vm]

TASK [app_deploy : Stop existing container] ************************************
changed: [lab04-vm]

TASK [app_deploy : Remove existing container] **********************************
changed: [lab04-vm]

TASK [app_deploy : Run new container] ******************************************
changed: [lab04-vm]

TASK [app_deploy : Wait for application port to be available] ******************
ok: [lab04-vm]

TASK [app_deploy : Verify health endpoint] *************************************
ok: [lab04-vm]

PLAY RECAP *********************************************************************
lab04-vm                   : ok=7    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

## Key Learnings

1. **Ansible Vault**: Successfully used for encrypting sensitive credentials. Variables are automatically decrypted when the playbook runs using the `.vault_pass` file.

2. **Role-based organization**: Modular structure makes playbooks reusable and maintainable.

3. **Idempotency**: Ansible modules ensure that running the same playbook multiple times produces consistent results. The provisioning playbook shows clear idempotency (only 1 change on second run for apt cache update).

4. **Docker integration**: Ansible's `docker_container` module provides a clean way to manage containers declaratively.

5. **Inventory management**: The `hosts.ini` file makes it easy to manage multiple target hosts.

## Troubleshooting

### Issue: Variables from encrypted group_vars not loading

**Problem:** Playbook failed with `'docker_image' is undefined` even though `group_vars/all.yml` was encrypted.

**Solution:** The playbook was in `playbooks/deploy.yml` but referenced `group_vars/all.yml`. Fixed by using relative path `../group_vars/all.yml`.

### Issue: Duplicate port warnings

**Problem:** Warning "Both option published_ports and its alias ports are set"

**Solution:** Removed `published_ports` parameter, kept only `ports` in `docker_container` task.

## Key Decisions

### Why use roles instead of plain playbooks?

Roles provide a structured, modular approach to organizing Ansible code. Instead of monolithic playbooks with all tasks inline, roles separate concerns into reusable components with standardized directories for tasks, handlers, variables, files, and templates. This organization makes code easier to maintain, test, and share across projects.

### How do roles improve reusability?

Roles encapsulate functionality independently, allowing them to be dropped into any project or shared via Ansible Galaxy. Variables are parameterized through defaults, enabling customization without modifying core logic. A single role can be used across multiple playbooks, projects, or teams, reducing duplication and ensuring consistent configuration patterns.

### What makes a task idempotent?

An idempotent task produces the same result whether executed once or multiple times, only making changes when the current state differs from the desired state. This is achieved by using stateful modules (like `apt: state=present`, `service: state=started`) that check current conditions before acting, rather than imperative commands (like `command: apt-get install`) that always execute.

### How do handlers improve efficiency?

Handlers provide event-driven task execution, running only when notified by a change in other tasks. For example, a Docker service restart handler only executes when configuration changes require it, not on every playbook run. This reduces unnecessary service interruptions and speeds up playbook execution by deferring expensive operations until actually needed.

### Why is Ansible Vault necessary?

Ansible Vault is essential for securely managing sensitive credentials (passwords, API keys, tokens) in version control. Without Vault, secrets would be either hardcoded in playbooks (security risk) or kept separate (operational burden). Vault encrypts these values so they can be safely committed to git while remaining protected, with automatic decryption during playbook execution.

## Bonus Task - Dynamic Inventory with AWS EC2 Plugin

### Overview

Implemented AWS EC2 dynamic inventory to automatically discover cloud VMs instead of hardcoding IPs in static inventory files. This enables automatic IP discovery when VMs are recreated and scales to multiple instances without manual inventory updates.

### Configuration

**File:** `inventory/aws_ec2.yml`

```yaml
---
plugin: amazon.aws.aws_ec2
regions:
  - us-east-1
filters:
  instance-state-name: running
  tag:Name: lab04-vm
keyed_groups:
  - key: tags.Name
    prefix: tag_Name_
  - key: tags.Environment
    prefix: tag_Environment_
compose:
  ansible_host: public_ip_address
  ansible_user: "'ubuntu'"
  ansible_ssh_private_key_file: "'~/.ssh/keys/labsuser.pem'"
strict: False
```

**Updated:** `ansible.cfg`

```ini
[defaults]
inventory = inventory/  # Changed from inventory/hosts.ini to inventory/

[inventory]
enable_plugins = amazon.aws.aws_ec2, host_list, script, auto, yaml, ini, toml
```

### How It Works

1. **Plugin Selection**: Uses `amazon.aws.aws_ec2` inventory plugin
2. **Region Filtering**: Searches only in `us-east-1`
3. **Instance Filtering**: Discovers only running instances with tag `Name: lab04-vm`
4. **Auto-grouping**: Creates groups based on instance tags
5. **Variable Composition**: Maps AWS metadata to Ansible variables:
   - `public_ip_address` → `ansible_host`
   - Sets SSH user and key path automatically

### Verification

**Test inventory graph:**
```bash
$ ansible-inventory --graph

@all:
  |--@ungrouped:
  |--@aws_ec2:
  |--@webservers:
  |  |--lab04-vm
```

**Test connectivity:**
```bash
$ ansible all -m ping

lab04-vm | SUCCESS => {
    "ping": "pong"
}
```

**Run playbooks with dynamic inventory:**
```bash
$ ansible-playbook playbooks/provision.yml

PLAY RECAP
lab04-vm                   : ok=13   changed=1    unreachable=0    failed=0

$ ansible-playbook playbooks/deploy.yml

PLAY RECAP
lab04-vm                   : ok=8    changed=3    unreachable=0    failed=0
```

### Benefits Compared to Static Inventory

| Feature | Static Inventory | Dynamic Inventory |
|---------|-----------------|-------------------|
| IP Updates | Manual edit required | Automatic discovery |
| Scaling | Add each host manually | Auto-discovers all matching VMs |
| VM Recreation | Update IP manually | No changes needed |
| Multi-region | Complex configuration | Simple filter addition |
| Tag-based grouping | Manual grouping | Automatic by tags |

### What Happens When VM IP Changes?

With dynamic inventory, **nothing needs to be updated**. When the VM is recreated with a new IP:
1. AWS EC2 plugin queries AWS API
2. Discovers new `public_ip_address`
3. Maps to `ansible_host` automatically
4. Playbooks run against new IP without any configuration changes

This is especially valuable in auto-scaling environments where VMs are frequently created/destroyed.

## References

- [Ansible Documentation](https://docs.ansible.com/)
- [Ansible Vault Guide](https://docs.ansible.com/ansible/latest/vault_guide/index.html)
- [Docker Container Module](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/docker_container_module.html)
- [Ansible Best Practices](https://docs.ansible.com/ansible/latest/user_guide/playbooks_best_practices.html)
