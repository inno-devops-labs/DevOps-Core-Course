# Lab 5 - Ansible Fundamentals (Local VM from Lab 4)

## 1. Architecture Overview

- Control node: Linux Mint 22.2
- Ansible version: `ansible [core 2.16.3]`
- Target VM: local VirtualBox VM from Lab 4 (`lab04-ubuntu24`)
- Target OS: Ubuntu 24.04.4 LTS
- Access path: `127.0.0.1:2222` (NAT port-forward to guest SSH)

Role-based structure used:

```text
ansible/
├── ansible.cfg
├── inventory/hosts.ini
├── group_vars/all.yml (vault encrypted)
├── playbooks/
│   ├── provision.yml
│   ├── deploy.yml
│   └── site.yml
└── roles/
    ├── common/
    ├── docker/
    └── app_deploy/
```

Why roles: separation of concerns, reusability, cleaner playbooks, and easier testing/idempotency analysis.

---

## 2. Roles Documentation

### `common`

- Purpose: baseline system setup (apt cache, common packages, timezone files).
- Key variables:
  - `common_packages`
  - `common_timezone`
- Handlers: none.
- Dependencies: none.

### `docker`

- Purpose: install and configure Docker Engine from official Docker apt repo.
- Key variables:
  - `docker_user`
  - `docker_arch_map`
  - `docker_packages`
- Handlers:
  - `restart docker`
- Dependencies: `common` role should run first to ensure baseline tooling.

### `app_deploy`

- Purpose: pull application image and run containerized app with health verification.
- Key variables:
  - `dockerhub_username`
  - `dockerhub_password`
  - `dockerhub_login_enabled`
  - `docker_image`
  - `docker_image_tag`
  - `app_port`
  - `app_container_name`
  - `app_restart_policy`
  - `app_environment`
- Handlers:
  - `restart app container`
- Dependencies: Docker engine must already be installed/running (`docker` role).

---

## 3. Idempotency Demonstration

### First `provision.yml` run

```text
PLAY RECAP *********************************************************************
lab04-local                : ok=13   changed=3    unreachable=0    failed=0    skipped=0
```

Changed tasks were Docker install and user group update (plus Docker handler).

### Second `provision.yml` run

```text
PLAY RECAP *********************************************************************
lab04-local                : ok=12   changed=0    unreachable=0    failed=0    skipped=0
```

No changes were required on second run, confirming idempotency.

Why idempotent:
- Used state-based modules (`apt state=present`, `service state=started`, `user append=true`, `file state=link`).
- Desired state is declared, not imperative shell steps.

---

## 4. Ansible Vault Usage

Sensitive variables are stored in encrypted `group_vars/all.yml`.

Where to put Docker Hub credentials:

1. Edit: `ansible/group_vars/all.yml` (vault-encrypted file)
2. Command:
   ```bash
   cd ansible
   ansible-vault edit group_vars/all.yml --vault-password-file .vault_pass
   ```
3. Fill these fields:
   ```yaml
   dockerhub_username: "YOUR_DOCKERHUB_USERNAME"
   dockerhub_password: "YOUR_DOCKERHUB_ACCESS_TOKEN"
   dockerhub_login_enabled: true
   ```

Encrypted file header evidence:

```text
$ANSIBLE_VAULT;1.1;AES256
373261366639656261306162626165383439623535316639363235393761613965...
```

Vault password strategy:
- Local vault password file: `ansible/.vault_pass`
- `ansible/.vault_pass` is excluded in `.gitignore`
- Playbook uses `vault_password_file = .vault_pass` from `ansible.cfg`

Why Vault matters: credentials and sensitive deployment variables stay encrypted at rest in Git.

---

## 5. Deployment Verification

### Deploy run (`deploy.yml`)

```text
PLAY RECAP *********************************************************************
lab04-local                : ok=10   changed=5    unreachable=0    failed=0    skipped=0
```

### Container status (`docker ps`)

```text
CONTAINER ID   IMAGE                                COMMAND           STATUS          PORTS                    NAMES
f8b231c4aa74   lanebo1/devops-info-service:latest   "python app.py"   Up 8 seconds    0.0.0.0:5000->5000/tcp   devops-app
```

### Health check (`/health`)

```json
{"status":"healthy","timestamp":"2026-02-26T22:19:07.185273+00:00","uptime_seconds":6}
```

### Root endpoint (`/`)

```json
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"6d2a3c776177","platform":"Linux","architecture":"x86_64"}}
```

Handler execution:
- `app_deploy : restart app container` executed after initial container creation.
- `app_deploy : Login to Docker Hub` executed successfully with Vault credentials.

---

## 6. Key Decisions

### Why use roles instead of plain playbooks?
Roles enforce modular boundaries. Provisioning and deployment logic stay isolated and maintainable as complexity grows.

### How do roles improve reusability?
Defaults and tasks are encapsulated by function (`common`, `docker`, `app_deploy`), so the same role can be reused across hosts and future labs with variable overrides.

### What makes a task idempotent?
Idempotent tasks declare end-state, and repeated execution converges to the same state with zero additional changes.

### How do handlers improve efficiency?
Handlers run only when notified by changed tasks, avoiding unnecessary service restarts on every playbook run.

### Why is Ansible Vault necessary?
It keeps credentials encrypted in repository history and allows safe collaboration without exposing secrets.

---

## 7. Challenges and Fixes

- First provisioning attempt failed due small root filesystem (cloud image default).
  - Fix: resized VDI to 20 GB and rebooted; root filesystem expanded to ~19 GB.

---
