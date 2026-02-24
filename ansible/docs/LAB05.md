# Lab 5 — Ansible Fundamentals

## 1. Architecture Overview

- **Ansible version:** 2.16+
- **Target VM:** Ubuntu 24.04 LTS on Yandex Cloud (Pulumi-created from Lab 4)
- **Connection:** SSH with key-based auth (`ubuntu` user)

### Role Structure

```
ansible/
├── ansible.cfg
├── inventory/hosts.ini
├── roles/
│   ├── common/        # System packages and timezone
│   ├── docker/        # Docker CE installation
│   └── app_deploy/    # App container deployment
├── playbooks/
│   ├── site.yml       # Full provisioning + deploy
│   ├── provision.yml  # System setup only
│   └── deploy.yml     # App deployment only
├── group_vars/
│   └── all.yml        # Encrypted with Ansible Vault
└── docs/
    └── LAB05.md
```

**Why roles instead of monolithic playbooks?** Roles separate concerns into reusable units. Each role handles one responsibility (system setup, Docker, app), making code easier to maintain, test, and reuse across projects.

## 2. Roles Documentation

### common

- **Purpose:** Update apt cache, install essential system packages, set timezone.
- **Variables:** `common_packages` (list of apt packages), `timezone` (default: UTC).
- **Handlers:** None.
- **Dependencies:** None.

### docker

- **Purpose:** Install Docker CE from official repo, enable service, add user to docker group.
- **Variables:** `docker_user` (user for docker group), `docker_packages` (Docker apt packages).
- **Handlers:** `restart docker` — triggered when Docker packages are installed/updated.
- **Dependencies:** Relies on `common` role for prerequisites (ca-certificates, curl, gnupg).

### app_deploy

- **Purpose:** Log in to Docker Hub, pull app image, run container with health verification.
- **Variables:** `app_port`, `app_restart_policy`, `app_env` (defaults). Vault vars: `dockerhub_username`, `dockerhub_password`, `docker_image`, `docker_image_tag`, `app_container_name`.
- **Handlers:** `restart app container` — restarts the application container.
- **Dependencies:** Requires `docker` role (Docker must be installed).

## 3. Idempotency Demonstration

### First Run

```
PLAY [Provision web servers] **************************************************************************************************************************************************************************************************

TASK [Gathering Facts] ********************************************************************************************************************************************************************************************************
[WARNING]: Host 'lab4-vm' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.20/reference_appendices/interpreter_discovery.html for more information.
ok: [lab4-vm]

TASK [common : Update apt cache] **********************************************************************************************************************************************************************************************
changed: [lab4-vm]

TASK [common : Install common packages] ***************************************************************************************************************************************************************************************
changed: [lab4-vm]

TASK [common : Set timezone] **************************************************************************************************************************************************************************************************
changed: [lab4-vm]

TASK [docker : Install prerequisites for Docker repository] *******************************************************************************************************************************************************************
ok: [lab4-vm]

TASK [docker : Create keyrings directory] *************************************************************************************************************************************************************************************
ok: [lab4-vm]

TASK [docker : Add Docker GPG key] ********************************************************************************************************************************************************************************************
changed: [lab4-vm]

TASK [docker : Add Docker repository] *****************************************************************************************************************************************************************************************
[WARNING]: Deprecation warnings can be disabled by setting `deprecation_warnings=False` in ansible.cfg.
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /Users/karinasiniatullina/innopolis/3 курс/2sem/devops/DevOps-Core-Course/ansible/roles/docker/tasks/main.yml:24:11

22 - name: Add Docker repository
23   apt_repository:
24     repo: "deb [arch={{ ansible_architecture | replace('x86_64', 'amd64') }} signed-by=/etc/apt/keyrings/docker.as...
             ^ column 11

Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.

changed: [lab4-vm]

TASK [docker : Install Docker packages] ***************************************************************************************************************************************************************************************
changed: [lab4-vm]

TASK [docker : Ensure Docker service is running and enabled] ******************************************************************************************************************************************************************
ok: [lab4-vm]

TASK [docker : Add user to docker group] **************************************************************************************************************************************************************************************
changed: [lab4-vm]

TASK [docker : Install python3-docker for Ansible docker modules] *************************************************************************************************************************************************************
changed: [lab4-vm]

RUNNING HANDLER [docker : restart docker] *************************************************************************************************************************************************************************************
changed: [lab4-vm]

PLAY RECAP ********************************************************************************************************************************************************************************************************************
lab4-vm                    : ok=13   changed=9    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0 
```

