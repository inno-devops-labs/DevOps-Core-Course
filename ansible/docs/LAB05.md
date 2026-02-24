# Lab 05

## 1. Architecture Overview

**Ansible version used:** ansible [core 2.18.11]

**Target VM OS and version:** Debian GNU/Linux 12 (bookworm)

**Role Structure:**

```
ansible/
├── inventory/
│   ├── hosts.ini              # Inventory configuration
│   ├── group_vars/
│   └── all.yml         # Encrypted credentials
├── playbooks/
│   ├── provision.yml          # Initial server setup
│   └── deploy.yml              # Application deployment
└── roles/
    ├── common/                 # Base system configuration
    │   ├── defaults/
    │   │   └── main.yml
    │   └── tasks/
    │       └── main.yml
    ├── docker/                  # Docker installation
    │   ├── defaults/
    │   │   └── main.yml
    │   ├── handlers/
    │   │   └── main.yml
    │   ├── tasks/
    │   │   └── main.yml
    │   └── templates/
    │       └── docker.sources.j2
    └── app_deploy/              # Application deployment
        ├── defaults/
        │   └── main.yml
        ├── handlers/
        │   └── main.yml
        └── tasks/
            └── main.yml
```

**Why roles instead of monolithic playbooks?**
Roles provide better organization, reusability, and maintainability by separating concerns into reusable components.

---

## 2. Roles Documentation

### Role: common

| Aspect | Description |
|--------|-------------|
| **Purpose** | Updates apt cache and installs common system packages" |
| **Variables** | `common_packages`: List of common packages to install |
| **Handlers** | None |
| **Dependencies** | None |

### Role: docker

| Aspect | Description |
|--------|-------------|
| **Purpose** | [What does this role do? - e.g., "Installs and configures Docker CE on Debian-based systems"] |
| **Variables** | `docker_user`: User to add to docker group<br>`docker_version`: Docker version constraint (empty = latest)<br>`docker_cli_version`: Docker CLI version constraint<br>`containerd_version`: containerd version constraint |
| **Handlers** | `restart docker`: Restarts Docker service |
| **Dependencies** | None |

### Role: app_deploy

| Aspect | Description |
|--------|-------------|
| **Purpose** | Deploys the Python application container using Docker |
| **Variables** | `app_port`: Application port (default: 5000)<br>`docker_restart_policy`: Container restart policy (default: unless-stopped)<br>`app_environment_vars`: Environment variables (default: {}) |
| **Handlers** | `restart app container`: Restarts the application container |
| **Dependencies** | docker (implicitly) |

---

## 3. Idempotency Demonstration

### First provision.yml run

```bash
ansible-playbook playbooks/provision.yml

PLAY [Provision web servers] *******************************************************************************************************

TASK [Gathering Facts] *************************************************************************************************************
ok: [your-vm-name]

TASK [common : Update apt cache] ***************************************************************************************************
changed: [your-vm-name]

TASK [common : Install common packages] ********************************************************************************************
changed: [your-vm-name]

TASK [docker : Update apt cache] ***************************************************************************************************
changed: [your-vm-name]

TASK [docker : Install required system packages] ***********************************************************************************
changed: [your-vm-name]

TASK [docker : Create keyrings directory] ******************************************************************************************
changed: [your-vm-name]

TASK [docker : Download Docker's official GPG key] *********************************************************************************
changed: [your-vm-name]

TASK [docker : Add Docker repository to apt sources] *******************************************************************************
changed: [your-vm-name]

TASK [docker : Update apt cache after adding Docker repo] **************************************************************************
changed: [your-vm-name]

TASK [docker : Install Docker packages] ********************************************************************************************
changed: [your-vm-name]

TASK [docker : Ensure Docker service is running and enabled] ***********************************************************************
ok: [your-vm-name]

TASK [docker : Add user to docker group] *******************************************************************************************
changed: [your-vm-name]

TASK [docker : Install python3-docker for Ansible docker modules] ******************************************************************
changed: [your-vm-name]

RUNNING HANDLER [docker : restart docker] ******************************************************************************************
changed: [your-vm-name]

PLAY RECAP *************************************************************************************************************************
your-vm-name               : ok=14   changed=12    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```

### Second provision.yml run

