# Lab 5 — Ansible Fundamentals

**Student:** `Danil Fishchenko`  
**Date:** `2026-02-26`  
**Lab branch:** `lab05` (target)  
**Repository:** `DevOps-Core-Course`

## 0. Execution Context and Important Constraints

This report includes:
- a complete role-based Ansible project (`ansible/`) for provisioning and deployment;
- real local validation results (inventory parsing, syntax-check, Vault encryption/decryption check);
- real end-to-end execution of `provision.yml` and `deploy.yml` on a local Ubuntu 24.04 test target;
- a clear explanation of what is still blocked for the optional cloud path (Lab 4 Yandex IAM issue).

### 0.1 What was used for full execution

Lab 4 documentation (`terraform/docs/LAB04.md`) shows that:
- Yandex Cloud VM creation was blocked by folder-level IAM permissions (no usable cloud Ubuntu VM);
- fallback SSH proof used in Lab 4 resolved to a local machine (`uname -s` = `Darwin`), which is **not** a supported target for these roles (`apt`, Ubuntu Docker repo, systemd service management).

To complete Lab 5 honestly in this environment, I created a **local Ubuntu target** and executed the playbooks there:
- Docker Desktop (host) was started locally;
- a privileged `geerlingguy/docker-ubuntu2404-ansible` container (Ubuntu 24.04 + systemd + Python) was launched;
- Ansible connected via `community.docker.docker` using `ansible/inventory/hosts.local-docker.ini`.

### 0.2 What is ready to run on a real VM

The lab is now fully runnable and locally verified. For a strict “real VM from Lab 4” submission path, you only need to:
1. update `ansible/inventory/hosts.ini` (or configure dynamic inventory);
2. replace placeholder credentials in `ansible/group_vars/all.yml` (via Vault);
3. run the same playbooks on the VM;
4. optionally replace local-test terminal outputs in sections 3 and 5 with VM outputs.

## 1. Architecture Overview

### 1.1 Ansible version used (control node)

Local control-node installation was performed on `2026-02-26`.

```text
$ HOME=/tmp ansible --version
ansible [core 2.20.3]
  ansible python module location = /opt/homebrew/Cellar/ansible/13.4.0/...
  executable location = /opt/homebrew/bin/ansible
  python version = 3.14.3
  jinja version = 3.1.6
  pyyaml version = 6.0.3
```

### 1.2 Target VM OS and version

Planned target (per Lab 5 requirements):
- **Ubuntu 24.04 LTS** or **Ubuntu 22.04 LTS**
- SSH user: typically `ubuntu` (matches Lab 4 Terraform/Pulumi defaults)
- Python 3 installed on target (`/usr/bin/python3`)

Actual execution target used for this report (local validation on `2026-02-26`):
- **Ubuntu 24.04.4 LTS**
- image: `geerlingguy/docker-ubuntu2404-ansible`
- connection type: `community.docker.docker` (via `ansible/inventory/hosts.local-docker.ini`)
- systemd running inside target container (required for Docker service management)

### 1.3 Role structure (implemented)

```text
ansible/
├── ansible.cfg
├── collections/requirements.yml
├── inventory/
│   ├── hosts.ini
│   ├── hosts.local-docker.ini          # local Ubuntu test target (docker connection)
│   ├── lab05.docker.yml                # fully local dynamic inventory plugin (bonus validation)
│   ├── yandex_compute.yml              # bonus template (lab-suggested path)
│   └── yandex_cloud_inventory.yml       # Yandex plugin fallback config (GitHub plugin)
├── group_vars/
│   ├── all.yml                           # encrypted (Ansible Vault)
│   └── all.yml.example                   # editable plaintext template
├── playbooks/
│   ├── provision.yml
│   ├── deploy.yml
│   └── site.yml
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
├── vars/
│   └── local_test.yml                    # local end-to-end test overrides
└── docs/LAB05.md
```

Local tree check:
```text
$ tree ansible
19 directories, 22 files
```

### 1.4 Why roles instead of monolithic playbooks

Roles separate concerns cleanly:
- `common` handles base OS prep;
- `docker` handles Docker engine installation and service management;
- `app_deploy` handles registry auth, image pull, container lifecycle, and health checks.

