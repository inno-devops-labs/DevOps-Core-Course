# LAB05 — Ansible Fundamentals (Role-Based)

## 1. Architecture Overview

- **Ansible version used:** Ansible Core 2.17.8.
- **Control node:** Windows 10 + Docker Desktop (Ansible executed in container).
- **Target VM:** Ubuntu 22.04/24.04 VM from Lab 4 (cloud), connected via SSH.
- **Role structure:** Three roles are used:
  - `common` - baseline OS preparation
  - `docker` - Docker engine installation and service setup
  - `app_deploy` - Dockerized app deployment and health verification
- **Why roles instead of one large playbook:** Roles isolate responsibilities, keep playbooks clean, and make each part reusable.

## 2. Roles Documentation

### Role: `common`

- **Purpose:** Prepare the system with required base packages and timezone.
- **Variables (defaults):**
  - `common_packages` - essential packages list (`curl`, `git`, `python3-pip`, etc.)
  - `common_timezone` - default `UTC`
- **Handlers:** None.
- **Dependencies:** `community.general` collection (for timezone module).

### Role: `docker`

- **Purpose:** Install Docker from the official Docker APT repository and prepare runtime access.
- **Variables (defaults):**
  - `docker_arch_map`, `docker_arch`
  - `docker_packages` (`docker-ce`, `docker-ce-cli`, `containerd.io`, plugins)
  - `docker_python_package` (`python3-docker`)
  - `docker_user` (user added to `docker` group)
- **Handlers:**
  - `restart docker` - restarts Docker service when package changes require it.
- **Dependencies:** Uses Ansible built-in modules; installs `python3-docker` on target host for Docker-related modules.

### Role: `app_deploy`

- **Purpose:** Authenticate to Docker Hub, pull image, replace container, and verify app health.
- **Variables (defaults):**
  - `app_name`, `docker_image`, `docker_image_tag`
  - `app_port`, `app_container_name`
  - `app_restart_policy`, `app_env`
  - `app_health_path`, `app_wait_timeout`
  - Vaulted vars: `dockerhub_username`, `dockerhub_password`
- **Handlers:**
  - `restart app container` - restarts running container when deployment task triggers notify.
- **Dependencies:** `community.docker` collection.

## 3. Idempotency Demonstration

### First run (`playbooks/provision.yml`)

```text
PLAY [Provision web servers]
...
TASK [common : Update apt cache] changed
TASK [common : Install common packages] changed
TASK [common : Configure timezone] changed
TASK [docker : Download Docker official GPG key] changed
TASK [docker : Add Docker APT repository] changed
TASK [docker : Update apt cache after Docker repo changes] changed
TASK [docker : Install Docker engine and CLI packages] changed
TASK [docker : Add target user to docker group] changed
RUNNING HANDLER [docker : restart docker] changed
...
PLAY RECAP
lab5-vm : ok=14 changed=9 unreachable=0 failed=0 skipped=0
```

### Second run (`playbooks/provision.yml`)

```text
PLAY [Provision web servers]
...
TASK [common : Update apt cache] ok
TASK [common : Install common packages] ok
TASK [common : Configure timezone] ok
TASK [docker : Download Docker official GPG key] ok
TASK [docker : Add Docker APT repository] ok
TASK [docker : Install Docker engine and CLI packages] ok
TASK [docker : Add target user to docker group] ok
TASK [docker : Update apt cache after Docker repo changes] skipping
...
PLAY RECAP
lab5-vm : ok=12 changed=0 unreachable=0 failed=0 skipped=1
```

### Analysis

- On the first run, resources are created/configured to match desired state (packages, repo, Docker service, group membership).
- On the second run, Ansible modules compare desired and current state and skip unnecessary changes, proving idempotent behavior.
- Idempotency is achieved by stateful modules (`apt`, `service`, `user`, `docker_container`) instead of ad-hoc shell commands.

## 4. Ansible Vault Usage

- Credentials are stored in `group_vars/all.yml` encrypted via Ansible Vault.
- Vault password is entered interactively (`--ask-vault-pass`) or provided via local password file that is ignored by Git.
- Tasks containing credentials use `no_log: true` to prevent secret leakage in logs.

### Encrypted file proof

```text
$ANSIBLE_VAULT;1.1;AES256
64383638346636396532383762376239633430663933613638326235653962353634323766343664
3436646365333032316364663736356565616462353663310a303061333835663866303562323132
65356163313437653263333138366561633533646662336634393333313737336439326132323666
```

### Why Vault is important

- Secrets can be committed safely only in encrypted form.
- Team members can share infrastructure code without exposing credentials.
- It reduces accidental secret leakage in repo history and CI logs.

## 5. Deployment Verification

### Deployment run (`playbooks/deploy.yml`)

```text
PLAY [Deploy application]
...
TASK [app_deploy : Log in to Docker Hub] changed
TASK [app_deploy : Pull application image] changed
TASK [app_deploy : Run application container] changed
TASK [app_deploy : Wait for app port to be ready] ok
TASK [app_deploy : Verify health endpoint] ok
RUNNING HANDLER [app_deploy : restart app container] changed
...
PLAY RECAP
lab5-vm : ok=8 changed=4 unreachable=0 failed=0 skipped=2
```

### Container status

```text
lab5-vm | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                                   COMMAND           CREATED          STATUS          PORTS                    NAMES
e45f2bb4472d   tsixphoenix/devops-info-python:latest   "python app.py"   58 seconds ago   Up 49 seconds   0.0.0.0:5000->5000/tcp   devops-info-python
```

### Health check

```text
curl http://89.169.158.161:5000/health
{"status":"healthy","timestamp":"2026-02-24T11:09:07.680263Z","uptime_seconds":14}

curl http://89.169.158.161:5000/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"e45f2bb4472d","platform":"Linux","platform_version":"5.15.0-170-generic","architecture":"x86_64","cpu_count":2,"python_version":"3.13.12"},"runtime":{"uptime_seconds":16,"uptime_human":"0 hours, 0 minutes","current_time":"2026-02-24T11:09:09.533021Z","timezone":"UTC"},"request":{"client_ip":"188.130.155.186","user_agent":"curl/8.16.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}
```

### Handler execution

- Docker role handler: executed when Docker package changes require service restart.
- App deploy handler: executes only when container deployment task reports changes.

## 6. Key Decisions

- **Why use roles instead of plain playbooks?**  
  Roles separate concerns and keep top-level playbooks minimal. This reduces complexity and improves readability as automation grows.

- **How do roles improve reusability?**  
  Roles encapsulate tasks + defaults + handlers. The same role can be reused across environments by changing only inventory and variables.

- **What makes a task idempotent?**  
  Idempotent tasks declare target state (for example, `state: present`, `state: started`) and change only when current state differs.

- **How do handlers improve efficiency?**  
  Handlers run only when notified by changed tasks, so expensive operations (like restarts) are not executed on every run.

- **Why is Ansible Vault necessary?**  
  It allows secure storage of credentials in versioned infrastructure code without exposing plaintext secrets.

## 7. Challenges

- Initial control-node setup on Windows (Ansible-in-Docker + mounted SSH key permissions).
- Correctly configuring Docker repository and architecture mapping.
- Verifying no secret values appear in output logs.

---