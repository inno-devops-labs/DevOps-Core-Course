# Lab 5 — Ansible Fundamentals

## 1. Architecture Overview

- **Ansible version**: 2.20.2 (ansible-core)
- **Target VM OS**: Ubuntu 22.04 LTS (Vagrant + libvirt/KVM)
- **VM IP**: 192.168.121.159
- **SSH user**: vagrant

### Role Structure

```
ansible/
├── inventory/
│   ├── hosts.ini                  # Static inventory
│   └── group_vars/
│       └── all.yml                # Encrypted variables (Vault)
├── roles/
│   ├── common/                    # Common system tasks
│   │   ├── tasks/main.yml
│   │   └── defaults/main.yml
│   ├── docker/                    # Docker installation
│   │   ├── tasks/main.yml
│   │   ├── handlers/main.yml
│   │   └── defaults/main.yml
│   └── app_deploy/                # Application deployment
│       ├── tasks/main.yml
│       ├── handlers/main.yml
│       └── defaults/main.yml
├── playbooks/
│   ├── site.yml                   # Full deployment
│   ├── provision.yml              # System provisioning
│   └── deploy.yml                 # App deployment only
├── ansible.cfg
├── Vagrantfile
└── docs/
    └── LAB05.md
```

### Why roles instead of monolithic playbooks?

Roles provide modular, reusable code organization. Each role encapsulates a single responsibility (e.g., installing Docker), making the playbooks themselves minimal — just a list of which roles to apply. This separation means I can reuse the `docker` role in any future project, test roles independently, and onboard new contributors easily since the structure is self-documenting.

---

## 2. Roles Documentation

### Common Role

- **Purpose**: Prepares the server with essential system packages, updates the apt cache, and sets the timezone.
- **Variables**:
  - `common_packages` — list of packages to install (curl, git, vim, htop, wget, etc.)
  - `common_timezone` — timezone to set (default: `UTC`)
- **Handlers**: None
- **Dependencies**: None

### Docker Role

- **Purpose**: Installs Docker CE from the official Docker repository, ensures the service is running/enabled, and adds the specified user to the `docker` group.
- **Variables**:
  - `docker_user` — user to add to docker group (default: `vagrant`)
  - `docker_packages` — list of Docker packages to install
- **Handlers**:
  - `restart docker` — restarts the Docker service; triggered when Docker packages are installed/updated
- **Dependencies**: Depends on `common` role (run before it in playbooks)

### App Deploy Role

- **Purpose**: Logs in to Docker Hub, pulls the application image, runs it as a container with proper port mapping and restart policy, then verifies the app is healthy.
- **Variables**:
  - `app_name` — application name (default: `devops-app`)
  - `app_port` — port to expose (default: `5000`)
  - `app_container_name` — container name
  - `app_restart_policy` — Docker restart policy (default: `unless-stopped`)
  - `app_env` — environment variables for the container
  - `docker_image`, `docker_image_tag`, `dockerhub_username`, `dockerhub_password` — defined in Vault
- **Handlers**:
  - `restart app container` — restarts the application container
- **Dependencies**: Depends on `docker` role (Docker must be installed)

---

## 3. Idempotency Demonstration

### First Run (`ansible-playbook playbooks/provision.yml`)

```
PLAY [Provision web servers] *****************************************************

TASK [Gathering Facts] ***********************************************************
ok: [devops-vm]

TASK [common : Update apt cache] *************************************************
ok: [devops-vm]

TASK [common : Install common packages] ******************************************
changed: [devops-vm]

TASK [common : Set timezone] *****************************************************
ok: [devops-vm]

TASK [docker : Install prerequisites for Docker repository] **********************
ok: [devops-vm]

TASK [docker : Create keyrings directory] ****************************************
ok: [devops-vm]

TASK [docker : Add Docker GPG key] ***********************************************
changed: [devops-vm]

TASK [docker : Add Docker repository] ********************************************
changed: [devops-vm]

TASK [docker : Install Docker packages] ******************************************
changed: [devops-vm]

TASK [docker : Ensure Docker service is running and enabled] *********************
ok: [devops-vm]

TASK [docker : Add user to docker group] *****************************************
changed: [devops-vm]

TASK [docker : Install python3-docker for Ansible docker modules] ****************
changed: [devops-vm]

RUNNING HANDLER [docker : restart docker] ****************************************
changed: [devops-vm]

PLAY RECAP ***********************************************************************
devops-vm    : ok=13   changed=7    unreachable=0    failed=0    skipped=0
```

### Second Run (`ansible-playbook playbooks/provision.yml`)

```
PLAY [Provision web servers] *****************************************************

TASK [Gathering Facts] ***********************************************************
ok: [devops-vm]

TASK [common : Update apt cache] *************************************************
ok: [devops-vm]

TASK [common : Install common packages] ******************************************
ok: [devops-vm]

TASK [common : Set timezone] *****************************************************
ok: [devops-vm]

TASK [docker : Install prerequisites for Docker repository] **********************
ok: [devops-vm]

TASK [docker : Create keyrings directory] ****************************************
ok: [devops-vm]

TASK [docker : Add Docker GPG key] ***********************************************
ok: [devops-vm]

TASK [docker : Add Docker repository] ********************************************
ok: [devops-vm]

TASK [docker : Install Docker packages] ******************************************
ok: [devops-vm]

TASK [docker : Ensure Docker service is running and enabled] *********************
ok: [devops-vm]

TASK [docker : Add user to docker group] *****************************************
ok: [devops-vm]

TASK [docker : Install python3-docker for Ansible docker modules] ****************
ok: [devops-vm]

PLAY RECAP ***********************************************************************
devops-vm    : ok=12   changed=0    unreachable=0    failed=0    skipped=0
```