This makes the code easier to reuse (same `docker` role for multiple services), easier to test (syntax/behavior per role), and easier to maintain (changes stay localized).

## 2. Roles Documentation

### 2.1 Role: `common`

**Purpose**
- Performs baseline Ubuntu setup needed for later automation.
- Ensures essential packages and timezone are configured idempotently.

**Tasks**
- `Update apt cache` with `cache_valid_time: 3600`
- `Install common packages` (`curl`, `git`, `vim`, `htop`, `python3-pip`, etc.)
- `Set timezone` via `community.general.timezone`

**Variables (defaults)**
- `common_packages` (list of essential packages)
- `common_manage_timezone` (`true`)
- `common_timezone` (`UTC`)

**Handlers**
- None (not required for this role)

**Dependencies**
- `community.general` collection (for timezone module)

### 2.2 Role: `docker`

**Purpose**
- Installs Docker Engine from the official Docker APT repository on Ubuntu.
- Ensures Docker service is enabled/running.
- Adds the target user to the `docker` group.
- Installs Python Docker SDK package for Ansible Docker modules.

**Tasks**
1. Install APT prerequisites (`ca-certificates`, `curl`, `gnupg`, etc.)
2. Ensure `/etc/apt/keyrings` exists
3. Download Docker GPG key
4. Add Docker APT repository (`download.docker.com`)
5. Install Docker packages (`docker-ce`, `docker-ce-cli`, `containerd.io`, plugins)
6. Install `python3-docker`
7. Manage `/etc/docker/daemon.json` (optional, default enabled)
8. Ensure Docker service is started and enabled
9. Add configured users to `docker` group

**Variables (defaults)**
- `docker_packages`
- `docker_prerequisite_packages`
- `docker_python_packages`
- `docker_users`
- `docker_gpg_key_url`
- `docker_repo_url`
- `docker_service_name`
- `docker_daemon_config`
- `docker_manage_daemon_config`

**Handlers**
- `restart docker` (triggered on package install / daemon config change)

**Dependencies**
- Ubuntu target (APT-based)
- `common` role should run first (recommended, but not hard dependency)

### 2.3 Role: `app_deploy`

**Purpose**
- Authenticates to Docker Hub using Vault-stored credentials.
- Pulls the application image.
- Recreates and starts the container.
- Waits for readiness and verifies `/health`.

**Tasks**
1. `docker_login` with `no_log: true`
2. `docker_image` pull
3. `docker_image_info` inspect desired local image metadata
4. Inspect existing container (`docker_container_info`)
5. Calculate whether container recreation is needed (only if image ID changed or recreate is forced)
6. Start/update container with a single `docker_container` task:
   - `restart_policy: unless-stopped`
   - port mapping (`5000:5000` by default)
   - environment variables (including `PORT=5000`)
7. Wait for TCP port to open
8. Verify health endpoint with `uri`
9. Assert JSON response contains `status=healthy`

**Variables (defaults)**
- `app_name`
- `app_container_name`
- `docker_image`, `docker_image_tag`
- `app_registry_login_enabled`, `app_registry_url`, `app_registry_reauthorize`
- `app_port`, `app_container_port`
- `app_restart_policy`
- `app_container_recreate` (default `false`)
- `app_env`
- `app_published_ports`
- `app_healthcheck_path`, `app_healthcheck_status`
- `app_wait_timeout`, `app_wait_delay`

**Handlers**
- `restart app container` (defined for manual/extended usage)

**Dependencies**
- Docker engine installed and running (`docker` role)
- `community.docker` collection
- Vault variables (`dockerhub_username`, `dockerhub_password`)

## 3. Idempotency Demonstration (Provisioning)

### 3.1 Target and command used  execution)

Provisioning was executed on the local Ubuntu 24.04 test target (`lab05-ubuntu2404`) via Docker connection:

```bash
cd ansible
HOME=/tmp ansible -i inventory/hosts.local-docker.ini webservers -m ping --vault-password-file /tmp/lab05_vault_pass_demo.txt
HOME=/tmp ansible-playbook -i inventory/hosts.local-docker.ini playbooks/provision.yml --vault-password-file /tmp/lab05_vault_pass_demo.txt -e '{"docker_users":["root"]}'
HOME=/tmp ansible-playbook -i inventory/hosts.local-docker.ini playbooks/provision.yml --vault-password-file /tmp/lab05_vault_pass_demo.txt -e '{"docker_users":["root"]}'
```

