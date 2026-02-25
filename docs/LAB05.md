# Lab 05

## Architecture

### Target VM

- **Host:** `88.218.62.21`
- **OS:** Debian
- **Access:** root via SSH

### Role Structure

```
ansible/
├── ansible.cfg                        # Global Ansible configuration
├── requirements.yml                   # Galaxy collections (community.docker, community.general)
├── .vault_pass                        # Vault password file (NOT committed — in .gitignore)
├── inventory/
│   ├── hosts.ini                      # Static inventory — devserver at 88.218.62.21
│   └── group_vars/
│       └── all.yml                    # AES256-encrypted vault (app configuration)
├── roles/
│   ├── common/                        # System baseline packages
│   │   ├── tasks/main.yml
│   │   └── defaults/main.yml
│   ├── docker/                        # Docker engine management
│   │   ├── tasks/main.yml
│   │   ├── handlers/main.yml
│   │   └── defaults/main.yml
│   └── app_deploy/                    # Build image and run container
│       ├── tasks/main.yml
│       ├── handlers/main.yml
│       └── defaults/main.yml
├── playbooks/
│   ├── provision.yml                  # Runs common + docker roles
│   ├── deploy.yml                     # Runs app_deploy role
│   └── site.yml                       # Master: imports provision + deploy
└── docs/
    └── LAB05.md                       # This file
```

### Why Roles Instead of Monolithic Playbooks?

A single flat playbook becomes hard to read, impossible to reuse, and
difficult to test independently. Roles enforce a contract: each role has a clear name,
owns its own defaults and handlers, and can be dropped into any other project.

---

## 2. Roles Documentation

### `common`

**Purpose:** Establish a reliable baseline on every managed host
**Variables (`defaults/main.yml`):**

| Variable          | Default                                                                                                      | Description                              |
| ----------------- | ------------------------------------------------------------------------------------------------------------ | ---------------------------------------- |
| `common_packages` | `[curl, git, vim, htop, ca-certificates, gnupg, lsb-release, apt-transport-https, python3-pip, unzip, wget]` | List of packages to ensure are installed |

**Tasks:**

1. `Update apt cache` — runs `apt update` (`cache_valid_time: 3600`)
2. `Install common packages` — installs the full list with `state: present`

**Handlers:** None — package installation does not require a service restart.

**Dependencies:** None.

---

### `docker`

**Purpose:** Ensure the Docker engine is installed and running. On servers that already have `docker.io` installed, the role detects this via `package_facts` and skips the installation block entirely

**Variables (`defaults/main.yml`):**

| Variable          | Default                                                                                  | Description                                         |
| ----------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------- |
| `docker_packages` | `[docker-ce, docker-ce-cli, containerd.io, docker-buildx-plugin, docker-compose-plugin]` | Official Docker CE package set                      |
| `docker_user`     | `root`                                                                                   | User to add to `docker` group (skipped when `root`) |

**Tasks:**

1. `Gather package facts` — collects installed package names into `ansible_facts.packages`
2. `Create Docker keyring directory` — ensures `/etc/apt/keyrings` exists
   (`state: directory`)
3. `Download Docker official GPG key` — fetches from
   `https://download.docker.com/linux/<distro>/gpg`; `force: false` prevents
   re-download (idempotent); **skipped** if Docker is already installed
4. `Get system architecture` — runs `dpkg --print-architecture`;
   `changed_when: false` so it never counts as a change
5. `Add Docker official repository` — uses `apt_repository` module;
   **skipped** if Docker already installed
6. `Install Docker CE packages` — installs the `docker_packages` list;
   **skipped** if Docker already installed; notifies `restart docker` handler
7. `Ensure Docker service is started and enabled` — idempotent service state
8. `Add user to docker group` — **skipped** when `docker_user == "root"`
9. `Install python3-docker library` — required by the `community.docker` Ansible modules

**Handlers:**

- `restart docker` — `service: name=docker state=restarted`; only triggered when Docker
  packages actually change (i.e., on a fresh installation)

