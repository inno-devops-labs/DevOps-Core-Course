#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-lab11}"
VAULT_POD="${VAULT_POD:-vault-0}"
ROLE_NAME="${ROLE_NAME:-devops-info-python}"
POLICY_NAME="${POLICY_NAME:-devops-info-python}"
SERVICE_ACCOUNT_NAME="${SERVICE_ACCOUNT_NAME:-devops-info-python-vault}"
VAULT_AUTH_PATH="${VAULT_AUTH_PATH:-auth/kubernetes}"
SECRET_KV_PATH="${SECRET_KV_PATH:-secret/devops-info-python/config}"
SECRET_POLICY_PATH="${SECRET_POLICY_PATH:-secret/data/devops-info-python/config}"
ROLE_AUDIENCE="${ROLE_AUDIENCE:-}"
APP_USERNAME="${APP_USERNAME:-lab11-user}"
APP_PASSWORD="${APP_PASSWORD:-lab11-password}"
DATABASE_URL="${DATABASE_URL:-postgresql://lab11-user:lab11-password@db.example.internal:5432/app}"
VAULT_ADDR="${VAULT_ADDR:-http://127.0.0.1:8200}"
VAULT_TOKEN="${VAULT_TOKEN:-root}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "missing required command: $1" >&2
    exit 1
  fi
}

vault_exec() {
  kubectl exec -i -n "${NAMESPACE}" "${VAULT_POD}" -- \
    env VAULT_ADDR="${VAULT_ADDR}" VAULT_TOKEN="${VAULT_TOKEN}" "$@"
}

discover_role_audience() {
  if [ -n "${ROLE_AUDIENCE}" ]; then
    return
  fi

  if ! command -v python3 >/dev/null 2>&1; then
    return
  fi

  ROLE_AUDIENCE="$(
    kubectl get --raw /.well-known/openid-configuration 2>/dev/null \
      | python3 -c 'import json, sys; print(json.load(sys.stdin).get("issuer", ""))' \
      || true
  )"
}

require_cmd kubectl

VAULT_AUTH_PATH="${VAULT_AUTH_PATH#/}"
VAULT_AUTH_PATH="${VAULT_AUTH_PATH%/}"

if [ -z "${VAULT_AUTH_PATH}" ]; then
  echo "VAULT_AUTH_PATH must not be empty" >&2
  exit 1
fi

if [[ "${VAULT_AUTH_PATH}" == auth/* ]]; then
  VAULT_AUTH_API_PATH="${VAULT_AUTH_PATH}"
  VAULT_AUTH_MOUNT_PATH="${VAULT_AUTH_PATH#auth/}"
else
  VAULT_AUTH_MOUNT_PATH="${VAULT_AUTH_PATH}"
  VAULT_AUTH_API_PATH="auth/${VAULT_AUTH_MOUNT_PATH}"
fi

kubectl get pod -n "${NAMESPACE}" "${VAULT_POD}" >/dev/null
kubectl get sa -n "${NAMESPACE}" "${SERVICE_ACCOUNT_NAME}" >/dev/null

discover_role_audience

if ! vault_exec vault auth list -format=json | grep -q "\"${VAULT_AUTH_MOUNT_PATH}/\""; then
  vault_exec vault auth enable -path="${VAULT_AUTH_MOUNT_PATH}" kubernetes
fi

vault_exec vault write "${VAULT_AUTH_API_PATH}/config" \
  kubernetes_host="https://kubernetes.default.svc:443" \
  disable_iss_validation=true

vault_exec vault kv put "${SECRET_KV_PATH}" \
  username="${APP_USERNAME}" \
  password="${APP_PASSWORD}" \
  database_url="${DATABASE_URL}"

cat <<EOF | vault_exec vault policy write "${POLICY_NAME}" -
path "${SECRET_POLICY_PATH}" {
  capabilities = ["read"]
}
EOF

role_write_args=(
  vault write "${VAULT_AUTH_API_PATH}/role/${ROLE_NAME}"
  bound_service_account_names="${SERVICE_ACCOUNT_NAME}"
  bound_service_account_namespaces="${NAMESPACE}"
  policies="${POLICY_NAME}"
  ttl="24h"
)

if [ -n "${ROLE_AUDIENCE}" ]; then
  role_write_args+=(audience="${ROLE_AUDIENCE}")
fi

vault_exec "${role_write_args[@]}"

echo "Vault Lab 11 bootstrap complete."
echo "Namespace: ${NAMESPACE}"
echo "Vault pod: ${VAULT_POD}"
echo "Auth path: ${VAULT_AUTH_API_PATH}"
echo "Role: ${ROLE_NAME}"
echo "ServiceAccount: ${SERVICE_ACCOUNT_NAME}"
echo "Secret path: ${SECRET_KV_PATH}"
if [ -n "${ROLE_AUDIENCE}" ]; then
  echo "Role audience: ${ROLE_AUDIENCE}"
else
  echo "Role audience: not configured"
fi
