# LAB06 — Advanced Ansible & CI/CD

> **Tech stack:** Ansible, Ansible Vault, Docker, Docker Compose (v2), GitHub Actions  
> **Goal:** Refactor roles using **blocks + tags**, migrate deployment to **Docker Compose**, add **role dependencies**, implement **wipe logic**, and automate deployment with **CI/CD**.

---

## 1). Overview

In this lab I improved my Ansible project with advanced practices:

- Refactored `common` and `docker` roles using **block / rescue / always**.
- Implemented a consistent **tag strategy** to run or skip specific parts of playbooks.
- Migrated deployment from `docker_container` (“docker run”-style) to **Docker Compose** using a Jinja2 template.
- Added **role dependency** so `web_app` automatically runs `docker` first.
- Implemented **wipe logic** (safe cleanup) controlled by **both** a variable and a tag.
- Added **GitHub Actions** workflow for linting + automated deployment.

Repository structure (key parts):

```text
ansible/
├── inventory/
│   ├── group_vars/
│   └── hosts.ini
├── playbooks/
│   ├── provision.yml
│   ├── deploy.yml
│   └── site.yml
└── roles/
    ├── common/
    ├── docker/
    └── web_app/
```

## 2). Blocks & Tags

### 2.1 Tag Strategy

| Tag              | Scope                | Purpose                                  |
| ---------------- | -------------------- | ---------------------------------------- |
| `common`         | role-level           | Run/skip entire `common` role            |
| `packages`       | block-level          | Install OS packages                      |
| `users`          | block-level          | User management                          |
| `docker`         | role-level           | Run/skip entire `docker` role            |
| `docker_install` | block-level          | Install Docker + Compose                 |
| `docker_config`  | block-level          | Docker post-install config               |
| `web_app`        | role-level           | Run/skip entire `web_app` role           |
| `app_deploy`     | block-level          | Application deployment tasks             |
| `compose`        | block-level          | Docker Compose template + up             |
| `web_app_wipe`   | tasks include + wipe | Wipe tasks (only with variable gate too) |

### 2.2 `common` role refactor

**Where:** `roles/common/tasks/main.yml`

Implementation highlights:

- Packages are grouped inside a block tagged `packages`.

    ```bash
    zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible-playbook playbooks/provision.yml --tags packages

    PLAY [Provision web servers] ***************************************************************************

    TASK [Gathering Facts] *********************************************************************************
    ok: [vm1]

    TASK [common : Common | Update apt cache] **************************************************************
    ok: [vm1]

    TASK [common : Common | Install common packages] *******************************************************
    ok: [vm1]

    TASK [common : Mark common packages done] **************************************************************
    ok: [vm1]

    PLAY RECAP *********************************************************************************************
    vm1                        : ok=4    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
    ```

    ![tags packages](/ansible/docs/screenshots/tags_packages.png)

- User management tasks are grouped inside a block tagged `users`.

    ```bash
    zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible-playbook playbooks/provision.yml --tags users  

    PLAY [Provision web servers] ********************************************************************

    TASK [Gathering Facts] **************************************************************************
    ok: [vm1]

    TASK [common : Ensure users exist] **************************************************************
    skipping: [vm1]

    TASK [common : Mark common users done] **********************************************************
    ok: [vm1]

    PLAY RECAP **************************************************************************************
    vm1                        : ok=2    changed=0    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0
    ```

    ![tags users](/ansible/docs/screenshots/tags_users.png)

- `rescue` handles apt cache issues using `apt-get update --fix-missing`.
- `always` writes a small marker/log file unider `/tmp` to confirm clock competition.

### 2.3 `docker` role refactor

**Where:** `roles/docker/tasks/main.yml`

Implementation highlights:

- Installation is grouped in a block tagged `docker install`.

    ```bash
    zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible-playbook playbooks/provision.yml --tags docker_
    install

    PLAY [Provision web servers] ********************************************************************

    TASK [Gathering Facts] **************************************************************************
    ok: [vm1]

    TASK [docker : Install prerequisites] ***********************************************************
    ok: [vm1]

    TASK [docker : Ensure /etc/apt/keyrings exists] *************************************************
    ok: [vm1]

    TASK [docker : Add Docker GPG key] **************************************************************
    ok: [vm1]

    TASK [docker : Add Docker repo] *****************************************************************
    ok: [vm1]

    TASK [docker : Install Docker packages] *********************************************************
    ok: [vm1]

    TASK [docker : Ensure Docker service enabled and running] ***************************************
    ok: [vm1]

    PLAY RECAP **************************************************************************************
    vm1                        : ok=7    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
    ```

    ![docker install](/ansible/docs/screenshots/tags_docker_install.png)

