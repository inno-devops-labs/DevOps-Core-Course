# Lab 5 - Ansible Fundamentals Documentation

## 1. Architecture Overview

### Ansible version used
```
ansible [core 2.20.2]
  config file = /Users/newspec/Desktop/DevOps/DevOps-Core-Course/ansible/ansible.cfg
  configured module search path = ['/Users/newspec/.ansible/plugins/modules', '/usr/share/ansible/plugins/modules']
  ansible python module location = /opt/homebrew/Cellar/ansible/13.3.0/libexec/lib/python3.14/site-packages/ansible
  ansible collection location = /Users/newspec/.ansible/collections:/usr/share/ansible/collections
  executable location = /opt/homebrew/bin/ansible
  python version = 3.14.3 (main, Feb  3 2026, 15:32:20) [Clang 17.0.0 (clang-1700.6.3.2)] (/opt/homebrew/Cellar/ansible/13.3.0/libexec/bin/python)
  jinja version = 3.1.6
  pyyaml version = 6.0.3 (with libyaml v0.2.5)
  ```

### Target VM OS and version
- **Operating System**: Ubuntu 24.04 LTS Vanilla

### Role structure diagram or explanation

This project uses a **role-based architecture** for maximum reusability and maintainability:

```
ansible/
├── roles/
│   ├── common/          # System provisioning (packages, timezone)
│   ├── docker/          # Docker installation and configuration
│   └── app_deploy/      # Application deployment with Docker
├── playbooks/
│   ├── site.yml         # Complete infrastructure + deployment
│   ├── provision.yml    # System provisioning only
│   └── deploy.yml       # Application deployment only
├── inventory/
│   └── hosts.ini        # Static inventory
└── group_vars/
    └── all.yml          # Encrypted variables (Ansible Vault)
```

### Why Roles Instead of Monolithic Playbooks?

**Roles provide:**

1. **Reusability**: Same role can be used across multiple projects
2. **Modularity**: Each role has a single, well-defined purpose
3. **Maintainability**: Changes are isolated to specific roles
4. **Testability**: Roles can be tested independently
5. **Sharing**: Roles can be shared via Ansible Galaxy
6. **Organization**: Clear structure makes code easy to navigate
7. **Scalability**: Easy to add new roles without affecting existing ones

**Example**: The `docker` role can be reused in any project that needs Docker, without modification.

---

## 2. Roles Documentation

### 2.1 Common Role

**Purpose**: Performs basic system provisioning tasks that every server needs.

**Key Variables** (from `defaults/main.yml`):
```yaml
common_packages:
  - python3-pip
  - curl
  - git
  - vim
  - htop
  - wget
  - unzip
  - software-properties-common
  - apt-transport-https
  - ca-certificates
  - gnupg
  - lsb-release

timezone: "UTC"
```

**Tasks**:
1. Update apt cache (with 3600s cache validity)
2. Install common packages
3. Set system timezone

**Handlers**: None (no services to restart)

**Dependencies**: None

**Tags**: `common`, `packages`, `timezone`

---

### 2.2 Docker Role

**Purpose**: Installs and configures Docker CE on Ubuntu systems.

**Key Variables** (from `defaults/main.yml`):
```yaml
docker_user: "ubuntu"
docker_version: "latest"
```

**Tasks**:
1. Install Docker prerequisites
2. Create directory for Docker GPG key
3. Add Docker GPG key
4. Detect Ubuntu release codename
5. Add Docker repository
6. Install Docker packages (docker-ce, docker-ce-cli, containerd.io)
7. Ensure Docker service is running and enabled
8. Add user to docker group
9. Install python3-docker (for Ansible docker modules)
10. Verify Docker installation

**Handlers**:
- `restart docker`: Restarts Docker service when repository or packages change

**Dependencies**: None (but typically runs after `common` role)

**Tags**: `docker`, `packages`, `service`, `user`, `verify`

**Idempotency Features**:
- Uses `apt_key` and `apt_repository` modules (stateful)
- Service module ensures desired state
- User module only adds to group if not already present

---

### 2.3 App Deploy Role

**Purpose**: Deploys containerized Python application using Docker.

**Key Variables** (from `defaults/main.yml`):
```yaml
app_port: 8000
app_restart_policy: "unless-stopped"
app_environment_vars: {}
```

