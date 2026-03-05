# Ansible — Lab 5 & 6

[![Ansible Deployment](https://github.com/pav0rkmert/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/pav0rkmert/DevOps-Core-Course/actions/workflows/ansible-deploy.yml) [![Ansible Deploy (Bonus)](https://github.com/pav0rkmert/DevOps-Core-Course/actions/workflows/ansible-deploy-bonus.yml/badge.svg)](https://github.com/pav0rkmert/DevOps-Core-Course/actions/workflows/ansible-deploy-bonus.yml)

Roles for VM provisioning (common, docker) and application deployment (web_app with Docker Compose). Single-app: `deploy.yml`. Multi-app (Lab 6 bonus): `deploy_python.yml`, `deploy_bonus.yml`, `deploy_all.yml`. Reports: [docs/LAB05.md](docs/LAB05.md), [docs/LAB06.md](docs/LAB06.md).

## Quick start

1. **Install dependencies**
   ```bash
   brew install ansible   # macOS
   cd ansible && ansible-galaxy collection install -r requirements.yml
   ```

2. **Inventory**  
   Set your VM IP in `inventory/hosts.ini` (from Lab 4), or use [dynamic inventory](docs/LAB05.md#8-bonus-dynamic-inventory-yandex-cloud) with `inventory/yandex.yml`.

3. **Vault**  
   Variables in `group_vars/all.yml` are encrypted. Use:
   ```bash
   ansible-playbook playbooks/deploy.yml --vault-password-file=.vault_pass
   ```
   Do not commit `.vault_pass`; encrypted `group_vars/all.yml` can be committed.

4. **Run**
   ```bash
   ansible all -m ping
   ansible-playbook playbooks/provision.yml
   ansible-playbook playbooks/provision.yml   # second run: idempotency
   ansible-playbook playbooks/deploy.yml --vault-password-file=.vault_pass
   ```
   Verify: `curl http://<VM-IP>:8000/health` (or 5000 if overridden in vault)

## Structure

| Path | Description |
|------|-------------|
| `inventory/hosts.ini` | Static inventory (group `webservers`) |
| `inventory/yandex.yml` | Dynamic inventory for Yandex Cloud (bonus) |
| `roles/common` | Base packages and timezone |
| `roles/docker` | Docker install and handler |
| `roles/web_app` | Docker Compose deploy, wipe logic (Lab 6) |
| `playbooks/provision.yml` | common + docker |
| `playbooks/deploy.yml` | web_app (single app, group_vars) |
| `playbooks/deploy_python.yml` | web_app for Python app (port 8000) |
| `playbooks/deploy_bonus.yml` | web_app for Go app (port 8001) |
| `playbooks/deploy_all.yml` | Deploy both apps |
| `playbooks/site.yml` | Full run |
| `vars/app_python.yml` | Python app variables (multi-app) |
| `vars/app_bonus.yml` | Bonus Go app variables (multi-app) |
| `group_vars/all.yml.example` | Variable template; real `all.yml` is vault-encrypted |

## Scripts

- `scripts/encrypt_vault.sh` — Encrypt `group_vars/all.yml`
- `scripts/update_inventory_from_lab4.sh` — Set VM IP in `hosts.ini` from Terraform/Pulumi output
- `scripts/use_dynamic_inventory.sh` — Run Ansible with Yandex dynamic inventory

## Submission

- Do **not** commit: `.vault_pass`, unencrypted secrets.
- Encrypted `group_vars/all.yml` is OK to commit.
- Report and screenshots: see `docs/LAB05.md`.