- Configuration is grouped in a block tagged `docker_config`.

    ```bash
    zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible-playbook playbooks/provision.yml --tags docker_
    config

    PLAY [Provision web servers] ********************************************************************

    TASK [Gathering Facts] **************************************************************************
    ok: [vm1]

    TASK [docker : Add user to docker group] ********************************************************
    ok: [vm1]

    TASK [docker : Install python docker SDK for Ansible docker modules] ****************************
    ok: [vm1]

    PLAY RECAP **************************************************************************************
    vm1                        : ok=3    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
    ```

    ![tags docker config](/ansible/docs/screenshots/tags_docker_config.png)

- `rescue` retries apt update in case of GPG/network flakiness.

    ![](/ansible/docs/screenshots/rescue.png)

- `always` ensures Docker service is enabled and running.

    ![docker status](/ansible/docs/screenshots/docker_status_vm.png)

### 2.4 Commands used for tag testing

```bash
# Run only docker role
ansible-playbook playbooks/provision.yml --tags "docker"

# Skip common role
ansible-playbook playbooks/provision.yml --skip-tags "common"

# Install packages only across all roles
ansible-playbook playbooks/provision.yml --tags "packages"

# Check mode (dry-run)
ansible-playbook playbooks/provision.yml --tags "docker" --check

# Run only docker installation tasks
ansible-playbook playbooks/provision.yml --tags "docker_install"

# List all tags
ansible-playbook playbooks/provision.yml --list-tags
```

![tags docker](/ansible/docs/screenshots/tags_docker.png)

![skip tags common](/ansible/docs/screenshots/skip_tags_common.png)

![tags packages](/ansible/docs/screenshots/tags_packages.png)

![tags docker check](/ansible/docs/screenshots/tags_docker_check.png)

![tags docker install](/ansible/docs/screenshots/tags_docker_install.png)

![list tags](/ansible/docs/screenshots/list_tags.png)

Rescue block triggered output:

![rescue triggered](/ansible/docs/screenshots/rescue.png)

## 3). Docker Compose Migration

### 3.1 Role rename and playbook updates

- Renamed role: `app_deploy` -> `web_app`.
- Updated references in playbooks to use `web_app`.

### 3.2 Docker Compose template

![docker outputs](/ansible/docs/screenshots/docker_vm.png)

**Where:** `roles/web_app/templates/docker-compose.yml.j2`.

Template supports:

- dynamic `app_name`
- image `docker image` + tag
- ports (`app_port` <-> `container_port`)
- `app_env` environment map
- restart policy

### 3.3 Role Dependancy

**Where:** `roles/web_app/meta/main.yml`.

`web_app` depends on `docker`, so running only deploy still install Docker first.

Test:

```bash
ansible-playbook playbooks/deploy.yml
# docker role runs automatically before web_app
```

![](/ansible/docs/screenshots/docker_test_web.png)

### 3.4 Deployment with docker_compose module

**Where:** `roles/web_app/tasks/main.yml`.

Deployment steps:

1. Create project dir (e.g `/opt/{{ app_name }}`).
2. Render `docker-compose.yml`.
3. Run `docker compose up` via Ansible module.
4. Health-check the app endpoint.

Required tags applied:

- `app_deploy`
- `compose`

### 3.5 Variables & Secrets (Vault)

Configuration is stored in `inventory/group_vars/main.yml` (and role defaults). Sensitive values are stored using Ansible Vault.

![](/ansible/docs/screenshots/cat_vars.png)

### 3.6 Full deployment and idempotency

```bash
# Full deployment
ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass

# Idempotency check: second run should show no changes (or minimal/no-op changes)
ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass

# Verify on target VM
curl -fsS "http://127.0.0.1:<APP_PORT>/health"
```

