#!/usr/bin/env bash
# Lab 13 — install Argo CD into the cluster (Task 1).
# Usage: ./install-argocd.sh
set -euo pipefail

echo "Adding Argo Helm repo..."
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

echo "Creating namespace argocd (if missing)..."
kubectl get namespace argocd >/dev/null 2>&1 || kubectl create namespace argocd

if helm status argocd -n argocd >/dev/null 2>&1; then
  echo "Helm release 'argocd' already exists; skipping install."
  echo "To upgrade the chart: helm upgrade argocd argo/argo-cd --namespace argocd --reuse-values"
else
  echo "Installing argo-cd..."
  helm install argocd argo/argo-cd --namespace argocd
fi

echo "Waiting for argocd-server to be ready (up to 180s)..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=180s

echo ""
echo "Next steps:"
echo "  UI:    kubectl port-forward svc/argocd-server -n argocd 8080:443"
echo "         Open https://localhost:8080  (accept self-signed cert); user: admin"
echo "  Pass:  kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d; echo"
echo "  CLI:   argocd login localhost:8080 --insecure"
echo ""
