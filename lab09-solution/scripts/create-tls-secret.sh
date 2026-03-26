#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERT_DIR="$DIR/certs"
mkdir -p "$CERT_DIR"
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "$CERT_DIR/tls.key" -out "$CERT_DIR/tls.crt" \
  -subj "/CN=local.example.com/O=local.example.com"

kubectl create secret tls tls-secret --namespace=lab09 \
  --key="$CERT_DIR/tls.key" --cert="$CERT_DIR/tls.crt" --dry-run=client -o yaml | kubectl apply -f -

echo "Add to /etc/hosts: <cluster-ip> local.example.com"
echo "Test: curl -k https://local.example.com/app1/  and  curl -k https://local.example.com/app2/"