**Dependencies:** `common` role (provides `ca-certificates`, `gnupg`,
`apt-transport-https` needed before adding the Docker repo).

---

### `app_deploy`

**Purpose:** Copy the FastAPI application source files to the server, build a Docker
image locally on the server, and run it as a named container with port mapping and
health check verification. Using a local build avoids any dependency on a Docker
registry — the image is always built from the current source in the repository.

**Variables (`defaults/main.yml`):**

| Variable             | Default          | Description                                            |
| -------------------- | ---------------- | ------------------------------------------------------ |
| `app_port`           | `8080`           | Host port mapped to container's internal port 8000     |
| `app_restart_policy` | `unless-stopped` | Container restart policy                               |
| `app_env_vars`       | `{}`             | Optional environment variables passed to the container |

**Variables from Vault (`inventory/group_vars/all.yml`):**

| Variable             | Value                | Description                             |
| -------------------- | -------------------- | --------------------------------------- |
| `app_name`           | `fastapi-devops-app` | Application name                        |
| `docker_image`       | `fastapi-devops-app` | Local image name used for build and run |
| `docker_image_tag`   | `latest`             | Image tag                               |
| `app_port`           | `8080`               | Host-side port (overrides role default) |
| `app_container_name` | `fastapi-devops-app` | Container name on the host              |

**Tasks:**

1. `Create app source directory on server` — ensures `/opt/fastapi-devops-app` exists
2. `Copy Dockerfile to server` — syncs `app_python/Dockerfile` from control node
3. `Copy application source to server` — syncs `app_python/main.py`
4. `Copy requirements.txt to server` — syncs `app_python/requirements.txt`
5. `Build Docker image from source` — uses `community.docker.docker_image` with
   `source: build`; `force_source: yes` rebuilds when any source file changes
6. `Stop existing container if running` — `state: stopped`, `failed_when: false` so it
   doesn't fail on first deploy when no container exists yet
7. `Remove existing container if present` — `state: absent` is a no-op if container
   doesn't exist (idempotent)
8. `Run application container` — starts container with port mapping `8080:8000`,
   restart policy, and env vars; notifies `restart app container` handler
9. `Wait for application port to be ready` — `wait_for` module polls `localhost:8080`
   for up to 30 seconds
10. `Verify application health endpoint` — `uri` module hits `/health`, retries 3 times
    with 5-second delay until HTTP 200
11. `Show health check response` — `debug` prints the JSON response to confirm the app
    is live

**Handlers:**

- `restart app container` — calls `community.docker.docker_container` with `restart: yes`
  on the named container; triggered if the container task reports a change

**Dependencies:** `docker` role (Docker engine and `python3-docker` must be present
before using `community.docker` modules).

---

## 3. Idempotency Demonstration

### First Run — `ansible-playbook playbooks/provision.yml`

```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [devserver]

TASK [common : Update apt cache] ***********************************************
changed: [devserver]

TASK [common : Install common packages] ****************************************
ok: [devserver]

TASK [docker : Gather package facts] *******************************************
ok: [devserver]

TASK [docker : Create Docker keyring directory] ********************************
ok: [devserver]

TASK [docker : Download Docker official GPG key] *******************************
skipping: [devserver]

TASK [docker : Get system architecture] ****************************************
ok: [devserver]

TASK [docker : Add Docker official repository] *********************************
skipping: [devserver]

TASK [docker : Install Docker CE packages] *************************************
skipping: [devserver]

TASK [docker : Ensure Docker service is started and enabled] *******************
ok: [devserver]

TASK [docker : Add user to docker group] ***************************************
skipping: [devserver]

TASK [docker : Install python3-docker library] *********************************
ok: [devserver]

PLAY RECAP *********************************************************************
devserver                  : ok=8    changed=1    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0
```

**Analysis — First Run:**

- `common : Update apt cache` → **changed** — the apt package index had not been
  refreshed within the last hour, so Ansible ran `apt update`. This is the only change
  because the check is time-based (`cache_valid_time: 3600`).
