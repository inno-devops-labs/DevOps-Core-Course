#!/usr/bin/env bash
# Lab 16 Task 1 — kube-prometheus-stack (cluster monitoring)
# Ref: https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack
set -euo pipefail

NS="${KUBE_PROMETHEUS_NAMESPACE:-monitoring}"
RELEASE="${KUBE_PROMETHEUS_RELEASE:-monitoring}"

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

kubectl get namespace "$NS" >/dev/null 2>&1 || kubectl create namespace "$NS"

if helm status "$RELEASE" -n "$NS" >/dev/null 2>&1; then
  echo "Helm release '$RELEASE' already in $NS; skipping install."
  echo "Upgrade: helm upgrade $RELEASE prometheus-community/kube-prometheus-stack -n $NS --reuse-values"
else
  echo "Installing kube-prometheus-stack as '$RELEASE' in namespace $NS..."
  helm install "$RELEASE" prometheus-community/kube-prometheus-stack \
    --namespace "$NS" \
    --set grafana.adminPassword=admin
fi

echo "Waiting for core pods (timeout 300s)..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=prometheus -n "$NS" --timeout=300s 2>/dev/null || true
kubectl get pods,svc -n "$NS"

echo ""
echo "Grafana:  kubectl port-forward svc/${RELEASE}-grafana -n ${NS} 3000:80"
echo "            User admin / password: prom-operator (unless overridden) or the password from:"
echo "            kubectl get secret ${RELEASE}-grafana -o jsonpath='{.data.admin-password}' | base64 -d; echo"
echo "Prometheus: kubectl port-forward svc/${RELEASE}-kube-prometheus-prometheus -n ${NS} 9090:9090"
echo "Alertmanager: kubectl port-forward svc/${RELEASE}-kube-prometheus-alertmanager -n ${NS} 9093:9093"
echo ""
