# Lab 05 — Ansible Fundamentals

## 1. Architecture Overview

**Ansible version:**
```bash
ansible [core 2.20.3]
  config file = /Users/marinalavrova/Documents/Projects/study_projects/DevOps-Core-Course/ansible/ansible.cfg
  configured module search path = ['/Users/marinalavrova/.ansible/plugins/modules', '/usr/share/ansible/plugins/modules']
  ansible python module location = /opt/homebrew/Cellar/ansible/13.4.0/libexec/lib/python3.14/site-packages/ansible
  ansible collection location = /Users/marinalavrova/.ansible/collections:/usr/share/ansible/collections
  executable location = /opt/homebrew/bin/ansible
  python version = 3.14.3 (main, Feb  3 2026, 15:32:20) [Clang 16.0.0 (clang-1600.0.26.6)] (/opt/homebrew/Cellar/ansible/13.4.0/libexec/bin/python)
  jinja version = 3.1.6
  pyyaml version = 6.0.3 (with libyaml v0.2.5)
```

**Target VM:** Ubuntu 22.04 LTS (from Lab 4, Yandex Cloud).  
**IP:** 89.169.151.150

**Role structure:**

```
ansible/
├── inventory/hosts.ini       # Static inventory (VM IP, user)
├── roles/
│   ├── common/               # System baseline (apt, packages, timezone)
│   ├── docker/               # Docker CE install + user in docker group
│   └── app_deploy/           # Docker login, pull image, run container, health check
├── playbooks/
│   ├── site.yml              # provision + deploy
│   ├── provision.yml         # common + docker
│   └── deploy.yml            # app_deploy
├── group_vars/all.yml        # Vault-encrypted (credentials, app_name, ports)
├── ansible.cfg
└── requirements.yml         # community.docker collection
```

**Why roles instead of monolithic playbooks?**  
Roles give a clear split of responsibilities (common / docker / app_deploy), can be reused across playbooks and projects, are easy to test and share (e.g. via Galaxy), and keep playbooks short and readable.

---

## 2. Roles Documentation

### common
- **Purpose:** Base system setup: update apt cache, install common packages (curl, git, vim, htop, etc.), set timezone.
- **Variables:** `common_packages` (list), `common_timezone` (e.g. UTC).
- **Handlers:** None.
- **Dependencies:** None.

### docker
- **Purpose:** Install Docker CE (GPG key, repo, packages), start and enable service, add user to `docker` group, install `python3-docker` for Ansible Docker modules.
- **Variables:** `docker_group_user` (default: `ansible_user_id`).
- **Handlers:** `restart docker` — restarts Docker service (notified when repo/key/packages change).
- **Dependencies:** None (common role usually runs first for apt dependencies).

### app_deploy
- **Purpose:** Log in to Docker Hub (Vault credentials), pull image, stop/remove old container, run new container with port mapping and restart policy, wait for port, verify `/health`.
- **Variables (defaults):** `app_port`, `app_restart_policy`, `app_env`, `app_health_path`, `app_wait_timeout`. From Vault: `dockerhub_username`, `dockerhub_password`, `app_name`, `docker_image`, `docker_image_tag`, `app_container_name`.
- **Handlers:** `restart app container` — restarts the app container.
- **Dependencies:** Expects Docker installed (run `provision.yml` first or use `site.yml`).

---

## 3. Idempotency Demonstration

