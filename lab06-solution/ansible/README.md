# Ansible Configuration

Advanced Ansible with blocks, tags, error handling, Docker Compose, and CI/CD.

## Requirements

- Ansible 2.16+
- Python 3.8+
- Ansible collections: community.docker, ansible.posix

## Setup

```bash
# Install dependencies
ansible-galaxy collection install -r requirements.yml

# Configure inventory
vim inventory/hosts.ini

# Set variables
vim group_vars/all.yml
```

## Roles

### common
- Updates apt cache
- Installs system packages
- Tags: `packages`, `common`

### docker
- Installs Docker and docker-compose
- Configures Docker daemon
- Tags: `docker_install`, `docker_config`, `docker`

### web_app  
- Deploys application with docker-compose
- Supports wipe logic for clean reinstall
- Depends on: docker role
- Tags: `app_deploy`, `compose`, `web_app_wipe`

## Playbooks

### provision.yml
Common + Docker installation for target servers.

### deploy.yml
Application deployment with docker-compose.

## Wipe Logic

Double-gating mechanism (variable + tag):

```bash
# Only deploy
ansible-playbook playbooks/deploy.yml

# Only wipe  
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true" \
  --tags web_app_wipe

# Clean reinstall (wipe → deploy)
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true"
```

## Variables

**defaults/main.yml** in each role contains role-specific variables.

**group_vars/all.yml** contains global variables.

## CI/CD Integration

GitHub Actions workflow validates Ansible code automatically on push:
- ansible-lint checks
- Playbook syntax validation
- Secrets management support