Connectivity proof:
```text
lab05-ubuntu2404 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

### 3.2 First `provision.yml` run output

```text
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab05-ubuntu2404]

TASK [common : Update apt cache] ***********************************************
changed: [lab05-ubuntu2404]

TASK [common : Install common packages] ****************************************
changed: [lab05-ubuntu2404]

TASK [common : Set timezone] ***************************************************
changed: [lab05-ubuntu2404]

TASK [docker : Install Docker apt prerequisites] *******************************
changed: [lab05-ubuntu2404]

TASK [docker : Ensure Docker apt keyrings directory exists] ********************
ok: [lab05-ubuntu2404]

TASK [docker : Download Docker GPG key] ****************************************
changed: [lab05-ubuntu2404]

TASK [docker : Configure Docker apt repository] ********************************
changed: [lab05-ubuntu2404]

TASK [docker : Install Docker engine packages] *********************************
changed: [lab05-ubuntu2404]

TASK [docker : Install Python Docker SDK package] ******************************
changed: [lab05-ubuntu2404]

TASK [docker : Configure Docker daemon settings] *******************************
changed: [lab05-ubuntu2404]

TASK [docker : Ensure Docker service is enabled and running] *******************
changed: [lab05-ubuntu2404]

TASK [docker : Add users to docker group] **************************************
changed: [lab05-ubuntu2404] => (item=root)

RUNNING HANDLER [docker : restart docker] **************************************
changed: [lab05-ubuntu2404]

PLAY RECAP *********************************************************************
lab05-ubuntu2404           : ok=14   changed=12   unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### 3.3 Second `provision.yml` run output

```text
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab05-ubuntu2404]

TASK [common : Update apt cache] ***********************************************
ok: [lab05-ubuntu2404]

TASK [common : Install common packages] ****************************************
ok: [lab05-ubuntu2404]

TASK [common : Set timezone] ***************************************************
ok: [lab05-ubuntu2404]

TASK [docker : Install Docker apt prerequisites] *******************************
ok: [lab05-ubuntu2404]

TASK [docker : Ensure Docker apt keyrings directory exists] ********************
ok: [lab05-ubuntu2404]

TASK [docker : Download Docker GPG key] ****************************************
ok: [lab05-ubuntu2404]

TASK [docker : Configure Docker apt repository] ********************************
ok: [lab05-ubuntu2404]

TASK [docker : Install Docker engine packages] *********************************
ok: [lab05-ubuntu2404]

TASK [docker : Install Python Docker SDK package] ******************************
ok: [lab05-ubuntu2404]

TASK [docker : Configure Docker daemon settings] *******************************
ok: [lab05-ubuntu2404]

TASK [docker : Ensure Docker service is enabled and running] *******************
ok: [lab05-ubuntu2404]

TASK [docker : Add users to docker group] **************************************
ok: [lab05-ubuntu2404] => (item=root)

PLAY RECAP *********************************************************************
lab05-ubuntu2404           : ok=13   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### 3.4 Analysis

The idempotency requirement is demonstrated successfully:
- first run: `changed=12`
- second run: `changed=0`

This happened because all tasks use stateful modules with explicit desired state (`apt`, `apt_repository`, `file`, `service`, `user`, `copy`) and the handler only ran on the first pass when Docker-related tasks changed.

### 3.5 Notes on local test target overrides

For the local Ubuntu Docker-based target, `docker_users` was overridden to `["root"]` because the test container uses `root` instead of the typical cloud VM user `ubuntu`.

## 4. Ansible Vault Usage

### 4.1 How credentials are stored securely

Sensitive variables are kept in:
- `ansible/group_vars/all.yml` (encrypted with Ansible Vault)

Plaintext template (safe to edit before encryption):
- `ansible/group_vars/all.yml.example`

This separates:
- **versioned encrypted secrets** (`all.yml`)
- **human-readable template** for quick setup (`all.yml.example`)

### 4.2 Vault password management strategy

Recommended strategy:
- keep vault password in local file `ansible/.vault_pass` (ignored by Git);
- set strict permissions (`chmod 600 ansible/.vault_pass`);
- optionally enable in `ansible.cfg` via `vault_password_file = .vault_pass` (commented in config now).

Important:
- do **not** commit `.vault_pass`;
- do **not** commit decrypted secret files.

### 4.3 Proof that `group_vars/all.yml` is encrypted

File header:
```text
$ sed -n '1,3p' ansible/group_vars/all.yml
$ANSIBLE_VAULT;1.1;AES256
33336132313935653332633533346363663334633932656231646236663733616133333565376137
3835666464626636616264303466363939303663303335330a333862626264306130343261626537
```

### 4.4 Vault decrypt/view verification

`ansible-vault view` was successfully tested locally with a temporary demo password file (not committed).

The decrypted content contains only placeholders (no real secrets), including:
- `dockerhub_username`
- `dockerhub_password`
- `docker_image`
- `app_port`
- `app_env`

### 4.5 Why Ansible Vault is important

Without Vault, Docker Hub credentials would be stored in plaintext YAML and could be leaked through:
- Git history
- pull requests
- backups
- screen sharing / logs

Vault keeps the repository usable for collaboration while protecting secrets at rest.

## 5. Deployment Verification

### 5.1 Local deployment execution path

`deploy.yml` was executed successfully on the same local Ubuntu 24.04 target.

Because no real Docker Hub credentials were committed or provided in this environment, I used a **local test override** (`ansible/vars/local_test.yml`) for runtime validation:
- built `app_python/` image locally;
- pushed it to a local registry (`127.0.0.1:5001`);
- configured the target Docker daemon to trust `host.docker.internal:5001` (insecure registry for local test only);
- set `app_registry_login_enabled: false` (the `docker_login` task exists and remains enabled by default for the real lab flow).

### 5.2 Deploy command used

```bash
cd ansible
HOME=/tmp ansible-playbook -i inventory/hosts.local-docker.ini playbooks/deploy.yml \
  --vault-password-file /tmp/lab05_vault_pass_demo.txt \
  -e @vars/local_test.yml
