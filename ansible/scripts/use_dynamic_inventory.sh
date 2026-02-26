#!/usr/bin/env bash
# Use Yandex Cloud dynamic inventory. Sources Lab 4 env (YANDEX_*) and runs Ansible with inventory/yandex.yml.
# Usage: ./scripts/use_dynamic_inventory.sh [ansible command...]
# Examples:
#   ./scripts/use_dynamic_inventory.sh ansible-inventory --graph
#   ./scripts/use_dynamic_inventory.sh ansible all -m ping
#   ./scripts/use_dynamic_inventory.sh ansible-playbook playbooks/provision.yml
set -e
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$(dirname "$0")/.."

# Use same key as Lab 4 (Terraform/Pulumi)
export YANDEX_SERVICE_ACCOUNT_KEY_FILE="${YANDEX_SERVICE_ACCOUNT_KEY_FILE:-$HOME/.yandex/key.json}"
export YC_ANSIBLE_SERVICE_ACCOUNT_FILE="${YC_ANSIBLE_SERVICE_ACCOUNT_FILE:-$YANDEX_SERVICE_ACCOUNT_KEY_FILE}"

if [[ ! -f "$YC_ANSIBLE_SERVICE_ACCOUNT_FILE" ]]; then
  echo "Error: Service account key not found at $YC_ANSIBLE_SERVICE_ACCOUNT_FILE" >&2
  echo "Set YANDEX_SERVICE_ACCOUNT_KEY_FILE or YC_ANSIBLE_SERVICE_ACCOUNT_FILE, or place key at ~/.yandex/key.json" >&2
  exit 1
fi

INV="-i inventory/yandex.yml"
if [[ $# -eq 0 ]]; then
  exec ansible-inventory $INV --graph
fi
# Run with dynamic inventory
if [[ "$1" == ansible-inventory ]]; then
  exec ansible-inventory $INV "${@:2}"
elif [[ "$1" == ansible-playbook ]]; then
  exec ansible-playbook $INV "${@:2}"
elif [[ "$1" == ansible ]]; then
  exec ansible $INV "${@:2}"
else
  exec ansible-inventory $INV "$@"
fi
