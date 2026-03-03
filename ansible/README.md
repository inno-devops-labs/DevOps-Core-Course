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

## CI/CD (GitHub-hosted runner)

The [Ansible Deployment](https://github.com/ilyalinhnguyen/DevOps-Core-Course/actions/workflows/ansible-deploy.yml) workflow uses a **GitHub-hosted runner** (`ubuntu-latest`). On push (when lint passes and secrets are set), it deploys to your VM over SSH.

**Secrets** (Settings → Secrets and variables → Actions):

| Secret | Required | Description |
|--------|----------|-------------|
| `ANSIBLE_VAULT_PASSWORD` | Yes | Password for `group_vars/all.yml` (Vault). |
| `SSH_PRIVATE_KEY` | Yes | Private key used to SSH from the runner to the VM (e.g. same key as Terraform). |
| `VM_HOST` | Yes | Target VM hostname or IP. |
| `VM_USER` | No | SSH user on the VM (default: `ubuntu`). |

The workflow writes the key to `~/.ssh/id_rsa` on the runner and generates `inventory/hosts.ci.ini` from `VM_HOST` and `VM_USER`, so no local key path or hardcoded host is needed in the repo.
