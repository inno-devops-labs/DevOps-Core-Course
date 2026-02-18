# Lab 5

## 1. Architecture Overview

**Ansible version:** `ansible [core 2.20.2]`

**VM OS and version:** `Ubuntu 22.04`

**Role structure diagram**
```bash
ansible/
├── inventory/
│   └── hosts.ini              # Static inventory
├── roles/
│   ├── common/                # Common system tasks
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   └── defaults/
│   │       └── main.yml
│   ├── docker/                # Docker installation
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   ├── handlers/
│   │   │   └── main.yml
│   │   └── defaults/
│   │       └── main.yml
│   └── app_deploy/            # Application deployment
│       ├── tasks/
│       │   └── main.yml
│       ├── handlers/
│       │   └── main.yml
│       └── defaults/
│           └── main.yml
├── playbooks/
│   ├── site.yml               # Main playbook
│   ├── provision.yml          # System provisioning
│   └── deploy.yml             # App deployment
├── group_vars/
│   └── all.yml               # Encrypted variables (Vault)
├── ansible.cfg               # Ansible configuration
└── docs/
    └── LAB05.md              # Documentation
```

**Why roles instead of monolithic playbooks?**
    - Reusability
    - Clean Architecture
    - Parallel Development
    - Selective Execution
    - Parameterization
    - Debugging & Maintenance
    - Scalability



## 2. Roles Documentation

#### 1. Common

- **Purpose:** Installs common system packages and configures the base system
- **Variables:** `common_packages`, `timezone`
- **Handlers:** No handlers in this role
- **Dependencies:** No dependencies; this is a base role

#### 2. Docker

- **Purpose:** Installs Docker and related components on target hosts
- **Variables:** `docker_users`, `docker_version`, `docker_repository`, `docker_repository_key_url`
- **Handlers:** Restart Docker
- **Dependencies:** Depends on the `common` role

#### 3. App Deploy

- **Purpose:** Deploys the containerized application on target hosts
- **Variables:** `dockerhub_username`, `dockerhub_password`, `app_name`, `app_port`, `app_host_port`, `docker_image`, `app_environment`
- **Handlers:** Restart app container
- **Dependencies:** Depends on the `docker` role


## 3. Idempotency Demonstration

**Terminal output from FIRST `provision.yml` run**
```bash
ansible-playbook playbooks/provision.yml
```
```bash
PLAY [Provision web servers] *************************************************************************************************************************************

TASK [Gathering Facts] *******************************************************************************************************************************************
ok: [info-service]

TASK [common : Update apt cache] *********************************************************************************************************************************
ok: [info-service]

TASK [common : Install common packages] **************************************************************************************************************************
changed: [info-service]

TASK [common : Set timezone] *************************************************************************************************************************************
changed: [info-service]

TASK [common : Ensure pip is installed] **************************************************************************************************************************
changed: [info-service]

TASK [common : Create .ssh directory for root] *******************************************************************************************************************
ok: [info-service]

TASK [docker : Install prerequisites for Docker] *****************************************************************************************************************
changed: [info-service]

TASK [docker : Add Docker GPG key] *******************************************************************************************************************************
changed: [info-service]

TASK [docker : Add Docker repository] ****************************************************************************************************************************
changed: [info-service]

TASK [docker : Update apt cache after adding Docker repo] ********************************************************************************************************
changed: [info-service]

TASK [docker : Install Docker packages] **************************************************************************************************************************
changed: [info-service]

TASK [docker : Ensure Docker service is running] *****************************************************************************************************************
ok: [info-service]

TASK [docker : Add users to docker group] ************************************************************************************************************************
changed: [info-service] => (item=ubuntu)
ok: [info-service] => (item=ubuntu)

TASK [docker : Install Docker SDK for Python] ********************************************************************************************************************
changed: [info-service]

RUNNING HANDLER [docker : Restart docker] ************************************************************************************************************************
changed: [info-service]

PLAY RECAP *******************************************************************************************************************************************************
info-service               : ok=15   changed=10    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

**Terminal output from SECOND provision.yml run**
```bash
ansible-playbook playbooks/provision.yml
```
```bash
PLAY [Provision web servers] *************************************************************************************************************************************

TASK [Gathering Facts] *******************************************************************************************************************************************
ok: [info-service]

TASK [common : Update apt cache] *********************************************************************************************************************************
ok: [info-service]

TASK [common : Install common packages] **************************************************************************************************************************
ok: [info-service]

TASK [common : Set timezone] *************************************************************************************************************************************
ok: [info-service]

TASK [common : Ensure pip is installed] **************************************************************************************************************************
ok: [info-service]

TASK [common : Create .ssh directory for root] *******************************************************************************************************************
ok: [info-service]

TASK [docker : Install prerequisites for Docker] *****************************************************************************************************************
ok: [info-service]

TASK [docker : Add Docker GPG key] *******************************************************************************************************************************
ok: [info-service]

TASK [docker : Add Docker repository] ****************************************************************************************************************************
ok: [info-service]

TASK [docker : Update apt cache after adding Docker repo] ********************************************************************************************************
changed: [info-service]

TASK [docker : Install Docker packages] **************************************************************************************************************************
ok: [info-service]

TASK [docker : Ensure Docker service is running] *****************************************************************************************************************
ok: [info-service]

