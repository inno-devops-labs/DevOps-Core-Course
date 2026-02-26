# Lab 5 — Ansible Fundamentals

Date: 2026-02-26

## 1. Architecture Overview

- Ansible version: `ansible [core 2.20.3]` (Ansible package `13.4.0`)
- Control node: macOS (Homebrew Ansible)
- Target VM from Lab 4: Ubuntu 24.04 LTS, IP `31.58.76.235`
- Inventory host: `boba`

Project structure:

```text
ansible/
├── ansible.cfg
├── inventory/hosts.ini
├── group_vars/all.yml
├── playbooks/
│   ├── site.yml
│   ├── provision.yml
│   └── deploy.yml
├── roles/
│   ├── common/
│   │   ├── tasks/main.yml
│   │   └── defaults/main.yml
│   ├── docker/
│   │   ├── tasks/main.yml
│   │   ├── defaults/main.yml
│   │   └── handlers/main.yml
│   └── app_deploy/
│       ├── tasks/main.yml
│       ├── defaults/main.yml
│       └── handlers/main.yml
└── docs/LAB05.md
```

Why roles instead of a single monolithic playbook:
- Roles split responsibility by domain (`common`, `docker`, `app_deploy`) and keep playbooks clean.
- Variables/defaults/handlers are scoped and reusable.
- Testing and troubleshooting are faster because each part is isolated.

---

## 2. Task 1 — Setup and Inventory

### Ansible configuration

`ansible.cfg`:

```ini
[defaults]
inventory = inventory/hosts.ini
roles_path = roles
host_key_checking = False
remote_user = ubuntu
retry_files_enabled = False

[privilege_escalation]
become = True
become_method = sudo
become_user = root
```

`inventory/hosts.ini`:

```ini
[webservers]
boba ansible_host=31.58.76.235 ansible_user=root

[webservers:vars]
ansible_python_interpreter=/usr/bin/python3
```

Note: `ansible_user=root` in inventory overrides `remote_user=ubuntu` from `ansible.cfg`.

---

## 3. Task 2 — Provisioning Roles

### 3.1 Role: `common`

Purpose:
- Base system preparation for every server.

What it does:
- Checks interrupted `dpkg` state and recovers with `dpkg --configure -a` if needed.
- Waits for SSH recovery after package reconfiguration.
- Updates apt cache.
- Installs common packages.
- Sets timezone.

Key variables (`roles/common/defaults/main.yml`):
- `common_packages`: `python3-pip`, `curl`, `git`, `vim`, `htop`
- `common_timezone`: `UTC`

Handlers:
- None.

Dependencies:
- Uses `community.general.timezone` collection.

### 3.2 Role: `docker`

Purpose:
- Install and configure Docker Engine from the official Docker Ubuntu repository.

What it does:
- Installs prerequisites (`ca-certificates`, `curl`).
- Creates `/etc/apt/keyrings`.
- Downloads Docker GPG key to `/etc/apt/keyrings/docker.asc`.
- Removes conflicting legacy Docker repo entries using `docker.gpg` signed-by path.
- Adds official Docker apt repo for current Ubuntu release.
- Installs Docker packages (`docker-ce`, `docker-ce-cli`, `containerd.io`, buildx, compose plugin).
- Installs `python3-docker` for Ansible Docker modules.
- Ensures Docker service is enabled and running.
- Adds selected users to `docker` group.

Key variables (`roles/docker/defaults/main.yml`):
- `docker_gpg_key_url`, `docker_gpg_key_path`
- `docker_packages`, `docker_package_state`, `docker_version_pin`
- `docker_service_name`
- `docker_users` (current value resolves to inventory user)

Handlers:
- `Restart docker` — restarts Docker service when package changes require it.

Dependencies:
- No role dependencies.

### 3.3 Provisioning playbook

`playbooks/provision.yml`:
- Includes pre-tasks to remove conflicting Docker apt source records before provisioning.
- Applies roles in order: `common`, then `docker`.

---

## 4. Idempotency Demonstration

### First `provision.yml` run recap

