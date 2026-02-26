#!/usr/bin/env bash
# Encrypt group_vars/all.yml with Ansible Vault. Run from repo root or ansible/.
set -e
cd "$(dirname "$0")/.."
if [[ ! -f .vault_pass ]]; then
  echo "Create .vault_pass with your vault password (one line), then run again."
  exit 1
fi
if grep -q '^\$ANSIBLE_VAULT' group_vars/all.yml 2>/dev/null; then
  echo "group_vars/all.yml is already encrypted."
  exit 0
fi
ansible-vault encrypt group_vars/all.yml --vault-password-file=.vault_pass --encrypt-vault-id=default
echo "Encrypted group_vars/all.yml. Edit with: ansible-vault edit group_vars/all.yml"