```bash
zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml --vault-password-file .vault_pass.sh

PLAY [Deploy application] ***********************************************************************************

TASK [Gathering Facts] **************************************************************************************
ok: [vm1]

TASK [docker : Install prerequisites] ***********************************************************************
ok: [vm1]

TASK [docker : Ensure /etc/apt/keyrings exists] *************************************************************
ok: [vm1]

TASK [docker : Add Docker GPG key] **************************************************************************
ok: [vm1]

TASK [docker : Add Docker repo] *****************************************************************************
ok: [vm1]

TASK [docker : Install Docker packages] *********************************************************************
ok: [vm1]

TASK [docker : Ensure Docker service enabled and running] ***************************************************
ok: [vm1]

TASK [docker : Add user to docker group] ********************************************************************
ok: [vm1]

TASK [docker : Install python docker SDK for Ansible docker modules] ****************************************
ok: [vm1]

TASK [web_app : Include wipe tasks] *************************************************************************
included: /home/zagur/projects/ansible/roles/web_app/tasks/wipe.yml for vm1

TASK [web_app : Remove old container by name if exists] *****************************************************
skipping: [vm1]

TASK [web_app : Gather running containers info] *************************************************************
skipping: [vm1]

TASK [web_app : Compute containers publishing the app port] *************************************************
skipping: [vm1]

TASK [web_app : Remove containers publishing the app port] **************************************************
skipping: [vm1]

TASK [web_app : Stop and remove compose stack] **************************************************************
skipping: [vm1]

TASK [web_app : Remove compose default network if exists] ***************************************************
skipping: [vm1]

TASK [web_app : Remove docker-compose.yml] ******************************************************************
skipping: [vm1]

TASK [web_app : Remove application directory] ***************************************************************
skipping: [vm1]

TASK [web_app : Log wipe completion] ************************************************************************
skipping: [vm1]

TASK [web_app : Login to Docker Hub] ************************************************************************
changed: [vm1]

TASK [web_app : Ensure compose project directory exists] ****************************************************
ok: [vm1]

TASK [web_app : Template docker-compose.yml] ****************************************************************
ok: [vm1]

TASK [web_app : Deploy via Docker Compose v2] ***************************************************************
changed: [vm1]

TASK [web_app : Health check] *******************************************************************************
ok: [vm1]

TASK [web_app : Log deploy completion marker] ***************************************************************
ok: [vm1]

RUNNING HANDLER [web_app : Wait for app to start] ***********************************************************
Pausing for 5 seconds
(ctrl+C then 'C' = continue early, ctrl+C then 'A' = abort)
ok: [vm1]

PLAY RECAP **************************************************************************************************
vm1                        : ok=17   changed=2    unreachable=0    failed=0    skipped=9    rescued=0    ignored=0
```
I ran the deployment playbook twice to validate idempotency:

- **1st run:** the application was deployed successfully.
- **2nd run:** the playbook finished successfully again and the application health check remained **OK**.

On the second run Ansible still reported a small number of `changed` tasks (**changed=2**). This is **expected** in my implementation and does not indicate configuration drift:

1) **Docker Hub login task**
- I use `community.docker.docker_login` with `reauthorize: true`, which refreshes the authentication and can be reported as a change on every run.
- This keeps the deployment robust (avoids failures due to expired credentials), but it is not strictly “no-op” in Ansible reporting.

2) **Docker Compose deployment task**
- I deploy via `community.docker.docker_compose_v2` and use an image tag such as `latest`.
- Docker Compose may perform a pull/check step on each run and Ansible can report it as `changed` even when the service state is effectively the same.

**Conclusion:** The playbook is idempotent in terms of the final system state: the service remains running, configuration stays consistent, and the health endpoint returns `200`. The observed `changed=2` is an acceptable change caused by authentication refresh and image update checks, not by repeated resource recreation.

```bash
zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml --vault-password-file .vault_pass.sh

PLAY [Deploy application] ***********************************************************************************

TASK [Gathering Facts] **************************************************************************************
ok: [vm1]

TASK [docker : Install prerequisites] ***********************************************************************
ok: [vm1]

TASK [docker : Ensure /etc/apt/keyrings exists] *************************************************************
ok: [vm1]

TASK [docker : Add Docker GPG key] **************************************************************************
ok: [vm1]

TASK [docker : Add Docker repo] *****************************************************************************
ok: [vm1]

TASK [docker : Install Docker packages] *********************************************************************
ok: [vm1]

TASK [docker : Ensure Docker service enabled and running] ***************************************************
ok: [vm1]

TASK [docker : Add user to docker group] ********************************************************************
ok: [vm1]

TASK [docker : Install python docker SDK for Ansible docker modules] ****************************************
ok: [vm1]

TASK [web_app : Include wipe tasks] *************************************************************************
included: /home/zagur/projects/ansible/roles/web_app/tasks/wipe.yml for vm1

TASK [web_app : Remove old container by name if exists] *****************************************************
skipping: [vm1]

TASK [web_app : Gather running containers info] *************************************************************
skipping: [vm1]

TASK [web_app : Compute containers publishing the app port] *************************************************
skipping: [vm1]

TASK [web_app : Remove containers publishing the app port] **************************************************
skipping: [vm1]

TASK [web_app : Stop and remove compose stack] **************************************************************
skipping: [vm1]

TASK [web_app : Remove compose default network if exists] ***************************************************
skipping: [vm1]

TASK [web_app : Remove docker-compose.yml] ******************************************************************
skipping: [vm1]

TASK [web_app : Remove application directory] ***************************************************************
skipping: [vm1]

TASK [web_app : Log wipe completion] ************************************************************************
skipping: [vm1]

TASK [web_app : Login to Docker Hub] ************************************************************************
changed: [vm1]

TASK [web_app : Ensure compose project directory exists] ****************************************************
ok: [vm1]

TASK [web_app : Template docker-compose.yml] ****************************************************************
ok: [vm1]

TASK [web_app : Deploy via Docker Compose v2] ***************************************************************
changed: [vm1]

TASK [web_app : Health check] *******************************************************************************
ok: [vm1]

TASK [web_app : Log deploy completion marker] ***************************************************************
ok: [vm1]

RUNNING HANDLER [web_app : Wait for app to start] ***********************************************************
Pausing for 5 seconds
(ctrl+C then 'C' = continue early, ctrl+C then 'A' = abort)
ok: [vm1]

PLAY RECAP **************************************************************************************************
vm1                        : ok=17   changed=2    unreachable=0    failed=0    skipped=9    rescued=0    ignored=0
```

