# Ansible — Lab 5

Roles for VM provisioning (common, docker) and application deployment (app_deploy). Full report: [docs/LAB05.md](docs/LAB05.md).

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
   Verify: `curl http://<VM-IP>:5000/health`

## Structure

| Path | Description |
|------|-------------|
| `inventory/hosts.ini` | Static inventory (group `webservers`) |
| `inventory/yandex.yml` | Dynamic inventory for Yandex Cloud (bonus) |
| `roles/common` | Base packages and timezone |
| `roles/docker` | Docker install and handler |
| `roles/app_deploy` | Docker Hub login, pull, container, health check |
| `playbooks/provision.yml` | common + docker |
| `playbooks/deploy.yml` | app_deploy |
| `playbooks/site.yml` | Full run |
| `group_vars/all.yml.example` | Variable template; real `all.yml` is vault-encrypted |

## Scripts

- `scripts/encrypt_vault.sh` — Encrypt `group_vars/all.yml`
- `scripts/update_inventory_from_lab4.sh` — Set VM IP in `hosts.ini` from Terraform/Pulumi output
- `scripts/use_dynamic_inventory.sh` — Run Ansible with Yandex dynamic inventory

## Submission

- Do **not** commit: `.vault_pass`, unencrypted secrets.
- Encrypted `group_vars/all.yml` is OK to commit.
- Report and screenshots: see `docs/LAB05.md`.
