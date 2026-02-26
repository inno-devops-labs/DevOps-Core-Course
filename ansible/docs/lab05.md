# LAB05 --- Ansible Fundamentals

## 1. Architecture Overview

### Ansible Version

    ansible [core 2.20.3]

### Target Infrastructure

-   Cloud Provider: Yandex Cloud
-   VM OS: Ubuntu 24.04 LTS
-   Public IP: 93.77.185.128
-   SSH User: ubuntu
-   Docker Engine installed via Ansible role

### Project Structure

    ansible/
    ├── inventory/
    │   └── hosts.ini
    ├── roles/
    │   ├── common/
    │   ├── docker/
    │   └── app_deploy/
    ├── playbooks/
    │   ├── provision.yml
    │   └── deploy.yml
    ├── group_vars/
    │   └── all.yml (encrypted with Vault)
    ├── ansible.cfg
    └── docs/
        └── LAB05.md

### Why Roles Instead of Monolithic Playbooks?

Roles isolate logic into reusable components: - common --- base system
configuration - docker --- Docker installation - app_deploy ---
application deployment

Benefits: - Reusability - Maintainability - Separation of concerns -
Scalability

------------------------------------------------------------------------

## 2. Roles Documentation

### Role: common

Purpose: - Update apt cache - Install essential packages - Configure
timezone

Variables:

``` yaml
common_packages:
  - python3-pip
  - curl
  - git
  - vim
  - htop

common_timezone: "UTC"
```

Idempotent Modules Used: - apt - timezone

------------------------------------------------------------------------

### Role: docker

Purpose: Install and configure Docker Engine from official repository.

Variables:

``` yaml
docker_user: "ubuntu"
docker_packages:
  - docker-ce
  - docker-ce-cli
  - containerd.io
```

Handler:

``` yaml
- name: Restart Docker
  service:
    name: docker
    state: restarted
```

------------------------------------------------------------------------

### Role: app_deploy

Purpose: Deploy containerized FastAPI application securely using Docker
and Ansible Vault.

Vault Variables:

``` yaml
dockerhub_username: "darriyan0"
dockerhub_password: "********"
app_name: "app_python"
docker_image: "{{ dockerhub_username }}/{{ app_name }}"
docker_image_tag: "latest"
app_port: 5000
app_container_name: "{{ app_name }}"
```

Tasks: - Docker login - Pull image - Remove old container - Run new
container - Wait for port - Verify health endpoint

------------------------------------------------------------------------

## 3. Idempotency Demonstration

First Run:

    PLAY RECAP
    ok=12 changed=1 unreachable=0 failed=0

Second Run:

    PLAY RECAP
    ok=12 changed=0 unreachable=0 failed=0

Explanation: Ansible modules enforce desired state and perform no
changes when the system already matches configuration.

------------------------------------------------------------------------

## 4. Ansible Vault Usage

Encrypted file header example:

    $ANSIBLE_VAULT;1.1;AES256

Playbook executed with:

    ansible-playbook playbooks/deploy.yml --vault-password-file ./.vault_pass

Vault ensures secure credential management.

------------------------------------------------------------------------

## 5. Deployment Verification

Deploy Result:

    PLAY RECAP
    ok=9 changed=4 unreachable=0 failed=0

Container Status:

    CONTAINER ID   IMAGE                         STATUS              PORTS                    NAMES
    79d405f8e48c   darriyan0/app_python:latest   Up About a minute   0.0.0.0:5000->5000/tcp   app_python

Health Check:

``` json
{
  "status": "healthy",
  "uptime_seconds": 70
}
```

Application accessible at: http://93.77.185.128:5000

------------------------------------------------------------------------

## 6. Key Decisions

-   Roles improve modularity and reusability.
-   Idempotency achieved through declarative modules.
-   Handlers prevent unnecessary service restarts.
-   Ansible Vault protects sensitive credentials.

------------------------------------------------------------------------

## 7. Conclusion

The lab demonstrates: - Role-based architecture - Idempotent
provisioning - Docker automation - Secure credential management -
Application deployment with health verification
