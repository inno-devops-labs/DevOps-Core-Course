# Ansible Configuration for Lab 05

This directory contains Ansible playbooks and configuration for managing the DevOps lab infrastructure.

## Prerequisites

```bash
# Install Ansible (macOS)
brew install ansible

# Install Docker collection
ansible-galaxy collection install community.docker
```

## Structure

```
ansible/
├── ansible.cfg              # Ansible configuration
├── inventory/
│   ├── hosts.yml            # Inventory file
│   └── group_vars/
│       └── all.yml          # Variables for all hosts
├── playbooks/
│   ├── ping.yml             # Test connectivity
│   ├── docker.yml           # Install Docker
│   └── deploy_app.yml       # Deploy application
└── README.md                # This file
```

## Usage

### Test Connectivity

```bash
# Ad-hoc ping
ansible all -m ping

# Run ping playbook
ansible-playbook playbooks/ping.yml
```

### Install Docker

```bash
ansible-playbook playbooks/docker.yml
```

### Deploy Application

```bash
ansible-playbook playbooks/deploy_app.yml
```

## Target Infrastructure

- **Host:** plumini
- **IP:** 62.84.119.211
- **User:** ubuntu
- **SSH Key:** ~/.ssh/test_vm
- **OS:** Ubuntu 24.04 LTS

## Variables

All configuration variables are in `inventory/group_vars/all.yml`:

- `app_image`: Docker image to deploy
- `app_port`: Port to expose
- `docker_packages`: Docker packages to install

## Security

- SSH key authentication (no passwords)
- Sudo access with no password (for automation)
- UFW firewall configured
- Ansible Vault for secrets (when needed)