TASK [docker : Add users to docker group] ************************************************************************************************************************
changed: [info-service] => (item=ubuntu)
ok: [info-service] => (item=ubuntu)

TASK [docker : Install Docker SDK for Python] ********************************************************************************************************************
ok: [info-service]

RUNNING HANDLER [docker : Restart docker] ************************************************************************************************************************
ok: [info-service]

PLAY RECAP *******************************************************************************************************************************************************
info-service               : ok=15    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

**What changed first time?**
- Install common packages
- Set timezone
- Ensured pip is installed
- Installed prerequisites for Docker
- Added Docker GPG key
- Added Docker repository
- Updated apt cache after adding Docker repo
- Installed Docker packages
- Installed Docker SDK for Python
- Restarted Docker

**What didn't change second time?**
- Update apt cache after adding Docker repo

**What makes your roles idempotent?**
- Status checks
- The `state` parameter
- Declarative approach
- Modular architecture


## 4. Ansible Vault Usage

### Store credentials securely

- Sensitive data is stored in encrypted YAML files
- Symmetric AES256 encryption is used

### Vault password management strategy

- Store files in `/group_vars`
- Use a password file
- Use environment variables

### `ansible/group_vars/all.yml`

```bash
$ANSIBLE_VAULT;1.1;AES256
66653565383132356534656566383838386364666139613762633333396565623931343239363439
...
37373362643837623333386131353464643161623435646134366564383135613233326631333037
34333963373935636335
```

### Ansible importance

- **Security** — passwords are not stored in plain text in Git
- **Compliance** — standards like PCI DSS, HIPAA, GDPR require secrets encryption
- **Collaboration** — safely share code with your team
- **CI/CD integration** — automate without exposing secrets
- **Idempotence** — commit all code, including encrypted configuration


## 5. Deployment Verification

**Terminal output from` deploy.yml` run**

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

```bash
Vault password: 

PLAY [Deploy application] ****************************************************************************************************************************************

TASK [Gathering Facts] *******************************************************************************************************************************************
ok: [info-service]

TASK [app_deploy : Login to Docker Hub] **************************************************************************************************************************
ok: [info-service]

TASK [app_deploy : Pull Docker image] ****************************************************************************************************************************
ok: [info-service]

TASK [app_deploy : Check if container exists] ********************************************************************************************************************
ok: [info-service]

TASK [app_deploy : Stop existing container if running] ***********************************************************************************************************
changed: [info-service]

TASK [app_deploy : Remove old container if exists] ***************************************************************************************************************
changed: [info-service]

TASK [app_deploy : Create application directory] *****************************************************************************************************************
ok: [info-service]

TASK [app_deploy : Deploy application container] *****************************************************************************************************************
changed: [info-service]

TASK [app_deploy : Wait for application to start] ****************************************************************************************************************
ok: [info-service]

TASK [app_deploy : Check application health endpoint] ************************************************************************************************************
ok: [info-service]

TASK [app_deploy : Display health check result] ******************************************************************************************************************
ok: [info-service] => {
    "msg": "Application is healthy! Response: {'status': 'healthy', 'timestamp': '2026-02-09T15:11:15.557890+00:00', 'uptime_seconds': 12}"
}

TASK [Show running containers] ***********************************************************************************************************************************
changed: [info-service]

TASK [Display container status] **********************************************************************************************************************************
ok: [info-service] => {
    "msg": [
        "NAMES          IMAGE                              STATUS          PORTS",
        "info-service   sayfetik/info-service:latest   Up 17 seconds   0.0.0.0:5000->5000/tcp"
    ]
}

PLAY RECAP *******************************************************************************************************************************************************
info-service               : ok=13   changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

**Container status: `docker ps` output**

```bash
"NAMES          IMAGE          STATUS          PORTS",
"info-service   sayfetik/info-service:latest   Up 17 seconds   0.0.0.0:5000->5000/tcp"
```

**Health check verification: `curl` outputs**

```bash
"msg": "Application is healthy! Response: {'status': 'healthy', 'timestamp': '2026-02-09T15:11:15.557890+00:00', 'uptime_seconds': 12}"
```


## 6. Key Decisions

**Why use roles instead of plain playbooks?**

Roles provide modular organization, separating configuration into reusable components. They promote code sharing and keep playbooks clean and readable, letting them orchestrate roles instead of containing all logic.

**How do roles improve reusability?**

Roles group related tasks, variables, and handlers into self-contained units that can be imported into multiple playbooks and projects. This enables teams to share standardized configurations and reduces code duplication.

**What makes a task idempotent?**

A task is idempotent if it checks the system's current state before making changes, ensuring it only modifies the system if the desired state is not already present. This allows safe repeated execution without unintended side effects.

**How do handlers improve efficiency?**

Handlers are triggered only by tasks that actually change the system state, avoiding unnecessary restarts or reloads. They run once at the end of the playbook, even if notified multiple times, minimizing service disruption.

**Why is Ansible Vault necessary?**

Ansible Vault encrypts sensitive data like passwords and API keys, preventing credential leaks in version control. It's essential for security compliance and safe collaboration when managing infrastructure as code.


## Bonus Task - Dynamic Inventory with Cloud Plugins

Dynamic inventory with cloud plugins: Yandex Cloud does not have an Ansible plugin.