```text
PLAY RECAP
boba : ok=17 changed=3 unreachable=0 failed=0 skipped=4 rescued=0 ignored=0
```

Changed tasks on first run:
- `docker : Add Docker apt repository`
- `docker : Install Docker SDK for Python`
- `docker : Add users to docker group`

Why these changed:
- Repository was added to reach desired package source state.
- Missing package `python3-docker` was installed.
- User group membership was updated.

### Second `provision.yml` run recap

```text
PLAY RECAP
boba : ok=17 changed=0 unreachable=0 failed=0 skipped=4 rescued=0 ignored=0
```

Why no changes on second run:
- Desired state already matched actual state.
- Stateful modules (`apt`, `apt_repository`, `service`, `user`, `lineinfile`, `file`) are idempotent.

---

## 5. Task 3 — Application Deployment Role

### 5.1 Vault usage

Secrets are stored in `group_vars/all.yml` encrypted with Ansible Vault.

Encrypted file proof:

```text
$ANSIBLE_VAULT;1.1;AES256
```

Vault operations used:
- `ansible-vault edit group_vars/all.yml`
- `ansible-playbook playbooks/deploy.yml --ask-vault-pass`

Password strategy:
- Password is entered interactively (`--ask-vault-pass`).
- Vault password file is not committed.

### 5.2 Role: `app_deploy`

Purpose:
- Securely deploy application container from Docker Hub.

What it does:
- Validates required variables (`dockerhub_username`, `dockerhub_password`, image, tag).
- Logs in to Docker Hub (`no_log: true`).
- Pulls image.
- Stops/removes existing container if present.
- Starts new container with configured ports/env/restart policy.
- Waits for app port readiness.
- Verifies health endpoint with retries.

Key variables (`roles/app_deploy/defaults/main.yml`):
- Registry + credentials variables.
- App identity and image/tag values.
- Runtime options (`app_container_name`, `app_port`, `app_container_port`, `app_restart_policy`, `app_environment`).
- Health-check controls (`app_healthcheck_path`, retries, delay).

Handlers:
- `Restart application container`.

Dependencies:
- Uses `community.docker` modules.

### 5.3 Deployment playbook

`playbooks/deploy.yml`:
- Hosts: `webservers`
- `become: true`
- Loads `../group_vars/all.yml` explicitly (playbook is inside `playbooks/`)
- Applies role `app_deploy`

---

## 6. Deployment Verification

### Deploy run recap

```text
PLAY RECAP
boba : ok=9 changed=3 unreachable=0 failed=0 skipped=2 rescued=0 ignored=0
```

### Container status

```text
ansible webservers -a "docker ps" --ask-vault-pass

CONTAINER ID   IMAGE                    COMMAND         STATUS         PORTS                    NAMES
d4f44d838400   cilc/devops_lab02:cilc   "python app.py"  Up ...      0.0.0.0:5000->8080/tcp   devops_lab02
```

### Health and main endpoint checks

```bash
curl http://31.58.76.235:5000/health
curl http://31.58.76.235:5000/
```

Observed result:
- `/health` returns HTTP 200 and JSON status `healthy`.
- `/` returns service/system/runtime payload from Flask app.

---

## 7. Key Decisions

Why roles instead of plain playbooks:
- Roles enforce a predictable structure and separate concerns by function.
- The top-level playbooks become orchestration-only and easier to review.

How roles improve reusability:
- Each role is parameterized with defaults/vars and can be reused in another environment with different inventory/values.
- Example: `docker` role can be reused independently from `app_deploy`.

What makes a task idempotent:
- A task is idempotent when repeated runs converge to the same state with no extra changes.
- Using desired-state modules (`state: present/started/absent`) is the core pattern.

How handlers improve efficiency:
- Handlers run only when notified by changed tasks.
- This avoids unnecessary service restarts on every run.

Why Ansible Vault is necessary:
- It keeps credentials in Git-safe encrypted form.
- Access to secrets is controlled by vault password, reducing accidental leaks.

---

## 8. Challenges and Fixes

1. Interrupted `dpkg` blocked apt installs.
- Fix: Added recovery block (`dpkg --configure -a`) with SSH reconnection wait in `common` role.

