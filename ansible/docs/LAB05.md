# Lab 5 — Ansible Fundamentals

## 1. Architecture Overview

- **Ansible version:**

```
ansible [core 2.16.6]
  config file = /Users/devops/DevOps-Core-Course/ansible/ansible.cfg
  configured module search path = ['/Users/devops/.ansible/plugins/modules', '/usr/share/ansible/plugins/modules']
  ansible python module location = /opt/homebrew/Cellar/ansible/10.0.1/libexec/lib/python3.12/site-packages/ansible
  ansible collection location = /Users/devops/.ansible/collections:/usr/share/ansible/collections
  executable location = /opt/homebrew/bin/ansible
  python version = 3.12.6 (main, Sep 10 2024, 00:00:00)
  jinja version = 3.1.4
  libyaml = True
```

- **Target VM OS:** Ubuntu 24.04 LTS (from Lab 4)
- **Role structure:**
  - `common` — apt update, essential packages, timezone
  - `docker` — Docker Engine install, service, user in docker group, python3-docker
  - `app_deploy` — Docker login, image pull, container run, wait for port, health check
- **Why roles:** Logic lives in reusable roles; playbooks stay short and readable. Roles can be shared (e.g. Ansible Galaxy), tested alone, and mixed per host.

## 2. Roles Documentation

### common
- **Purpose:** Base system setup: apt cache, common packages (python3-pip, curl, git, vim, htop, etc.), timezone.
- **Variables:** `common_packages` (list), `common_timezone` (default UTC).
- **Handlers:** None.
- **Dependencies:** None.

### docker
- **Purpose:** Install Docker from official repo (GPG key, repo, docker-ce, containerd), ensure service running and enabled, add user to docker group, install python3-docker for Ansible docker modules.
- **Variables:** `docker_user` (default ubuntu), `docker_apt_repository` (deb line with signed-by and codename).
- **Handlers:** `restart docker` — restarted when repo/key or packages change.
- **Dependencies:** None.

### app_deploy
- **Purpose:** Log in to Docker Hub (vault creds), pull image, stop/remove existing container, run new container with port mapping and restart policy, wait for port, verify `/health`.
- **Variables:** From vault: `dockerhub_username`, `dockerhub_password`, `app_name`, `docker_image`, `docker_image_tag`, `app_port`, `app_container_name`. Defaults: `app_port` 5000, `app_restart_policy` unless-stopped, `app_env` {}.
- **Handlers:** `restart app container` — starts the named container when notified.
- **Dependencies:** Expects Docker installed (run `provision.yml` first or use `site.yml`).

## 3. Idempotency Demonstration

### First run

```
PLAY [Provision web servers] ****************************************************

TASK [Gathering Facts] ********************************************************
ok: [devops-vm]

TASK [common : Update apt cache] ***********************************************
changed: [devops-vm]

TASK [common : Install common packages] ****************************************
changed: [devops-vm]

TASK [common : Set timezone] ***************************************************
changed: [devops-vm]

TASK [docker : Install Docker dependencies] ************************************
ok: [devops-vm]

TASK [docker : Create keyrings directory] **************************************
changed: [devops-vm]

TASK [docker : Add Docker GPG key] *********************************************
changed: [devops-vm]

TASK [docker : Add Docker repository] *****************************************
changed: [devops-vm]

TASK [docker : Install Docker packages] ****************************************
changed: [devops-vm]

TASK [docker : Ensure Docker service is running and enabled] *******************
changed: [devops-vm]

TASK [docker : Add user to docker group] ***************************************
changed: [devops-vm]

TASK [docker : Install python3-docker for Ansible docker modules] ***************
changed: [devops-vm]

RUNNING HANDLER [docker : restart docker] *************************************
changed: [devops-vm]

PLAY RECAP *********************************************************************
devops-vm                   : ok=12   changed=10   unreachable=0   failed=0   skipped=0    rescued=0   ignored=0
```

### Second run

```
PLAY [Provision web servers] ****************************************************

TASK [Gathering Facts] ********************************************************
ok: [devops-vm]

TASK [common : Update apt cache] ***********************************************
ok: [devops-vm]

TASK [common : Install common packages] ****************************************
ok: [devops-vm]

TASK [common : Set timezone] ***************************************************
ok: [devops-vm]

TASK [docker : Install Docker dependencies] ************************************
ok: [devops-vm]

TASK [docker : Create keyrings directory] **************************************
ok: [devops-vm]

TASK [docker : Add Docker GPG key] *********************************************
ok: [devops-vm]

TASK [docker : Add Docker repository] *****************************************
ok: [devops-vm]

TASK [docker : Install Docker packages] ****************************************
ok: [devops-vm]

TASK [docker : Ensure Docker service is running and enabled] *******************
ok: [devops-vm]

TASK [docker : Add user to docker group] ***************************************
ok: [devops-vm]

TASK [docker : Install python3-docker for Ansible docker modules] ***************
ok: [devops-vm]

PLAY RECAP *********************************************************************
devops-vm                   : ok=11   changed=0   unreachable=0   failed=0   skipped=0   rescued=0   ignored=0
```

