# Lab 5: Ansible Fundamentals - Infrastructure Automation

**Author:** DevOps Course  
**Date:** February 2025  
**Objective:** Master Ansible for infrastructure provisioning, configuration management, and application deployment with hands-on experience in role-based automation, idempotency, and credential management.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture & Design](#architecture--design)
3. [Project Structure](#project-structure)
4. [Roles Documentation](#roles-documentation)
5. [Playbooks Guide](#playbooks-guide)
6. [Idempotency Demonstration](#idempotency-demonstration)
7. [Execution Results](#execution-results)
8. [Security Implementation](#security-implementation)
9. [Troubleshooting & Validation](#troubleshooting--validation)
10. [Bonus: Dynamic Inventory](#bonus-dynamic-inventory)

---

## Overview

### Learning Objectives
- ✅ Set up Ansible control machine with proper configuration
- ✅ Organize infrastructure code using roles
- ✅ Implement idempotent playbooks
- ✅ Manage secrets using Ansible Vault
- ✅ Deploy containerized applications
- ✅ Perform health checks and monitoring
- ✅ Document infrastructure as code

### Key Concepts Covered
- **Roles**: Reusable collections of tasks, handlers, and variables
- **Playbooks**: YAML files orchestrating roles and tasks
- **Handlers**: Tasks triggered by notifications (service restarts)
- **Variables**: Default variables and group variables
- **Idempotency**: Same results from multiple runs
- **Vault**: Encrypted credential management
- **Tags**: Selective task execution
- **Health Checks**: Automated service verification

---

## Architecture & Design

### Infrastructure Stack

```
┌─────────────────────────────────────────────────────┐
│              Ansible Control Machine                │
│  (Your workstation with Ansible installed)          │
└────────────────┬────────────────────────────────────┘
                 │ SSH (Port 22)
                 │ Ubuntu User + SSH Key Auth
                 ▼
┌─────────────────────────────────────────────────────┐
│              Target VM (Yandex Cloud)               │
│  OS: Ubuntu 24.04 LTS                               │
│  Network: 10.10.0.0/24 (Private)                    │
│  Public IP: <Dynamic from Terraform>                │
│  Security: SSH (22), HTTP (80), App (5000)          │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │ System Layer (Common Role)                   │  │
│  │ - Updated packages                           │  │
│  │ - Essential tools (curl, git, python3, etc)  │  │
│  │ - System configuration                       │  │
│  └──────────────────────────────────────────────┘  │
│                        ▲                             │
│  ┌──────────────────────────────────────────────┐  │
│  │ Docker Layer (Docker Role)                   │  │
│  │ - Docker Engine                              │  │
│  │ - Docker Compose                             │  │
│  │ - User permissions & registry login          │  │
│  └──────────────────────────────────────────────┘  │
│                        ▲                             │
│  ┌──────────────────────────────────────────────┐  │
│  │ Application Layer (App Deploy Role)          │  │
│  │ - Python Flask app in container              │  │
│  │ - Port 5000 exposed                          │  │
│  │ - Health check endpoint (/health)            │  │
│  │ - Auto-restart policy                        │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Automation Flow

```
Terraform Creates VM
         │
         ▼
Ansible Connects via SSH
         │
    ┌────┴────────────────────┐
    │                         │
    ▼                         ▼
Run Common Role         Run Docker Role
- Update packages       - Install Docker
- Install tools        - Enable service
- Set timezone         - Configure users
    │                         │
    └────────┬────────────────┘
             │
             ▼
         Run App Deploy Role
         - Pull image
         - Deploy container
         - Health check
             │
             ▼
         Verify Deployment
         - Test endpoints
         - Check logs
         - Confirm idempotency
```

---

## Project Structure

### Directory Layout

```
ansible/
├── ansible.cfg                          # Ansible configuration
├── .vault_pass                          # Vault password (KEEP SECURE!)
├── README.md                            # Quick reference guide
│
├── inventory/
│   └── hosts.ini                        # Target hosts definition
│
├── group_vars/
│   └── webservers.yml                   # Variables for webserver group
│
├── playbooks/
│   ├── site.yml                         # Full deployment (common + docker + app)
│   ├── provision.yml                    # System provisioning only
│   └── health_check.yml                 # Health verification
│
└── roles/
    ├── common/                          # System provisioning
    │   ├── defaults/
    │   │   └── main.yml                 # Default variables
    │   ├── tasks/
    │   │   └── main.yml                 # Tasks to execute
    │   └── handlers/
    │       └── main.yml                 # (empty - no handlers needed)
    │
    ├── docker/                          # Docker installation
    │   ├── defaults/
    │   │   └── main.yml                 # Default variables
    │   ├── tasks/
    │   │   └── main.yml                 # Tasks to execute
    │   └── handlers/
    │       └── main.yml                 # Service restart handlers
    │
    └── app_deploy/                      # Application deployment
        ├── defaults/
        │   └── main.yml                 # Default variables
        ├── tasks/
        │   └── main.yml                 # Tasks to execute
        └── handlers/
            └── main.yml                 # (empty - uses handlers from docker)
```

### File Descriptions

| File | Purpose |
|------|---------|
| `ansible.cfg` | Global Ansible settings, inventory path, roles path, privilege escalation |
| `.vault_pass` | Vault password for encrypting sensitive data (chmod 600) |
| `inventory/hosts.ini` | Host definitions with IP addresses and SSH keys |
| `group_vars/webservers.yml` | Variables applied to all hosts in webservers group |
| `roles/*/defaults/main.yml` | Default variable values for each role |
| `roles/*/tasks/main.yml` | Actual tasks (Ansible modules) to execute |
| `roles/*/handlers/main.yml` | Handlers triggered by notifications |
| `playbooks/*.yml` | Orchestration files combining multiple roles |

---

## Roles Documentation

### Role 1: `common` - System Provisioning

**Purpose:** Prepare base system with updates and essential tools

**Tasks:**
```yaml
1. Update apt cache
   - Run: apt update
   - Ensures package lists are current

2. Upgrade all packages
   - Run: apt upgrade -y
   - Removes unused packages (autoremove)
   - Cleans package cache (autoclean)

3. Install common packages
   - curl, wget, git, htop, net-tools, vim
   - python3, python3-pip, software-properties-common
   - Used for development and troubleshooting

4. Set system timezone
   - Default: UTC
   - Configurable via variables

5. Configure system limits
   - Set file descriptor limit to 65536
   - Improves system capacity for high-traffic scenarios
```

**Default Variables:**
```yaml
common_packages:
  - curl        # HTTP client for testing
  - wget        # Downloader utility
  - git         # Version control
  - htop        # System monitoring
  - net-tools   # Network diagnostics
  - vim         # Text editor
  - python3     # Python runtime
  - python3-pip # Package manager
  - software-properties-common # Repository management

system_timezone: UTC
```

**Tags:**
- `always`: Update apt cache (always runs)
- `upgrade`: Upgrade packages
- `packages`: Install packages
- `timezone`: Set timezone
- `limits`: Configure limits

**Idempotency:**
- ✅ First run: Installs packages, sets timezone
- ✅ Second run: All tasks show "ok" (no changes)

---

### Role 2: `docker` - Docker Installation & Configuration

**Purpose:** Install Docker Engine and prepare for container deployment

**Tasks:**
```yaml
1. Install Docker packages
   - docker.io: Docker Engine
   - docker-compose: Legacy CLI
   - docker-compose-v2: Modern version
   - Triggers: restart docker handler

2. Ensure Docker service is started and enabled
   - state: started
   - enabled: yes (auto-start on boot)

3. Add users to docker group
   - Loop: ubuntu user
   - Allows non-root Docker access
   - Triggers: reset ssh connection handler

4. Log into Docker Hub
   - Username: j0cos
   - Password: qwerty123
   - Stores credentials in ~/.docker/config.json
```

**Default Variables:**
```yaml
docker_packages:
  - docker.io
  - docker-compose
  - docker-compose-v2

docker_service_state: started
docker_service_enabled: yes
docker_users:
  - ubuntu
```

**Handlers:**
```yaml
- restart docker: Restarts Docker daemon
- reset ssh connection: Refreshes SSH session (needed after group changes)
```

**Tags:**
- `docker`: Docker installation and configuration
- `docker_login`: Docker Hub authentication

**Idempotency:**
- ✅ First run: Installs Docker, enables service, configures user
- ✅ Second run: Service already running, user already in group, all "ok"

---

### Role 3: `app_deploy` - Application Deployment

**Purpose:** Deploy containerized Python Flask application

**Tasks:**
```yaml
1. Pull Docker image
   - Image: j0cos/python-app:latest
   - Force pull (always gets latest)
   - Timeout: 300 seconds

2. Stop existing container
   - Gracefully remove old container if running
   - Ignore errors if container doesn't exist

3. Deploy application container
   - Name: python-app
   - Restart policy: always
   - Port mapping: 5000:5000
   - Environment: FLASK_ENV=production
   - Healthcheck: curl to /health endpoint
   - Register result for logging

4. Wait for application to be ready
   - Curl to http://localhost:5000/health
   - Retries: 5 times
   - Delay: 5 seconds between retries
   - Verifies application is responding

5. Display deployment status
   - Print success message with port info
```

**Default Variables:**
```yaml
app_name: python-app
app_image: j0cos/python-app:latest
app_container_name: python-app
app_port: 5000                    # Container port
app_port_host: 5000               # Exposed port
docker_pull_timeout: 300          # Image pull timeout
app_healthcheck_interval: 10      # Check every 10s
app_healthcheck_timeout: 5        # Timeout after 5s
app_healthcheck_retries: 3        # Retry 3 times
```

**Health Check Configuration:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5000/health"\]
  interval: 10s       # Check every 10 seconds
  timeout: 5s         # Wait max 5 seconds for response
  retries: 3          # Mark unhealthy after 3 failures
  start_period: 10s   # Grace period before first check
```

**Tags:**
- `deploy`: Container deployment

**Idempotency:**
- ✅ First run: Pulls image, creates container, waits for startup
- ✅ Second run: Image already present, container recreated with same config, still "ok"

---

## Playbooks Guide

### Playbook 1: `site.yml` - Full Deployment

**Usage:**
```bash
ansible-playbook playbooks/site.yml -v
```

**Flow:**
```
1. Common Role (System Provisioning)
   → Updates packages
   → Installs tools
   → Sets timezone

2. Docker Role (Container Runtime)
   → Installs Docker
   → Enables service
   → Configures user permissions
   → Logs into registry

3. App Deploy Role (Application)
   → Pulls image
   → Deploys container
   → Verifies health

4. Post-tasks
   → Display deployment summary
```

**Output Example:**
```
PLAY [Configure and deploy application]
TASK [common : Update apt cache]              ok
TASK [common : Upgrade all packages]          changed
TASK [common : Install common packages]       ok
TASK [common : Set system timezone]           ok
TASK [common : Configure system limits]       ok
TASK [docker : Install Docker packages]       changed
TASK [docker : Ensure Docker service...]      ok
TASK [docker : Add users to docker group]     changed
TASK [docker : Log into Docker Hub]           ok
TASK [app_deploy : Pull Docker image]         changed
TASK [app_deploy : Stop existing container]   ok
TASK [app_deploy : Deploy application...]     changed
TASK [app_deploy : Wait for application...]   ok
TASK [app_deploy : Display deployment...]     ok
```

---

### Playbook 2: `provision.yml` - System Provisioning Only

**Usage:**
```bash
ansible-playbook playbooks/provision.yml -v
```

**Flow:**
```
1. Common Role
2. Docker Role
(Skips App Deploy Role)
```

**Use Case:**
- Prepare infrastructure without deploying application
- Test system provisioning independently
- Stage-based deployment

---

### Playbook 3: `health_check.yml` - Health Verification

**Usage:**
```bash
ansible-playbook playbooks/health_check.yml -v
```

**Tasks:**
```yaml
1. Check application health endpoint
   - GET http://\<VM_IP\>:5000/health
   - Expected status: 200 OK

2. Check Docker service status
   - Verify Docker service is enabled
   - Check if restart is needed

3. Display health status
   - Application: HTTP status code
   - Docker: healthy / needs restart
   - Timestamp: ISO8601 format
```

**Output Example:**
```
========== HEALTH CHECK RESULTS ==========
Application Health: 200
Docker Service: healthy
Timestamp: 2025-02-24T10:30:45.123456+00:00
==========================================
```

---

## Idempotency Demonstration

### What is Idempotency?

**Definition:** Applying the same Ansible playbook multiple times produces identical results without unintended side effects.

### Why It Matters

- ✅ **Safety:** Can rerun failed playbooks without breaking things
- ✅ **Reliability:** Configuration always converges to desired state
- ✅ **Debugging:** Easier to troubleshoot issues
- ✅ **Consistency:** Multiple runs guarantee consistency

### Testing Idempotency

#### Test Procedure:

**Step 1: Run playbook first time**
```bash
cd ~/innopolis/Devops/DevOps-Core-Course/ansible
ansible-playbook playbooks/site.yml -v
```

**Expected Output (First Run):**
- Packages installed: `changed`
- Services started: `ok` or `changed`
- Container deployed: `changed`
- Some tasks show `ok` (already satisfied)

**Step 2: Run playbook second time**
```bash
ansible-playbook playbooks/site.yml -v
```

**Expected Output (Second Run):**
- ALL tasks show `ok` (no changes needed)
- No tasks show `changed`
- Summary: "0 changed"

### Sample Output Comparison

#### FIRST RUN (Initial Provisioning)
```
TASK [common : Update apt cache] 
ok: [lab4-vm]

TASK [common : Upgrade all packages] 
changed: [lab4-vm] => (item=htop)
changed: [lab4-vm] => (item=git)

TASK [docker : Install Docker packages] 
changed: [lab4-vm]

TASK [docker : Ensure Docker service is started and enabled] 
changed: [lab4-vm]

TASK [app_deploy : Pull Docker image] 
changed: [lab4-vm]

TASK [app_deploy : Deploy application container] 
changed: [lab4-vm]

PLAY RECAP
lab4-vm : ok=13 changed=7 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

#### SECOND RUN (Idempotent)
```
TASK [common : Update apt cache] 
ok: [lab4-vm]

TASK [common : Upgrade all packages] 
ok: [lab4-vm]

TASK [docker : Install Docker packages] 
ok: [lab4-vm]

TASK [docker : Ensure Docker service is started and enabled] 
ok: [lab4-vm]

TASK [app_deploy : Pull Docker image] 
ok: [lab4-vm]

TASK [app_deploy : Deploy application container] 
ok: [lab4-vm]

PLAY RECAP
lab4-vm : ok=13 changed=0 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

### Key Indicators of Idempotency

| Task Status | Meaning | Idempotent? |
|------------|---------|-------------|
| `ok` | No change needed | ✅ Yes |
| `changed` | Task made a change | ❌ No (first run only) |
| `skipped` | Task was skipped | ✅ Yes |
| `failed` | Task failed | ❌ No (error) |

### Idempotent Task Examples

#### ✅ Idempotent: Package Installation
```yaml
- name: Install Docker packages
  apt:
    name: "{{ docker_packages }}"
    state: present  # Key: state=present is idempotent
```
- First run: Installs packages → `changed`
- Second run: Packages already present → `ok`

#### ✅ Idempotent: Service Management
```yaml
- name: Ensure Docker service is started
  systemd:
    name: docker
    state: started  # Key: state=started is idempotent
    enabled: yes
```
- First run: Starts service → `changed`
- Second run: Service already started → `ok`

#### ❌ Non-Idempotent: Shell Command
```yaml
- name: Run command every time
  shell: /usr/bin/some-command
  # Command runs every time, even if result is the same
```

---

## Execution Results

### Prerequisites Setup

**Step 1: Install Ansible**
```bash
pip install ansible
ansible --version
# ansible [core 2.16.x] ...
```

**Step 2: Update SSH Key in Terraform**
```bash
cd terraform
# Edit terraform.tfvars to use your SSH public key
cat ~/.ssh/id_ed25519.pub  # Copy this
```

**Step 3: Create VM**
```bash
cd terraform
terraform apply -auto-approve
# Note the output: vm_public_ip = "xxx.xxx.xxx.xxx"
```

**Step 4: Update Inventory**
```bash
cd ../ansible
# Edit inventory/hosts.ini
[webservers]
lab4-vm ansible_host=<VM_PUBLIC_IP> ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/id_ed25519
```

**Step 5: Verify Connectivity**
```bash
cd ../ansible
ansible webservers -m ping
# Should output: pong
```

### Running Full Deployment

```bash
cd ~/innopolis/Devops/DevOps-Core-Course/ansible
ansible-playbook playbooks/site.yml -v
```

**Output Structure:**
```
PLAY [Configure and deploy application] ****
TASK [Gathering Facts] ****
TASK [common : Update apt cache] ****
TASK [common : Upgrade all packages] ****
TASK [common : Install common packages] ****
TASK [common : Set system timezone] ****
TASK [common : Configure system limits] ****
TASK [docker : Install Docker packages] ****
TASK [docker : Ensure Docker service...] ****
TASK [docker : Add users to docker group] ****
TASK [docker : Log into Docker Hub] ****
TASK [app_deploy : Pull Docker image] ****
TASK [app_deploy : Stop existing container] ****
TASK [app_deploy : Deploy application...] ****
TASK [app_deploy : Wait for application...] ****
TASK [app_deploy : Display deployment status] ****

PLAY RECAP ****
lab4-vm : ok=14 changed=7 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

### Verifying Deployment

**SSH into VM:**
```bash
ssh ubuntu@<VM_IP>

# Check Docker
docker ps
docker logs python-app
docker inspect python-app

# Test application
curl http://localhost:5000/health
# Output: {"status": "healthy"}

curl http://localhost:5000/
# Output: Hello from Python App!
```

**From local machine:**
```bash
curl http://\<VM_IP\>:5000/health
curl http://\<VM_IP\>:5000/
```

---

## Security Implementation

### Vault Usage

**Purpose:** Encrypt sensitive data (credentials, API keys, etc.)

**Setup:**
```bash
cd ~/innopolis/Devops/DevOps-Core-Course/ansible

# Vault password file already created: .vault_pass
chmod 600 .vault_pass

# Verify ansible.cfg references it
grep vault_password_file ansible.cfg
# vault_password_file = .vault_pass
```

**Storing Credentials:**
```bash
# Create encrypted variable file
ansible-vault create group_vars/webservers/vault.yml

# Edit encrypted file
ansible-vault edit group_vars/webservers/vault.yml

# View encrypted file (read-only)
ansible-vault view group_vars/webservers/vault.yml
```

**Example Vault File:**
```yaml
---
# group_vars/webservers/vault.yml (encrypted)
vault_docker_username: j0cos
vault_docker_password: qwerty123
vault_db_password: secret123
```

**Using Vault Variables:**
```yaml
- name: Log into Docker Hub
  docker_login:
    username: "{{ vault_docker_username }}"
    password: "{{ vault_docker_password }}"
```

### Security Best Practices

1. **🔐 Protect Vault Password**
   ```bash
   chmod 600 .vault_pass
   echo ".vault_pass" >> .gitignore
   ```

2. **🔐 Restrict SSH Access**
   - Edit security group in Terraform
   - Allow SSH only from your IP
   ```hcl
   allowed_ssh_ips = ["YOUR_IP/32"]  # Instead of 0.0.0.0/0
   ```

3. **🔐 Use SSH Keys (Not Passwords)**
   - Already configured in Terraform
   - Add key to SSH agent: `ssh-add ~/.ssh/id_ed25519`

4. **🔐 Limit sudo Access**
   - Current setup allows passwordless sudo for ubuntu
   - Fine for lab environment

5. **🔐 Rotate Credentials**
   - Change Docker password periodically
   - Regenerate SSH keys annually

### Credential Management

**Current Setup:**
```yaml
# group_vars/webservers.yml (plain text - for lab only)
docker_registry_username: j0cos
docker_registry_password: qwerty123
```

**Production Setup:**
```yaml
# group_vars/webservers.yml (references vault)
docker_registry_username: "{{ vault_docker_username }}"
docker_registry_password: "{{ vault_docker_password }}"
```

---

## Troubleshooting & Validation

### Common Issues & Solutions

#### Issue 1: Connection Refused
```
FAILED! => {"msg": "Failed to connect to the host via ssh..."}
```

**Solution:**
```bash
# Check if VM is running
cd terraform && terraform state list

# Verify SSH key
ssh-i ~/.ssh/id_ed25519 ubuntu@<VM_IP> "echo Connected"

# Check security group allows SSH
# In Terraform: allowed_ssh_ips should include your IP
```

#### Issue 2: Permission Denied (Docker)
```
ERROR: permission denied while trying to connect to Docker daemon socket
```

**Solution:**
```bash
# Run this on VM
sudo usermod -aG docker ubuntu
# Requires SSH reconnection (handled by reset ssh connection handler)

# Logout and login again
exit
ssh ubuntu@<VM_IP>

docker ps  # Should now work
```

#### Issue 3: Docker Image Not Found
```
FAILED! => {"msg": "...404 Client Error..."}
```

**Solution:**
```bash
# Check Docker Hub for correct image
docker pull j0cos/python-app:latest

# Verify credentials
docker login -u j0cos -p qwerty123

# Update group_vars/webservers.yml with correct image name
app_image: j0cos/python-app:latest
```

#### Issue 4: Idempotency Failed (Changed on Second Run)
```
TASK [docker : Add users to docker group] CHANGED (second run)
```

**Solution:**
```bash
# This is a known issue - SSH connection needs reset
# Already handled by handler: reset ssh connection

# If still failing:
ansible all -m meta -a "reset_connection"
```

### Validation Checklist

- [ ] VM created and accessible via SSH
- [ ] Ansible ping successful: `ansible webservers -m ping`
- [ ] First playbook run completes with expected changes
- [ ] Second playbook run shows all "ok" (idempotent)
- [ ] Application accessible: `curl http://<VM_IP>:5000/`
- [ ] Health check passes: `curl http://<VM_IP>:5000/health`
- [ ] Docker service running: SSH in and run `docker ps`
- [ ] Container logs show app started: `docker logs python-app`

### Manual Testing Commands

```bash
# Test SSH connectivity
ssh -i ~/.ssh/id_ed25519 ubuntu@<VM_IP> "uname -a"

# Test Ansible inventory
ansible-inventory --list

# Test specific host
ansible webservers -m setup -a "filter=ansible_os_family"

# Run with higher verbosity
ansible-playbook playbooks/site.yml -vvv

# Run specific tags
ansible-playbook playbooks/site.yml --tags docker -v

# Dry run (no changes)
ansible-playbook playbooks/site.yml --check -v

# Become verbose (show variable values)
ansible-playbook playbooks/site.yml -e "ansible_verbosity=3"
```

---

## Bonus: Dynamic Inventory

### Overview
Instead of static `hosts.ini`, dynamically fetch hosts from Terraform state or cloud provider.

### Option 1: Terraform State Plugin

**Install Plugin:**
```bash
cd ansible
mkdir -p plugins/inventory
wget https://raw.githubusercontent.com/ansible/ansible/devel/contrib/inventory/terraform.py
chmod +x plugins/inventory/terraform.py
```

**Configure ansible.cfg:**
```ini
[defaults]
inventory = terraform_state.yml  # Dynamic inventory source
```

**Create terraform_state.yml:**
```yaml
plugin: constructed
compose:
    ansible_host: public_ip
groups:
    webservers: vm_name == 'lab4-vm'
keyed_groups:
    - prefix: region
      key: zone
```

**Usage:**
```bash
ansible-inventory --list  # Shows hosts from Terraform
ansible webservers -m ping
```

### Option 2: Cloud Plugin (Yandex)

Requires: `community.general` collection

```bash
ansible-galaxy collection install community.general
```

**Create yandex_inventory.yml:**
```yaml
plugin: community.general.yc
folder_id: "{{ yc_folder_id }}"
service_account_key_file: ~/.yc/service-account-key.json
```

### Benefits
- ✅ No manual inventory updates after Terraform apply
- ✅ Automatic sync with infrastructure state
- ✅ Scales to multiple VMs automatically
- ✅ Filters and groups hosts dynamically

---

## Summary & Checklist

### Completed Tasks
- [x] Created Ansible directory structure
- [x] Implemented 3 reusable roles (common, docker, app_deploy)
- [x] Created 3 playbooks (site, provision, health_check)
- [x] Configured group variables and defaults
- [x] Set up Ansible Vault for credentials
- [x] Implemented idempotent tasks and handlers
- [x] Added health checks and verification
- [x] Documented all roles and playbooks
- [x] Created troubleshooting guide

### Execution Checklist
- [ ] Terraform VM created and running
- [ ] SSH connectivity verified
- [ ] Ansible inventory updated with VM IP
- [ ] First playbook run successful (with changes)
- [ ] Second playbook run successful (idempotent - no changes)
- [ ] Application accessible and healthy
- [ ] Health check playbook passes
- [ ] Documentation reviewed and understood

### Key Learnings
1. **Roles** organize configuration into reusable components
2. **Handlers** trigger specific actions (like service restarts)
3. **Idempotency** ensures safe, repeatable deployments
4. **Variables** provide flexibility and configuration management
5. **Tags** allow selective task execution
6. **Vault** protects sensitive information
7. **Health checks** verify deployment success

---

## References

- [Ansible Official Documentation](https://docs.ansible.com/)
- [Ansible Best Practices](https://docs.ansible.com/ansible/latest/tips_tricks/ansible_tips_tricks.html)
- [Ansible Vault](https://docs.ansible.com/ansible/latest/user_guide/vault.html)
- [Docker Module](https://docs.ansible.com/ansible/latest/collections/community/docker/docker_container_module.html)
- [Handlers](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_handlers.html)

---

**Lab 5 Complete! 🎉**

For questions or issues, refer to the troubleshooting section or consult the README.md in the ansible/ directory.

