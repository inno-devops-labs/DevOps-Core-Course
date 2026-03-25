#!/usr/bin/env bash
# Build the Python app image in minikube's Docker and tag devops-info-service:latest
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

if ! command -v minikube &>/dev/null; then
  echo "minikube not found in PATH" >&2
  exit 1
fi

eval "$(minikube docker-env)"

docker build -t devops-info-service:latest -f app_python/Dockerfile app_python
echo "Built devops-info-service:latest in minikube Docker. In kustomization.yaml set:"
echo "  newName: devops-info-service"
echo "  newTag: latest"
echo "Keep imagePullPolicy IfNotPresent (or Never) for a local-only image."
