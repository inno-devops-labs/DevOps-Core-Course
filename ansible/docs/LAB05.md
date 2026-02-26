# Lab 05 - Ansible Fundamentals (Local VM)

## 1. Architecture Overview

- Ansible version: `ansible [core 2.19.7]` (`ansible` package `12.3.0`)
- Target VM: local QEMU VM from Lab 4
- Target OS: `Ubuntu 24.04.4 LTS` (`aarch64`)
- Runtime on VM after provisioning:
  - `Python 3.12.3`
  - `Docker version 29.2.1`

Project structure:

```text
ansible/
├── ansible.cfg
├── inventory/hosts.ini
├── group_vars/all.yml
├── requirements.yml
├── playbooks/
│   ├── site.yml
│   ├── provision.yml
│   └── deploy.yml
├── roles/
│   ├── common/
│   │   ├── defaults/main.yml
│   │   └── tasks/main.yml
│   ├── docker/
│   │   ├── defaults/main.yml
│   │   ├── handlers/main.yml
│   │   └── tasks/main.yml
│   └── app_deploy/
│       ├── defaults/main.yml
│       ├── handlers/main.yml
│       └── tasks/main.yml
└── docs/LAB05.md
```

I used roles instead of one big playbook because each concern stays isolated: base OS setup, Docker runtime, and application release. That made idempotency easier to reason about and reduced risk while iterating on one part.

## 2. Roles Documentation

### `common` role

- Purpose: base Ubuntu preparation for automation and day-to-day operations.
- Variables:
  - `common_apt_cache_valid_time` (default `3600`)
  - `common_packages` (python3-pip, curl, git, vim, htop, ca-certificates, gnupg, lsb-release)
  - `common_configure_timezone` (default `true`)
  - `common_timezone` (default `UTC`)
- Handlers: none.
- Dependencies: none.

### `docker` role

- Purpose: install Docker from the official Docker APT repository and prepare non-root usage.
- Variables:
  - `docker_apt_arch`
  - `docker_apt_repo`
  - `docker_packages`
  - `docker_manage_user`
- Handlers:
  - `Restart docker`
- Dependencies:
  - assumes base packages are available (handled by `common` in `provision.yml` ordering).

### `app_deploy` role

- Purpose: pull and run the containerized app, wait for readiness, then verify health endpoint.
- Variables:
  - `dockerhub_username`
  - `dockerhub_login_enabled`
  - `docker_image_repository`
  - `docker_image_tag`
  - `docker_image`
  - `app_port`
  - `app_container_name`
  - `app_restart_policy`
  - `app_environment`
  - `app_wait_delay`
  - `app_wait_timeout`
  - `app_healthcheck_url`
  - `app_healthcheck_status_code`
- Handlers:
  - `Restart application container`
- Dependencies:
  - Docker engine and python Docker bindings from `docker` role.

## 3. Idempotency Demonstration

First run (`provision.yml`):

```bash
$ ansible-playbook playbooks/provision.yml --vault-password-file .vault_pass

PLAY [Provision web servers] *****************************************************************************

TASK [Gathering Facts] ***********************************************************************************
ok: [lab4-qemu-vm]

TASK [common : Update apt cache] *************************************************************************
ok: [lab4-qemu-vm]

TASK [common : Install common packages] ******************************************************************
changed: [lab4-qemu-vm]

TASK [common : Configure timezone] ***********************************************************************
changed: [lab4-qemu-vm]

TASK [docker : Install apt dependencies for Docker repository] *******************************************
ok: [lab4-qemu-vm]

TASK [docker : Ensure apt keyrings directory exists] *****************************************************
ok: [lab4-qemu-vm]

TASK [docker : Add Docker GPG key] ***********************************************************************
changed: [lab4-qemu-vm]

TASK [docker : Add Docker repository] ********************************************************************
changed: [lab4-qemu-vm]

TASK [docker : Install Docker packages] ******************************************************************
changed: [lab4-qemu-vm]

TASK [docker : Ensure Docker service is enabled and running] *********************************************
ok: [lab4-qemu-vm]

TASK [docker : Add deployment user to docker group] ******************************************************
changed: [lab4-qemu-vm]

RUNNING HANDLER [docker : Restart docker] ****************************************************************
changed: [lab4-qemu-vm]

PLAY RECAP ***********************************************************************************************
lab4-qemu-vm               : ok=12   changed=7    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

Changed tasks on first run:
- `common : Install common packages`
- `common : Configure timezone`
- `docker : Add Docker GPG key`
- `docker : Add Docker repository`
- `docker : Install Docker packages`
- `docker : Add deployment user to docker group`
- handler `docker : Restart docker`

Second run (`provision.yml` again):

```bash
$ ansible-playbook playbooks/provision.yml --vault-password-file .vault_pass

PLAY [Provision web servers] *****************************************************************************

TASK [Gathering Facts] ***********************************************************************************
ok: [lab4-qemu-vm]

TASK [common : Update apt cache] *************************************************************************
ok: [lab4-qemu-vm]

TASK [common : Install common packages] ******************************************************************
ok: [lab4-qemu-vm]

TASK [common : Configure timezone] ***********************************************************************
ok: [lab4-qemu-vm]

TASK [docker : Install apt dependencies for Docker repository] *******************************************
ok: [lab4-qemu-vm]

