# Lab 5 — Ansible Fundamentals Documentation

## 1. Architecture Overview

- **Ansible version:** 2.20.0
- **Target VM OS:** Ubuntu 24.04 LTS
- **Role-based structure:**
  The project uses a modular role-based approach with three main roles: `common`, `docker`, and `app_deploy`. Each role contains tasks, handlers, and default variables to ensure reusability and maintainability.

**Role structure diagram:**

```
ansible/
├── roles/
│ ├── common/
│ ├── docker/
│ └── app_deploy/
├── playbooks/
│ ├── site.yml
│ ├── provision.yml
│ └── deploy.yml
├── inventory/
│ └── hosts.ini
├── group_vars/
│ └── all.yml
└── ansible.cfg
```


**Why roles instead of monolithic playbooks?**
Roles allow modular, reusable, and maintainable automation. Changes can be made in one role without affecting others, and roles can be reused across multiple playbooks or projects.

---

## 2. Roles Documentation

### 2.1 `common` Role

- **Purpose:** System provisioning, including updating apt cache, installing essential packages, and configuring basic system settings.
- **Variables (defaults/main.yml):**
```yaml
  common_packages:
    - python3-pip
    - curl
    - git
    - vim
    - htop
```

- Tasks:
    - Update apt cache
    - Install common packages
- Handlers: None
- Dependencies: None

2.2 `docker` **Role**
- Purpose: Install Docker engine, manage Docker service, and configure user access.
- Variables (defaults/main.yml):
```yaml
docker_user: ubuntu
docker_packages:
  - docker-ce
  - docker-ce-cli
  - containerd.io
```

- Tasks:
    - Add Docker GPG key and repository
    - Install Docker packages
    - Add user to docker group

- Handlers:
    - `restart docker` — triggered if Docker service needs to restart

- Dependencies: None

2.3 `app_deploy` Role
- Purpose: Deploy containerized Python application.
- Variables (vaulted in group_vars/all.yml):
```yaml
dockerhub_username: <vaulted>
dockerhub_password: <vaulted>
app_name: devops-app
docker_image: "{{ dockerhub_username }}/{{ app_name }}"
docker_image_tag: latest
app_port: 5000
app_container_name: "{{ app_name }}"
```

- Tasks:
    - Docker login with vaulted credentials
    - Pull Docker image
    - Stop and remove existing container
    - Run new container with port mapping and restart policy
    - Wait for port to become available
    - Health check via /health endpoint

- Handlers:
    - `restart app container` — triggered if container needs to restart

- Dependencies: Docker must be installed (docker role)

## 3. Idempotency Demonstration

### First Run (provision.yml)
```text
TASK [common : Update apt cache] ... changed
TASK [common : Install common packages] ... changed
TASK [docker : Install Docker packages] ... changed
TASK [docker : Add user to docker group] ... changed
```

### Second Run (provision.yml)
```text
TASK [common : Update apt cache] ... ok
TASK [common : Install common packages] ... ok
TASK [docker : Install Docker packages] ... ok
TASK [docker : Add user to docker group] ... ok
```

### Analysis:

- First run shows changed because packages and users were added.
- Second run shows ok because the desired state is already achieved.
- This confirms idempotency of roles and tasks.

---

## 4. Ansible Vault Usage

- Purpose: Securely store sensitive credentials (Docker Hub username and password).
- Vault file: inventory/group_vars/all.yml
- Vault commands used:

```bash
ansible-vault create inventory/group_vars/all.yml
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

- Vault password management: Prompted interactively during playbook runs. Password not stored in repo.

- Importance: Prevents sensitive data from being exposed in version control or logs.

---

## 5. Deployment Verification

- Playbook run:

```text
TASK [app_deploy : Login to Docker Hub] ... ok
TASK [app_deploy : Pull Docker image] ... ok
TASK [app_deploy : Run app container] ... ok
```

- Container status:

```
yandex-cluod | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                           COMMAND           CREATED          STATUS          PORTS                              NAMES
d55ac5f0abd1   danielambda/devops-app:latest   "python app.py"   47 minutes ago   Up 47 minutes   0.0.0.0:5000->5000/tcp, 8000/tcp   devops-app
```

- Health check:

```bash
 󰘧 curl http://89.169.148.189:5000/health
{"status":"healthy","timestamp":"2026-02-25T17:54:54.118796+00:00","uptime_seconds":2987}
```

- Handler execution:
The `restart app container` handler triggers only if the container needs a restart.

---

## 6. Key Decisions

- Why use roles instead of plain playbooks?
    Roles improve modularity, reusability, and maintainability; tasks are organized logically.

- How do roles improve reusability?
    Each role can be used in multiple playbooks or projects without rewriting tasks.

- What makes a task idempotent?
    Tasks use stateful modules (`apt`, `service`, `docker_container`) to ensure repeated runs produce the same outcome.

- How do handlers improve efficiency?
    Handlers run only when triggered, reducing unnecessary service restarts and optimizing playbook execution.

- Why is Ansible Vault necessary?
    Vault encrypts sensitive credentials (like Docker Hub passwords), allowing secure storage in version control.

---

## 7. Challenges (Optional)
- Initial confusion with group_vars location; fixed by placing it under inventory/.
- Docker image 404 error because image was not pushed to Docker Hub; resolved by building and pushing the image.
- Ensuring idempotency in package installation and Docker tasks.