![curl on vm](/ansible/docs/screenshots/curl_on_vm.png)

## 4). Wipe Logic Implementation

### 4.1 Requirements satisfied

Wipe logic is:

- controlled by vriable: `web_app_wipe: true`
- gated by tag: `web_app_wipe`
- does not use the special `never` tag
- default behavior: wipe does not run unless explicitly requested

### 4.2 How it works

- Wipe tasks are included at the top of `web_app` execution.
- Wipe removes the application stack (Compose down/absent) and related files/dirs.
- Deployment continues normally after wipe (for “clean install”), unless running wipe-only.

### 4.3 Commands used

```bash
# Wipe only (remove application completely)
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe

# Clean install: wipe first, then deploy
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"

# Normal deploy: wipe tasks skipped (default)
ansible-playbook playbooks/deploy.yml
```

```bash
zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe --vault-password-file .vault_pass.sh

PLAY [Deploy application] ******************************************************************************

TASK [Gathering Facts] *********************************************************************************
ok: [vm1]

TASK [../roles/web_app : Include wipe tasks] ***********************************************************
included: /home/zagur/projects/ansible/roles/web_app/tasks/wipe.yml for vm1

TASK [../roles/web_app : Remove old container by name if exists] ***************************************
changed: [vm1]

TASK [../roles/web_app : Find containers publishing app_port] ******************************************
ok: [vm1]

TASK [../roles/web_app : Remove containers publishing app_port (wipe)] *********************************
skipping: [vm1]

TASK [../roles/web_app : Remove old container by name if exists] ***************************************
ok: [vm1]

TASK [../roles/web_app : Stop and remove compose stack] ************************************************
changed: [vm1]

TASK [../roles/web_app : Remove compose default network if exists] *************************************
ok: [vm1]

TASK [../roles/web_app : Remove docker-compose.yml] ****************************************************
changed: [vm1]

TASK [../roles/web_app : Remove application directory] *************************************************
changed: [vm1]

TASK [../roles/web_app : Log wipe completion] **********************************************************
ok: [vm1] => {
    "msg": "Application devops-info-service wiped successfully"
}

PLAY RECAP *********************************************************************************************
vm1                        : ok=10   changed=4    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0
```