```bash
PLAY [Provision web servers] *******************************************************************************************************

TASK [Gathering Facts] *************************************************************************************************************
ok: [your-vm-name]

TASK [common : Update apt cache] ***************************************************************************************************
ok: [your-vm-name]

TASK [common : Install common packages] ********************************************************************************************
ok: [your-vm-name]

TASK [docker : Update apt cache] ***************************************************************************************************
ok: [your-vm-name]

TASK [docker : Install required system packages] ***********************************************************************************
ok: [your-vm-name]

TASK [docker : Create keyrings directory] ******************************************************************************************
ok: [your-vm-name]

TASK [docker : Download Docker's official GPG key] *********************************************************************************
ok: [your-vm-name]

TASK [docker : Add Docker repository to apt sources] *******************************************************************************
ok: [your-vm-name]

TASK [docker : Update apt cache after adding Docker repo] **************************************************************************
ok: [your-vm-name]

TASK [docker : Install Docker packages] ********************************************************************************************
ok: [your-vm-name]

TASK [docker : Ensure Docker service is running and enabled] ***********************************************************************
ok: [your-vm-name]

TASK [docker : Add user to docker group] *******************************************************************************************
ok: [your-vm-name]

TASK [docker : Install python3-docker for Ansible docker modules] ******************************************************************
ok: [your-vm-name]

PLAY RECAP *************************************************************************************************************************
your-vm-name               : ok=13   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```

**Analysis:**

- **What changed first time?** [Explain what was installed/configured]
- **What didn't change second time?** [Explain what remained the same]
- **Why?** Ansible checks the current state before making changes. If a package is already installed or a service is already running, Ansible skips that task.

**What makes your roles idempotent?**
My roles use Ansible modules that are inherently idempotent (apt, systemd, get_url, etc.). These modules check the current system state before applying changes, ensuring they only make modifications when necessary.

---

## 4. Ansible Vault Usage

**How credentials are stored securely:**
Sensitive data like Docker Hub credentials are stored in encrypted vault files using Ansible Vault. These files are committed to version control but remain encrypted.

**Vault password management strategy:**
The vault password is provided at runtime using --ask-vault-pass flag, never stored in plain text or committed to version control."

**Example of encrypted file:**

```yaml

$ANSIBLE_VAULT;1.1;AES256
65303433666634303436373461313837653238613463363931643361653664316238623264393266
3834336566373731306136323631346136643466666436650a356664396463666436646163383565
64303335303366376537316266346234383761323864623639343035343565356430336461303462
3161613031356666360a393161313162396363613033323639313264363637373230326532313565
65643334663232396230616434643730343732646638646131333865643664343064363366643432
62366635613738393661323062353134356436313135656638656133613866383836396633356235
65616263316431636133343866643865343031333633306631663366653530303362376533353132
65303434646666383937396432356261323461613761636539393966303335313034666662383339
61303062343637613734326531336533346663323931393366323033313534616230653763616566
31333730626563656530656531313563303433346663356461313364333837316536343864626631
37303336613536643939376432616332633361653564633037623231316233613562353938383732
36626264386437376466303763666366366238333831393133323534643532356664366233313132
62666337393731326133333632313661656533363034663536363535633333303838663839633465
66633761373963336638623938396139313266646538343534623230376632383331323063626235
31316132333137633636623532373239313230346133393535616139393438393361323030343739
36326366393037396266333635373162636338333562313639363332646538623738663233346661
62366437653532333439313362396636366332343062306463383830343334613235353534333737
34316461346334666533313662626331363237636335306636646137373861306537393138616639
65346431383739636238623237643130336630313532333236386163356666666330326562613730
32303032643639623761
...
```

**Why Ansible Vault is important:**
Ansible Vault ensures sensitive information like passwords, API keys, and tokens are never exposed in plain text, even when playbooks are stored in version control systems or shared among team members.

---

## 5. Deployment Verification

### deploy.yml run output