### Analysis

**First run**: 7 tasks changed — these installed new packages (common packages, Docker GPG key, Docker repo, Docker packages, python3-docker), added the user to the docker group, and the Docker restart handler executed because Docker was newly installed.

**Second run**: 0 tasks changed — every task returned "ok" because the desired state was already achieved. Packages are already installed (`state: present`), the GPG key already exists, the Docker service is already running, and the user is already in the docker group. The handler did NOT run because no task notified it (nothing changed).

**What makes the roles idempotent**: Every task uses declarative state modules (`apt` with `state: present`, `service` with `state: started`, `user` with `append: yes`). These modules check current state before acting and only make changes when necessary.

---

## 4. Ansible Vault Usage

### How credentials are stored

Sensitive data (DockerHub username/password, app configuration) is stored in `inventory/group_vars/all.yml`, encrypted with Ansible Vault. This file is safe to commit to version control because it's encrypted with AES-256.

### Vault password management

The vault password is stored in a `.vault_pass` file (added to `.gitignore`). Due to the mounted filesystem not supporting `chmod 600`, `ansible.cfg` references the password file at an absolute path (`/tmp/.vault_pass`). When running playbooks, use `ANSIBLE_CONFIG=$PWD/ansible.cfg` to load the config, or pass `--vault-password-file /tmp/.vault_pass` explicitly. Alternatively, `--ask-vault-pass` can be used at runtime.

### Encrypted file example

```
$ cat inventory/group_vars/all.yml
$ANSIBLE_VAULT;1.1;AES256
65373735616431663364353939343031313535373535336533666365643339646233336162336138
3462636636303335613733356266643239646338376533650a316664363538376566353537613237
...
```

The file is completely opaque without the vault password.

### Why Ansible Vault is important

Without Vault, credentials would be stored in plaintext YAML files, visible in version control history. Vault encrypts them at rest so they can be versioned alongside the code without exposing secrets. This is critical for CI/CD pipelines and team collaboration.

---

## 5. Deployment Verification

### Deploy playbook output

```
PLAY [Deploy application] ********************************************************

TASK [Gathering Facts] ***********************************************************
ok: [devops-vm]

TASK [app_deploy : Log in to Docker Hub] *****************************************
changed: [devops-vm]

TASK [app_deploy : Pull Docker image] ********************************************
changed: [devops-vm]

TASK [app_deploy : Stop existing container] **************************************
ok: [devops-vm]

TASK [app_deploy : Run application container] ************************************
changed: [devops-vm]

TASK [app_deploy : Wait for application to be ready] *****************************
ok: [devops-vm]

TASK [app_deploy : Verify health endpoint] ***************************************
ok: [devops-vm]

TASK [app_deploy : Display health check result] **********************************
ok: [devops-vm] => {
    "health_check.json": {
        "status": "healthy",
        "timestamp": "2026-02-25T12:28:07.757Z",
        "uptime_seconds": 5
    }
}

RUNNING HANDLER [app_deploy : restart app container] *****************************
changed: [devops-vm]

PLAY RECAP ***********************************************************************
devops-vm    : ok=9    changed=4    unreachable=0    failed=0    skipped=0
```

### Container status

```
$ docker ps
CONTAINER ID   IMAGE                                    COMMAND          STATUS       PORTS                    NAMES
72b86a1b60e9   graymansion/devops-info-service:latest   "python app.py"  Up 8 secs    0.0.0.0:5000->5000/tcp   devops-app
```

### Health check

```
$ curl http://192.168.121.159:5000/health
{
    "status": "healthy",
    "timestamp": "2026-02-25T12:28:23.715Z",
    "uptime_seconds": 13
}
```

### Main endpoint

```
$ curl http://192.168.121.159:5000/
{
    "service": {
        "name": "devops-info-service",
        "version": "1.0.0",
        "description": "DevOps course info service",
        "framework": "FastAPI"
    },
    "system": {
        "hostname": "72b86a1b60e9",
        "platform": "Linux",
        ...
    },
    ...
}
```

### Handler execution

The `restart app container` handler fired because the "Run application container" task created a new container (changed state), triggering the handler via `notify`.

---

## 6. Key Decisions

### Why use roles instead of plain playbooks?

Roles enforce a standard directory structure that separates tasks, handlers, defaults, and templates. This makes the code self-documenting and allows independent development and testing of each component.

### How do roles improve reusability?

The `docker` role can be dropped into any project that needs Docker installed — it uses variables for customization (user, packages) and doesn't contain project-specific logic. Similarly, `common` is a generic base role usable across all servers.

### What makes a task idempotent?

A task is idempotent when it checks the current state before acting and only makes changes to reach the desired state. Ansible's declarative modules (e.g., `apt: state=present`) handle this automatically — they don't reinstall packages that already exist.

### How do handlers improve efficiency?

Handlers run only once at the end of a play, even if notified multiple times. This prevents unnecessary service restarts — for example, if multiple Docker-related tasks change, Docker only restarts once rather than after each task.

### Why is Ansible Vault necessary?

Vault encrypts sensitive data (passwords, API keys) so it can be safely committed to version control. Without it, secrets would be in plaintext, visible to anyone with repository access and in git history forever.

---

## 7. Challenges

- **Fish shell**: Heredoc syntax (`<< EOF`) doesn't work in fish, requiring alternative methods for creating multi-line files.
- **group_vars location**: Ansible's `group_vars/` must be alongside the inventory directory (not the project root) when using a subdirectory-based inventory path. Moved `group_vars/` into `inventory/`.
