#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VM_DIR="${SCRIPT_DIR}/.artifacts/vm"
VM_NAME="${VM_NAME:-lab4-qemu-vm}"
PID_FILE_PATH="${VM_DIR}/${VM_NAME}.pid"
VM_USER="${VM_USER:-devops}"
SSH_PORT="${SSH_PORT:-2222}"

if [[ ! -f "${PID_FILE_PATH}" ]]; then
  echo "VM is not running"
  exit 0
fi

PID_VALUE="$(cat "${PID_FILE_PATH}")"
if kill -0 "${PID_VALUE}" >/dev/null 2>&1; then
  ssh -o BatchMode=yes -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o LogLevel=ERROR -o ConnectTimeout=2 -p "${SSH_PORT}" "${VM_USER}@127.0.0.1" "sudo shutdown -h now" >/dev/null 2>&1 || true
  for _ in $(seq 1 30); do
    if ! kill -0 "${PID_VALUE}" >/dev/null 2>&1; then
      rm -f "${PID_FILE_PATH}"
      echo "VM stopped"
      exit 0
    fi
    sleep 1
  done
  kill "${PID_VALUE}" >/dev/null 2>&1 || true
  for _ in $(seq 1 10); do
    if ! kill -0 "${PID_VALUE}" >/dev/null 2>&1; then
      rm -f "${PID_FILE_PATH}"
      echo "VM stopped"
      exit 0
    fi
    sleep 1
  done
  kill -9 "${PID_VALUE}" >/dev/null 2>&1 || true
fi

rm -f "${PID_FILE_PATH}"
echo "VM stopped"
