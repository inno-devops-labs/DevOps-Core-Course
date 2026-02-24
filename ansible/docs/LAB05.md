
---

# Lab 5 — Ansible Fundamentals

---

# 1️⃣ Architecture Overview

## Ansible Version

```bash
ansible --version
```

Output:

```
ansible [core 2.20.3]
```

---

## Target VM

* OS: Ubuntu Server (cloud image)
* Python interpreter: `/usr/bin/python3`
* Provisioned previously using Terraform (Lab 4)
* Remote access via SSH with private key authentication

---

## Project Structure

```
ansible/
├── ansible.cfg
├── inventory/
│   └── hosts
├── playbooks/
│   └── site.yml
├── roles/
│   ├── common/
│   ├── docker/
│   └── app_deploy/
└── .env (not committed)
```

---

## Why Roles Instead of a Single Playbook?

Roles provide:

* Clear separation of concerns
* Reusability across projects
* Logical modularization
* Easier debugging and maintenance
* Independent testing of infrastructure layers

Instead of one large monolithic playbook, the infrastructure is divided into:

* `common` → base system configuration
* `docker` → container runtime setup
* `app_deploy` → application deployment logic

This structure follows production-grade DevOps practices.

---

# 2️⃣ Roles Documentation

---

## 🔹 Role: common

### Purpose

Performs base system configuration:

* Updates apt cache
* Upgrades system packages
* Installs essential utilities
* Configures timezone
* Configures system limits

### Idempotency

Uses declarative modules:

```yaml
apt:
  name: package_name
  state: present
```

This ensures:

* Packages are only installed if missing
* Configuration changes are applied only when necessary

---

## 🔹 Role: docker

### Purpose

Installs and configures Docker Engine.

### Tasks Performed

* Install Docker packages
* Enable and start Docker service
* Add user to docker group
* Log into Docker Hub

### Docker Service Verification

From second run:

```
State: running
Enabled: true
```

The service was already active, so no change occurred — demonstrating idempotency.

---

### Docker Login Implementation

```yaml
- name: Log into Docker Hub
  docker_login:
    username: "{{ lookup('env', 'DOCKER_HUB_USERNAME') }}"
    password: "{{ lookup('env', 'DOCKER_HUB_PASSWORD') }}"
    state: present
  become_user: "{{ docker_users[0] }}"
```

This retrieves credentials from environment variables instead of storing them in repository files.

---

## 🔹 Role: app_deploy

### Purpose

Deploys containerized application:

Image:

```
j0cos/devops-info-service:latest
```

Port:

```
5000
```

### Tasks

* Pull Docker image
* Stop existing container
* Deploy new container
* Wait for health endpoint
* Display deployment summary

---

## Running Container Verification

```bash
docker ps
```

Output:

```
CONTAINER ID   IMAGE                              COMMAND           CREATED         STATUS                     PORTS                    NAMES
871be6745962   j0cos/devops-info-service:latest   "python app.py"   4 minutes ago   Up 4 minutes               0.0.0.0:5000->5000/tcp   devops-info-service
```

---

# 3️⃣ Idempotency Demonstration

## First Run

```
PLAY RECAP
lab4-vm : ok=17  changed=9  unreachable=0  failed=0
```

Explanation:

Changes occurred because:

* Docker packages were installed
* System packages were upgraded
* Container was created
* Image was pulled

---

## Second Run

```
PLAY RECAP
lab4-vm : ok=16  changed=3  unreachable=0  failed=0
```

### Why 3 Changes?

The only change came from:

```
TASK [common : Upgrade all packages]
```

The system removed outdated kernel packages:

```
linux-headers-6.8.0-60
linux-image-6.8.0-60-generic
...
```

All infrastructure-related tasks remained idempotent:

* Docker already installed
* Service already running
* Image already present
* Container already configured

This demonstrates convergence toward desired state.

---

# 4️⃣ Secret Management Strategy

Secrets are NOT stored in repository.

Instead:

```
.env (excluded from git)
```

Example:

```
DOCKER_HUB_USERNAME=your_docker_hub_username
DOCKER_HUB_PASSWORD=your_docker_hub_password
```

The playbook retrieves them using:

```yaml
lookup('env', 'DOCKER_HUB_USERNAME')
```

### Why This Is Secure

* `.env` is excluded from Git
* Credentials never appear in playbooks
* `no_log: true` prevents leaking in output
* Compatible with CI/CD pipelines

---

# 5️⃣ Application Verification

Public IP:

```
http://93.77.177.72:5000
```

---

## Root Endpoint

```bash
curl http://93.77.177.72:5000
```

Response:

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "framework": "Flask"
  },
  "system": {
    "architecture": "x86_64",
    "cpu_count": 2,
    "python_version": "3.13.12"
  }
}
```

---

## Health Endpoint

```bash
curl http://93.77.177.72:5000/health
```

Response:

```json
{
  "status": "healthy",
  "timestamp": "...",
  "uptime_seconds": 180
}
```

The health check returned HTTP 200 and confirmed application readiness.

---

# 6️⃣ Key DevOps Decisions

## Why Roles?

Roles provide modular infrastructure layers and allow reuse in future environments.

---

## What Makes a Task Idempotent?

An idempotent task declares desired state instead of executing imperative commands.

Example:

```yaml
service:
  name: docker
  state: started
  enabled: true
```

Running it multiple times does not cause additional changes.

---

## Why Use Environment-Based Secret Injection?

* Avoids committing credentials
* Keeps repository clean
* Works in CI/CD
* Allows runtime injection

---

# 7️⃣ Challenges Faced

1. SSH hostname resolution failed due to environment variables not being exported.
2. Docker login failed due to undefined variables.
3. Learned difference between:

   * Ansible variables
   * OS environment variables
4. Fixed by properly exporting `.env` and using `lookup('env', ...)`.

---