```bash

bulatgazizov@fedora:~/Projects/DevOps-Core-Course/ansible$ ansible-playbook playbooks/deploy.yml --ask-vault-pass
Vault password: 

PLAY [Deploy application] **********************************************************************************************************

TASK [Gathering Facts] *************************************************************************************************************
ok: [your-vm-name]

TASK [app_deploy : Log in to Docker Hub] *******************************************************************************************
changed: [your-vm-name]

TASK [app_deploy : Pull Docker image] **********************************************************************************************
changed: [your-vm-name]

TASK [app_deploy : Check if container is running] **********************************************************************************
ok: [your-vm-name]

TASK [app_deploy : Stop existing container if running] *****************************************************************************
skipping: [your-vm-name]

TASK [app_deploy : Remove old container if exists] *********************************************************************************
skipping: [your-vm-name]

TASK [app_deploy : Run new container] **********************************************************************************************
changed: [your-vm-name]

TASK [app_deploy : Wait for application to be ready on port 5000] ******************************************************************
ok: [your-vm-name]

TASK [app_deploy : Verify health endpoint] *****************************************************************************************
ok: [your-vm-name]

TASK [app_deploy : Display health check result] ************************************************************************************
ok: [your-vm-name] => {
    "msg": "Health check succeeded with status 200"
}

RUNNING HANDLER [app_deploy : restart app container] *******************************************************************************
changed: [your-vm-name]

PLAY RECAP *************************************************************************************************************************
your-vm-name               : ok=9    changed=4    unreachable=0    failed=0    skipped=2    rescued=0    ignored=0   
```


### Container status

```bash
ansible webservers -a "docker ps" --ask-vault-pass

your-vm-name | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                            COMMAND           CREATED         STATUS              PORTS                    NAMES
61ea6197ce1f   bulatgazizov/python_app:latest   "python app.py"   2 minutes ago   Up About a minute   0.0.0.0:5000->5000/tcp   python_app
```

### Health check verification

```bash
curl http://45.150.238.55:5000/health

{"status":"healthy","timestamp":"2026-02-24T22:07:07.446233+00:00","uptime_seconds":145}

curl http://45.150.238.55:5000/

{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"61ea6197ce1f","platform":"Linux","platform_version":"6.1.0-9-amd64","architecture":"x86_64","cpu_count":1,"python_version":"3.12.12"},"runtime":{"uptime_seconds":2937,"uptime_human":"0 hours, 48 minutes","current_time":"2026-02-24T22:53:39.605386+00:00","timezone":"UTC"},"request":{"client_ip":"80.71.232.39","user_agent":"curl/8.11.1","method":"GET","path":"/"},"endpoints":[{"path":"/openapi.json","description":"openapi","methods":["GET","HEAD"]},{"path":"/docs","description":"swagger_ui_html","methods":["GET","HEAD"]},{"path":"/docs/oauth2-redirect","description":"swagger_ui_redirect","methods":["GET","HEAD"]},{"path":"/redoc","description":"redoc_html","methods":["GET","HEAD"]},{"path":"/","description":"read_root","methods":["GET"]},{"path":"/health","description":"health","methods":["GET"]}]}
```

### Handler execution

The 'restart app container' handler was triggered when a new image was pulled."

---

## 6. Key Decisions

**Why use roles instead of plain playbooks?**
Roles provide better organization by separating configuration into logical components (common, docker, app_deploy), making the codebase easier to navigate and maintain. They also enable reusability across different projects and allow team members to work on different parts independently without merge conflicts.

**How do roles improve reusability?**
Roles are self-contained units with their own variables, tasks, handlers, and templates that can be easily shared across different playbooks and projects. For example, my Docker role can be reused in any project requiring Docker installation without copying code, and variables allow customization for different environments.

**What makes a task idempotent?**
A task is idempotent when it checks the current state before making changes and only acts if the desired state differs from the current state. Ansible modules like apt, systemd, and get_url are inherently idempotent because they verify package installation status, service running state, or file existence before applying changes.

**How do handlers improve efficiency?**
Handlers run only when notified by tasks and execute once at the end of the play, preventing unnecessary restarts. For instance, if multiple tasks modify Docker configuration, the Docker service is restarted only once after all changes are applied, rather than after each individual change.

**Why is Ansible Vault necessary?**
Ansible Vault encrypts sensitive data like passwords, API tokens, and private keys so they can be safely stored in version control systems. Without it, secrets would be exposed in plain text, creating security risks when playbooks are shared or stored in repositories like GitHub.