TASK [docker : Ensure apt keyrings directory exists] *****************************************************
ok: [lab4-qemu-vm]

TASK [docker : Add Docker GPG key] ***********************************************************************
ok: [lab4-qemu-vm]

TASK [docker : Add Docker repository] ********************************************************************
ok: [lab4-qemu-vm]

TASK [docker : Install Docker packages] ******************************************************************
ok: [lab4-qemu-vm]

TASK [docker : Ensure Docker service is enabled and running] *********************************************
ok: [lab4-qemu-vm]

TASK [docker : Add deployment user to docker group] ******************************************************
ok: [lab4-qemu-vm]

PLAY RECAP ***********************************************************************************************
lab4-qemu-vm               : ok=11   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

Analysis: first run converged the VM to the desired state, so second run only verified it. Tasks are idempotent because they use state-driven modules (`apt`, `service`, `user`, `file`, `apt_repository`) instead of imperative shell commands.

## 4. Ansible Vault Usage

Sensitive variables are stored in `ansible/group_vars/all.yml` as an encrypted Vault file. I kept password material outside git using `ansible/.vault_pass` (ignored by `.gitignore`) for local execution.

Encrypted file example:

```text
$ANSIBLE_VAULT;1.1;AES256
35633766353661333363656132336632343263663631373031323332383837313731363931613238
3561356462383561393137373761373438306431353832390a646636613664346165363031386465
...
```

Why Vault matters: without encryption, registry passwords and tokens are exposed in repository history. Vault keeps infrastructure code shareable while separating secrets from source control.

## 5. Deployment Verification

Deploy run (`deploy.yml`):

```bash
$ ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass

PLAY [Deploy application] ********************************************************************************

TASK [Gathering Facts] ***********************************************************************************
ok: [lab4-qemu-vm]

TASK [app_deploy : Validate Docker Hub credentials are provided] *****************************************
skipping: [lab4-qemu-vm]

TASK [app_deploy : Login to Docker Hub] ******************************************************************
skipping: [lab4-qemu-vm]

TASK [app_deploy : Pull application image] ***************************************************************
ok: [lab4-qemu-vm]

TASK [app_deploy : Get current container state] **********************************************************
ok: [lab4-qemu-vm]

TASK [app_deploy : Stop existing application container] **************************************************
skipping: [lab4-qemu-vm]

TASK [app_deploy : Remove existing application container] ************************************************
skipping: [lab4-qemu-vm]

TASK [app_deploy : Run application container] ************************************************************
ok: [lab4-qemu-vm]

TASK [app_deploy : Wait for application port] ************************************************************
ok: [lab4-qemu-vm]

TASK [app_deploy : Verify health endpoint] ***************************************************************
ok: [lab4-qemu-vm]

PLAY RECAP ***********************************************************************************************
lab4-qemu-vm               : ok=6    changed=0    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0
```

Container status:

```bash
$ ansible webservers -m shell -a "docker ps" --vault-password-file .vault_pass
CONTAINER ID   IMAGE                                          COMMAND           CREATED          STATUS          PORTS                    NAMES
8f85ba402d69   hikariatama/devops-info-service-python:lab02   "python app.py"   10 minutes ago   Up 10 minutes   0.0.0.0:5000->5000/tcp   devops-info-service
```

Health check:

```bash
$ curl http://127.0.0.1:5000/health
{"status":"healthy","timestamp":"2026-02-26T19:12:42.481510+00:00","uptime_seconds":632}
```

Main endpoint:

```bash
$ curl http://127.0.0.1:5000/
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"10.0.2.2","method":"GET","path":"/","user_agent":"curl/8.7.1"},"runtime":{"current_time":"2026-02-26T19:12:34.141298+00:00","timezone":"UTC","uptime_human":"0 hours, 10 minutes","uptime_seconds":623},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"aarch64","cpu_count":2,"hostname":"8f85ba402d69","platform":"Linux","platform_version":"#100-Ubuntu SMP PREEMPT_DYNAMIC Tue Jan 13 16:39:21 UTC 2026","python_version":"3.13.11"}}
```

Handler execution:
- Docker handler executed during first provisioning run.
- App handler is defined and ready for restart flows, but was not needed in this initial deployment path.

## 6. Key Decisions

Why use roles instead of plain playbooks?
Roles keep concerns separated and reusable. In practice, this made troubleshooting faster because each role had a small and clear responsibility.

How do roles improve reusability?
A role can be dropped into another inventory with minimal changes, mostly variable overrides. This avoids copying large playbooks and reduces drift between environments.

What makes a task idempotent?
A task is idempotent when re-running it does not create extra side effects after state is already correct. Using module parameters like `state: present`, `state: started`, and declarative repository definitions gives this behavior.

How do handlers improve efficiency?
Handlers run only when notified by changed tasks, so services are not restarted on every playbook run. That keeps runs faster and avoids unnecessary downtime.

Why is Ansible Vault necessary?
Infrastructure repositories are often shared with teammates and CI systems. Vault allows committing encrypted variables safely while preserving normal Ansible workflows.

## 7. Challenges

- `latest` image tag was not present in Docker Hub for this repository, so I switched to the available published tag `lab02`.
- Ansible 2.19 enforces strict boolean conditionals, so I updated `when` clauses to explicit `| bool`.
- To keep local execution smooth with a public image, login is configurable through `dockerhub_login_enabled`.
