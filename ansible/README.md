# Ansible Lab 06: Advanced Ansible & CI/CD

[![Ansible Deployment](https://github.com/j0cos/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/j0cos/DevOps-Core-Course/actions/workflows/ansible-deploy.yml)

## Quick Start

```bash
cd /home/j0cos/innopolis/Devops/DevOps-Core-Course
source .venv/bin/activate
cd ansible
ansible-galaxy collection install -r collections/requirements.yml
set -a
source .env
set +a
```

## Secrets (Ansible Vault)

Sensitive values are stored in `group_vars/all.yml` (encrypted).

```bash
# Edit encrypted secrets
ansible-vault edit group_vars/all.yml

# View encrypted secrets
ansible-vault view group_vars/all.yml

# Re-key vault password
ansible-vault rekey group_vars/all.yml
```

## Playbooks

```bash
# Provision host only
ansible-playbook playbooks/provision.yml

# Deploy web app using Docker Compose
ansible-playbook playbooks/deploy.yml

# Legacy full flow (kept for compatibility)
ansible-playbook playbooks/site.yml

# Check health
ansible-playbook playbooks/health_check.yml
```

## Tags

```bash
ansible-playbook playbooks/provision.yml --list-tags
ansible-playbook playbooks/provision.yml --tags "docker"
ansible-playbook playbooks/provision.yml --tags "docker_install"
ansible-playbook playbooks/provision.yml --tags "docker_config"
ansible-playbook playbooks/provision.yml --skip-tags "common"
ansible-playbook playbooks/provision.yml --tags "packages"
```

## Wipe Logic (Double Gate)

Wipe tasks run only when both are set:
1. variable `web_app_wipe=true`
2. tag `web_app_wipe`

```bash
# Wipe only
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe

# Clean reinstall (wipe -> deploy)
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"
```

## Structure

```text
ansible/
├── group_vars/webservers.yml
├── playbooks/
│   ├── provision.yml
│   ├── deploy.yml
│   ├── site.yml
│   └── health_check.yml
└── roles/
    ├── common/
    ├── docker/
    └── web_app/
        ├── defaults/main.yml
        ├── meta/main.yml
        ├── tasks/main.yml
        ├── tasks/wipe.yml
        └── templates/docker-compose.yml.j2
```