2. Docker apt source conflict (`docker.gpg` vs `docker.asc`).
- Fix: Added cleanup of conflicting repo entries in `provision.yml` pre-tasks and `docker` role.

3. Vault variables not loaded for `deploy.yml`.
- Root cause: playbook location (`playbooks/`) didn’t auto-resolve `group_vars` as expected.
- Fix: added explicit `vars_files: ../group_vars/all.yml`.

4. Docker image pull failures.
- Root causes:
  - Missing `latest` tag.
  - Image manifest initially not matching target VM architecture (`linux/amd64`).
- Fix: use existing valid tag and ensure pushed image supports VM architecture.

5. Runtime port mismatch.
- App listens on container port `8080`.
- Fix: deployment uses mapping `5000:8080`.

---

## 9. Final Status

- Task 1 (setup, structure, inventory): completed.
- Task 2 (provisioning roles + idempotency): completed.
- Task 3 (deployment role + Vault + verification): completed.
- Task 4 documentation: completed in this file.

---

## 10. Terminal Output

### 10.1 Provisioning — First Run

```text
igor@cilc ansible % ansible-playbook playbooks/provision.yml

PLAY [Provision web servers] ******************************************************************

TASK [Gathering Facts] ************************************************************************
ok: [boba]

TASK [Find conflicting Docker apt source files (docker.gpg)] **********************************
ok: [boba]

TASK [Remove conflicting Docker apt source files (docker.gpg)] ********************************
skipping: [boba]

TASK [Remove conflicting Docker apt source lines from sources.list (docker.gpg)] **************
ok: [boba]

TASK [common : Check for interrupted dpkg transactions] ***************************************
ok: [boba]

TASK [common : Recover interrupted dpkg state] ************************************************
skipping: [boba]

TASK [common : Clear host errors after dpkg recovery] *****************************************
skipping: [boba]

TASK [common : Wait for SSH to come back after package reconfiguration] ***********************
skipping: [boba]

TASK [common : Update apt cache] **************************************************************
ok: [boba]

TASK [common : Install common packages] *******************************************************
ok: [boba]

TASK [common : Set timezone] ******************************************************************
ok: [boba]

TASK [docker : Install Docker prerequisite packages] ******************************************
ok: [boba]

TASK [docker : Ensure apt keyrings directory exists] ******************************************
ok: [boba]

TASK [docker : Add Docker official GPG key] ***************************************************
ok: [boba]

TASK [docker : Find conflicting Docker repo files in sources.list.d (docker.gpg)] *************
ok: [boba]

TASK [docker : Remove conflicting Docker repo files in sources.list.d (docker.gpg)] ***********
skipping: [boba]

TASK [docker : Remove conflicting Docker repo lines from main sources.list (docker.gpg)] ******
ok: [boba]

TASK [docker : Add Docker apt repository] *****************************************************
changed: [boba]

TASK [docker : Install Docker packages] *******************************************************
ok: [boba]

TASK [docker : Install Docker SDK for Python] *************************************************
changed: [boba]

TASK [docker : Ensure Docker service is enabled and running] **********************************
ok: [boba]

TASK [docker : Add users to docker group] *****************************************************
changed: [boba] => (item=root)

PLAY RECAP ************************************************************************************
boba                       : ok=17   changed=3    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0
```

### 10.2 Provisioning — Second Run

