
# Lab 6 — Advanced Ansible & CI/CD

## Overview

In this lab the Ansible automation created in Lab 5 was extended with advanced infrastructure automation techniques and CI/CD integration.

The environment was migrated from a simple container deployment to a **Docker Compose based architecture**, roles were improved using **blocks and tags**, a safe **wipe logic** was implemented, and the entire deployment process was automated using **GitHub Actions**.

The final system allows automatic deployment of the application to a **remote production server** whenever changes are pushed to the repository.

Technologies used:
- Ansible
- Docker
- Docker Compose
- GitHub Actions
- SSH
- Ansible Vault
- Jinja2 templates

## Task 1 — Blocks & Tags

### Blocks Implementation

Blocks were introduced to group logically related tasks and add centralized error handling.

Example from the docker role:

```yaml
- name: Docker | install block
  tags:
    - docker
    - docker_install
  block:

    - name: Docker | install docker packages
      apt:
        name: "{{ docker_packages }}"
        state: present
        update_cache: true

  rescue:

    - name: Docker | wait before retry
      pause:
        seconds: 10

    - name: Docker | retry install docker packages
      apt:
        name: "{{ docker_packages }}"
        state: present
```

Blocks allow grouping tasks and handling failures in a controlled way.

### Tag Strategy

Tags allow selective execution of tasks.

Tags implemented:

| Tag | Purpose |
|----|----|
| packages | system packages installation |
| docker | docker related tasks |
| docker_install | docker installation only |
| docker_config | docker configuration |
| app_deploy | application deployment |
| compose | docker compose tasks |
| web_app_wipe | application cleanup |

Example usage:

```bash
ansible-playbook playbooks/provision.yml --tags docker
```

Run only docker related tasks.

## Task 2 — Docker Compose Migration

### Why Docker Compose

Docker Compose replaces manual `docker run` commands and provides:

- declarative configuration
- easier service management
- reproducible deployments
- simpler updates

### Role Refactoring

Role `app_deploy` was renamed to:

```
roles/web_app
```

This better represents the role purpose and supports reuse for multiple web applications.

### Docker Compose Template

File:

```
roles/web_app/templates/docker-compose.yml.j2
```

Example template:

```yaml
services:
  {{ app_name }}:
    image: {{ docker_image }}:{{ docker_tag }}
    container_name: {{ app_name }}

    ports:
      - "{{ app_port }}:{{ app_internal_port }}"

    restart: unless-stopped
```

Values are injected using Ansible variables.

### Role Dependencies

File:

```
roles/web_app/meta/main.yml
```

```yaml
dependencies:
  - role: docker
```

This ensures Docker is installed before deploying the application.

### Deployment

Application deployment command:

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

Verification commands:

```bash
docker ps
curl http://89.111.170.95:5000
```

### Screenshots
Tags:
`screenshots/6-1-tags.png`, `screenshots/6-2-tags.png`

First & second run:
`screenshots/6-3-run1.png`, `screenshots/6-4-run2.png`

Working curl:
`screenshots/6-5-curl.png`

## Task 3 — Wipe Logic

### Purpose

Wipe logic enables safe cleanup of an existing deployment before redeploying.

Use cases:

- clean reinstallation
- environment reset
- automation safety

### Implementation

File:

```
roles/web_app/tasks/wipe.yml
```

Example:

```yaml
- name: Wipe web application
  when: web_app_wipe | bool
  tags:
    - web_app_wipe
  block:

    - name: Compose down
      command: docker compose down
      args:
        chdir: "{{ compose_project_dir }}"

    - name: Remove compose file
      file:
        path: "{{ compose_project_dir }}/docker-compose.yml"
        state: absent

    - name: Remove application directory
      file:
        path: "{{ compose_project_dir }}"
        state: absent
```
### Screenshots
Wipe only:
`screenshots/6-6-wipeonly.png`

Clean reinstall:
`screenshots/6-7-reinstall.png`

Safety check:
`screenshots/6-8-safety.png`

## Task 4 — CI/CD with GitHub Actions

### Workflow File

Location:

```
.github/workflows/ansible-deploy.yml
```

Example workflow:

```yaml
name: Ansible Deployment

on:
  push:
    branches:
      - master
      - lab06
    paths:
      - 'ansible/**'

jobs:

  lint:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Install Ansible
        run: pip install ansible ansible-lint

      - name: Run ansible-lint
        run: |
          cd ansible
          ansible-lint playbooks/*.yml

  deploy:
    needs: lint
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_ed25519
          chmod 600 ~/.ssh/id_ed25519
          ssh-keyscan -H "${{ secrets.VM_HOST }}" >> ~/.ssh/known_hosts

      - name: Deploy with Ansible
        run: |
          cd ansible
          echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > vault_pass
          ansible-playbook playbooks/deploy.yml --vault-password-file vault_pass
```

## Testing Results

### SSH Connectivity

```bash
ansible all -m ping
```

Result:

```
prod | SUCCESS => pong
```

### Deployment

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

Application container successfully deployed and accessible.

### Workflow result
https://github.com/kvassoedik/DevOps-Core-Course/actions/runs/23014695994/job/66834837081

## Summary

This lab demonstrated advanced infrastructure automation using Ansible.

Main achievements:

- role refactoring with blocks and tags
- Docker Compose deployment
- safe wipe logic
- automated CI/CD pipeline using GitHub Actions
- deployment to a remote server

The environment can now be deployed automatically and reproducibly through a Git push.

## Time Spent

Approximate time spent: **5-6 hours**