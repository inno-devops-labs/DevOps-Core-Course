# Lab 05 — Ansible Fundamentals

## 1. Architecture Overview

### Ansible version used

```bash
ansible --version
```

```text
ansible [core 2.20.2]
python version = 3.14.3
```

### Target VM OS and version

```bash
ansible webservers -a "uname -a"
```

```text
Linux fv48ri0v9h7addr29frj ... Ubuntu 22.04.5 LTS ...
```

Connectivity check:

```bash
ansible all -m ping
```

```text
lab05-vm | SUCCESS => {"ping": "pong"}
```

### Role structure explanation

Project layout:

```text
ansible/
├── ansible.cfg
├── inventory/hosts.ini
├── group_vars/all.yml        # encrypted with Ansible Vault
├── playbooks/
│   ├── provision.yml
│   ├── deploy.yml
│   └── site.yml
└── roles/
    ├── common/
    ├── docker/
    └── app_deploy/
```

### Why roles instead of monolithic playbooks

Roles make the automation modular and reusable: `common` handles baseline OS setup, `docker` handles runtime installation, and `app_deploy` handles application rollout. This separation reduces duplication, keeps playbooks clean, and makes troubleshooting easier because each concern has its own defaults/tasks/handlers.

---

## 2. Roles Documentation

### Role: `common`

- **Purpose:** baseline system provisioning for every server.
- **Variables (defaults):**
  - `common_packages` (list of essential packages: `python3-pip`, `curl`, `git`, `vim`, `htop`, etc.).
- **Handlers:** none.
- **Dependencies:** no direct role dependencies.

### Role: `docker`

- **Purpose:** install and configure Docker Engine on Ubuntu hosts.
- **Variables (defaults):**
  - `docker_user`
  - `docker_packages`
  - `docker_apt_arch_map`, `docker_apt_arch`
  - `docker_repo`
- **Handlers:**
  - `restart docker` (triggered when key/repo/packages change).
- **Dependencies:** relies on apt and systemd, and is intended to run after baseline common setup.

### Role: `app_deploy`

- **Purpose:** deploy containerized Python app with Vault-backed configuration and runtime checks.
- **Variables (defaults + vaulted overrides):**
  - `dockerhub_username`, `dockerhub_password` (from Vault)
  - `docker_image`, `docker_image_tag`
  - `app_name`, `app_port`, `app_internal_port`, `app_container_name`
  - `app_restart_policy`, `app_environment`, `app_healthcheck_path`
- **Handlers:**
  - `restart app container`.
- **Dependencies:** requires Docker service and Python Docker SDK on target host (provided by `docker` role).

---

## 3. Idempotency Demonstration

### First `provision.yml` run

```bash
ansible-playbook playbooks/provision.yml
```

Key result:

```text
PLAY RECAP
lab05-vm : ok=12 changed=8 failed=0
```

Changed tasks on first run included apt cache update, package installation, Docker key/repo setup, Docker package installation, user group update, and Docker handler execution.

### Second `provision.yml` run

```bash
ansible-playbook playbooks/provision.yml
```

Key result:

```text
PLAY RECAP
lab05-vm : ok=11 changed=0 failed=0
```

### Analysis

The first run changed the host from initial state to desired state. The second run produced zero changes, proving idempotency. This is achieved by state-based modules (`apt state=present`, `service state=started enabled=true`, `file state=directory`, `user append=true`) instead of imperative shell commands.

---

## 4. Ansible Vault Usage

### How credentials are stored securely

Sensitive values are stored in `group_vars/all.yml`, encrypted with Ansible Vault.

Encrypted file proof:

```text
$ANSIBLE_VAULT;1.1;AES256
...
```

### Vault password management strategy

- Local password file: `ansible/.vault_pass`
- `ansible.cfg` uses `vault_password_file = .vault_pass`
- `.vault_pass` is excluded from Git via root `.gitignore`

### Decrypted view verification

```bash
ansible-vault view group_vars/all.yml --vault-password-file .vault_pass
```

Vaulted variables include Docker Hub credential fields and app configuration. In this lab run placeholders (`CHANGE_ME`) are used for credentials; role logic performs registry login only when real credentials are provided.

---

## 5. Deployment Verification

### Deployment playbook run

```bash
ansible-playbook playbooks/deploy.yml
```

Key result:

```text
PLAY RECAP
lab05-vm : ok=9 changed=5 skipped=3 failed=0
```

### Container status proof

```bash
ansible webservers -a "docker ps"
```

```text
CONTAINER ID   IMAGE              COMMAND                 ...   NAMES
...            python:3.12-slim   "python3 /app/app.py"  ...   devops-app
```

### Health check verification

```bash
curl http://158.160.162.138:5000/health
```

```text
{"status": "healthy", "uptime_seconds": ...}
```

Root endpoint:

```bash
curl http://158.160.162.138:5000/
```

```text
{"message": "Hello from Ansible deployed app", ...}
```

### Handler execution

The `app_deploy` handler (`restart app container`) was triggered on initial deploy after app source copy.

---

## 6. Key Decisions and Challenges

- Chose role-based layout exactly as requested by the lab to keep responsibilities separated.
- Implemented Docker installation using official Ubuntu repository and keyring approach.
- Added conditional Docker Hub login so the role remains secure and reusable for private images while still working with public images.
- Verified idempotency with repeated provisioning runs and documented both outcomes.