```bash
zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml -e "web_app_wipe=true" --vault-password-file .vault_pass.sh

PLAY [Deploy application] ******************************************************************************

TASK [Gathering Facts] *********************************************************************************
ok: [vm1]

TASK [docker : Docker | Install prerequisites] *********************************************************
ok: [vm1]

TASK [docker : Docker | Ensure /etc/apt/keyrings exists] ***********************************************
ok: [vm1]

TASK [docker : Docker | Add Docker GPG key] ************************************************************
ok: [vm1]

TASK [docker : Docker | Add Docker apt repository] *****************************************************
ok: [vm1]

TASK [docker : Docker | Install Docker packages] *******************************************************
ok: [vm1]

TASK [docker : Docker | Ensure Docker service enabled+running (always)] ********************************
ok: [vm1]

TASK [docker : Docker | Add user to docker group] ******************************************************
ok: [vm1]

TASK [docker : Docker | Install python docker SDK for Ansible modules] *********************************
ok: [vm1]

TASK [../roles/web_app : Include wipe tasks] ***********************************************************
included: /home/zagur/projects/ansible/roles/web_app/tasks/wipe.yml for vm1

TASK [../roles/web_app : Remove old container by name if exists] ***************************************
ok: [vm1]

TASK [../roles/web_app : Find containers publishing app_port] ******************************************
ok: [vm1]

TASK [../roles/web_app : Remove containers publishing app_port (wipe)] *********************************
skipping: [vm1]

TASK [../roles/web_app : Remove old container by name if exists] ***************************************
ok: [vm1]

TASK [../roles/web_app : Stop and remove compose stack] ************************************************
fatal: [vm1]: FAILED! => {"changed": false, "msg": "\"/opt/devops-info-service\" is not a directory"}
...ignoring

TASK [../roles/web_app : Remove compose default network if exists] *************************************
ok: [vm1]

TASK [../roles/web_app : Remove docker-compose.yml] ****************************************************
ok: [vm1]

TASK [../roles/web_app : Remove application directory] *************************************************
ok: [vm1]

TASK [../roles/web_app : Log wipe completion] **********************************************************
ok: [vm1] => {
    "msg": "Application devops-info-service wiped successfully"
}

TASK [../roles/web_app : Login to Docker Hub] **********************************************************
changed: [vm1]

TASK [../roles/web_app : Ensure compose project directory exists] **************************************
changed: [vm1]

TASK [../roles/web_app : Template docker-compose.yml] **************************************************
changed: [vm1]

TASK [../roles/web_app : Deploy via Docker Compose v2] *************************************************
changed: [vm1]

TASK [../roles/web_app : Give app time to start] *******************************************************
Pausing for 5 seconds
(ctrl+C then 'C' = continue early, ctrl+C then 'A' = abort)
ok: [vm1]

TASK [../roles/web_app : Health check] *****************************************************************
ok: [vm1]

TASK [../roles/web_app : Log deploy completion marker] *************************************************
ok: [vm1]

PLAY RECAP *********************************************************************************************
vm1                        : ok=25   changed=4    unreachable=0    failed=0    skipped=1    rescued=0   
ignored=1   
```

```bash
zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml -
-tags web_app_wipe --vault-password-file .vault_pass.sh

PLAY [Deploy application] ******************************************************************************

TASK [Gathering Facts] *********************************************************************************
ok: [vm1]

TASK [../roles/web_app : Include wipe tasks] ***********************************************************
included: /home/zagur/projects/ansible/roles/web_app/tasks/wipe.yml for vm1

TASK [../roles/web_app : Remove old container by name if exists] ***************************************
skipping: [vm1]

TASK [../roles/web_app : Find containers publishing app_port] ******************************************
skipping: [vm1]

TASK [../roles/web_app : Remove containers publishing app_port (wipe)] *********************************
skipping: [vm1]

TASK [../roles/web_app : Remove old container by name if exists] ***************************************
skipping: [vm1]

TASK [../roles/web_app : Stop and remove compose stack] ************************************************
skipping: [vm1]

TASK [../roles/web_app : Remove compose default network if exists] *************************************
skipping: [vm1]

TASK [../roles/web_app : Remove docker-compose.yml] ****************************************************
skipping: [vm1]

TASK [../roles/web_app : Remove application directory] *************************************************
skipping: [vm1]

TASK [../roles/web_app : Log wipe completion] **********************************************************
skipping: [vm1]

PLAY RECAP *********************************************************************************************
vm1                        : ok=2    changed=0    unreachable=0    failed=0    skipped=9    rescued=0    ignored=0
```

