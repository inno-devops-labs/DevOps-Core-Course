Quick Ansible usage (Linux/WSL):

Collections must be installed before running playbooks:
```bash
ansible-galaxy collection install -r requirements.yml
```

Vaulted credentials ready with password `dev-ops`.

Run provision:
```bash
ansible-playbook playbooks/provision.yml
```

Run deploy:
```bash
ansible-playbook playbooks/deploy.yml
```

Note: Vault password is read from `.vault_pass` (not committed).
