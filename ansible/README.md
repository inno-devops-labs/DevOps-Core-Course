# Ansible Automation for DevOps Course

[![Ansible Deployment](https://github.com/Nexonm/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/Nexonm/DevOps-Core-Course/actions/workflows/ansible-deploy.yml)

## Overview

This directory contains Ansible automation for Lab 5 and Lab 6, implementing:

- **Infrastructure provisioning** with common packages and Docker installation
- **Docker Compose deployment** for containerized applications
- **Role-based architecture** for modularity and reusability
- **Wipe logic** with double-gating (variable + tag) for safe cleanup
- **CI/CD integration** with GitHub Actions and self-hosted runners
- **Multi-app deployment** supporting Python and Java applications

## Directory Structure

```
ansible/
├── inventory/
│   └── hosts.ini              # Target server inventory
├── group_vars/
│   └── all.yml                # Encrypted variables (Ansible Vault)
├── vars/
│   ├── app_python.yml         # Python app configuration
│   └── app_java.yml           # Java app configuration
├── roles/
│   ├── common/                # System packages and configuration
│   ├── docker/                # Docker CE installation
│   └── web_app/               # Docker Compose deployment
├── playbooks/
│   ├── provision.yml          # System provisioning
│   ├── deploy.yml             # Single app deployment (legacy)
│   ├── deploy_python.yml      # Python app deployment
│   ├── deploy_java.yml        # Java app deployment
│   ├── deploy_all.yml         # Multi-app deployment
│   └── site.yml               # Complete infrastructure
├── docs/
│   ├── LAB05.md               # Lab 5 documentation
│   ├── LAB06.md               # Lab 6 documentation
│   └── screenshots/           # Evidence screenshots
└── ansible.cfg                # Ansible configuration

```

## Usage

### Provision Infrastructure

```bash
ansible-playbook playbooks/provision.yml
```

### Deploy Applications

```bash
# Python app only
ansible-playbook playbooks/deploy_python.yml

# Java app only
ansible-playbook playbooks/deploy_java.yml

# Both apps
ansible-playbook playbooks/deploy_all.yml
```

### Selective Execution with Tags

```bash
# Run only Docker installation
ansible-playbook playbooks/provision.yml --tags "docker_install"

# Skip common role
ansible-playbook playbooks/provision.yml --skip-tags "common"
```

### Wipe Logic

```bash
# Wipe Python app only
ansible-playbook playbooks/deploy_python.yml -e "web_app_wipe=true" --tags web_app_wipe

# Clean reinstallation (wipe + deploy)
ansible-playbook playbooks/deploy_python.yml -e "web_app_wipe=true"
```

## Documentation

- [Lab 5 Documentation](docs/LAB05.md) - Ansible fundamentals, roles, and Vault
- [Lab 6 Documentation](docs/LAB06.md) - Advanced Ansible with blocks, tags, and CI/CD

## CI/CD

Automated deployment is configured with GitHub Actions. The workflow:
1. Runs `ansible-lint` for syntax validation
2. Deploys to target VPS using self-hosted runner
3. Verifies deployment health

See [`.github/workflows/ansible-deploy.yml`](../.github/workflows/ansible-deploy.yml) for details.
