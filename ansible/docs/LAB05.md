# LAB05 — Ansible Fundamentals

## 1. Architecture Overview

- **Ansible Version:** 2.16+
- **Target OS:** Ubuntu 24.04 LTS
- **Cloud Provider:** Yandex Cloud
- **Application:** DevOps Info Service (FastAPI)
- **Container Runtime:** Docker

This lab implements a fully automated, role-based infrastructure provisioning and container deployment system using Ansible.

### Why Roles?

Roles were used instead of monolithic playbooks to achieve:

- Modularity
- Reusability
- Separation of concerns
- Clean project structure
- Easier scalability and maintenance

---

## 2. Role Structure

### common role
Purpose: Basic system preparation

Tasks:
- Update APT cache
- Install essential packages (curl, git, vim, htop, python3-pip)
- Configure timezone

Idempotency ensured using:
- `apt` module with `state: present`
- `timezone` module

---

### docker role
Purpose: Install and configure Docker

Tasks:
- Install Docker from Ubuntu repository
- Enable and start docker service
- Add user to docker group
- Install python3-docker for Ansible Docker modules

Handlers:
- Restart Docker service (if needed)

All tasks are state-based and idempotent.

---

### web_app role
Purpose: Deploy containerized application securely

Tasks:
- Pull Docker image
- Remove old container if exists
- Run container with restart policy
- Wait for application port
- Perform health check via HTTP

Security:
- Docker Hub credentials stored in encrypted Vault file
- `no_log: true` used for sensitive tasks

---

## 3. Idempotency Demonstration

### First Run

Initial execution resulted in multiple `changed` tasks because packages and services were installed.

### Second Run

Second execution showed:


changed=0


This confirms idempotency.

Idempotency is achieved by:
- Using declarative modules
- Avoiding raw shell commands
- Defining desired system state explicitly

---

## 4. Application Deployment Verification

After deployment:

- Container is running (`docker ps`)
- Port 5000 is exposed publicly
- Health endpoint returns HTTP 200
- Root endpoint returns system metadata

Public URL:

http://93.77.190.119:5000

Health endpoint:

http://93.77.190.119:5000/health

---

## 5. Ansible Vault

Sensitive variables are stored in:


group_vars/all.yml


File is encrypted using:


$ANSIBLE_VAULT;1.1;AES256


Vault ensures:
- Secrets are not stored in plaintext
- Safe version control
- Secure automation

---

## 6. Key DevOps Principles Applied

- Infrastructure as Code
- Idempotent configuration management
- Secure secret management
- Containerized deployment
- Automated verification
- Role-based modular architecture

---

## 7. Conclusion

The system successfully provisions infrastructure, installs Docker, and deploys a containerized application using Ansible roles.

The solution is:

- Idempotent
- Secure
- Modular
- Reproducible
- Production-ready