- `common : Install common packages` → **ok** — all listed packages (`curl`, `git`,
  `vim`, etc.) were already present on the Debian 12 server.
- Docker tasks `Download GPG key`, `Add repository`, `Install packages`,
  `Add user to group` → **skipped** — `package_facts` detected that `docker.io` was
  already installed, so the entire installation block was bypassed via `when` conditions.
- `Ensure Docker service started and enabled` → **ok** — Docker was already running.
- `Install python3-docker` → **ok** — already installed at version 5.0.3.

---

### Second Run — `ansible-playbook playbooks/provision.yml`

```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [devserver]

TASK [common : Update apt cache] ***********************************************
ok: [devserver]

TASK [common : Install common packages] ****************************************
ok: [devserver]

TASK [docker : Gather package facts] *******************************************
ok: [devserver]

TASK [docker : Create Docker keyring directory] ********************************
ok: [devserver]

TASK [docker : Download Docker official GPG key] *******************************
skipping: [devserver]

TASK [docker : Get system architecture] ****************************************
ok: [devserver]

TASK [docker : Add Docker official repository] *********************************
skipping: [devserver]

TASK [docker : Install Docker CE packages] *************************************
skipping: [devserver]

TASK [docker : Ensure Docker service is started and enabled] *******************
ok: [devserver]

TASK [docker : Add user to docker group] ***************************************
skipping: [devserver]

TASK [docker : Install python3-docker library] *********************************
ok: [devserver]

PLAY RECAP *********************************************************************
devserver                  : ok=8    changed=0    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0
```

**Analysis — Second Run:**

- `common : Update apt cache` → **ok** — the cache was refreshed less than an hour ago;
  `cache_valid_time: 3600` tells Ansible to skip the update entirely.
  **This is the key difference from run 1.**
- Everything else → **ok** or **skipped** — identical outcome to run 1.
- **`changed=0`** — the system is already in the desired state; Ansible made zero
  modifications.

**What makes the roles idempotent:**

| Technique                                           | Where used                                                    |
| --------------------------------------------------- | ------------------------------------------------------------- |
| `apt: state=present`                                | Only installs if package is absent, never re-installs         |
| `cache_valid_time: 3600`                            | Skips `apt update` if cache is fresh enough                   |
| `file: state=directory`                             | Creates directory only if it doesn't already exist            |
| `get_url: force=false`                              | Skips download if destination file already exists             |
| `apt_repository` module                             | Compares the repo line before writing; no-op if identical     |
| `service: state=started`                            | Checks current service state before taking any action         |
| `when: "'docker.io' not in ansible_facts.packages"` | Skips entire install block when any Docker variant is present |

---

## 4. Ansible Vault Usage

### How Secrets Are Stored

All configuration that should not be committed in plaintext lives in
`inventory/group_vars/all.yml`, which is AES-256 encrypted by Ansible Vault. The
plaintext is never written to disk unencrypted in the repository.

### Encrypted File (excerpt)

```
$ANSIBLE_VAULT;1.1;AES256
32343232613830303638346634366336373234623439613639343931366632616664623730336633
6635643237393431333733396362366435303331363432320a373161666635323533386137643335
...
```

The `$ANSIBLE_VAULT;1.1;AES256` header proves the file is encrypted. No values are
readable without the vault password

### Vault Password Management

A `.vault_pass` file holds the vault password locally:

```
ansible/.vault_pass    # chmod 600 — listed in .gitignore
```

`ansible.cfg` references it so decryption is fully automatic:

```ini
vault_password_file = .vault_pass
```

This means `ansible-playbook playbooks/deploy.yml` decrypts on the fly with no
`--ask-vault-pass` prompt needed

### Useful Vault Commands

```bash
# Decrypt to stdout for verification (never redirect to a tracked file)
ansible-vault decrypt --output=- inventory/group_vars/all.yml

# Edit vault contents interactively
ansible-vault edit inventory/group_vars/all.yml

# Re-encrypt a plaintext file
ansible-vault encrypt --encrypt-vault-id default plaintext.yml \
  --output=inventory/group_vars/all.yml
```