```

### 5.3 `deploy.yml` output after idempotency fix

```text
PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab05-ubuntu2404]

TASK [app_deploy : Login to Docker Hub] ****************************************
skipping: [lab05-ubuntu2404]

TASK [app_deploy : Pull application image] *************************************
ok: [lab05-ubuntu2404]

TASK [app_deploy : Inspect desired image metadata] *****************************
ok: [lab05-ubuntu2404]

TASK [app_deploy : Inspect current application container] **********************
ok: [lab05-ubuntu2404]

TASK [app_deploy : Calculate deployment state] *********************************
ok: [lab05-ubuntu2404]

TASK [app_deploy : Run application container] **********************************
ok: [lab05-ubuntu2404]

TASK [app_deploy : Wait for application port to become available] **************
ok: [lab05-ubuntu2404]

TASK [app_deploy : Verify application health endpoint] *************************
ok: [lab05-ubuntu2404]

TASK [app_deploy : Assert healthy status in response body] *********************
ok: [lab05-ubuntu2404] => {
    "changed": false,
    "msg": "Health endpoint returned status=healthy"
}

PLAY RECAP *********************************************************************
lab05-ubuntu2404           : ok=9    changed=0    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0
```

### 5.3.1 Repeated deploy run

The deployment playbook was executed twice in a row after the fix, and both runs were idempotent:

```text
PLAY RECAP *********************************************************************
lab05-ubuntu2404           : ok=9    changed=0    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0
```

This confirms there is no forced stop/remove/recreate on every run anymore.

### 5.4 Container status verification

Collected via Ansible ad-hoc on the target:

```text
lab05-ubuntu2404 | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                                                  COMMAND           CREATED              STATUS              PORTS                              NAMES
a4bce08b43bd   host.docker.internal:5001/devops-info-service:latest   "python app.py"   About a minute ago   Up About a minute   3000/tcp, 0.0.0.0:5000->5000/tcp   devops-info-service
```

### 5.5 Health and endpoint verification

Health check (`/health`):
```text
lab05-ubuntu2404 | CHANGED | rc=0 >>
{"status":"healthy","timestamp":"2026-02-26T18:30:29.199256+00:00","uptime_seconds":52}
```

Main endpoint (`/`):
```text
lab05-ubuntu2404 | CHANGED | rc=0 >>
{"endpoints":[{"description":"Service and system information","method":"GET","path":"/"},{"description":"Health check endpoint","method":"GET","path":"/health"}],"request":{"client_ip":"172.18.0.1","method":"GET","path":"/","user_agent":"curl/8.5.0"},"runtime":{"current_time":"2026-02-26T18:30:52.039493+00:00","timezone":"UTC","uptime_human":"0 hours, 1 minute","uptime_seconds":74},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"aarch64","cpu_count":10,"hostname":"a4bce08b43bd","platform":"Linux","platform_version":"#1 SMP Sat May 17 08:28:57 UTC 2025","python_version":"3.13.12"}}
```

### 5.6 Handler execution note

No handler was triggered during the successful `deploy.yml` run.  
The `app_deploy` role defines `restart app container`, but the current task flow starts/recreates the container directly without `notify`.

### 5.7 Local nested-Docker issue and fix (important)

The first deployment attempt failed on `docker_container` due nested Docker overlayfs limitations inside the test container (`overlay ... invalid argument`).  
Fix: local test daemon config was updated to `storage-driver: vfs` in `ansible/vars/local_test.yml`, after which deployment succeeded.

## 6. Key Decisions (2-3 sentences each)

### 6.1 Why use roles instead of plain playbooks?

Roles enforce separation of concerns and standard structure, which makes the automation readable and maintainable as the project grows. In this lab, it prevents `provision.yml` and `deploy.yml` from turning into long monolithic task lists.

### 6.2 How do roles improve reusability?

The `docker` role can be reused for any service, not only this Flask app. The `app_deploy` role can also be reused with a different image and ports just by overriding variables.

### 6.3 What makes a task idempotent?

An idempotent task declares the desired final state and lets Ansible decide whether a change is needed. Modules like `apt`, `service`, `user`, and `docker_container` are idempotent when used with explicit state parameters.

### 6.4 How do handlers improve efficiency?

Handlers run only when notified by a changed task, so services are not restarted unnecessarily. In this lab, Docker restart is tied to package/config changes instead of happening on every run.

### 6.5 Why is Ansible Vault necessary?

Automation often needs credentials (registry tokens, API keys, passwords). Vault allows those values to stay in version control in encrypted form, which is much safer than plaintext YAML.

## 7. Challenges (Optional)

- **Lab 4 cloud blocker:** Yandex Cloud VM was not created due folder IAM permission errors, so there was no valid Ubuntu target to run against.
- **Sandbox issue:** after installing Ansible, it failed to write to `~/.ansible`; fixed locally by running commands with `HOME=/tmp`.
- **Docker daemon not running locally:** Docker Desktop had to be started manually before local end-to-end validation.
- **Nested Docker storage driver issue:** first `deploy.yml` attempt failed with overlayfs mount error inside the Ubuntu test container; fixed by switching nested Docker to `storage-driver: vfs` (local test override only).
- **Yandex bonus plugin packaging mismatch:** the lab hint references `yandex.cloud.yandex_compute`, but `yandex.cloud` is not present on Galaxy in this environment (`Galaxy API count=0`). I kept the template and additionally validated a public Yandex inventory plugin fallback from GitHub to plugin/auth stage.

## 8. Bonus Task — Dynamic Inventory (Locally Validated + Yandex Cloud Path)

### 8.1 Lab-suggested Yandex Cloud template (kept)

Created and kept the lab-style Yandex template:
- `ansible/inventory/yandex_compute.yml` (`plugin: yandex.cloud.yandex_compute`)

Design goals covered in config:
- plugin name specified (`yandex.cloud.yandex_compute`)
- credentials via environment variables (`YC_IAM_TOKEN`, `YC_FOLDER_ID`, `YC_CLOUD_ID`)
- `compose` maps public IP to `ansible_host`
- `compose` sets `ansible_user` and Python interpreter
- `groups` creates `webservers` from running VMs
- `keyed_groups` creates groups from labels

### 8.2 Why `yandex.cloud.yandex_compute` could not be validated here

The plugin could not be executed locally because `yandex.cloud` is not available in this environment:

Galaxy API proof (`yandex/cloud` collection lookup):
```json
{"meta":{"count":0}, "...": "...", "data":[]}
```

And Ansible plugin lookup fails:

```text
$ HOME=/tmp ansible-doc -t inventory yandex.cloud.yandex_compute
[WARNING]: Error loading plugin 'yandex.cloud.yandex_compute': No module named 'ansible_collections.yandex'
[WARNING]: yandex.cloud.yandex_compute was not found
```

And inventory parsing fails for the same reason:

```text
$ HOME=/tmp ansible-inventory -i inventory/yandex_compute.yml --graph
[WARNING]: ... unknown plugin 'yandex.cloud.yandex_compute'
@all:
  |--@ungrouped:
