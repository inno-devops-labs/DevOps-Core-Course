#!/usr/bin/env bash
# Run from WSL/Git Bash from repo ansible/ dir. Fixes "role monitoring not found"
# when ansible.cfg is ignored (world-writable dir under /mnt/c).
cd "$(dirname "$0")"
export ANSIBLE_ROLES_PATH="$(pwd)/roles"
exec ansible-playbook -i inventory/hosts.ini playbooks/deploy-monitoring.yml "$@"
