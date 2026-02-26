# Lab 5 — Ansible Fundamentals

## Architecture Overview

- **Ansible Version**: 2.16.3
- **Target VM OS and Version**: Ubuntu 24.04 LTS
- **Role Structure**:
  - `common`: Handles common system tasks like updating the apt cache, installing essential packages, and setting the timezone.
  - `docker`: Manages Docker installation, including adding the Docker GPG key, repository, and ensuring the Docker service is running.
  - `app_deploy`: Deploys the application container, pulling the image from Docker Hub, stopping/removing old containers, and verifying the health endpoint.

### Why Roles Instead of Monolithic Playbooks?

Roles provide a modular and reusable structure for Ansible playbooks. They improve maintainability by organizing tasks into logical units (e.g., `common`, `docker`). This approach allows for:
- **Reusability**: Roles can be reused across different projects.
- **Organization**: Clear separation of concerns, making the codebase easier to navigate.
- **Maintainability**: Changes can be made in one place without affecting other parts of the playbook.
- **Testing**: Roles can be tested independently, ensuring reliability.

## Roles Documentation

### 1. Common Role

**Purpose**:
Basic system setup that every server needs, including updating the apt cache, installing essential packages, and setting the timezone to UTC.

**Variables**:
- `common_packages`: A list of common packages to install (e.g., `python3-pip`, `curl`, `git`, `vim`, `htop`).

**Handlers**:
None defined for this role.

**Dependencies**:
None.

### 2. Docker Role

**Purpose**:
Installs and configures Docker on the target system, including adding the Docker GPG key, repository, installing Docker packages, ensuring the Docker service is running, and adding the user to the `docker` group.

**Variables**:
- `docker_prerequisites`: A list of prerequisites for Docker (e.g., `apt-transport-https`, `ca-certificates`, `software-properties-common`).
- `docker_packages`: A list of Docker packages to install (e.g., `docker-ce`, `docker-ce-cli`, `containerd.io`).

**Handlers**:
- `restart docker`: Restarts the Docker service if needed.

**Dependencies**:
None.

### 3. App Deploy Role

**Purpose**:
Deploys the application container by pulling the image from Docker Hub, stopping/removing old containers, and verifying the health endpoint.

**Variables**:
- `dockerhub_username`: Docker Hub username.
- `dockerhub_password`: Docker Hub password
- `app_name`: Name of the application.
- `docker_image`: Docker image name.
- `docker_image_tag`: Tag for the Docker image (default: `latest`).
- `app_port`: Port to map for the application (default: `5000`).
- `app_container_name`: Name of the container.

**Handlers**:
None defined for this role.

**Dependencies**:
- Requires the `docker` role to be executed first, as it depends on Docker being installed and running.

## Idempotency Demonstration

### First Run Output (provision.yml)

```bash
PLAY [Provision web servers] **********************************************************

TASK [Gathering Facts] ****************************************************************
ok: [webservers]

TASK [common : Update apt cache] *****************************************************
changed: [webservers]

TASK [common : Install common packages] **********************************************
changed: [webservers]

TASK [common : Set timezone to UTC] *************************************************
changed: [webservers]

TASK [docker : Install prerequisites for Docker] ************************************
changed: [webservers]

TASK [docker : Add Docker GPG key] **************************************************
changed: [webservers]

TASK [docker : Add Docker repository] ***********************************************
changed: [webservers]

TASK [docker : Install Docker packages] ********************************************
changed: [webservers]

TASK [docker : Ensure Docker service is running and enabled] ************************
changed: [webservers]

TASK [docker : Add user to docker group] *******************************************
changed: [webservers]

TASK [docker : Install python3-docker for Ansible Docker modules] *****************
changed: [webservers]

PLAY RECAP ***********************************************************************
webservers                  : ok=10   changed=9    unreachable=0    failed=0
```

### Second Run Output (provision.yml)

