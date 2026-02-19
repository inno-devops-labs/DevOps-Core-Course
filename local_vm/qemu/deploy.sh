#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARTIFACTS_DIR="${SCRIPT_DIR}/.artifacts"
IMAGE_DIR="${ARTIFACTS_DIR}/images"
CLOUD_INIT_DIR="${ARTIFACTS_DIR}/cloud-init"
VM_DIR="${ARTIFACTS_DIR}/vm"

VM_NAME="${VM_NAME:-lab4-qemu-vm}"
VM_USER="${VM_USER:-devops}"
VM_ARCH="${VM_ARCH:-$(uname -m)}"
VM_RAM_MB="${VM_RAM_MB:-2048}"
VM_CPUS="${VM_CPUS:-2}"
VM_DISK_GB="${VM_DISK_GB:-20}"
SSH_PORT="${SSH_PORT:-2222}"
HTTP_PORT="${HTTP_PORT:-8080}"
APP_PORT="${APP_PORT:-5000}"

mkdir -p "${IMAGE_DIR}" "${CLOUD_INIT_DIR}" "${VM_DIR}"

case "${VM_ARCH}" in
  arm64|aarch64)
    IMAGE_FILE="noble-server-cloudimg-arm64.img"
    IMAGE_URL="https://cloud-images.ubuntu.com/noble/current/${IMAGE_FILE}"
    QEMU_BIN="${QEMU_BIN:-qemu-system-aarch64}"
    UEFI_CODE_PATH="${UEFI_CODE_PATH:-/opt/homebrew/share/qemu/edk2-aarch64-code.fd}"
    MACHINE_ARGS=(-machine virt,accel=hvf -cpu host)
    ;;
  x86_64|amd64)
    IMAGE_FILE="noble-server-cloudimg-amd64.img"
    IMAGE_URL="https://cloud-images.ubuntu.com/noble/current/${IMAGE_FILE}"
    QEMU_BIN="${QEMU_BIN:-qemu-system-x86_64}"
    UEFI_CODE_PATH="${UEFI_CODE_PATH:-/opt/homebrew/share/qemu/edk2-x86_64-code.fd}"
    MACHINE_ARGS=(-machine q35,accel=hvf -cpu host)
    ;;
  *)
    echo "Unsupported VM_ARCH: ${VM_ARCH}"
    exit 1
    ;;
esac

BASE_IMAGE_PATH="${IMAGE_DIR}/${IMAGE_FILE}"
DISK_IMAGE_PATH="${VM_DIR}/${VM_NAME}.qcow2"
SEED_IMAGE_PATH="${VM_DIR}/${VM_NAME}-seed.iso"
USER_DATA_PATH="${CLOUD_INIT_DIR}/user-data"
META_DATA_PATH="${CLOUD_INIT_DIR}/meta-data"
PID_FILE_PATH="${VM_DIR}/${VM_NAME}.pid"
SERIAL_LOG_PATH="${VM_DIR}/${VM_NAME}-serial.log"

if [[ ! -f "${UEFI_CODE_PATH}" ]]; then
  echo "UEFI firmware not found at: ${UEFI_CODE_PATH}"
  exit 1
fi

if [[ -f "${PID_FILE_PATH}" ]]; then
  RUNNING_PID="$(cat "${PID_FILE_PATH}")"
  if kill -0 "${RUNNING_PID}" >/dev/null 2>&1; then
    echo "VM already running with PID ${RUNNING_PID}"
    exit 0
  fi
  rm -f "${PID_FILE_PATH}"
fi

if [[ -n "${SSH_PUB_KEY:-}" ]]; then
  SSH_KEY_CONTENT="${SSH_PUB_KEY}"
elif [[ -f "${HOME}/.ssh/id_ed25519.pub" ]]; then
  SSH_KEY_CONTENT="$(cat "${HOME}/.ssh/id_ed25519.pub")"
elif [[ -f "${HOME}/.ssh/id_rsa.pub" ]]; then
  SSH_KEY_CONTENT="$(cat "${HOME}/.ssh/id_rsa.pub")"
else
  echo "No SSH public key found. Set SSH_PUB_KEY or create ~/.ssh/id_ed25519.pub"
  exit 1
fi

printf '%s\n' \
  '#cloud-config' \
  "hostname: ${VM_NAME}" \
  'users:' \
  "  - name: ${VM_USER}" \
  '    groups: [adm, sudo]' \
  '    shell: /bin/bash' \
  '    sudo: ALL=(ALL) NOPASSWD:ALL' \
  '    ssh_authorized_keys:' \
  "      - \"${SSH_KEY_CONTENT}\"" \
  'package_update: true' \
  'packages:' \
  '  - openssh-server' \
  > "${USER_DATA_PATH}"

printf '%s\n' \
  "instance-id: ${VM_NAME}" \
  "local-hostname: ${VM_NAME}" \
  > "${META_DATA_PATH}"

if [[ ! -f "${BASE_IMAGE_PATH}" ]]; then
  curl -fL "${IMAGE_URL}" -o "${BASE_IMAGE_PATH}"
fi

if [[ ! -f "${DISK_IMAGE_PATH}" ]]; then
  qemu-img create -f qcow2 -F qcow2 -b "${BASE_IMAGE_PATH}" "${DISK_IMAGE_PATH}" "${VM_DISK_GB}G" >/dev/null
fi

hdiutil makehybrid -quiet -ov -o "${SEED_IMAGE_PATH}" "${CLOUD_INIT_DIR}" -iso -joliet -default-volume-name cidata

"${QEMU_BIN}" \
  "${MACHINE_ARGS[@]}" \
  -smp "${VM_CPUS}" \
  -m "${VM_RAM_MB}" \
  -bios "${UEFI_CODE_PATH}" \
  -drive "if=virtio,format=qcow2,file=${DISK_IMAGE_PATH}" \
  -drive "if=virtio,format=raw,file=${SEED_IMAGE_PATH}" \
  -netdev "user,id=net0,hostfwd=tcp:127.0.0.1:${SSH_PORT}-:22,hostfwd=tcp:127.0.0.1:${HTTP_PORT}-:80,hostfwd=tcp:127.0.0.1:${APP_PORT}-:5000" \
  -device virtio-net-pci,netdev=net0 \
  -daemonize \
  -pidfile "${PID_FILE_PATH}" \
  -serial "file:${SERIAL_LOG_PATH}" \
  -display none

echo "VM name: ${VM_NAME}"
echo "SSH command: ssh -p ${SSH_PORT} ${VM_USER}@127.0.0.1"
echo "Forwarded ports: ${SSH_PORT}->22, ${HTTP_PORT}->80, ${APP_PORT}->5000"
