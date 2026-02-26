# Lab 05 - Ansible Fundamentals

## Status

- Main lab tasks (1-4): completed
- Bonus task (dynamic inventory): not implemented (optional)

## 1. Architecture Overview

- **Ansible version:** `ansible [core 2.16.3]`
- **Target VM:** Ubuntu `24.04.3 LTS` (from SSH session output)
- **Inventory group:** `webservers` with host `lab05-vm`
- **Execution model:** role-based (`common` -> `docker` -> `app_deploy`) via dedicated playbooks

### Role structure

```text
ansible/
  inventory/hosts.ini
  roles/
    common/{tasks,defaults}/main.yml
    docker/{tasks,handlers,defaults}/main.yml
    app_deploy/{tasks,handlers,defaults}/main.yml
  playbooks/{site,provision,deploy}.yml
  group_vars/all.yml
  ansible.cfg
```

### Why roles instead of monolithic playbooks?

Roles isolate provisioning and deployment concerns, keep variables near their domain, and make each part reusable in future labs (especially Lab 06+). This also improves testability and idempotent behavior analysis per role.

## 2. Roles Documentation

### `common` role

- **Purpose:** baseline host setup (APT cache, common packages, timezone)
- **Variables:**
  - `common_packages`
  - `common_apt_cache_valid_time`
  - `common_configure_timezone`
  - `common_timezone`
- **Handlers:** none
- **Dependencies:** none

### `docker` role

- **Purpose:** install and configure Docker engine on Ubuntu hosts
- **Variables:**
  - `docker_apt_prerequisites`, `docker_keyring_dir`, `docker_keyring_path`
  - `docker_arch_map`, `docker_arch`, `docker_apt_repo`
  - `docker_service_name`, `docker_packages`, `docker_python_packages`, `docker_users`
- **Handlers:** `restart docker` (runs when engine packages change)
- **Dependencies:** depends on base OS readiness (typically after `common` role)

### `app_deploy` role

- **Purpose:** authenticate to Docker Hub, pull app image, run container, verify endpoints
- **Variables:**
  - Registry/auth: `dockerhub_username`, `dockerhub_password`, `docker_registry_url`
  - App/container: `app_name`, `app_image`, `app_container_name`, `app_port`, `app_container_port`, `app_restart_policy`
  - Runtime/verification: `app_environment`, `app_wait_timeout`, `app_wait_delay`, `app_healthcheck_url`, `app_main_url`, `app_force_redeploy`, `app_force_restart`
- **Handlers:** `restart app container` (triggered only when `app_force_restart=true`)
- **Dependencies:** Docker engine must already be installed/running (`docker` role)

## 3. Idempotency Demonstration

### First `provision.yml` run

```bash
(.venv) ~/IU/DevOps/DevOps-Core-Course/ansible [lab05]
19:01 $ ansible-playbook playbooks/provision.yml

PLAY [Provision web servers] **********************************************************************************

TASK [Gathering Facts] ****************************************************************************************
ok: [lab05-vm]

TASK [common : Update apt cache] ******************************************************************************
changed: [lab05-vm]

TASK [common : Install common packages] ***********************************************************************
changed: [lab05-vm]

TASK [common : Read current timezone] *************************************************************************
ok: [lab05-vm]

TASK [common : Set system timezone] ***************************************************************************
changed: [lab05-vm]

TASK [docker : Install Docker apt prerequisites] **************************************************************
ok: [lab05-vm]

TASK [docker : Create Docker apt keyring directory] ***********************************************************
ok: [lab05-vm]

TASK [docker : Add Docker GPG key] ****************************************************************************
changed: [lab05-vm]

TASK [docker : Add Docker apt repository] *********************************************************************
changed: [lab05-vm]

TASK [docker : Refresh apt cache after repository change] *****************************************************
changed: [lab05-vm]

TASK [docker : Install Docker engine packages] ****************************************************************
changed: [lab05-vm]

TASK [docker : Ensure Docker service is enabled and running] **************************************************
ok: [lab05-vm]

TASK [docker : Add users to docker group] *********************************************************************
changed: [lab05-vm] => (item=ubuntu)

TASK [docker : Install python Docker bindings] ****************************************************************
changed: [lab05-vm]

RUNNING HANDLER [docker : Restart docker] *********************************************************************
changed: [lab05-vm]

PLAY RECAP ****************************************************************************************************
lab05-vm                   : ok=15   changed=10   unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Second `provision.yml` run

```bash
(.venv) ~/IU/DevOps/DevOps-Core-Course/ansible [lab05]
19:07 $ ansible-playbook playbooks/provision.yml

PLAY [Provision web servers] **********************************************************************************

TASK [Gathering Facts] ****************************************************************************************
ok: [lab05-vm]

TASK [common : Update apt cache] ******************************************************************************
ok: [lab05-vm]

TASK [common : Install common packages] ***********************************************************************
ok: [lab05-vm]

TASK [common : Read current timezone] *************************************************************************
ok: [lab05-vm]

TASK [common : Set system timezone] ***************************************************************************
skipping: [lab05-vm]

TASK [docker : Install Docker apt prerequisites] **************************************************************
ok: [lab05-vm]

TASK [docker : Create Docker apt keyring directory] ***********************************************************
ok: [lab05-vm]

TASK [docker : Add Docker GPG key] ****************************************************************************
ok: [lab05-vm]

TASK [docker : Add Docker apt repository] *********************************************************************
ok: [lab05-vm]

TASK [docker : Refresh apt cache after repository change] *****************************************************
skipping: [lab05-vm]

TASK [docker : Install Docker engine packages] ****************************************************************
ok: [lab05-vm]

