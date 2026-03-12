# LAB05 Report - Ansible Fundamentals

## 1. Architecture Overview

- Ansible version: `ansible-core 2.16.3`
- Target host mode: Local VM Alternative (WSL2 Ubuntu host)
- Target connection: SSH to `127.0.0.1` with inventory group `webservers`
- Role-based layout:
  - `roles/common`: baseline OS packages
  - `roles/docker`: Docker engine and runtime prerequisites
  - `roles/app_deploy`: containerized app deployment and health check

Why roles instead of one large playbook:
- Roles separate concerns and make task sets reusable.
- Defaults/tasks/handlers are easier to test and evolve independently.
- The playbooks stay short and orchestration-focused.

## 2. Roles Documentation

### common role

- Purpose:
  - Updates apt cache.
  - Installs common packages (`python3-pip`, `curl`, `git`, `vim`, `htop`).
- Variables:
  - `common_packages` in `roles/common/defaults/main.yml`.
- Handlers:
  - None.
- Dependencies:
  - None.

### docker role

- Purpose:
  - Adds Docker apt key/repository.
  - Installs Docker engine packages.
  - Enables and starts Docker service.
  - Adds selected user to `docker` group.
  - Installs `python3-docker`.
- Variables:
  - `docker_user`
  - `docker_packages`
- Handlers:
  - `restart docker`
- Dependencies:
  - None (but commonly run after `common` role).

### app_deploy role

- Purpose:
  - Validates required deployment credentials.
  - Logs in to Docker Hub.
  - Pulls application image.
  - Recreates container with required port mapping and restart policy.
  - Waits for service readiness and checks `/health`.
- Variables:
  - `dockerhub_username` (vaulted)
  - `dockerhub_password` (vaulted)
  - `app_name`
  - `docker_image`
  - `docker_image_tag`
  - `app_port`
  - `app_container_name`
  - `app_restart_policy`
  - `app_env`
  - `app_healthcheck_url`
- Handlers:
  - `restart app container`
- Dependencies:
  - Requires Docker to be installed/running.

## 3. Idempotency Demonstration

### First run: provision

Command:

```bash
cd ansible
export ANSIBLE_CONFIG=$PWD/ansible.cfg
ansible-playbook playbooks/provision.yml -K
```

Output (paste your terminal output):

```

PLAY [Provision web servers] *****************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************
ok: [wsl]

TASK [common : Update apt cache] *************************************************************************************************************
ok: [wsl]

TASK [common : Install common packages] ******************************************************************************************************
ok: [wsl]

TASK [docker : Install Docker apt prerequisites] *********************************************************************************************
ok: [wsl]

TASK [docker : Ensure apt keyrings directory exists] *****************************************************************************************
ok: [wsl]

TASK [docker : Add Docker GPG key] ***********************************************************************************************************
ok: [wsl]

TASK [docker : Add Docker repository] ********************************************************************************************************
ok: [wsl]

TASK [docker : Install Docker packages] ******************************************************************************************************
ok: [wsl]

TASK [docker : Ensure Docker service is enabled and running] *********************************************************************************
ok: [wsl]

TASK [docker : Add user to docker group] *****************************************************************************************************
ok: [wsl]

TASK [docker : Install python Docker bindings] ***********************************************************************************************
ok: [wsl]

PLAY RECAP ***********************************************************************************************************************************
wsl                        : ok=11   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

```

### Second run: provision

Command:

```bash
ansible-playbook playbooks/provision.yml -K
```

Output (paste your terminal output):

```PLAY [Provision web servers] *****************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************
ok: [wsl]

TASK [common : Update apt cache] *************************************************************************************************************
ok: [wsl]

TASK [common : Install common packages] ******************************************************************************************************
ok: [wsl]

TASK [docker : Install Docker apt prerequisites] *********************************************************************************************
ok: [wsl]

TASK [docker : Ensure apt keyrings directory exists] *****************************************************************************************
ok: [wsl]

TASK [docker : Add Docker GPG key] ***********************************************************************************************************
ok: [wsl]

TASK [docker : Add Docker repository] ********************************************************************************************************
ok: [wsl]

TASK [docker : Install Docker packages] ******************************************************************************************************
ok: [wsl]

TASK [docker : Ensure Docker service is enabled and running] *********************************************************************************
ok: [wsl]

TASK [docker : Add user to docker group] *****************************************************************************************************
ok: [wsl]

TASK [docker : Install python Docker bindings] ***********************************************************************************************
ok: [wsl]

PLAY RECAP ***********************************************************************************************************************************
wsl                        : ok=11   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

```