**Variables from Vault** (group_vars/all.yml):
```yaml
dockerhub_username: <encrypted>
dockerhub_password: <encrypted>
app_name: devops-app
docker_image: "{{ dockerhub_username }}/{{ app_name }}"
docker_image_tag: latest
app_container_name: "{{ app_name }}"
```

**Tasks**:
1. Log in to Docker Hub (credentials from Vault, `no_log: true`)
2. Pull Docker image
3. Stop existing container (if running)
4. Remove old container (if exists)
5. Run new container with proper configuration
6. Wait for application port to be available
7. Verify health endpoint
8. Display health check result

**Handlers**:
- `restart application`: Restarts the application container

**Dependencies**: Requires `docker` role to be run first

**Tags**: `app`, `deploy`, `verify`

**Security Features**:
- Uses `no_log: true` for Docker login (prevents credential exposure)
- Credentials stored in encrypted Ansible Vault
- Uses Docker Hub access tokens (not passwords)

---

## 3. Idempotency Demonstration

### Terminal output from FIRST provision.yml run

```bash
PLAY [Provision web servers] *********************************************************************************************

TASK [Gathering Facts] ***************************************************************************************************
ok: [lab04-vm]

TASK [common : Update apt cache] *****************************************************************************************
changed: [lab04-vm]

TASK [common : Install common packages] **********************************************************************************
changed: [lab04-vm]

TASK [common : Set timezone] *********************************************************************************************
changed: [lab04-vm]

TASK [docker : Install prerequisites for Docker] *************************************************************************
ok: [lab04-vm]

TASK [docker : Create directory for Docker GPG key] **********************************************************************
ok: [lab04-vm]

TASK [docker : Add Docker GPG key] ***************************************************************************************
changed: [lab04-vm]

TASK [docker : Get Ubuntu release codename] ******************************************************************************
ok: [lab04-vm]

TASK [docker : Get system architecture] **********************************************************************************
ok: [lab04-vm]

TASK [docker : Add Docker repository] ************************************************************************************
changed: [lab04-vm]

TASK [docker : Install Docker packages] **********************************************************************************
changed: [lab04-vm]

TASK [docker : Ensure Docker service is running and enabled] *************************************************************
ok: [lab04-vm]

TASK [docker : Add user to docker group] *********************************************************************************
changed: [lab04-vm]

TASK [docker : Install python3-docker for Ansible docker modules] ********************************************************
changed: [lab04-vm]

TASK [docker : Verify Docker installation] *******************************************************************************
ok: [lab04-vm]

TASK [docker : Display Docker version] ***********************************************************************************
ok: [lab04-vm] => {
    "msg": "Docker version installed: Docker version 29.2.1, build a5c7197"
}

RUNNING HANDLER [docker : restart docker] ********************************************************************************
changed: [lab04-vm]

PLAY RECAP ***************************************************************************************************************
lab04-vm                   : ok=17   changed=9    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0  
```

### Terminal output from SECOND provision.yml run

```bash
PLAY [Provision web servers] *******************************************************************************************************************************************************************

TASK [Gathering Facts] *************************************************************************************************************************************************************************
ok: [lab04-vm]

TASK [common : Update apt cache] ***************************************************************************************************************************************************************
ok: [lab04-vm]

TASK [common : Install common packages] ********************************************************************************************************************************************************
ok: [lab04-vm]

TASK [common : Set timezone] *******************************************************************************************************************************************************************
ok: [lab04-vm]

TASK [docker : Install prerequisites for Docker] ***********************************************************************************************************************************************
ok: [lab04-vm]

TASK [docker : Create directory for Docker GPG key] ********************************************************************************************************************************************
ok: [lab04-vm]

TASK [docker : Add Docker GPG key] *************************************************************************************************************************************************************
ok: [lab04-vm]

TASK [docker : Get Ubuntu release codename] ****************************************************************************************************************************************************
ok: [lab04-vm]

TASK [docker : Get system architecture] ********************************************************************************************************************************************************
ok: [lab04-vm]

TASK [docker : Add Docker repository] **********************************************************************************************************************************************************
ok: [lab04-vm]

TASK [docker : Install Docker packages] ********************************************************************************************************************************************************
ok: [lab04-vm]

TASK [docker : Ensure Docker service is running and enabled] ***********************************************************************************************************************************
ok: [lab04-vm]

TASK [docker : Add user to docker group] *******************************************************************************************************************************************************
ok: [lab04-vm]

TASK [docker : Install python3-docker for Ansible docker modules] ******************************************************************************************************************************
ok: [lab04-vm]

TASK [docker : Verify Docker installation] *****************************************************************************************************************************************************
ok: [lab04-vm]

TASK [docker : Display Docker version] *********************************************************************************************************************************************************
ok: [lab04-vm] => {
    "msg": "Docker version installed: Docker version 29.2.1, build a5c7197"
}

PLAY RECAP *************************************************************************************************************************************************************************************
lab04-vm                   : ok=16   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0 
```

