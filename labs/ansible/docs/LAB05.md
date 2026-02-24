# Lab 05 #

## Architecture Overview ##

- Ansible version: v2.16.3
- Target VM OS: Ubuntu 24.04 LTS
- Role structure is the same as was asked in task:
    1) inventory contains VM data
    2) group_vars contains secrets
    3) Own folders for playbooks and roles
- Roles instead of monolithic playbooks because they are more reusable, modular, testable, and maintainable

## Roles Documentation ##

### Common Role ###

- Purpose: to prepare system with installations and timezone
- Variables: common_packages and timezone
- No Handlers and dependencies

### Docker Role ###

- Purpose: Docker installation and configuration with Python
- Variables: docker_version, docker_packages and docker_user
- Handler: restart docker
- Dependency: Common (needs a base system)

### Deploy Role ###

- Purpose: Deploy python application from previous labs
- Variables: app_image, app_container_name, app_port, app_restart_policy, app_env
- Handler: restart app container
- Dependency: Docker (no containerization is possible without it)

## Idempotency Demonstration ##

### First run ###

```bash
PLAY [Provision web servers] *****************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************
ok: [compute-vm-2-2-20-ssd-1771947628469]

TASK [common : Update apt cache] *************************************************************************************************************************
changed: [compute-vm-2-2-20-ssd-1771947628469]

TASK [common : Install common packages] ******************************************************************************************************************
changed: [compute-vm-2-2-20-ssd-1771947628469]

TASK [common : Set timezone] *****************************************************************************************************************************
ok: [compute-vm-2-2-20-ssd-1771947628469]

TASK [docker : Remove conflicting packages] **************************************************************************************************************
ok: [compute-vm-2-2-20-ssd-1771947628469]

TASK [docker : Add Docker GPG key] ***********************************************************************************************************************
changed: [compute-vm-2-2-20-ssd-1771947628469]

TASK [docker : Add Docker repository] ********************************************************************************************************************
changed: [compute-vm-2-2-20-ssd-1771947628469]

TASK [docker : Install Docker packages] ******************************************************************************************************************
changed: [compute-vm-2-2-20-ssd-1771947628469]

TASK [docker : Ensure Docker service is running and enabled] *********************************************************************************************
ok: [compute-vm-2-2-20-ssd-1771947628469]

TASK [docker : Add user to docker group] *****************************************************************************************************************
changed: [compute-vm-2-2-20-ssd-1771947628469]

TASK [docker : Install Python Docker module] *************************************************************************************************************
changed: [compute-vm-2-2-20-ssd-1771947628469]

PLAY RECAP ***********************************************************************************************************************************************
compute-vm-2-2-20-ssd-1771947628469 : ok=11   changed=7    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Second run ###

```bash
PLAY [Provision web servers] *******************************************************************************************************************************************************************

TASK [Gathering Facts] *************************************************************************************************************************************************************************
ok: [compute-vm-2-2-20-ssd-1771947628469]

TASK [common : Update apt cache] ***************************************************************************************************************************************************************
ok: [compute-vm-2-2-20-ssd-1771947628469]

TASK [common : Install common packages] ********************************************************************************************************************************************************
ok: [compute-vm-2-2-20-ssd-1771947628469]

TASK [common : Set timezone] *******************************************************************************************************************************************************************
ok: [compute-vm-2-2-20-ssd-1771947628469]

TASK [docker : Remove conflicting packages] ****************************************************************************************************************************************************
ok: [compute-vm-2-2-20-ssd-1771947628469]

TASK [docker : Add Docker GPG key] *************************************************************************************************************************************************************
ok: [compute-vm-2-2-20-ssd-1771947628469]

TASK [docker : Add Docker repository] **********************************************************************************************************************************************************
ok: [compute-vm-2-2-20-ssd-1771947628469]

TASK [docker : Install Docker packages] ********************************************************************************************************************************************************
ok: [compute-vm-2-2-20-ssd-1771947628469]

TASK [docker : Ensure Docker service is running and enabled] ***********************************************************************************************************************************
ok: [compute-vm-2-2-20-ssd-1771947628469]