Many tasks show **changed** (yellow) — packages installed, Docker added, etc.

### Second Run

```
PLAY [Provision web servers] **************************************************************************************************************************************************************************************************

TASK [Gathering Facts] ********************************************************************************************************************************************************************************************************
[WARNING]: Host 'lab4-vm' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.20/reference_appendices/interpreter_discovery.html for more information.
ok: [lab4-vm]

TASK [common : Update apt cache] **********************************************************************************************************************************************************************************************
ok: [lab4-vm]

TASK [common : Install common packages] ***************************************************************************************************************************************************************************************
ok: [lab4-vm]

TASK [common : Set timezone] **************************************************************************************************************************************************************************************************
ok: [lab4-vm]

TASK [docker : Install prerequisites for Docker repository] *******************************************************************************************************************************************************************
ok: [lab4-vm]

TASK [docker : Create keyrings directory] *************************************************************************************************************************************************************************************
ok: [lab4-vm]

TASK [docker : Add Docker GPG key] ********************************************************************************************************************************************************************************************
ok: [lab4-vm]

TASK [docker : Add Docker repository] *****************************************************************************************************************************************************************************************
ok: [lab4-vm]

TASK [docker : Install Docker packages] ***************************************************************************************************************************************************************************************
ok: [lab4-vm]

TASK [docker : Ensure Docker service is running and enabled] ******************************************************************************************************************************************************************
ok: [lab4-vm]

TASK [docker : Add user to docker group] **************************************************************************************************************************************************************************************
ok: [lab4-vm]

TASK [docker : Install python3-docker for Ansible docker modules] *************************************************************************************************************************************************************
ok: [lab4-vm]

PLAY RECAP ********************************************************************************************************************************************************************************************************************
lab4-vm                    : ok=12   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

All tasks show **ok** (green), zero **changed** — desired state already achieved.

### Analysis

First run installs packages and configures Docker — these are real changes. Second run finds everything already in place: apt cache is fresh, packages present, Docker running, user in group. No changes needed = idempotent.

**What makes roles idempotent:** Using `state: present` (not shell commands), `cache_valid_time` to skip redundant updates, and `state: started` + `enabled: yes` for services.

## 4. Ansible Vault Usage

Credentials are stored in `group_vars/all.yml`, encrypted with Ansible Vault.

### How credentials are stored

```bash
ansible-vault create group_vars/all.yml   # create encrypted file
ansible-vault edit group_vars/all.yml     # edit when needed
ansible-vault view group_vars/all.yml     # view contents
```

### Vault password management

Password stored in `.vault_pass` file (added to `.gitignore`). Referenced in `ansible.cfg` via `vault_password_file = .vault_pass`.

### Encrypted file contents (proof of encryption)

```
$ANSIBLE_VAULT;1.1;AES256
30393432633237303934313263383265356264383239396134376464306232336665623934343533
3062306666346630636233303664363637373563316231370a636235326263616638393166336133
63306436333363343266643666653534643666343337333735383938643132303764636663626133
6464653336656233650a353363616161396232623035343535363364396332316134373961616438
64323639376336666162613038633463383132393038303639616537313038383937343036373362
66656437393364353138646334353262396166346461386632356636326533323061393738323465
32306237633236636461646566313866373835323064313635346565396462303339366564383835
34356135333562303539386631303733653739646336656462626434616366306434363136396366
61353161326361313562373437353634393532313766663239613164303931343066353366623431
34343338356465333561373430363166343365373339646636343965313838636263663263633431
35353430353232343135666637326361616266333838366434613332346632323230613432633461
64343264396461643830303762343339346239396433333932623264643062326165383534313938
32323561616336653936656137333835656430323437353964343838306230393362616130373061
66353064383462643066386430313563303932663833356436623162356537326534656631663133
31303935373961656335383561346132393734353463386165323462363236366233666230376265
33386339316639376639363338326561343631646436333761666166656462376232333736386434
3066
```

### Why Vault is important

Secrets (Docker Hub token, passwords) must never be in plaintext in git. Vault encrypts them with AES256, so the file is safe to commit while remaining usable by Ansible at runtime.

## 5. Deployment Verification

### Deployment output

```
PLAY [Deploy application] *****************************************************************************************************************************************************************************************************

