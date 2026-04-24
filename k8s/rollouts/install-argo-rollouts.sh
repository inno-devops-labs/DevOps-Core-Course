#!/usr/bin/env bash
# Lab 14 — Argo Rollouts controller + dashboard (Task 1).
# Docs: https://argoproj.github.io/argo-rollouts/installation/
set -euo pipefail

NS=argo-rollouts
INSTALL_URL="https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml"
DASH_URL="https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml"

echo "Creating namespace ${NS} (if needed)..."
kubectl get namespace "$NS" >/dev/null 2>&1 || kubectl create namespace "$NS"

echo "Installing Argo Rollouts controller..."
kubectl apply -n "$NS" -f "$INSTALL_URL"

echo "Installing Rollouts dashboard..."
kubectl apply -n "$NS" -f "$DASH_URL"

echo "Waiting for rollout controller to be available..."
kubectl rollout status deploy/argo-rollouts -n "$NS" --timeout=180s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argo-rollouts-dashboard -n "$NS" --timeout=120s 2>/dev/null || true

echo ""
echo "kubectl plugin (install separately):"
echo "  https://argoproj.github.io/argo-rollouts/installation/#kubectl-plugin-installation"
echo "  e.g. Linux amd64: curl -LO .../kubectl-argo-rollouts-linux-amd64 && chmod +x && sudo mv ... /usr/local/bin/kubectl-argo-rollouts"
echo ""
echo "Dashboard: kubectl port-forward svc/argo-rollouts-dashboard -n ${NS} 3100:3100"
echo "            http://localhost:3100"
echo "CLI:       kubectl argo rollouts version"
echo "           kubectl argo rollouts get rollout <name> -n <namespace> -w"
echo ""
