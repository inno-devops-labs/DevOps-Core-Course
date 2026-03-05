# Ansible — Configuration Management

[![Ansible Deployment](https://github.com/abdughafforzoda/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/abdughafforzoda/DevOps-Core-Course/actions/workflows/ansible-deploy.yml)

Role-based Ansible automation for Lab 5–6: system provisioning (common, docker) and application deployment (web_app) via Docker Compose.

## Quick start

```bash
# Edit inventory with your VM
vim inventory/hosts.ini

# Create vault (one-time)
ansible-vault create group_vars/all.yml  # use structure from group_vars/all.yml.example

# Provision
ansible-playbook playbooks/provision.yml

# Deploy app
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

## Tags (Lab 6)

```bash
ansible-playbook playbooks/provision.yml --tags "docker"
ansible-playbook playbooks/provision.yml --skip-tags "common"
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe  # wipe only
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"                      # clean reinstall
```

## CI/CD

Secrets required: `ANSIBLE_VAULT_PASSWORD`, `SSH_PRIVATE_KEY`, `VM_HOST`, `VM_USER`. See `.github/workflows/ansible-deploy.yml`.