TASK [Gathering Facts] ********************************************************************************************************************************************************************************************************
[WARNING]: Host 'lab4-vm' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.20/reference_appendices/interpreter_discovery.html for more information.
ok: [lab4-vm]

TASK [app_deploy : Log in to Docker Hub] **************************************************************************************************************************************************************************************
ok: [lab4-vm]

TASK [app_deploy : Pull Docker image] *****************************************************************************************************************************************************************************************
ok: [lab4-vm]

TASK [app_deploy : Remove old container (stops and removes)] ******************************************************************************************************************************************************************
changed: [lab4-vm]

TASK [app_deploy : Run application container] *********************************************************************************************************************************************************************************
changed: [lab4-vm]

TASK [app_deploy : Wait for application to start] *****************************************************************************************************************************************************************************
ok: [lab4-vm]

TASK [app_deploy : Verify health endpoint] ************************************************************************************************************************************************************************************
ok: [lab4-vm]

TASK [app_deploy : Display health check result] *******************************************************************************************************************************************************************************
ok: [lab4-vm] => {
    "health_result.json": {
        "status": "healthy",
        "timestamp": "2026-02-23T14:29:37.749967+00:00",
        "uptime_seconds": 12
    }
}

PLAY RECAP ********************************************************************************************************************************************************************************************************************
lab4-vm                    : ok=8    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0 
```

### Container status

```
[WARNING]: Host 'lab4-vm' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.20/reference_appendices/interpreter_discovery.html for more information.
lab4-vm | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                                   COMMAND           CREATED          STATUS                    PORTS                    NAMES
816f4c38415c   karishka1222/devops-python-app:latest   "python app.py"   10 minutes ago   Up 10 minutes (healthy)   0.0.0.0:5000->5000/tcp   devops-python-app
```

### Health check

```
{"status":"healthy","timestamp":"2026-02-23T14:40:04.087099+00:00","uptime_seconds":638}

{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"45.89.244.78","method":"GET","path":"/","user_agent":"curl/8.7.1"},"runtime":{"current_time":"2026-02-23T14:40:09.457006+00:00","timezone":"UTC","uptime_human":"10 minutes","uptime_seconds":643},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":2,"hostname":"816f4c38415c","platform":"Linux","platform_version":"#100-Ubuntu SMP PREEMPT_DYNAMIC Tue Jan 13 16:40:06 UTC 2026","python_version":"3.13.12"}}
```

## 6. Key Decisions

**Why use roles instead of plain playbooks?** Roles enforce separation of concerns and standard directory layout. They are reusable across environments and projects, and each role can be developed and tested independently.

**How do roles improve reusability?** A role like `docker` can be used in any project that needs Docker — just include it in the playbook. Variables and defaults make it configurable without code changes.

**What makes a task idempotent?** Using declarative modules (`apt`, `service`, `user`) with desired-state parameters (`state: present`, `state: started`). Ansible checks current state before acting, only making changes when needed.

**How do handlers improve efficiency?** Handlers run only when notified (e.g., restart Docker only if packages changed). This avoids unnecessary service restarts on every playbook run.

**Why is Ansible Vault necessary?** It encrypts sensitive data (passwords, tokens) so they can live in version control without exposing secrets. Without Vault, credentials would be plaintext in the repo.

## 7. Challenges

- Docker GPG key method changed — `apt_key` is deprecated, using `get_url` to `/etc/apt/keyrings/` instead.
- Need `python3-docker` on the target for Ansible docker modules to work.
