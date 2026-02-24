# Lab 05 — Ansible Fundamentals Implementation

## 1. Architecture Overview

**Ansible Version:** 2.16+  
**Target VM OS:** Ubuntu 24.04.4 LTS (WLS) 

### Role Structure

```
ansible/
│
├─ docs/
│   ├─ screenshots/                 # Screenshots of terminal
│   └─ LAB05.md                     # This documentation
│
├─ group_vars/
│   └─ all.yml                      # Encrypted credentials
│
├─ inventory/
│   └─ hosts.ini                    # Static inventory
│
├─ playbooks/
│   ├─ deploy.yml                   # Application deployment 
│   └─ provision.yml                # System provisioning playbook
│
├─ roles/
│   ├─ app_deploy/                  # Application deployment
│   │   ├─ defaults/main.yml
│   │   ├─ handlers/main.yml
│   │   └─ tasks/main.yml
│   │
│   ├─ common/                      # System provisioning
│   │   ├─ defaults/main.yml
│   │   └─ tasks/main.yml
│   │
│   └─ docker/                      # Docker installation
│       ├─ defaults/main.yml
│       ├─ handlers/main.yml
│       └─ tasks/main.yml
│
└─ ansible.cfg                      # Configuration

```

### Why Roles Instead of Monolithic Playbooks?

**Benefits of Role-Based Structure:**

1. **Reusability:** Each role can be used independently across projects
2. **Maintainability:** Changes to one role don't affect others
3. **Scalability** — Easy to add new roles
4. **Clarity:** Clear separation of concerns
5. **Organization** — Clear structure, easy to navigate
6. **Modularity:** Combine roles as needed.

---

## 2. Roles Documentation

### Role 1: Common Role

**Purpose:** Basic system setup

**Variables (defaults/main.yml):**
```yaml
common_packages:
  - python3-pip
  - curl
  - git
  - vim
  - htop
  - wget
```

**Tasks:**
1. Update apt cache with 3600s validity (prevents redundant updates)
2. Install packages from `common_packages` variable with `state: present`

**Handlers:** None

**Idempotency Notes:**
- `apt` module with `state: present` checks if packages exist
- `cache_valid_time: 3600` prevents unnecessary cache updates within 1 hour

---

### Role 2: Docker Role

**Purpose:** Docker installation and configuration

**Variables (defaults/main.yml):**
```yaml
docker_user: "{{ ansible_user }}"
```

**Tasks:**
1. Add Docker official GPG key
2. Add Docker APT repository for Ubuntu
3. Install docker-ce, docker-ce-cli, containerd.io packages
4. Start Docker service and enable for auto-start
5. Add ansible user to docker group 
6. Install python3-docker module 

**Handlers:**
```yaml
- name: restart docker
  service:
    name: docker
    state: restarted
```

**Idempotency Notes:**
- `apt_key` checks if GPG key exists before adding
- `apt_repository` verifies repository before adding
- `service` module only starts if not already running
- `user` module only adds group if not already present
- Handler only runs if a task makes changes

---

### Role 3: App_Deploy Role

**Purpose:** Deploy containerized application using Docker

**Variables (defaults/main.yml):**
```yaml
app_port: 5000
app_restart_policy: unless-stopped
app_environment: {}
```

**Variables (from group_vars/all.yml - encrypted with Vault):**
```yaml
dockerhub_username: DOCKER_USERNAME
dockerhub_password: DOCKER_PASSWORD
app_name: "devops-info-service"
docker_image: "{{ dockerhub_username }}/{{ app_name }}"
docker_image_tag: "latest"
app_port: 5000
app_container_name: "{{ app_name }}"
```

**Tasks:**
1. Login to Docker Hub
2. Pull Docker image
3. Stop existing container
4. Run new container
5. Wait for app to be ready
6. Verify health endpoint

**Handlers:**
```yaml
- name: restart app
  docker_container:
    name: "{{ app_container_name }}"
    state: started
    restart: yes
```

**Idempotency Notes:**
- `docker_login` is idempotent (just refreshes credentials)
- `docker_image` checks if image exists before pulling
- `docker_container` checks if container is running
- `wait_for` retries until port is available
- `uri` retries until health check passes

