# Ansible (Lab 5)

Install Ansible and collections:

```bash
# macOS
brew install ansible

# Then install collections
ansible-galaxy collection install -r requirements.yml
```

For deploy: create encrypted vars with `ansible-vault create group_vars/all.yml` (use content from `group_vars/all.yml.example`). Then run `ansible-playbook playbooks/provision.yml` (twice) and `ansible-playbook playbooks/deploy.yml --ask-vault-pass`.

Documentation: `docs/LAB05.md`.