```bash
zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml --vault-pa
ssword-file .vault_pass.sh

PLAY [Deploy application] ***************************************************************************************

TASK [Gathering Facts] ******************************************************************************************
ok: [vm1]

TASK [docker : Install prerequisites] ***************************************************************************
ok: [vm1]

TASK [docker : Ensure /etc/apt/keyrings exists] *****************************************************************
ok: [vm1]

TASK [docker : Add Docker GPG key] ******************************************************************************
ok: [vm1]

TASK [docker : Add Docker repo] *********************************************************************************
ok: [vm1]

TASK [docker : Install Docker packages] *************************************************************************
ok: [vm1]

TASK [docker : Ensure Docker service enabled and running] *******************************************************
ok: [vm1]

TASK [docker : Add user to docker group] ************************************************************************
ok: [vm1]

TASK [docker : Install python docker SDK for Ansible docker modules] ********************************************
ok: [vm1]

TASK [web_app : Include wipe tasks] *****************************************************************************
included: /home/zagur/projects/ansible/roles/web_app/tasks/wipe.yml for vm1

TASK [web_app : Remove old container by name if exists] *********************************************************
skipping: [vm1]

TASK [web_app : Gather running containers info] *****************************************************************
skipping: [vm1]

TASK [web_app : Compute containers publishing the app port] *****************************************************
skipping: [vm1]

TASK [web_app : Remove containers publishing the app port] ******************************************************
skipping: [vm1]

TASK [web_app : Stop and remove compose stack] ******************************************************************
skipping: [vm1]

TASK [web_app : Remove compose default network if exists] *******************************************************
skipping: [vm1]

TASK [web_app : Remove docker-compose.yml] **********************************************************************
skipping: [vm1]

TASK [web_app : Remove application directory] *******************************************************************
skipping: [vm1]

TASK [web_app : Log wipe completion] ****************************************************************************
skipping: [vm1]

TASK [web_app : Login to Docker Hub] ****************************************************************************
changed: [vm1]

TASK [web_app : Ensure compose project directory exists] ********************************************************
ok: [vm1]

TASK [web_app : Template docker-compose.yml] ********************************************************************
ok: [vm1]

TASK [web_app : Deploy via Docker Compose v2] *******************************************************************
changed: [vm1]

TASK [web_app : Health check] ***********************************************************************************
ok: [vm1]

TASK [web_app : Log deploy completion marker] *******************************************************************
ok: [vm1]

RUNNING HANDLER [web_app : Wait for app to start] ***************************************************************
Pausing for 5 seconds
(ctrl+C then 'C' = continue early, ctrl+C then 'A' = abort)
ok: [vm1]

PLAY RECAP ******************************************************************************************************
vm1                        : ok=17   changed=2    unreachable=0    failed=0    skipped=9    rescued=0    ignored=0
```

## 5). CI/CD Integration (GitHub Actions)

### 5.1 Workflow summary

CI/CD pipeline:

```code
Push/PR → ansible-lint → run ansible-playbook (deploy) → verify health endpoint
```

### 5.2 Setup steps

1. Add workflow file: `.github/workflows/ansible-deploy.yml`
2. Configure repository secrets:
    - `ANSIBLE_VAULT_PASSWORD`
    - `SSH_PRIVATE_KEY`
    - `VM_HOST`
    - `VM_USER`
3. Push to `lab06` (or `main` / `master`) to trigger CI.

![lint](/ansible/docs/screenshots/lint_github.png)

```bash
Run . .venv/bin/activate
  
PLAY [Deploy application] ******************************************************
TASK [Gathering Facts] *********************************************************
Warning: : Host 'vm1' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.20/reference_appendices/interpreter_discovery.html for more information.
ok: [vm1]
TASK [docker : Install prerequisites] ******************************************
ok: [vm1]
TASK [docker : Ensure /etc/apt/keyrings exists] ********************************
ok: [vm1]
TASK [docker : Add Docker GPG key] *********************************************
ok: [vm1]
TASK [docker : Add Docker repo] ************************************************
Warning: : Deprecation warnings can be disabled by setting `deprecation_warnings=False` in ansible.cfg.
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /home/zagur/actions-runner/_work/DevOps-Core-Course/DevOps-Core-Course/ansible/roles/docker/tasks/main.yml:29:15
27     - name: Add Docker repo
28       ansible.builtin.apt_repository:
29         repo: "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu {{...
                 ^ column 15
Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.
ok: [vm1]
TASK [docker : Install Docker packages] ****************************************
ok: [vm1]
TASK [docker : Ensure Docker service enabled and running] **********************
ok: [vm1]
TASK [docker : Add user to docker group] ***************************************
ok: [vm1]
TASK [docker : Install python docker SDK for Ansible docker modules] ***********
ok: [vm1]
TASK [web_app : Include wipe tasks] ********************************************
included: /home/zagur/actions-runner/_work/DevOps-Core-Course/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for vm1
TASK [web_app : Remove old container by name if exists] ************************
skipping: [vm1]
TASK [web_app : Gather running containers info] ********************************
skipping: [vm1]
TASK [web_app : Compute containers publishing the app port] ********************
skipping: [vm1]
TASK [web_app : Remove containers publishing the app port] *********************
skipping: [vm1]
TASK [web_app : Stop and remove compose stack] *********************************
skipping: [vm1]
TASK [web_app : Remove compose default network if exists] **********************
skipping: [vm1]
TASK [web_app : Remove docker-compose.yml] *************************************
skipping: [vm1]
TASK [web_app : Remove application directory] **********************************
skipping: [vm1]
TASK [web_app : Log wipe completion] *******************************************
skipping: [vm1]
TASK [web_app : Login to Docker Hub] *******************************************
changed: [vm1]
TASK [web_app : Ensure compose project directory exists] ***********************
ok: [vm1]
TASK [web_app : Template docker-compose.yml] ***********************************
ok: [vm1]
TASK [web_app : Deploy via Docker Compose v2] **********************************
ok: [vm1]
TASK [web_app : Health check] **************************************************
ok: [vm1]
TASK [web_app : Log deploy completion marker] **********************************
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /home/zagur/actions-runner/_work/DevOps-Core-Course/DevOps-Core-Course/ansible/roles/web_app/tasks/main.yml:76:18
74       ansible.builtin.copy:
75         dest: "/tmp/web_app_deploy_done"
76         content: "web_app deploy completed on {{ ansible_date_time.iso8601 }}\n"
                    ^ column 18
Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.
ok: [vm1]
PLAY RECAP *********************************************************************
vm1                        : ok=16   changed=1    unreachable=0    failed=0    skipped=9    rescued=0    ignored=0   
```