Analysis:
- First run should show multiple `changed` tasks while converging the system.
- Second run should show mostly/all `ok` and ideally `changed=0`.
- This demonstrates idempotency: same desired state, no repeated unnecessary changes.

## 4. Ansible Vault Usage

- Sensitive credentials are stored in `ansible/group_vars/all.yml` and encrypted with Ansible Vault.
- Vault password file strategy for local lab:
  - Use local `.vault_pass` file.
  - Keep it out of Git via `.gitignore`.
- Why Vault is important:
  - Prevents plain-text credential leaks in repository history.
  - Allows safe sharing of infrastructure code without exposing secrets.

Encrypted file evidence:

```bash
head -n 5 ansible/group_vars/all.yml
```

Expected prefix:

```text
$ANSIBLE_VAULT;1.1;AES256
...
```

## 5. Deployment Verification

Run deployment:

```bash
cd ansible
export ANSIBLE_CONFIG=$PWD/ansible.cfg
ansible-playbook playbooks/deploy.yml -K --vault-password-file ../.vault_pass
```

Verify container and health:

```bash
ansible webservers -a "docker ps" -K
curl http://127.0.0.1:5000/health
curl http://127.0.0.1:5000/
```

Deployment output:

```BECOME password: 

PLAY [Deploy application] ********************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************
ok: [wsl]

TASK [app_deploy : Validate required deployment variables] ***********************************************************************************
ok: [wsl] => {
    "changed": false,
    "msg": "All assertions passed"
}

TASK [app_deploy : Log in to Docker Hub] *****************************************************************************************************
ok: [wsl]

TASK [app_deploy : Pull application image] ***************************************************************************************************
ok: [wsl]

TASK [app_deploy : Remove old application container if present] ******************************************************************************
changed: [wsl]

TASK [app_deploy : Run application container] ************************************************************************************************
changed: [wsl]

TASK [app_deploy : Wait for application port] ************************************************************************************************
ok: [wsl]

TASK [app_deploy : Verify health endpoint] ***************************************************************************************************
ok: [wsl]

PLAY RECAP ***********************************************************************************************************************************
wsl                        : ok=8    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

BECOME password: 
wsl | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                     COMMAND           CREATED         STATUS         PORTS                    NAMES
5cebf003dc03   nonamecorn/myapp:latest   "python app.py"   7 seconds ago   Up 7 seconds   0.0.0.0:5000->5000/tcp   myapp
```

Container status output:

```
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"172.17.0.1","method":"GET","path":"/","user_agent":"curl/8.5.0"},"runtime":{"current_time":"2026-03-05T15:02:11.615472.000Z","human":"0 hours, 3 minutes","seconds":202,"timezone":"UTC"},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","hostname":"5cebf003dc03","platform":"Linux","python_version":"3.14.3"}}
```

Health endpoint output:

```
{"status":"healthy","timestamp":"2026-03-05T14:58:55.407763+00:00","uptime_seconds":6}
```

## 6. Key Decisions

Why use roles instead of plain playbooks:
- Roles isolate concerns and keep orchestration readable.
- They support reuse across environments and future labs.

How roles improve reusability:
- Variables/defaults make behavior configurable without rewriting tasks.
- Roles can be shared or composed in multiple playbooks.

What makes a task idempotent:
- Module-driven desired state (`state: present`, `state: started`) avoids repeated changes.
- Re-running converges to the same result.

How handlers improve efficiency:
- Handlers run only when notified by a changed task.
- Services restart only when needed, reducing unnecessary disruptions.

Why Ansible Vault is necessary:
- Credentials must not be committed in plain text.
- Vault keeps secrets encrypted while still usable in automation.

## 7. Challenges

- Running from `/mnt/c/...` causes Ansible to ignore local `ansible.cfg` unless `ANSIBLE_CONFIG` is explicitly set.
- SSH key setup was required for local `andre@127.0.0.1` login.
- Global `become=True` requires sudo password (`-K`) unless passwordless sudo is configured.
