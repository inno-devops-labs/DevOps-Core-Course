# Lab 5 — Ansible Fundamentals

## 1. Architecture Overview

### Ansible Version

Command:

```bash
ansible --version
```

`/docs/screenshots/15-ansible-ver.png`

Ansible was installed locally and used as a control node.

### Target Host

Instead of a cloud VM, the local machine was configured as a managed node:

```
Control Node → SSH → localhost
```

SSH server (`openssh-server`) was installed and enabled so Ansible could connect to the same machine via SSH, simulating a real server environment.

`/docs/screenshots/17-ssh.png`

This approach is common for development and testing automation.

### Why Roles Instead of a Single Playbook?

Roles provide:

* Modular structure
* Reusability across projects
* Separation of concerns
* Easier testing and maintenance
* Industry-standard organization

## 2. Project Structure

Command:

```bash
tree ansible/
```

Structure:

```
ansible/
├── inventory/
├── roles/
│   ├── common/
│   ├── docker/
│   └── app_deploy/
├── playbooks/
├── group_vars/
├── ansible.cfg
└── docs/
```

## 3. Inventory Configuration

Inventory file:

`inventory/hosts.ini`

```
[webservers]
local ansible_host=127.0.0.1 ansible_user=kapi ansible_connection=ssh

[webservers:vars]
ansible_python_interpreter=/usr/bin/python3
```

Test connectivity:

```bash
ansible all -m ping
```

`/docs/screenshots/16-ansible-ping.png`

## 4. Role: common (System Provisioning)

Purpose:
Install base utilities required for any server.

Tasks include:

* Updating apt cache
* Installing essential packages

## 5. Role: docker (Docker Installation)

Purpose:
Prepare system for container workloads.

Tasks:

* Install Docker packages
* Enable and start Docker service
* Add user to docker group

Handler:
Restart Docker if configuration changes.

## 6. Idempotency Demonstration

### First Run

```bash
ansible-playbook playbooks/provision.yml
```

Tasks showed `changed` because the system was configured for the first time.

`/docs/screenshots/18-ansible-run1.png`


### Second Run

```bash
ansible-playbook playbooks/provision.yml
```

Tasks returned `ok` — no changes required.

`/docs/screenshots/19-ansible-run2.png`

### Why This Is Important

Idempotency ensures:

* Safe re-execution
* No configuration drift
* Predictable automation
* Reliability in CI/CD pipelines

## 7. Ansible Vault Usage

Sensitive variables were stored securely using Ansible Vault.

Creation command:

```bash
ansible-vault create group_vars/all.yml
```

Vault content includes:

* Application configuration
* Container settings

Encrypted file preview:

```bash
cat group_vars/all.yml
```

`/docs/screenshots/20-ansible-vault.png`

Vault prevents secrets from being exposed in version control.

## 8. Role: app_deploy (Application Deployment)

Purpose:
Deploy containerized application using Docker.

Tasks:

* Run container
* Expose port
* Wait for service readiness
* Perform HTTP health check

Deployment command:

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

`/docs/screenshots/21-ansible-deploy.png`

## 9. Deployment Verification

Check running container:

```bash
docker ps
```

`/docs/screenshots/22-ansible-docker.png`

Health check:

```bash
curl http://127.0.0.1:5000
```

`/docs/screenshots/23-ansible-health.png`

## 10. Key Design Decisions

### Why Use Roles?

Roles isolate responsibilities and allow reuse across environments.

### How Do Roles Improve Reusability?

Each role can be reused independently (e.g., docker role reused in another project).

### What Makes a Task Idempotent?

State-based modules ensure configuration converges to desired state without repetition.

### How Do Handlers Improve Efficiency?

Handlers run only when changes occur, preventing unnecessary service restarts.

### Why Is Ansible Vault Necessary?

It protects credentials and configuration secrets from exposure in repositories.

## 11. Challenges Encountered

* SSH server had to be enabled locally to simulate a remote host.
* Sudo required passwordless configuration for automation.
* Vault variables required explicit inclusion to ensure availability.
* Debugging variable scope helped understand Ansible execution context.

These issues were resolved by configuring SSH keys, sudoers, and structured variable loading.

## 12. Conclusion

This lab demonstrated how Ansible enables reproducible infrastructure configuration using:

* Role-based architecture
* Idempotent provisioning
* Secure secret management with Vault
* Automated container deployment

The environment successfully simulated a production workflow using localhost as a managed node, proving the flexibility of Ansible for both development and real infrastructure.