---

## 3. Idempotency Demonstration

### Configuration Details

**Inventory (inventory/hosts.ini):**
```ini
[webservers]
wsl-local ansible_host=127.0.0.1 ansible_port=22 ansible_user=andpe
```

**Ansible Config (ansible.cfg):**
```ini
[defaults]
inventory = inventory/hosts.ini
roles_path = roles
host_key_checking = False
remote_user = andpe
retry_files_enabled = False
private_key_file = ~/.ssh/id_rsa

[privilege_escalation]
become = True
become_method = sudo
become_user = root
become_ask_pass = True
```

### First Run: `ansible-playbook playbooks/provision.yml`

```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [wsl-local]

TASK [common : Update apt cache] ***********************************************
changed: [wsl-local]

TASK [common : Install common packages] ****************************************
changed: [wsl-local]

TASK [docker : Add Docker GPG key] *********************************************
changed: [wsl-local]

TASK [docker : Add Docker repository] ******************************************
changed: [wsl-local]

TASK [docker : Install Docker packages] ****************************************
changed: [wsl-local]

o use pipx install xyz, which will manage a\n    virtual environment for you. Make sure you have pipx installed.\n    \n    See /usr/share/doc/python3.12/README.venv for more information.\n\nnote: If you believe this is a mistake, please contact your Python installation or OS distribution provider. You can override this, at the risk of breaking your Python installation or OS, by passing --break-system-packages.\nhint: See PEP 668 for the detailed specification.\n"}

PLAY RECAP *********************************************************************
wsl-local                  : ok=9    changed=5    unreachable=0    failed=1    skipped=0    rescued=0    ignored=0
o use pipx install xyz, which will manage a\n    virtual environment for you. Make sure you have pipx installed.\n    \n    See /usr/share/doc/python3.12/README.venv for more information.\n\nnote: If you believe this is a mistake, please contact your Python installation or OS distribution provider. You can override this, at the risk of breaking your Python installation or OS, by passing --break-system-packages.\nhint: See PEP 668 for the detailed specification.\n"}

o use pipx install xyz, which will manage a\n    virtual environment for you. Make sure you have pipx installed.\n    \n    See /usr/share/doc/python3.12/README.venv for more information.\n\nnote: If you believe this is a o use pipx install xyz, which will manage a\n    virtual environment for you. Make sure you have pipx installed.\n    \n    See /usr/share/doc/python3.12/README.venv for more information.\n\nnote: If you believe this is a mistake, please contact your Python installation or OS distribution provider. You can override this, at the risk of breaking your Python installation or OS, by passing --break-system-packages.\nhint: See PEP 668 for the detailed specification.\n"}

PLAY RECAP *********************************************************************
wsl-local                  : ok=9    changed=5    unreachable=0    failed=1    skipped=0    rescued=0    ignored=0
```

### Second Run: `ansible-playbook playbooks/provision.yml`

```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [wsl-local]

TASK [common : Update apt cache] ***********************************************
ok: [wsl-local]

TASK [common : Install common packages] ****************************************
ok: [wsl-local]

TASK [docker : Add Docker GPG key] *********************************************
ok: [wsl-local]

TASK [docker : Add Docker repository] ******************************************
ok: [wsl-local]

TASK [docker : Install Docker packages] ****************************************
ok: [wsl-local]

TASK [docker : Ensure Docker is running and enabled] ***************************
changed: [wsl-local]

TASK [docker : Install Python Docker module for Ansible] ***********************
ok: [wsl-local]

PLAY RECAP *********************************************************************
wsl-local                  : ok=9    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Third Run: `ansible-playbook playbooks/provision.yml`

```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [wsl-local]

TASK [common : Update apt cache] ***********************************************
ok: [wsl-local]

TASK [common : Install common packages] ****************************************
ok: [wsl-local]

TASK [docker : Add Docker GPG key] *********************************************
ok: [wsl-local]

TASK [docker : Add Docker repository] ******************************************
ok: [wsl-local]

TASK [docker : Install Docker packages] ****************************************
ok: [wsl-local]

