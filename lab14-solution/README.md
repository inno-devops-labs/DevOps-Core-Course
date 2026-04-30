# Lab 14 Solution

Kubernetes manifests for Argo Rollouts canary and blue-green deployments.

Use:
- `kubectl apply -f lab14-solution/service.yaml --dry-run=client --validate=false`
- `kubectl apply -f lab14-solution/analysis-template.yaml --dry-run=client --validate=false`
- `kubectl apply -f lab14-solution/rollout-canary.yaml --dry-run=client --validate=false`
- `kubectl apply -f lab14-solution/rollout-bluegreen.yaml --dry-run=client --validate=false`
- `kubectl apply -f lab14-solution/preview-service.yaml --dry-run=client --validate=false`