### Analysis: What Changed First Time? What Didn't Change Second Time?

#### First Run Analysis (9 tasks changed)

**Tasks That Changed (Yellow "changed" status):**

1. **`common : Update apt cache`** - Changed because apt cache was outdated or didn't exist
2. **`common : Install common packages`** - Changed because packages were not installed yet
3. **`common : Set timezone`** - Changed because timezone was not set to UTC
4. **`docker : Add Docker GPG key`** - Changed because GPG key was not present in system
5. **`docker : Add Docker repository`** - Changed because Docker repository was not configured
6. **`docker : Install Docker packages`** - Changed because Docker was not installed
7. **`docker : Add user to docker group`** - Changed because user was not in docker group
8. **`docker : Install python3-docker`** - Changed because python3-docker package was not installed
9. **`HANDLER: restart docker`** - Executed because Docker repository and packages were added (notified by tasks)

**Tasks That Didn't Change (Green "ok" status):**

1. **`Gathering Facts`** - Always runs to collect system information (not a change)
2. **`docker : Install prerequisites for Docker`** - Prerequisites already present on Ubuntu 24.04
3. **`docker : Create directory for Docker GPG key`** - Directory `/etc/apt/keyrings` already existed
4. **`docker : Get Ubuntu release codename`** - Read-only command (marked with `changed_when: false`)
5. **`docker : Get system architecture`** - Read-only command (marked with `changed_when: false`)
6. **`docker : Ensure Docker service is running and enabled`** - Service already running after installation
7. **`docker : Verify Docker installation`** - Read-only verification command
8. **`docker : Display Docker version`** - Debug task (always shows "ok")

**Summary**: 9 out of 17 tasks made actual changes to the system.

---

#### Second Run Analysis (0 tasks changed)

**All Tasks Showed "ok" Status (Green):**

Every task verified that the desired state already exists and made no changes:

1. **`common : Update apt cache`** - Cache still valid (within 3600s window)
2. **`common : Install common packages`** - All packages already installed at correct versions
3. **`common : Set timezone`** - Timezone already set to UTC
4. **`docker : Install prerequisites for Docker`** - Prerequisites already present
5. **`docker : Create directory for Docker GPG key`** - Directory already exists
6. **`docker : Add Docker GPG key`** - GPG key already present in keyring
7. **`docker : Add Docker repository`** - Repository already configured in sources list
8. **`docker : Install Docker packages`** - Docker packages already installed at correct versions
9. **`docker : Ensure Docker service is running and enabled`** - Service already running and enabled
10. **`docker : Add user to docker group`** - User already member of docker group
11. **`docker : Install python3-docker`** - Package already installed

**No Handlers Executed:**
- `restart docker` handler was NOT triggered because no tasks reported "changed" status
- Handlers only run when notified by tasks that make changes

**Key Difference**:
- **First run**: `ok=17 changed=9` (9 changes + 1 handler)
- **Second run**: `ok=16 changed=0` (no changes, no handlers)

---

### What Makes These Roles Idempotent?

**1. Stateful Modules**:
- `apt`: Uses `state=present` (not `command: apt install`)
- `service`: Uses `state=started` (not `command: systemctl start`)
- `user`: Uses `groups` with `append=yes`
- `file`: Uses `state=directory`

**2. Conditional Execution**:
- `cache_valid_time: 3600` prevents unnecessary apt updates
- `changed_when: false` for read-only commands
- `ignore_errors: yes` for cleanup tasks

**3. Declarative Approach**:
- Describe desired state, not steps to achieve it
- Ansible determines what changes are needed
- Only executes necessary actions

**4. Handler Pattern**:
- Handlers only run when notified
- Handlers only run once per play (even if notified multiple times)
- Handlers run at end of play (after all tasks)

---

## 4. Ansible Vault Usage

### How you store credentials securely