## 6). Testing results 

### 6.1 Tags & selective execution

I verified that tags allow running only specific parts of the automation:

- `--tags packages` executes only the package installation block in `common`
- `--tags users` executes only the user management block in `common`
- `--tags docker_install` executes only Docker installation tasks
- `--tags docker_config` executes only Docker post-install configuration
- `--list-tags` shows all available tags for the project

Evidence: terminal outputs and screenshots are attached in `docs/screenshots/` for each command.

### 6.2 Docker Compose deployment

I confirmed that the application is deployed via Docker Compose (v2 module):

- `docker-compose.yml` is rendered to `/opt/{{ app_name }}/docker-compose.yml`
- the compose stack is started with `community.docker.docker_compose_v2`
- health endpoint `/health` returns HTTP 200

Evidence attached:
- successful `ansible-playbook deploy.yml` output (previous sections)
- curl output `/health` from inside the VM

![](/ansible/docs/screenshots/curl_on_vm.png)

### 6.3 Idempotency check

I ran the deploy playbook twice:

- Run #1: successful deployment
- Run #2: the final system state is unchanged (service stays running and healthy)

On the second run Ansible still reported `changed=2`. This is expected in my implementation:
- Docker Hub login refresh (`reauthorize: true`) can be reported as `changed`
- Docker Compose may re-check/pull images (e.g., tag `latest`) and be reported as `changed`

Despite these small changes, the deployment is idempotent in terms of **resulting state**:
the service remains running and passes the health check.

### 6.4 Wipe logic test scenarios

I validated all wipe scenarios required by the lab:

1) Normal deploy: wipe tasks are skipped by default  
2) Wipe-only: `-e web_app_wipe=true --tags web_app_wipe` removes the stack and files  
3) Clean reinstall: `-e web_app_wipe=true` performs wipe first, then deploys again  
4) Safety check: `--tags web_app_wipe` with default variable `false` does not wipe anything

Evidence: terminal outputs for each scenario are included in this report.

## 7). Challenges & Solutions

### 1. Docker container name conflict
**Challenge:**  
Deployment failed with `Conflict. The container name "/devops-info-service" is already in use`, because an old container with the same name already existed on the VM (leftovers from a previous deployment not managed by the current Compose project).

**Solution:**  
Implemented a **wipe** procedure (double-gated by `web_app_wipe=true` and the `web_app_wipe` tag) that removes leftovers before redeploy:
- force-removes the legacy container by name (`docker_container: state=absent`)
- removes the Compose stack (`docker_compose_v2: state=absent, remove_orphans=true`)
- deletes the project directory and `docker-compose.yml` from the VM

This ensured the Compose deployment could create resources without naming conflicts.

### 2. CI failed because `.vault_pass` was missing on GitHub Actions
**Challenge:** `ansible-lint` triggers `ansible-playbook --syntax-check`, and Ansible tried to read `vault_password_file = .vault_pass` from `ansible.cfg`. On GitHub runners this file does not exist, so syntax-check failed before linting even started.

**Solution:** Provide the vault password file dynamically in the workflow and point Ansible to it via `ANSIBLE_VAULT_PASSWORD_FILE` (or remove `vault_password_file` from `ansible.cfg` and pass `--vault-password-file` explicitly in CI).

### 3. `ignore_errors` is discouraged and flagged by lint
**Challenge:** Wipe tasks used `ignore_errors: true` in multiple places. ansible-lint flags this as unpredictable because it hides failures and makes runs harder to debug.