TASK [docker : Ensure Docker service is enabled and running] **************************************************
ok: [lab05-vm]

TASK [docker : Add users to docker group] *********************************************************************
ok: [lab05-vm] => (item=ubuntu)

TASK [docker : Install python Docker bindings] ****************************************************************
ok: [lab05-vm]

PLAY RECAP ****************************************************************************************************
lab05-vm                   : ok=12   changed=0    unreachable=0    failed=0    skipped=2    rescued=0    ignored=0
```

### Idempotency analysis

- First run changed host state (packages, repo, timezone, Docker setup).
- Second run reported `changed=0`, proving roles are idempotent.
- Idempotency is achieved via declarative module states (`state: present`, service enabled/started), conditional tasks, and handler notifications only on real changes.

## 4. Ansible Vault Usage

- Sensitive variables are stored in `ansible/group_vars/all.yml` as an encrypted vault file.
- `ansible.cfg` uses `vault_password_file = .vault_pass`.
- Vault password file is excluded from git (`.vault_pass` remains local only).

### Encrypted file evidence

```text
$ANSIBLE_VAULT;1.1;AES256
35346139383236636531393032333633356464333734623165303462323633393562613934363463
6461616437333834326662633839633063356634623662310a373264653635633238323032346665
...
```

### Why Vault is important

Vault prevents committing plaintext Docker Hub credentials and deployment secrets, while still allowing fully automated playbook runs in CI/local execution with controlled password access.

## 5. Deployment Verification

### `deploy.yml` run output

```bash
(.venv) ~/IU/DevOps/DevOps-Core-Course/ansible [lab05]
19:34 $ ansible-playbook playbooks/deploy.yml

PLAY [Deploy application] *************************************************************************************

TASK [Gathering Facts] ****************************************************************************************
ok: [lab05-vm]

TASK [app_deploy : Validate Docker Hub credentials] ***********************************************************
ok: [lab05-vm] => {
    "changed": false,
    "msg": "All assertions passed"
}

TASK [app_deploy : Log in to Docker Hub] **********************************************************************
ok: [lab05-vm]

TASK [app_deploy : Pull application image] ********************************************************************
ok: [lab05-vm]

TASK [app_deploy : Read current container info] ***************************************************************
ok: [lab05-vm]

TASK [app_deploy : Decide whether container recreation is required] *******************************************
ok: [lab05-vm]

TASK [app_deploy : Stop existing container before recreation] *************************************************
skipping: [lab05-vm]

TASK [app_deploy : Remove existing container before recreation] ***********************************************
skipping: [lab05-vm]

TASK [app_deploy : Ensure application container is running] ***************************************************
ok: [lab05-vm]

TASK [app_deploy : Wait for application port] *****************************************************************
ok: [lab05-vm]

TASK [app_deploy : Verify health endpoint] ********************************************************************
ok: [lab05-vm]

TASK [app_deploy : Verify main endpoint] **********************************************************************
ok: [lab05-vm]

TASK [app_deploy : Trigger app restart handler when explicitly requested] *************************************
skipping: [lab05-vm]

PLAY RECAP ****************************************************************************************************
lab05-vm                   : ok=10   changed=0    unreachable=0    failed=0    skipped=3    rescued=0    ignored=0
```

### Health endpoint verification

```bash
19:35 $ curl http://93.77.191.173:5000/health
{"status":"healthy","timestamp":"2026-02-26T16:36:29.694058+00:00","uptime_seconds":227}
```

### Container status verification

```bash
19:37 $ ssh ubuntu@93.77.191.173
...
ubuntu@fhmf3hj9e8h3s9qsuucs:~$ docker ps -a
CONTAINER ID   IMAGE                         COMMAND           CREATED          STATUS         PORTS                    NAMES
d586ea30b83e   ebortsov/devops-info:latest   "python app.py"   12 minutes ago   Up 5 minutes   0.0.0.0:5000->5000/tcp   devops-info
```

### Handler execution note

- Docker handler executed during provisioning (`RUNNING HANDLER [docker : Restart docker]`).
- App restart handler was intentionally not triggered because `app_force_restart` was not enabled.

## 6. Key Decisions

### Why use roles instead of plain playbooks?

Roles provide clear boundaries (`common`, `docker`, `app_deploy`) and keep tasks, defaults, and handlers together. This makes the automation easier to review and evolve across labs.

### How do roles improve reusability?

Each role can be reused in different playbooks and environments with variable overrides, without copying task blocks. The same `docker` role can provision multiple VMs consistently.

### What makes a task idempotent?

An idempotent task converges to desired state and does not report changes when state is already correct. Using declarative modules and guarded commands (`when`) avoids unnecessary reconfiguration.

### How do handlers improve efficiency?

Handlers run only when notified by changed tasks, so services are restarted only when needed. This reduces disruption and speeds up repeated runs.

### Why is Ansible Vault necessary?

Credentials (Docker Hub username/password) must not be stored in plaintext in Git. Vault encryption keeps secrets safe while preserving automated deployment workflows.

## 7. Challenges

- Initial provisioning changed many tasks because Docker repository and engine were not yet installed.
- Validating idempotency required a second full run and comparison of recap counters.
- Secret handling was solved by vault-encrypting `group_vars/all.yml` and keeping `.vault_pass` out of version control.

## Completion Checklist

- [x] Role-based structure created
- [x] `common`, `docker`, and `app_deploy` roles implemented
- [x] `provision.yml` and `deploy.yml` working
- [x] Idempotency demonstrated with two runs
- [x] Ansible Vault used for credentials
- [x] Deployment verified with `curl` and `docker ps`
- [x] Documentation completed with architecture, role details, analysis, and evidence