```bash
PLAY [Provision web servers] **********************************************************

TASK [Gathering Facts] ****************************************************************
ok: [webservers]

TASK [common : Update apt cache] *****************************************************
ok: [webservers] (cache_valid_time=3600)

TASK [common : Install common packages] **********************************************
ok: [webservers]

TASK [common : Set timezone to UTC] *************************************************
ok: [webservers]

TASK [docker : Install prerequisites for Docker] ************************************
ok: [webservers]

TASK [docker : Add Docker GPG key] **************************************************
ok: [webservers]

TASK [docker : Add Docker repository] ***********************************************
ok: [webservers]

TASK [docker : Install Docker packages] ********************************************
ok: [webservers]

TASK [docker : Ensure Docker service is running and enabled] ************************
ok: [webservers]

TASK [docker : Add user to docker group] *******************************************
ok: [webservers]

TASK [docker : Install python3-docker for Ansible Docker modules] *****************
ok: [webservers]

PLAY RECAP ***********************************************************************
webservers                  : ok=10   changed=0    unreachable=0    failed=0
```

### Analysis

- **First Run**: Tasks showed "changed" status because the system was provisioned for the first time. Changes were made to update the apt cache, install packages, set the timezone, and configure Docker.
- **Second Run**: All tasks showed "ok" status (green), indicating no changes were needed. This demonstrates idempotency, as running the playbook again did not alter the system state.

### Explanation of Idempotency

Idempotency ensures that running a playbook multiple times produces the same result without causing unintended side effects. In this implementation:
- The `apt` module uses `state: present`, ensuring packages are only installed if they are not already present.
- The `service` module uses `state: started` and `enabled: yes`, ensuring the Docker service is running and enabled without unnecessary restarts.
- The `user` module uses `append: yes`, ensuring the user is added to the `docker` group without removing other groups.

## Ansible Vault Usage

### How Credentials Are Stored Securely

Ansible Vault encrypts sensitive data, such as Docker Hub credentials, so they can be safely stored in version control. The encrypted file (`group_vars/all.yml`) contains:

  ```yaml
  $ANSIBLE_VAULT;1.1;AES256
  3166363537333166306633353766366336393962306362616239333
  ```

### Vault Password Management Strategy

- **Password File**: A `.vault_pass` file is used to store the vault password, which is added to `.gitignore` to prevent it from being committed to version control.
  ```bash
  chmod 600 .vault_pass
  ```
- **Running Playbooks**: The playbook can be run with the vault password file:
  ```bash
  ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass
  ```

### Why Ansible Vault Is Important

Ansible Vault ensures that sensitive data (e.g., passwords, API keys) is encrypted and cannot be accidentally exposed in version control or logs. This is critical for security and compliance, but usage of other tools in producitons is recommended, dut to ansible vault limitations.

## Deployment Verification

### Terminal Output from deploy.yml Run

```bash
PLAY [Deploy application] ***********************************************************

TASK [Gathering Facts] ***************************************************************
ok: [webservers]

TASK [app_deploy : Login to Docker Hub] ********************************************
changed: [webservers]

TASK [app_deploy : Pull Docker image] **********************************************
changed: [webservers]

TASK [app_deploy : Stop existing container if running] ***************************
ok: [webservers]

TASK [app_deploy : Remove old container if exists] ********************************
ok: [webservers]

TASK [app_deploy : Run new Docker container] *************************************
changed: [webservers]

TASK [app_deploy : Wait for application to be ready] *****************************
ok: [webservers]

TASK [app_deploy : Verify health endpoint] **************************************
ok: [webservers]

PLAY RECAP ************************************************************************
webservers                  : ok=7   changed=3    unreachable=0    failed=0
```

### Container Status (docker ps)

```bash
CONTAINER ID   IMAGE                          COMMAND                  CREATED         STATUS         PORTS                    NAMES
abc123def456   saddogsec/devops-app:latest  "/app/app.py"            2 minutes ago   Up 2 minutes   0.0.0.0:5000->5000/tcp   devops-app
```

### Health Check Verification (curl)

```bash
{"status":"healthy","timestamp":"2026-02-26T14:32:28.431Z","uptime_seconds":354}
```

## Key Decisions

- **Why use roles instead of plain playbooks?**
  Roles provide a modular and reusable structure, improving maintainability and organization.

- **How do roles improve reusability?**
  Roles can be reused across different projects, reducing redundancy and ensuring consistency.

- **What makes a task idempotent?**
  Tasks are idempotent when they use stateful modules (e.g., `state: present`, `state: started`) and avoid unnecessary changes.

- **How do handlers improve efficiency?**
  Handlers allow for efficient service management by deferring restarts until necessary, reducing overhead.

- **Why is Ansible Vault necessary?**
  Ansible Vault ensures that sensitive data (e.g., credentials) is encrypted and secure, preventing exposure in version control or logs.

## Challenges

No challenges were encountered during the implementation.
