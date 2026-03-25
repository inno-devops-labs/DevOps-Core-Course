#!/usr/bin/env bash
# Generate self-signed TLS cert and create Secret tls-secret in the target namespace (Lab 9 bonus)
set -euo pipefail
HOST="${1:-local.lab09.local}"
NS="${2:-default}"

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "$TMPDIR/tls.key" -out "$TMPDIR/tls.crt" \
  -subj "/CN=${HOST}/O=lab09"

kubectl create secret tls tls-secret \
  --namespace="$NS" \
  --key "$TMPDIR/tls.key" \
  --cert "$TMPDIR/tls.crt" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Secret tls-secret applied in namespace '$NS' for host $HOST"