**First run** (many tasks should show "changed"):
```bash
cd ansible/
ansible-galaxy collection install -r requirements.yml
ansible-playbook playbooks/provision.yml
```
Output:
```bash
PLAY [Provision web servers] *********************************************************************************************************

TASK [Gathering Facts] ***************************************************************************************************************
ok: [devops-lab04-vm]

TASK [common : Update apt cache] *****************************************************************************************************
changed: [devops-lab04-vm]

TASK [common : Install common packages] **********************************************************************************************
changed: [devops-lab04-vm]

TASK [common : Get current timezone] *************************************************************************************************
ok: [devops-lab04-vm]

TASK [common : Set timezone] *********************************************************************************************************
changed: [devops-lab04-vm]

TASK [docker : Install dependencies for Docker] **************************************************************************************
ok: [devops-lab04-vm]

TASK [docker : Create directory for Docker key] **************************************************************************************
ok: [devops-lab04-vm]

TASK [docker : Add Docker GPG key] ***************************************************************************************************
changed: [devops-lab04-vm]

TASK [docker : Add Docker repository] ************************************************************************************************
changed: [devops-lab04-vm]

TASK [docker : Install Docker packages] **********************************************************************************************
changed: [devops-lab04-vm]

TASK [docker : Ensure Docker service is started and enabled] *************************************************************************
ok: [devops-lab04-vm]

TASK [docker : Add user to docker group] *********************************************************************************************
changed: [devops-lab04-vm]

TASK [docker : Install python3-docker for Ansible docker modules] ********************************************************************
changed: [devops-lab04-vm]

RUNNING HANDLER [docker : restart docker] ********************************************************************************************
changed: [devops-lab04-vm]

PLAY RECAP ***************************************************************************************************************************
devops-lab04-vm            : ok=14   changed=9    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

**Second run** (tasks should show "ok", no changes):
```bash
ansible-playbook playbooks/provision.yml
```
Output:
```bash
PLAY [Provision web servers] *********************************************************************************************************

TASK [Gathering Facts] ***************************************************************************************************************
ok: [devops-lab04-vm]

TASK [common : Update apt cache] *****************************************************************************************************
ok: [devops-lab04-vm]

TASK [common : Install common packages] **********************************************************************************************
ok: [devops-lab04-vm]

TASK [common : Get current timezone] *************************************************************************************************
ok: [devops-lab04-vm]

TASK [common : Set timezone] *********************************************************************************************************
skipping: [devops-lab04-vm]

TASK [docker : Install dependencies for Docker] **************************************************************************************
ok: [devops-lab04-vm]

TASK [docker : Create directory for Docker key] **************************************************************************************
ok: [devops-lab04-vm]

TASK [docker : Add Docker GPG key] ***************************************************************************************************
ok: [devops-lab04-vm]

TASK [docker : Add Docker repository] ************************************************************************************************
ok: [devops-lab04-vm]

TASK [docker : Install Docker packages] **********************************************************************************************
ok: [devops-lab04-vm]

TASK [docker : Ensure Docker service is started and enabled] *************************************************************************
ok: [devops-lab04-vm]

TASK [docker : Add user to docker group] *********************************************************************************************
ok: [devops-lab04-vm]

TASK [docker : Install python3-docker for Ansible docker modules] ********************************************************************
ok: [devops-lab04-vm]

PLAY RECAP ***************************************************************************************************************************
devops-lab04-vm            : ok=12   changed=0    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0
```

**Analysis:**
- First run: apt cache update, package installs, Docker repo/key/packages, service start, user added to docker group — all show "changed" because the desired state was not yet present.
- Second run: Same tasks report "ok" because current state already matches (packages installed, service running, user in group). Idempotency: re-running does not change anything when the system is already in the desired state.

---

## 4. Ansible Vault Usage

- **Storage:** Credentials and app config are in `group_vars/all.yml`, encrypted with `ansible-vault create` (or `encrypt`). See `group_vars/all.yml.example` for the structure.
- **Password:** Use `--ask-vault-pass` when running playbooks, or a password file (e.g. `.vault_pass`) with `vault_password_file` in `ansible.cfg`. `.vault_pass` is in `.gitignore` and must not be committed.
- **Encrypted file example:** Running `head -5 group_vars/all.yml` shows something like:
  ```
  $ANSIBLE_VAULT;1.1;AES256
  663864396537386534...
  ```
  So the file is stored encrypted in the repo.
- **Why Vault:** Keeps Docker Hub and other secrets in version control without exposing them in plain text; only someone with the vault password can use or view them.

---

## 5. Deployment Verification

**Run deployment:**
```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```
Output (successful deploy):
```bash
PLAY [Deploy application] ************************************************************************************************************

TASK [Gathering Facts] ***************************************************************************************************************
ok: [devops-lab04-vm]

TASK [app_deploy : Log in to Docker Hub] *********************************************************************************************
ok: [devops-lab04-vm]

TASK [app_deploy : Pull Docker image] ************************************************************************************************
changed: [devops-lab04-vm]

