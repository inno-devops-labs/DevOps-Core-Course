#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

VAULT_NAMESPACE="${VAULT_NAMESPACE:-vault}"
VAULT_POD="${VAULT_POD:-vault-0}"
VAULT_SERVICE_ACCOUNT="${VAULT_SERVICE_ACCOUNT:-vault}"
APP_NAMESPACE="${APP_NAMESPACE:-lab11}"
APP_SERVICE_ACCOUNT="${APP_SERVICE_ACCOUNT:-devops-info-vault}"
VAULT_POLICY_NAME="${VAULT_POLICY_NAME:-devops-info}"
VAULT_ROLE_NAME="${VAULT_ROLE_NAME:-devops-info-role}"
KV_MOUNT_PATH="${KV_MOUNT_PATH:-secret}"
APP_SECRET_SUBPATH="${APP_SECRET_SUBPATH:-devops-info/config}"
APP_USERNAME="${APP_USERNAME:-vault-user}"
APP_PASSWORD="${APP_PASSWORD:-vault-password}"

vault_exec() {
  kubectl exec -n "$VAULT_NAMESPACE" "$VAULT_POD" -- env VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root "$@"
}

echo "Using in-cluster Kubernetes API settings for Vault auth"
KUBERNETES_HOST="https://kubernetes.default.svc:443"
TOKEN_REVIEW_JWT="$(kubectl create token "$VAULT_SERVICE_ACCOUNT" -n "$VAULT_NAMESPACE")"

echo "Ensuring the KV v2 engine exists at ${KV_MOUNT_PATH}/"
if ! vault_exec vault secrets list | grep -q "^${KV_MOUNT_PATH}/"; then
  vault_exec vault secrets enable -path="$KV_MOUNT_PATH" kv-v2
fi

echo "Writing application credentials to ${KV_MOUNT_PATH}/${APP_SECRET_SUBPATH}"
vault_exec vault kv put "${KV_MOUNT_PATH}/${APP_SECRET_SUBPATH}" username="$APP_USERNAME" password="$APP_PASSWORD"

echo "Ensuring the Kubernetes auth method is enabled"
if ! vault_exec vault auth list | grep -q '^kubernetes/'; then
  vault_exec vault auth enable kubernetes
fi

echo "Configuring Vault Kubernetes authentication"
vault_exec vault write auth/kubernetes/config \
  kubernetes_host="$KUBERNETES_HOST" \
  token_reviewer_jwt="$TOKEN_REVIEW_JWT" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt

echo "Uploading the application policy"
kubectl exec -i -n "$VAULT_NAMESPACE" "$VAULT_POD" -- sh -c \
  "cat > /tmp/${VAULT_POLICY_NAME}.hcl && env VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root vault policy write ${VAULT_POLICY_NAME} /tmp/${VAULT_POLICY_NAME}.hcl" \
  < "${SCRIPT_DIR}/devops-info-policy.hcl"

echo "Creating the Vault role bound to ${APP_NAMESPACE}/${APP_SERVICE_ACCOUNT}"
vault_exec vault write "auth/kubernetes/role/${VAULT_ROLE_NAME}" \
  bound_service_account_names="${APP_SERVICE_ACCOUNT}" \
  bound_service_account_namespaces="${APP_NAMESPACE}" \
  policies="${VAULT_POLICY_NAME}" \
  ttl="24h"

echo "Vault development setup is complete"
echo "Secret path: ${KV_MOUNT_PATH}/data/${APP_SECRET_SUBPATH}"
echo "Role name: ${VAULT_ROLE_NAME}"