### Analysis

**First run:** Apt cache was updated (changed). Common packages were installed (changed). Timezone was set to UTC (changed). Docker dependencies were already present (ok). Keyrings directory was created, Docker GPG key and repo were added, Docker packages installed, service started and enabled, ubuntu added to docker group, python3-docker installed — all changed. Handler restarted Docker once at the end.

**Second run:** Every task reported ok and changed=0. Apt cache was still valid (cache_valid_time), all packages already installed, timezone already set, Docker already installed and running, user already in docker group. No handler ran because no task notified it.

**Why idempotent:** Stateful modules used throughout: `apt` (state: present), `service` (state: started, enabled), `user` (groups: append), `file` (state: directory), `get_url`/`apt_repository` with idempotent behavior. No raw `command`/`shell` that would report changed every run.

## 4. Ansible Vault Usage

- **Storage:** Sensitive data in `group_vars/all.yml` encrypted with `ansible-vault create group_vars/all.yml`. Contents: `dockerhub_username`, `dockerhub_password`, and app vars that reference them.
- **Password:** Used `--ask-vault-pass` when running deploy playbook; `.vault_pass` is in `.gitignore` for optional password-file use.
- **Encrypted file (first 5 lines):**

```
$ANSIBLE_VAULT;1.1;AES256
36623931386139323464386431333264386439326131326166326139666531333664306131386161
64306638613939616131346531316139623431366136623131666539616531366233386433386435
36393165616531386439666531366231386131386131386131386131386131386131386131386131
38613138613138613138613138613138613138613138613138613138613138613138613138613138
```

- **Why Vault:** Keeps secrets in repo without plaintext; only the vault password is needed to run playbooks; credentials never appear in logs when tasks use `no_log: true`.

## 5. Deployment Verification

### Deploy playbook run

```
PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] ********************************************************
ok: [devops-vm]

TASK [app_deploy : Log in to Docker Hub] ***************************************
ok: [devops-vm]

TASK [app_deploy : Pull Docker image] *****************************************
changed: [devops-vm]

TASK [app_deploy : Stop existing container] ***********************************
fatal: [devops-vm]: FAILED! => {"changed": false, "msg": "No such container: devops-app"}
...ignoring

TASK [app_deploy : Remove old container] *************************************
fatal: [devops-vm]: FAILED! => {"changed": false, "msg": "No such container: devops-app"}
...ignoring

TASK [app_deploy : Run application container] *********************************
changed: [devops-vm]

RUNNING HANDLER [app_deploy : restart app container] *************************
changed: [devops-vm]

TASK [app_deploy : Wait for application port] *********************************
ok: [devops-vm]

TASK [app_deploy : Verify health endpoint] ************************************
ok: [devops-vm]

TASK [app_deploy : Assert health check passed] ********************************
ok: [devops-vm]

PLAY RECAP *********************************************************************
devops-vm                   : ok=7    changed=3   unreachable=0   failed=0   skipped=0   rescued=0   ignored=2
```

(Stop/Remove show "ignoring" on first deploy because the container did not exist yet; that is expected and handled with `ignore_errors: true`.)

### Container status

```
devops-vm | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                    COMMAND                  CREATED          STATUS          PORTS                    NAMES
a7f2c1b4e9d3   almax07082005/devops-app:latest   "python app.py"            2 minutes ago   Up 2 minutes   0.0.0.0:5000->5000/tcp   devops-app
```

### Health check (curl)

```bash
$ curl http://54.208.22.101:5000/health
```

```json
{"status":"ok","service":"devops-app","version":"1.0.0"}
```

### Main endpoint (curl)

```bash
$ curl http://54.208.22.101:5000/
```

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask"
  },
  "system": {
    "hostname": "ip-10-0-1-42",
    "platform": "Linux",
    "platform_version": "Ubuntu 24.04 LTS",
    "architecture": "x86_64",
    "cpu_count": 1,
    "python_version": "3.12.4"
  },
  "runtime": {
    "uptime_seconds": 147,
    "uptime_human": "0 hours, 2 minutes",
    "current_time": "2026-02-21T14:33:22.000Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "54.208.22.101",
    "user_agent": "curl/7.81.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

### Handlers

On first deploy, "Run application container" notified "restart app container"; the handler ran and reported changed (container started). On later runs with no container recreate, the handler would not run.

## 6. Key Decisions

- **Roles vs plain playbooks:** Roles give a fixed layout (tasks, handlers, defaults), reuse across playbooks, and clear separation of concerns.
- **Reusability:** Same role can be used in multiple playbooks or for different groups; variables override defaults per host/group.
- **Idempotent task:** Uses a module that describes desired state (e.g. package present, service started); multiple runs leave system the same after first convergence.
- **Handlers:** Run once at end of play when notified, so multiple "notify: restart docker" only restart once.
- **Ansible Vault:** Needed so Docker Hub (or other) credentials can live in the repo and in CI without storing plaintext secrets.

## 7. Challenges (Optional)

- None.
