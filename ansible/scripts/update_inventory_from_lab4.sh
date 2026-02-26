#!/usr/bin/env bash
# Set ansible inventory VM IP from Terraform or Pulumi output. Run from repo root.
set -e
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ANSIBLE_INV="$REPO_ROOT/ansible/inventory/hosts.ini"
IP=""

# Try Terraform first
if [[ -d "$REPO_ROOT/terraform" ]]; then
  IP=$(cd "$REPO_ROOT/terraform" && terraform output -raw vm_public_ip 2>/dev/null || true)
fi
# Then Pulumi
if [[ -z "$IP" && -d "$REPO_ROOT/pulumi" ]]; then
  IP=$(cd "$REPO_ROOT" && pulumi stack output vm_public_ip 2>/dev/null || true)
fi

if [[ -z "$IP" ]]; then
  echo "Could not get VM IP from Terraform or Pulumi. Set ansible_host in $ANSIBLE_INV manually."
  exit 1
fi

# Replace CHANGE_ME or existing ansible_host with new IP (portable sed)
if grep -q 'CHANGE_ME' "$ANSIBLE_INV" 2>/dev/null; then
  sed "s/ansible_host=CHANGE_ME/ansible_host=$IP/" "$ANSIBLE_INV" > "${ANSIBLE_INV}.tmp" && mv "${ANSIBLE_INV}.tmp" "$ANSIBLE_INV"
else
  sed "s/ansible_host=[0-9.]*/ansible_host=$IP/" "$ANSIBLE_INV" > "${ANSIBLE_INV}.tmp" && mv "${ANSIBLE_INV}.tmp" "$ANSIBLE_INV"
fi
echo "Updated $ANSIBLE_INV with IP $IP"
