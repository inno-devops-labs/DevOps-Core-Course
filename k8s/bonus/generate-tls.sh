#!/usr/bin/env bash
set -euo pipefail

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=local.example.com/O=local.example.com"

kubectl -n devops-lab09 create secret tls devops-local-tls \
  --key tls.key \
  --cert tls.crt \
  --dry-run=client -o yaml > tls-secret.yml

echo "Generated tls.key, tls.crt and tls-secret.yml"