```

### 8.3 Yandex Cloud plugin fallback (GitHub) — validated locally to plugin/auth stage

To still validate a Yandex Cloud dynamic inventory path, I used a public plugin from GitHub:
- repo: `mzatolokin/ansible-yandex-cloud-inventory`
- plugin config in repo: `ansible/inventory/yandex_cloud_inventory.yml`
- plugin name: `yandex_cloud_inventory`

Local validation steps completed:
1. Cloned plugin repo to `/tmp/ansible-yc-inventory-plugin`
2. Installed `yandexcloud` SDK into the Homebrew Ansible runtime
3. Ran `ansible-inventory` with `ANSIBLE_INVENTORY_PLUGINS=/tmp/ansible-yc-inventory-plugin/inventory_plugins`

Plugin-level validation (no token provided) succeeded up to plugin option checks:
```text
Either 'service_account_key_file', 'iam_token', or 'YC_IAM_TOKEN' environment variable must be provided
```

Validation with a dummy token shows the plugin reaches Yandex SDK/API auth stage:
```text
StatusCode.UNAUTHENTICATED
details = "Authentication failed"
```

Why full YC host discovery still cannot be completed here:
- local `yc` CLI profile is not configured in this environment (`yc iam create-token` fails with missing credentials);
- therefore no real IAM token is available for inventory discovery.

### 8.4 Fully local dynamic inventory plugin validation (end-to-end)

To satisfy full local plugin-based validation, I added:
- `ansible/inventory/lab05.docker.yml` using `community.docker.docker_containers`

This plugin is fully executed locally and used to run playbooks.

`ansible-inventory --graph`:
```text
@all:
  |--@ungrouped:
  |--@webservers:
  |  |--lab05-ubuntu2404
