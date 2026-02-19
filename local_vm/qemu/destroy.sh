#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARTIFACTS_DIR="${SCRIPT_DIR}/.artifacts"
VM_DIR="${ARTIFACTS_DIR}/vm"
CLOUD_INIT_DIR="${ARTIFACTS_DIR}/cloud-init"
VM_NAME="${VM_NAME:-lab4-qemu-vm}"
REMOVE_BASE_IMAGE="${REMOVE_BASE_IMAGE:-0}"

"${SCRIPT_DIR}/stop.sh" >/dev/null 2>&1 || true

rm -f "${VM_DIR}/${VM_NAME}.qcow2"
rm -f "${VM_DIR}/${VM_NAME}-seed.iso"
rm -f "${VM_DIR}/${VM_NAME}.pid"
rm -f "${VM_DIR}/${VM_NAME}-serial.log"
rm -f "${CLOUD_INIT_DIR}/meta-data"
rm -f "${CLOUD_INIT_DIR}/user-data"

if [[ "${REMOVE_BASE_IMAGE}" == "1" ]]; then
  rm -f "${ARTIFACTS_DIR}"/images/noble-server-cloudimg-*.img
fi

echo "VM artifacts removed"
