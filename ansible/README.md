[![Ansible Deployment](https://github.com/4hellboy4/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/4hellboy4/DevOps-Core-Course/actions/workflows/ansible-deploy.yml)

# Ansible Configuration for Lab 06

This directory contains Ansible playbooks and roles for managing the DevOps lab infrastructure with Docker Compose deployment, blocks/tags, wipe logic, and CI/CD integration.

## Prerequisites

```bash
# Install Ansible (macOS)
brew install ansible

# Install required collections
ansible-galaxy collection install community.docker community.general
```

## Structure

```
ansible/
├── ansible.cfg              # Ansible configuration
├── inventory/
│   ├── hosts.yml            # Inventory file
│   └── group_vars/
│       ├── all.yml          # Variables for all hosts
│       └── secrets.yml      # Vault-encrypted secrets
├── playbooks/
│   ├── ping.yml             # Test connectivity
│   ├── provision.yml        # Provision server (common + docker)
│   ├── deploy.yml           # Deploy application (web_app role)
│   ├── full_setup.yml       # Full setup (all roles)
│   ├── docker.yml           # Install Docker (standalone)
│   └── deploy_app.yml       # Deploy app (standalone, legacy)
├── roles/
│   ├── common/              # System packages and user config
│   ├── docker/              # Docker installation and config
│   └── web_app/             # Docker Compose app deployment
│       ├── defaults/        # Default variables
│       ├── meta/            # Role dependencies
│       ├── tasks/           # Deployment and wipe tasks
│       └── templates/       # Docker Compose Jinja2 template
├── docs/
│   └── LAB06.md             # Lab 6 documentation
└── README.md                # This file
```

## Usage

### Provision Server

```bash
ansible-playbook playbooks/provision.yml
```

### Deploy Application

```bash
ansible-playbook playbooks/deploy.yml
```

### Selective Execution with Tags

```bash
# Run only docker tasks
ansible-playbook playbooks/provision.yml --tags "docker"

# Run only package installation
ansible-playbook playbooks/provision.yml --tags "packages"

# Skip common role
ansible-playbook playbooks/provision.yml --skip-tags "common"

# List all available tags
ansible-playbook playbooks/full_setup.yml --list-tags
```

### Wipe Logic

```bash
# Wipe only (remove app)
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe

# Clean reinstall (wipe + deploy)
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"
```

## Target Infrastructure

- **Host:** plumini
- **IP:** 62.84.119.211
- **User:** ubuntu
- **SSH Key:** ~/.ssh/test_vm
- **OS:** Ubuntu 24.04 LTS

## Variables

Configuration variables are in `inventory/group_vars/all.yml` and `roles/*/defaults/main.yml`:

- `app_name`: Application/container name
- `docker_image`: Docker Hub image
- `docker_tag`: Image tag
- `app_port`: Host port
- `app_internal_port`: Container port
- `web_app_wipe`: Wipe control variable (default: false)

## Security

- SSH key authentication (no passwords)
- Ansible Vault for secrets
- Double-gated wipe logic (variable + tag)
- GitHub Actions secrets for CI/CD