TASK [docker : Ensure Docker is running and enabled] ***************************
ok: [wsl-local]

TASK [docker : Install Python Docker module for Ansible] ***********************
ok: [wsl-local]

PLAY RECAP *********************************************************************
wsl-local                  : ok=9    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Analysis

- The first run installed Docker components (5 changes) but failed to install the Python Docker module due to Ubuntu's external environment protection. 
- After adjusting the playbook, the second run successfully started Docker (1 change) and installed the module. 
- The third run made zero changes, proving idempotency. Idempotency is ensured by Ansible modules that check current state before acting. The Python module installation was fixed.

---

## 4. Ansible Vault Usage

### How We Store Credentials Securely

Sensitive data (Docker Hub credentials) are stored in an encrypted vault file and enter password:

```bash
ansible-vault create group_vars/all.yml
```

### Vault File Contents (Example - Encrypted)

When you run `ansible-vault create`, the file is automatically encrypted:

```
$ANSIBLE_VAULT;1.1;AES256
38313064313339353362333464663764613962323038636536646135303337633537653238663831
3263633234346166643231633463616234373361303237640a333834626563336462366462393732
36393039323132336134353438663831303838633263363233613665376461383037626466323462
3730323964323861640a313032663761636563323465653038653066373439323139643433346361
63306261373562326438363039633961353963636262643363626463663039343963343534383731
32613233656438386537386433363633326237303262646235323661633339363765343938663230
32623831333262366138343931363663383835383133666536643261666434616138643235386365
64623862636132303837653965363139336166323037313235393066346637393761373937636531
64323064393136343130613638636630363439343036306365306662623961346637373931326161
39343031323037626531633237326638653036386536333763633965306263386233656463646266
32626133316166333832313439386137636462633536313933623462353661393438373430616335
34643738646666353062393835613265303332303236366463366530396463613134633332643832
38616634616132386363396661663038646231343061643832323566303763313435633861656362
36613730663337333439303966653963396632623630376237663231626335613836366534636463
38323266646630393639306634316164303332656332663238383637386464313238663135336637
32643461646335663536663064346132303063653935303835653261323365653138366232333065
32323564363639643264393430646535643537393134613362383930326264363033
```

To view it (with password):
```bash
ansible-vault view group_vars/all.yml
```

### Decrypted Content (for reference)

```yaml
---
dockerhub_username: DOCKER_USERNAME
dockerhub_password: DOCKER_PASSWORD
app_name: "devops-info-service"
docker_image: "{{ dockerhub_username }}/{{ app_name }}"
docker_image_tag: "latest"
app_port: 5000
app_container_name: "{{ app_name }}"
```

### Vault Password Management Strategy

**Option 1: Interactive Prompt (Recommended for security)**
```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

**Option 2: Password File (For development/automation)**
```bash
# Create vault password file (NEVER commit this!)
echo "password" > .vault_pass
chmod 600 .vault_pass

# Add to .gitignore
echo ".vault_pass" >> .gitignore

# Update ansible.cfg to use it
[defaults]
vault_password_file = .vault_pass

# Run without password prompt
ansible-playbook playbooks/deploy.yml
```

### Integration with Deployment Playbook

The `playbooks/deploy.yml` file loads encrypted variables:

```yaml
---
- name: Deploy application
  hosts: webservers
  become: true
  vars_files:
    - ../group_vars/all.yml
  tasks:
    - name: Show dockerhub_username (for debugging)
      debug:
        var: dockerhub_username
  roles:
    - app_deploy
```

### Why Ansible Vault is Important

1. **Security:** Docker Hub passwords never stored in plain text in repository
2. **Version Control Safety:** Can safely commit encrypted `group_vars/all.yml` to Git
3. **Best Practice:** Industry standard approach for managing sensitive credentials
4. **Prevention of Accidents:** Encrypted data prevents accidental exposure if repository is leaked

**Without Vault:**
- Passwords in plain text in Git history forever
- Anyone with repo access has credentials
- Exposure if repository becomes public

**With Vault:**
- Credentials encrypted with AES-256
- Even if repository exposed, credentials are protected
- Password can be rotated independently from code
- Access control can be managed separately

---

## 5. Deployment Verification

### Run Deployment Playbook

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

**Output:**

```
Vault password:

PLAY [Deploy application] *************************************************************

TASK [Gathering Facts] ****************************************************************
ok: [wsl-local]

TASK [app_deploy : Login to Docker Hub] ***********************************************
changed: [wsl-local]

TASK [app_deploy : Pull Docker image] *************************************************
changed: [wsl-local]

TASK [app_deploy : Stop existing container] *******************************************
ok: [wsl-local]

TASK [app_deploy : Run new container] *************************************************
changed: [wsl-local]

TASK [app_deploy : Wait for app to be ready] ******************************************
ok: [wsl-local]

TASK [app_deploy : Check health endpoint] *********************************************
ok: [wsl-local]

TASK [Show dockerhub_username] ********************************************************
ok: [wsl-local] => {
    "dockerhub_username": "chaleshka"
}

RUNNING HANDLER [app_deploy : restart app] ********************************************
changed: [wsl-local]

PLAY RECAP ****************************************************************************
wsl-local                  : ok=9    changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Container Status: `docker ps`

Run on target VM:
```bash
ansible webservers -a "docker ps"
```

**Output:**
```
  CREATED              STATUS          PORTS                    NAMES
4095d294d7c1   chaleshka/devops-info-service:latest   "python -u app.py"   About a minute ago   Up 47 seconds   0.0.0.0:5000->5000/tcp   devops-info-service
```

Container is running with:
- Image: `chaleshka/devops-app:latest`
- Port mapping: `5000:5000` (host:container)
- Status: `Up 47 seconds`
- Restart policy: `unless-stopped`

### Health Check Verification

```bash
curl http://127.0.0.1:5000/health
```

**Output:**
```json
{"status":"healthy","timestamp":"2026-02-24T17:44:08.925903+00:00","uptime_seconds":52.801416}
```

**Detailed check with verbose output:**
```bash
curl -v http://127.0.0.1:5000/health
```

**Output:**
```
*   Trying 127.0.0.1:5000...
* Connected to 127.0.0.1 (127.0.0.1) port 5000
> GET /health HTTP/1.1
> Host: 127.0.0.1:5000
> User-Agent: curl/8.5.0
> Accept: */*
>
< HTTP/1.1 200 OK
< Server: Werkzeug/3.1.5 Python/3.12.12
< Date: Tue, 24 Feb 2026 17:45:03 GMT
< Content-Type: application/json
< Content-Length: 95
< Connection: close
<
{"status":"healthy","timestamp":"2026-02-24T17:45:03.015410+00:00","uptime_seconds":67.890923}
* Closing connection
```

### Main Application Endpoint

```bash
curl http://127.0.0.1:5000/
```

**Output:**
```
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"172.17.0.1","method":"GET","path":"/","user_agent":"curl/8.5.0"},"runtime":{"current_time":"2026-02-24T17:45:21.335095+00:00","timezone":"UTC","uptime_human":"0.0h 1.0m","uptime_seconds":86.210608},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":12,"hostname":"4095d294d7c1","platform":"Linux","platform_version":"#1 SMP Tue Nov 5 00:21:55 UTC 2024","python_version":"3.12.12"}}
```

---

## 6. Key Decisions

### Why use roles instead of plain playbooks?

Roles provide modularity and reusability. 
A single role can be used in multiple projects at the same time by simply including it in different playbooks.
Roles establish a standard directory structure that makes code maintenance easier and allows team members to quickly understand the codebase.

### How do roles improve reusability?

Each role contains its tasks, handlers, defaults, and templates. 
Every role directory can be copied to another project and immediately used.


### What makes a task idempotent?

Check the current state before making changes and make changes only if necessary to achieve the desired state. 
Have no side effects from repeated execution

### How do handlers improve efficiency?

Runs only if notified by a task and runs only one, even if it triggered multiple times. 

### Why is Ansible Vault necessary?

This prevents public access to credentials, which allows you to commit encrypted data to git. Only users with password can edit and decrypt current vault.