**Encrypted File** (`group_vars/all.yml`):
```
$ANSIBLE_VAULT;1.1;AES256
64646331363832623830316636666263633265316239373332653234623633333434643135306638
3639333565353461386639613533356433623135616634650a663166353437643861363063393166
34393639333066326165333439653936613538333931663161303333663665656261663536346538
3432306235663933310a313364323164633930306161396466333264626336393163623366666332
62623333366637343830353337366364393437643264326466633839666466623633396130623435
30626237653337323635653965393432316562333462356333333066636363373939326361316462
37393662376630373266666135353432376536666436323866313530636234353733353232346539
30663063316166376264626462356565393035373835636338343834343838623333376433633938
32626663313033376465616462313934353431376532356334373762353264633338633438633366
32383161663064636337396663636638343335363535343734333132373139343530366435323538
64666239666133326632376531353663383534646538623135393962363564393632373265613565
64313164636565633635376634396231646636353339626465303166386334663063633937363832
35383236653731613538383236376233393063363736613237366564326266623135
...
```

### Vault Password Management Strategy
Use password file (`.vault_pass`) for convenience, with strict `.gitignore` rules.

### Example of encrypted file (show it's encrypted!)
**Encrypted File** (`group_vars/all.yml`):
```
$ANSIBLE_VAULT;1.1;AES256
64646331363832623830316636666263633265316239373332653234623633333434643135306638
3639333565353461386639613533356433623135616634650a663166353437643861363063393166
34393639333066326165333439653936613538333931663161303333663665656261663536346538
3432306235663933310a313364323164633930306161396466333264626336393163623366666332
62623333366637343830353337366364393437643264326466633839666466623633396130623435
30626237653337323635653965393432316562333462356333333066636363373939326361316462
37393662376630373266666135353432376536666436323866313530636234353733353232346539
30663063316166376264626462356565393035373835636338343834343838623333376433633938
32626663313033376465616462313934353431376532356334373762353264633338633438633366
32383161663064636337396663636638343335363535343734333132373139343530366435323538
64666239666133326632376531353663383534646538623135393962363564393632373265613565
64313164636565633635376634396231646636353339626465303166386334663063633937363832
35383236653731613538383236376233393063363736613237366564326266623135
...
```

### Why Ansible Vault is Important

**Security Risks Without Vault:**

1. **Credential Exposure in Version Control**
   - Plain text passwords visible in Git history
   - Anyone with repository access can see credentials
   - Credentials remain in history even after deletion
   - Public repositories expose secrets to the world

2. **Compliance Violations**
   - Most security standards prohibit plain text credentials
   - GDPR, PCI-DSS, SOC 2 require encrypted credential storage
   - Audit failures if secrets found in version control
   - Legal and financial consequences

3. **Insider Threats**
   - All team members can access all credentials
   - No access control or audit trail
   - Difficult to rotate credentials
   - Former employees retain access through Git history

4. **Accidental Exposure**
   - Easy to accidentally commit secrets
   - Secrets can leak through logs, screenshots, or error messages
   - CI/CD pipelines may expose credentials
   - Third-party integrations may access repository

---

## 5. Deployment Verification

### Terminal output from deploy.yml run

```bash
PLAY [Deploy application] **********************************************************************************************************************************************************************

TASK [Gathering Facts] *************************************************************************************************************************************************************************
ok: [lab04-vm]

TASK [app_deploy : Log in to Docker Hub] *******************************************************************************************************************************************************
ok: [lab04-vm]

TASK [app_deploy : Pull Docker image] **********************************************************************************************************************************************************
ok: [lab04-vm]

TASK [app_deploy : Stop and remove existing container (if exists)] *****************************************************************************************************************************
changed: [lab04-vm]

TASK [app_deploy : Run new container] **********************************************************************************************************************************************************
changed: [lab04-vm]

TASK [app_deploy : Wait for application port to be available] **********************************************************************************************************************************
ok: [lab04-vm]

TASK [app_deploy : Verify health endpoint] *****************************************************************************************************************************************************
ok: [lab04-vm]

TASK [app_deploy : Display health check result] ************************************************************************************************************************************************
ok: [lab04-vm] => {
    "msg": "Application is healthy: {'status': 'healthy', 'timestamp': '2026-02-21T18:07:25.200649+00:00', 'uptime_seconds': 5}"
}

RUNNING HANDLER [app_deploy : restart application] *********************************************************************************************************************************************
changed: [lab04-vm]

PLAY RECAP *************************************************************************************************************************************************************************************
lab04-vm                   : ok=9    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```
---

### Container status: docker ps output