```

Connectivity:
```text
lab05-ubuntu2404 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

Playbooks via dynamic inventory plugin ):
```text
$ ansible-playbook -i inventory/lab05.docker.yml playbooks/provision.yml ...
PLAY RECAP ... changed=0

$ ansible-playbook -i inventory/lab05.docker.yml playbooks/deploy.yml ...
PLAY RECAP ... changed=0
```

### 8.5 How to complete strict Yandex Cloud bonus on your machine

1. Use a Yandex dynamic inventory plugin available in your environment:
   - if `yandex.cloud.yandex_compute` becomes available in your setup, use `inventory/yandex_compute.yml`;
   - otherwise use the validated GitHub fallback plugin path (`yandex_cloud_inventory`).
2. Export credentials:
   ```bash
   export YC_IAM_TOKEN="$(yc iam create-token)"
   export YC_FOLDER_ID="<folder-id>"
   # for the lab-suggested template also export:
   export YC_CLOUD_ID="<cloud-id>"
   ```
3. Test inventory:
   ```bash
   cd ansible
   # Lab-suggested template (if plugin exists in your env)
   ansible-inventory -i inventory/yandex_compute.yml --graph

   # GitHub fallback plugin example
   ANSIBLE_INVENTORY_PLUGINS=/path/to/inventory_plugins ansible-inventory -i inventory/yandex_cloud_inventory.yml --graph
   ```