```text
igor@cilc ansible % ansible-playbook playbooks/provision.yml

PLAY [Provision web servers] ******************************************************************

TASK [Gathering Facts] ************************************************************************
ok: [boba]

TASK [Find conflicting Docker apt source files (docker.gpg)] **********************************
ok: [boba]

TASK [Remove conflicting Docker apt source files (docker.gpg)] ********************************
skipping: [boba]

TASK [Remove conflicting Docker apt source lines from sources.list (docker.gpg)] **************
ok: [boba]

TASK [common : Check for interrupted dpkg transactions] ***************************************
ok: [boba]

TASK [common : Recover interrupted dpkg state] ************************************************
skipping: [boba]

TASK [common : Clear host errors after dpkg recovery] *****************************************
skipping: [boba]

TASK [common : Wait for SSH to come back after package reconfiguration] ***********************
skipping: [boba]

TASK [common : Update apt cache] **************************************************************
ok: [boba]

TASK [common : Install common packages] *******************************************************
ok: [boba]

TASK [common : Set timezone] ******************************************************************
ok: [boba]

TASK [docker : Install Docker prerequisite packages] ******************************************
ok: [boba]

TASK [docker : Ensure apt keyrings directory exists] ******************************************
ok: [boba]

TASK [docker : Add Docker official GPG key] ***************************************************
ok: [boba]

TASK [docker : Find conflicting Docker repo files in sources.list.d (docker.gpg)] *************
ok: [boba]

TASK [docker : Remove conflicting Docker repo files in sources.list.d (docker.gpg)] ***********
skipping: [boba]

TASK [docker : Remove conflicting Docker repo lines from main sources.list (docker.gpg)] ******
ok: [boba]

TASK [docker : Add Docker apt repository] *****************************************************
ok: [boba]

TASK [docker : Install Docker packages] *******************************************************
ok: [boba]

TASK [docker : Install Docker SDK for Python] *************************************************
ok: [boba]

TASK [docker : Ensure Docker service is enabled and running] **********************************
ok: [boba]

TASK [docker : Add users to docker group] *****************************************************
ok: [boba] => (item=root)

PLAY RECAP ************************************************************************************
boba                       : ok=17   changed=0    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0
```

### 10.3 Deploy Run + Verification

```text
igor@cilc ansible % ansible-playbook playbooks/deploy.yml --ask-vault-pass

Vault password:

PLAY [Deploy application] *************************************************************************************

TASK [Gathering Facts] ****************************************************************************************
ok: [boba]

TASK [app_deploy : Validate required deployment variables] ****************************************************
ok: [boba] => {
    "changed": false,
    "msg": "All assertions passed"
}

TASK [app_deploy : Log in to Docker Hub] **********************************************************************
ok: [boba]

TASK [app_deploy : Pull application image] ********************************************************************
changed: [boba]

TASK [app_deploy : Get existing container info] ***************************************************************
ok: [boba]

TASK [app_deploy : Stop existing container if running] ********************************************************
skipping: [boba]

TASK [app_deploy : Remove old container if exists] ************************************************************
skipping: [boba]

TASK [app_deploy : Run application container] *****************************************************************
changed: [boba]

TASK [app_deploy : Wait for application port to be ready] *****************************************************
ok: [boba]

TASK [app_deploy : Verify health endpoint] ********************************************************************
ok: [boba]

RUNNING HANDLER [app_deploy : Restart application container] **************************************************
changed: [boba]

PLAY RECAP ****************************************************************************************************
boba                       : ok=9    changed=3    unreachable=0    failed=0    skipped=2    rescued=0    ignored=0
```

```text
igor@cilc ansible % ansible webservers -a "docker ps" --ask-vault-pass
Vault password:
boba | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                    COMMAND                  CREATED          STATUS          PORTS                  NAMES
d4f44d838400   cilc/devops_lab02:cilc   "python app.py"          54 minutes ago   Up 54 minutes   0.0.0.0:5000->8080/tcp devops_lab02
```

```text
igor@cilc ansible % curl http://31.58.76.235:5000/health
{"status":"healthy","timestamp":"2026-02-26T10:13:56.193654+00:00","uptime_seconds":3357}
igor@cilc ansible % curl http://31.58.76.235:5000
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"212.118.42.178","method":"GET","path":"/","user_agent":"curl/8.4.0"},"runtime":{"current_time":"2026-02-26T10:14:21.655288+00:00","timezone":"UTC","uptime_human":"0 hours, 56 minutes","uptime_seconds":3382},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":2,"hostname":"d4f44d838400","platform":"Linux","platform_version":"#35-Ubuntu SMP PREEMPT_DYNAMIC Mon May 20 15:51:52 UTC 2024","python_version":"3.13.12"}}
```