TASK [app_deploy : Stop existing container if running] *******************************************************************************
[ERROR]: Task failed: Module failed: Cannot create container when image is not specified!
...ignoring

TASK [app_deploy : Remove old container if exists] ***********************************************************************************
ok: [devops-lab04-vm]

TASK [app_deploy : Run application container] ****************************************************************************************
changed: [devops-lab04-vm]

TASK [app_deploy : Wait for application to be ready] *********************************************************************************
ok: [devops-lab04-vm]

TASK [app_deploy : Verify health endpoint] *******************************************************************************************
ok: [devops-lab04-vm]

TASK [app_deploy : Report deployment success] ****************************************************************************************
ok: [devops-lab04-vm] => {
    "msg": "Application devops-info-service is running and healthy at http://89.169.151.150:5000/health"
}

PLAY RECAP ***************************************************************************************************************************
devops-lab04-vm            : ok=9    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=1
```

**Container status on the VM:**
```bash
ansible webservers -a "docker ps" --ask-vault-pass
```
Output:
```bash
devops-lab04-vm | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                                    COMMAND           CREATED         STATUS         PORTS                    NAMES
3298cf9e24c3   mclavrushka/devops-info-service:latest   "python app.py"   6 minutes ago   Up 6 minutes   0.0.0.0:5000->5000/tcp   devops-info-service
```

Because `group_vars/all.yml` is encrypted with Vault, Ansible prompts for the vault password when running ad-hoc commands. Run the command with `--ask-vault-pass`, or configure `vault_password_file` in `ansible.cfg`.

**Health check from your machine:**
```bash
curl -s http://89.169.151.150:5000/health
curl -s http://89.169.151.150:5000/
```
Output:
```bash
$ curl -s http://89.169.151.150:5000/health
{"status":"healthy","timestamp":"2026-02-26T10:17:18.503308+00:00","uptime_seconds":57}

$ curl -s http://89.169.151.150:5000/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"3298cf9e24c3","platform":"Linux","platform_version":"#180-Ubuntu SMP Fri Jan 9 16:10:31 UTC 2026","architecture":"x86_64","cpu_count":2,"python_version":"3.13.12"},"runtime":{"uptime_seconds":61,"uptime_human":"0 hours, 1 minutes","current_time":"2026-02-26T10:17:22.994802+00:00","timezone":"UTC"},"request":{"client_ip":"188.187.180.34","user_agent":"curl/8.7.1","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}
```

**Handler execution:** Handlers in this lab run when Docker is installed/updated (restart docker) or when a task notifies "restart app container". If you add such a task later, document when the handler ran.

---

## 6. Key Decisions

- **Why roles instead of plain playbooks?** Roles separate concerns (common / docker / app), are reusable and testable, and keep playbooks small and readable.
- **How do roles improve reusability?** The same role can be included in different playbooks or for different groups; variables and defaults allow adaptation without changing the role code.
- **What makes a task idempotent?** Using declarative modules (e.g. `apt` with `state: present`, `service` with `state: started`, `docker_container` with `state: started`) that compare current state to desired state and only change when needed.
- **How do handlers improve efficiency?** They run once at the end of the play for all notifications (e.g. one "restart docker" instead of restarting after every task that notifies it).
- **Why is Ansible Vault necessary?** To store secrets (Docker Hub, API keys) in the repo safely and use them in playbooks without leaving plain-text credentials in history or on disk.

---

## 7. Challenges 

- **Vault password / encryption:** Once the Vault password was entered incorrectly or forgotten, so `ansible-vault edit` and the playbook could not decrypt `group_vars/all.yml`. Fix: remove the file, copy `all.yml.example` again, encrypt with a new password, and store it safely.
- **Vault variables (`dockerhub_password` is undefined):** Ansible did not see the variable until `group_vars/all.yml` was created and encrypted with the correct keys and, in addition, explicitly included via `vars_files` in `deploy.yml`.
- **Wrong Docker image name:** On first deploy, the image `mclavrushka/devops-app:latest` did not exist on Docker Hub (404). Fixed by updating `docker_image`/`app_name` in `group_vars/all.yml` to the actual image from previous labs.