4. Run playbooks with dynamic inventory:
   ```bash
   ansible-playbook -i inventory/yandex_compute.yml playbooks/provision.yml
   ansible-playbook -i inventory/yandex_compute.yml playbooks/deploy.yml --ask-vault-pass
   ```

### 8.6 Benefits vs static inventory

- No manual IP updates when VM is recreated.
- Hosts can be grouped by labels automatically.
- Same playbooks work across multiple VMs without editing `hosts.ini`.

## 9. Local Validation Summary

### 9.1 Static/default inventory parse and out-of-box ping

```text
$ HOME=/tmp ansible-inventory -i ansible/inventory/hosts.ini --graph
@all:
  |--@ungrouped:
  |--@webservers:
  |  |--lab05-ubuntu2404
```

Default inventory from `ansible.cfg` works without `-i` (Vault password file still required because `group_vars/all.yml` is encrypted):
```text
$ cd ansible
$ HOME=/tmp ansible all -m ping --vault-password-file /tmp/lab05_vault_pass_demo.txt
lab05-ubuntu2404 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

### 9.2 Playbook syntax checks

```text
$ cd ansible
$ HOME=/tmp ansible-playbook playbooks/provision.yml --syntax-check
playbook: playbooks/provision.yml

$ HOME=/tmp ansible-playbook playbooks/deploy.yml --syntax-check --vault-password-file /tmp/lab05_vault_pass_demo.txt
playbook: playbooks/deploy.yml

$ HOME=/tmp ansible-playbook playbooks/site.yml --syntax-check --vault-password-file /tmp/lab05_vault_pass_demo.txt
playbook: playbooks/site.yml
```

### 9.3 End-to-end execution summary (local Ubuntu target)

- `ansible ping` to local Ubuntu target (`hosts.local-docker.ini`) succeeded.
- `provision.yml` first run: `changed=12`
- `provision.yml` second run: `changed=0` (idempotency proven)
- `deploy.yml` successful run with health verification (`wait_for` + `uri` + `assert`)
- `app_deploy` idempotency fix validated:
  - repeated run #1: `changed=0`
  - repeated run #2: `changed=0`
  - no unconditional stop/remove/recreate on repeat runs

### 9.4 Bonus validation summary (dynamic inventory)

- `community.docker.docker_containers` dynamic inventory plugin fully validated locally:
  - `ansible-inventory --graph` works
  - `ansible -m ping` works
  - `provision.yml` and `deploy.yml` both run via dynamic inventory
- Yandex Cloud plugin path validated to plugin/auth stage via GitHub fallback (`yandex_cloud_inventory`)
- `yandex.cloud.yandex_compute` lab template remains present, but the `yandex.cloud` collection is unavailable on Galaxy in this environment (`count=0`)

### 9.5 Collections / runtime status (control node)

`community.docker` and `community.general` are available in the installed Ansible package.  
`yandexcloud` Python SDK was installed into the Homebrew Ansible runtime for Yandex plugin fallback validation.

## 10. Completion Checklist

### 10.1 Main Lab (completed locally)

- [x] Proper role-based directory structure created
- [x] `common`, `docker`, `app_deploy` roles implemented
- [x] `ansible.cfg` configured
- [x] Static inventory configured (`hosts.ini`) and local test inventory added (`hosts.local-docker.ini`)
- [x] Provisioning playbook implemented and executed
- [x] Idempotency demonstrated (`second run changed=0`)
- [x] Ansible Vault file created and encrypted (`group_vars/all.yml`)
- [x] Deployment playbook executed successfully (local Ubuntu target)
- [x] Container status and health checks verified
- [x] `app_deploy` repeat-run idempotency verified (`changed=0`, no forced redeploy)
- [x] Documentation completed with outputs and analysis

### 10.2 Bonus (validated locally)

- [x] Dynamic inventory plugin configured and executed locally (`community.docker.docker_containers`)
- [x] `ansible-inventory --graph` output captured for plugin-based dynamic inventory
- [x] Playbooks executed through dynamic inventory plugin
- [x] Yandex Cloud inventory plugin fallback loaded and validated to auth/API stage
- [x] Yandex Cloud plugin blockers documented with evidence (`yandex.cloud` missing on Galaxy, no local `yc` credentials)