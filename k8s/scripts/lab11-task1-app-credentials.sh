#!/usr/bin/env bash
# Lab 11 Task 1: create and inspect Secret app-credentials (imperative kubectl).
set -euo pipefail

NS="${NAMESPACE:-default}"

kubectl create secret generic app-credentials \
  --namespace "$NS" \
  --from-literal=username=demo-user \
  --from-literal=password=demo-pass \
  --dry-run=client -o yaml | kubectl apply -f -

echo "=== kubectl get secret app-credentials -o yaml ==="
kubectl get secret app-credentials -n "$NS" -o yaml

echo "=== Decoded (base64 -d) ==="
echo -n "username: "
kubectl get secret app-credentials -n "$NS" -o jsonpath='{.data.username}' | base64 -d
echo
echo -n "password: "
kubectl get secret app-credentials -n "$NS" -o jsonpath='{.data.password}' | base64 -d
echo