**Solution:** Replace `ignore_errors` with explicit error handling:
- Use `failed_when: false` for "best-effort cleanup" tasks.
- Optionally keep `changed_when: false` to avoid noisy diffs.
This keeps playbooks reliable and lint-compliant.

## 8). Research Answers

### Blocks & Tags

**Q: What happens if the rescue block also fails?**  
If a task inside `rescue:` fails, the whole block fails and the playbook stops (unless errors are ignored). `always:` still runs (because it executes regardless of success/failure). In production, rescue should be conservative (log context, retry safely, and fail with a clear message if recovery is impossible).

**Q: Can you have nested blocks?**  
Yes. Blocks can be nested to structure complex flows (e.g., “install → configure → verify”), each with its own rescue/always. This can improve readability, but too much nesting can make playbooks hard to follow.

**Q: How do tags inherit to tasks within blocks?**  
Tags applied at the block level apply to all tasks inside the block. Tasks may also define their own tags. When running with `--tags X`, tasks run if they match tag `X` either directly or via inheritance.

### Docker Compose

**Q: What’s the difference between `restart: always` and `restart: unless-stopped`?**  
- `always`: the container always restarts after failure and also after daemon restarts, even if the user manually stopped it (it will start again on daemon restart).  
- `unless-stopped`: it restarts on failure/daemon restart, but if the container was manually stopped, it will not be restarted automatically.

**Q: How do Docker Compose networks differ from Docker bridge networks?**  
Compose creates project-scoped networks automatically and connects services by service name (internal DNS). A “bridge network” is a Docker network driver type; Compose typically creates a bridge network for the project, but it is isolated and named per project. Compose makes multi-container networking reproducible and consistent.

**Q: Can you reference Ansible Vault variables in the template?**  
Yes. Vault-encrypted variables are decrypted at runtime (with the vault password) and can be used like normal Ansible variables in Jinja2 templates, including docker-compose.yml.j2.

### Wipe logic

**Q: Why use both variable AND tag (double gating)?**  
This provides two independent safety checks:
- the variable indicates intent (“I really want to wipe”)
- the tag indicates scope (“run only wipe logic now”)
Accidental wipe becomes much less likely.

**Q: What’s the difference between using `never` tag and this approach?**  
`never` prevents tasks from running unless explicitly tagged, but it’s a special tag with a particular behavior. The lab explicitly requests NOT using it. Double gating (var + tag) achieves safety without relying on `never`.

**Q: Why must wipe logic come BEFORE deployment in main.yml?**  
Because the “clean reinstall” scenario requires deterministic order: remove old deployment first, then deploy fresh. If wipe was after deployment, it could delete the newly deployed stack.

**Q: When would you want clean reinstall vs rolling update?**  
- Clean reinstall: corrupted state, major reconfiguration, troubleshooting, or decommissioning.  
- Rolling update: normal upgrades where downtime should be minimized, and state should be preserved.

**Q: How would you extend wipe to remove images/volumes too?**  
You could add optional tasks guarded by another variable (e.g., `web_app_wipe_images=true`) to:
- remove specific images (`community.docker.docker_image state: absent`)
- remove volumes (`docker volume rm ...` or compose down with volume removal)
This should be carefully gated because it is destructive and affects disk usage/state.

### CI/CD (GitHub Actions)

**Q: What are the security implications of storing SSH keys in GitHub Secrets?**  
Secrets are encrypted and not visible in logs by default, but any workflow with write access could potentially misuse them. Best practices:
- use least-privileged SSH keys (restricted user, limited commands if possible)
- rotate keys periodically
- restrict who can modify workflows/merge to main
- prefer self-hosted runner + private network when possible

**Q: How would you implement a staging → production pipeline?**  
Use two environments (staging/prod) with separate inventories and secrets, and add manual approval for production:
- on push → deploy to staging automatically
- on release tag / manual approval → deploy to production
GitHub Environments can enforce approvals and secret separation.

**Q: What would you add to make rollbacks possible?**  
Pin images to immutable tags (version/SHA) instead of `latest`. Keep previous versions available, and allow redeploying with an older tag. Optionally store deployment metadata and provide a “rollback” workflow that redeploys last known good version.

**Q: How does a self-hosted runner improve security compared to GitHub-hosted?**  
A self-hosted runner can live inside the same private network as the target VM, avoiding exposing SSH to the internet and reducing key distribution. It also allows tighter control over the execution environment, but it requires maintaining runner security and updates.
