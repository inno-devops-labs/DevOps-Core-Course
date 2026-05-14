# Install kube-prometheus-stack (PowerShell). Run from repo root or any cwd.
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
if ($LASTEXITCODE -ne 0) {
  Write-Host "prometheus-community repo already present (ok)." -ForegroundColor DarkYellow
}
helm repo update

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack `
  --namespace monitoring --create-namespace `
  -f (Join-Path $here "values-minikube.yaml")

Write-Host "Wait until all pods are Running, then:" -ForegroundColor Cyan
Write-Host "  kubectl get pods,svc -n monitoring" -ForegroundColor Cyan
Write-Host "  kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80" -ForegroundColor Cyan
Write-Host "  Grafana: admin / prom-operator" -ForegroundColor Cyan
