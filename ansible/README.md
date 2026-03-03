# Ansible Automation

[![Ansible Deployment](https://github.com/ilyalinhnguyen/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/ilyalinhnguyen/DevOps-Core-Course/actions/workflows/ansible-deploy.yml)

Ansible playbooks and roles for provisioning servers and deploying the application (Labs 5–6).

## Structure

| Path | Description |
|------|--------------|
| `ansible.cfg` | Defaults (inventory, remote_user, become) |
| `inventory/` | Hosts and group_vars (vault for secrets) |
| `group_vars/all.yml` | Shared variables (encrypted with Ansible Vault) |
| `playbooks/` | `provision.yml`, `deploy.yml`, `site.yml` |
| `roles/` | `common`, `docker`, `web_app` |
| `docs/` | Lab write-ups (LAB05.md, LAB06.md) |

## Roles

- **common** — Base system: apt cache, packages, timezone, optional users. Tags: `packages`, `users`, `common`.
- **docker** — Docker CE and Compose plugin. Tags: `docker`, `docker_install`, `docker_config`.
- **web_app** — Deploy app with Docker Compose (templated), optional wipe. Tags: `app_deploy`, `compose`, `web_app_wipe`. Depends on `docker`.

## Quick run

```bash
# Provision (common + docker)
ansible-playbook playbooks/provision.yml --ask-vault-pass

# Deploy app (uses web_app role; installs docker if needed)
ansible-playbook playbooks/deploy.yml --ask-vault-pass

# Wipe then redeploy
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --ask-vault-pass
```

## Selective runs (tags)

```bash
ansible-playbook playbooks/provision.yml --tags "docker"
ansible-playbook playbooks/provision.yml --skip-tags "common"
ansible-playbook playbooks/provision.yml --list-tags
```

## CI/CD (self-hosted runner)

The [Ansible Deployment](https://github.com/ilyalinhnguyen/DevOps-Core-Course/actions/workflows/ansible-deploy.yml) workflow runs the **deploy** job on a **self-hosted runner** (your machine). On push (when lint passes), it deploys to localhost using `inventory/hosts.local.ini`.

**Secret** (Settings → Secrets and variables → Actions): **`ANSIBLE_VAULT_PASSWORD`** — your Vault password for `group_vars/all.yml`.