### Why Ansible Vault Is Necessary

Configuration values such as image names, ports, and container names seem harmless but
can reveal infrastructure topology. More critically, the vault pattern is the foundation
for storing genuinely sensitive values like API keys and registry tokens later.
Vault encrypts at rest so the ciphertext is safe to commit to Git. The secret travels
only in memory at playbook runtime and is never printed to the terminal or CI logs.

---

## 5. Deployment Verification

### Deploy Run — `ansible-playbook playbooks/deploy.yml`

```
PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [devserver]

TASK [app_deploy : Create app source directory on server] **********************
ok: [devserver]

TASK [app_deploy : Copy Dockerfile to server] **********************************
ok: [devserver]

TASK [app_deploy : Copy application source to server] **************************
ok: [devserver]

TASK [app_deploy : Copy requirements.txt to server] ****************************
ok: [devserver]

TASK [app_deploy : Build Docker image from source] *****************************
changed: [devserver]

TASK [app_deploy : Stop existing container if running] *************************
ok: [devserver]

TASK [app_deploy : Remove existing container if present] ***********************
ok: [devserver]

TASK [app_deploy : Run application container] **********************************
changed: [devserver]

TASK [app_deploy : Wait for application port to be ready] **********************
ok: [devserver]

TASK [app_deploy : Verify application health endpoint] *************************
ok: [devserver]

TASK [app_deploy : Show health check response] *********************************
ok: [devserver] => {
    "msg": "App is healthy: {'status': 'healthy', 'timestamp': '2026-02-25T19:50:23.102380+00:00', 'uptime_seconds': 5}"
}

RUNNING HANDLER [app_deploy : restart app container] ***************************
changed: [devserver]

PLAY RECAP *********************************************************************
devserver                  : ok=13   changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Container Status

```
$ ssh root@88.218.62.21 "docker ps --filter name=fastapi-devops-app"

CONTAINER ID   IMAGE                       COMMAND                  CREATED          STATUS          PORTS                    NAMES
fcb562ca7d32   fastapi-devops-app:latest   "uvicorn main:app --…"   15 minutes ago   Up 14 minutes   0.0.0.0:8080->8000/tcp   fastapi-devops-app
```

### Health Check Verification

```
$ curl -s http://88.218.62.21:8080/health | python3 -m json.tool
{
    "status": "healthy",
    "timestamp": "2026-02-25T20:05:05.836387+00:00",
    "uptime_seconds": 871
}
```

```
$ curl -s http://88.218.62.21:8080/ | python3 -m json.tool
{
    "service": {
        "name": "devops-info-service",
        "version": "1.0.0",
        "description": "DevOps course info service",
        "framework": "FastAPI"
    },
    "system": {
        "hostname": "fcb562ca7d32",
        "platform": "Linux",
        "platform_version": "#1 SMP PREEMPT_DYNAMIC Debian 6.1.76-1 (2024-02-01)",
        "architecture": "x86_64",
        "cpu_count": 2,
        "python_version": "3.13.12"
    },
    "runtime": {
        "uptime_seconds": 871,
        "uptime_human": "0 hours, 14 minutes",
        "current_time": "2026-02-25T20:05:05.945352+00:00",
        "timezone": "UTC"
    },
    "request": {
        "client_ip": "45.85.105.210",
        "user_agent": "curl/8.5.0",
        "method": "GET",
        "path": "/"
    },
    "endpoints": [
        {"path": "/", "method": "GET", "description": "Service information"},
        {"path": "/health", "method": "GET", "description": "Health check"}
    ]
}
```

### Handler Execution

The `restart app container` handler is defined in `app_deploy/handlers/main.yml`.
It fired on the first deployment because the `Run application container` task reported
`changed` (the container was freshly created). On a subsequent run where the source
files have not changed and the container is already running with the same image,
the build task reports `ok` and the handler does **not** fire — demonstrating that
handlers only execute when actually needed.

---
