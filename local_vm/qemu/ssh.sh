#!/usr/bin/env bash
set -euo pipefail

VM_USER="${VM_USER:-devops}"
SSH_PORT="${SSH_PORT:-2222}"
exec ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o LogLevel=ERROR -p "${SSH_PORT}" "${VM_USER}@127.0.0.1" "$@"