TASK [docker : Add user to docker group] *******************************************************************************************************************************************************
ok: [compute-vm-2-2-20-ssd-1771947628469]

TASK [docker : Install Python Docker module] ***************************************************************************************************************************************************
ok: [compute-vm-2-2-20-ssd-1771947628469]

PLAY RECAP *************************************************************************************************************************************************************************************
compute-vm-2-2-20-ssd-1771947628469 : ok=11   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```

First time many tasks that require installing packages or adding repositories were changed, because they were actually busy doing this.
At the second time, nothing was changed, because everything already was installed and idempotency holds.

## Ansible Vault Usage ##

- Secrets are stored in froup_vars/all.yml. File is encrypted
- Password is stored in a local file .vault_pass and referenced in ansible.cfg
- File encrypted like that:

```bash
$ANSIBLE_VAULT;1.1;AES256
66386439653236336... (truncated)
```
- Ansible vault is important as it allows to commit code without exposing its secrets


## Deployment ##

Output:

```bash
PLAY [Deploy application] **********************************************************************************************************************************************************************

TASK [Gathering Facts] *************************************************************************************************************************************************************************
ok: [compute-vm-2-2-20-ssd-1771947628469]

TASK [app_deploy : Log in to Docker Hub] *******************************************************************************************************************************************************
ok: [compute-vm-2-2-20-ssd-1771947628469]

TASK [app_deploy : Pull the application image] *************************************************************************************************************************************************
ok: [compute-vm-2-2-20-ssd-1771947628469]

TASK [app_deploy : Stop existing container (if running)] ***************************************************************************************************************************************
changed: [compute-vm-2-2-20-ssd-1771947628469]

TASK [app_deploy : Remove old container (if exists)] *******************************************************************************************************************************************
changed: [compute-vm-2-2-20-ssd-1771947628469]

TASK [app_deploy : Run new container] **********************************************************************************************************************************************************
changed: [compute-vm-2-2-20-ssd-1771947628469]

TASK [app_deploy : Wait for application port to be open] ***************************************************************************************************************************************
ok: [compute-vm-2-2-20-ssd-1771947628469]

TASK [app_deploy : Verify health endpoint] *****************************************************************************************************************************************************
ok: [compute-vm-2-2-20-ssd-1771947628469]

PLAY RECAP *************************************************************************************************************************************************************************************
compute-vm-2-2-20-ssd-1771947628469 : ok=8    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0 
```

```bash
docker up
```

```bash
CONTAINER ID   IMAGE               COMMAND                  CREATED             STATUS             PORTS                    NAMES
19b0242536b3   thevex/simple-app   "python app.py --hos…"   About an hour ago   Up About an hour   0.0.0.0:5000->8000/tcp   simple-app
```

```bash
curl -v http://localhost:5000/health
```

```bash
* Host localhost:5000 was resolved.
* IPv6: ::1
* IPv4: 127.0.0.1
*   Trying [::1]:5000...
* connect to ::1 port 5000 from ::1 port 37834 failed: Connection refused
*   Trying 127.0.0.1:5000...
* Connected to localhost (127.0.0.1) port 5000
> GET /health HTTP/1.1
> Host: localhost:5000
> User-Agent: curl/8.5.0
> Accept: */*
> 
< HTTP/1.1 200 OK
< date: Tue, 24 Feb 2026 20:01:54 GMT
< server: uvicorn
< content-length: 83
< content-type: application/json
< 
* Connection
{"status":"healthy","timestamp":"2026-02-24T20:01:55.724878","uptime_seconds":4467}
```

## Key decisions ##

- Because roles are more reusable, modular, testable, and maintainable.
- Roles can be shared across multiple playbooks or even different projects. Variables allow customization without changing role code.
- A task is idempotent if running it multiple times always results in the same state without unintended side effects.
- Handlers are only triggered when notified by a task that actually made a change. This avoids unnecessary restarts and speeds up playbook runs.
- To securely store sensitive data like passwords, API tokens, and private keys in version control. Without Vault, secrets would be exposed in plain text, creating a severe security risk.
