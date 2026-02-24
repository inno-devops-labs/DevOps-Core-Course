# Lab 05 Completion (`lab5c`)


## Structure

- `ansible/ansible.cfg` - project configuration
- `ansible/inventory/hosts.ini` - static inventory template
- `ansible/roles/common` - base system setup role
- `ansible/roles/docker` - Docker installation role
- `ansible/roles/app_deploy` - app deployment role
- `ansible/playbooks/provision.yml` - provisioning playbook
- `ansible/playbooks/deploy.yml` - deployment playbook
- `ansible/playbooks/site.yml` - full provision + deploy flow
- `ansible/group_vars/all.yml.example` - vault variable template
- `ansible/docs/LAB05.md` - documentation template with analysis

## Control-Node Setup (WSL)

```bash
sudo apt update
sudo apt install -y ansible
ansible-galaxy collection install -r requirements.yml
```

Bonus dynamic-inventory collection:

```bash
ansible-galaxy collection install -r requirements-bonus.yml
```

## Typical Run Order

```bash
ansible all -m ping
ansible-playbook playbooks/provision.yml
ansible-playbook playbooks/provision.yml
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```