```bash
lab04-vm | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                       COMMAND           CREATED              STATUS          PORTS                    NAMES
a08611d9d5bf   newspec/python_app:latest   "python app.py"   About a minute ago   Up 52 seconds   0.0.0.0:8000->8000/tcp   python_app
```

---

### Health check verification: curl outputs

```bash
lab04-vm | CHANGED | rc=0 >>
{"status":"healthy","timestamp":"2026-02-21T18:10:04.436185+00:00","uptime_seconds":156}
```

---

### Handler Execution

**When Handlers Run**:
- Handlers are triggered by `notify` in tasks
- Handlers only run if task reports "changed"
- Handlers run at end of play (after all tasks)
- Each handler runs only once per play

**Example**: If Docker repository is added (changed), the `restart docker` handler is notified and runs at the end.

**In Our Deployment**:
- `restart application` handler **WAS triggered** and executed
- Handler was notified by the "Run new container" task (line 479) which reported "changed"
- The handler ran at the end of the play, after all tasks completed
- This demonstrates proper handler usage: the container was started, then the handler ensured it was properly restarted with all configurations applied

**Why the handler triggered**:
The "Run new container" task includes `notify: restart application` in [`roles/app_deploy/tasks/main.yml`](../roles/app_deploy/tasks/main.yml:45). Since this task reported "changed" status (the container was newly created), the handler was notified and executed at the end of the play.

---

## 6. Key Decisions

### Why use roles instead of plain playbooks?

Roles provide **modularity and reusability**. Instead of one large playbook with all tasks, we have:
- **Separate concerns**: Each role has one purpose
- **Reusable components**: Docker role can be used in any project
- **Easy maintenance**: Changes to Docker installation only affect docker role
- **Clear structure**: Standard directory layout makes code easy to understand
- **Independent testing**: Each role can be tested separately

**Example**: If we need to add MongoDB to our infrastructure, we create a new `mongodb` role without touching existing roles.

---

### How do roles improve reusability?

1. **Parameterization**: Variables in `defaults/main.yml` make roles configurable
2. **No hardcoding**: Roles use variables, not hardcoded values
3. **Standard structure**: Anyone familiar with Ansible can understand our roles
4. **Ansible Galaxy**: Roles can be shared publicly or privately
5. **Version control**: Roles can be versioned independently

**Example**: The `docker` role can be used to install Docker on any Ubuntu system, just by including it in a playbook.

---

### What makes a task idempotent?

A task is idempotent when:
1. **Uses stateful modules**: `apt`, `service`, `user`, `file` (not `command` or `shell`)
2. **Describes desired state**: "Package should be present" not "Install package"
3. **Checks before acting**: Module checks current state before making changes
4. **No side effects**: Running twice doesn't cause problems

**Example**:
```yaml
# ✅ Idempotent
- name: Install nginx
  apt:
    name: nginx
    state: present

# ❌ Not idempotent
- name: Install nginx
  command: apt install -y nginx
```

The first task checks if nginx is installed before installing. The second always runs `apt install`.

---

### How do handlers improve efficiency?

Handlers provide **smart service management**:

1. **Deferred execution**: Handlers run at end of play, not immediately
2. **Run once**: Even if notified multiple times, handler runs only once
3. **Conditional execution**: Only run if notified (i.e., if something changed)
4. **Grouped restarts**: Multiple changes trigger one restart

**Example**: If we update Docker repository AND install Docker packages, both tasks notify `restart docker`, but Docker only restarts once at the end.

**Without handlers**: We'd restart Docker after each change (inefficient).

**With handlers**: Docker restarts once after all changes (efficient).

---

### Why is Ansible Vault necessary?

Ansible Vault is **essential for security**:

1. **Protects credentials**: Passwords, API keys, tokens encrypted
2. **Safe version control**: Encrypted files can be committed to Git
3. **Compliance**: Meets security requirements for credential storage
4. **Audit trail**: Changes to encrypted files tracked in Git
5. **Access control**: Only those with vault password can decrypt

**Without Vault**: Credentials in plain text, visible in Git history, easily exposed.

**With Vault**: Credentials encrypted, safe to commit, only accessible with password.

**Real-world scenario**: If our Git repository is compromised, attackers cannot access our Docker Hub credentials because they're encrypted.

---

## 7. Challenges and Solutions

### Challenge 1: Docker Repository Architecture Detection

**Issue**: Docker repository URL needs correct architecture (amd64 vs arm64).

**Solution**: Dynamic definition of architecture.
