# Lab 9 solution

Kubernetes manifests in `k8s/`. Replace `your-dockerhub-username/devops-info-service:latest` in `deployment.yml` with your Lab 2 image. Build from `../lab02-solution/app_python` if needed.

**Apply:** `kubectl apply -f k8s/namespace.yaml` then `kubectl apply -f k8s/` (or apply remaining files except ingress until TLS secret exists).

**Bonus (Ingress + TLS):** Enable ingress controller (e.g. `minikube addons enable ingress`), run `scripts/create-tls-secret.ps1`, add `local.example.com` to hosts pointing at cluster IP, then `kubectl apply -f k8s/ingress.yml`.

Details: `k8s/README.md`.
