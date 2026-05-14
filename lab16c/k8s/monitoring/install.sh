#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null || true
helm repo update

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  -f "${HERE}/values-minikube.yaml"

echo "Wait until pods are Running, then:"
echo "  kubectl get pods,svc -n monitoring"
echo "  kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80"
echo "  Grafana: admin / prom-operator"
