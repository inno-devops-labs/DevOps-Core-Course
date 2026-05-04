# Lab 9 — Kubernetes Fundamentals

Deployment of the `devops-info` Flask application to a local Kubernetes cluster
(minikube) with declarative manifests, health checks, scaling, rolling updates
and an Ingress + TLS bonus.

## Architecture Overview

```
                      ┌──────────────────────────────┐
                      │   ingress-nginx (TLS term.)  │
                      │   host: local.example.com    │
                      └─────┬──────────────────┬─────┘
                /app1       │                  │     /app2
                            ▼                  ▼
              Service devops-info       Service devops-info-v2
              (NodePort 30080)          (ClusterIP)
                  │                            │
            5 Pods (Deployment)        2 Pods (Deployment)
            merkulovlr05/devops-info   merkulovlr05/devops-info
            (replicas, RollingUpdate)  (variant=v2)
```

- **Cluster:** minikube (Docker driver), single node, Kubernetes v1.35.1
- **Primary deployment:** 5 replicas, RollingUpdate (`maxSurge=1`,
  `maxUnavailable=0`) → zero-downtime updates
- **Resource allocation:** every Pod requests `50m` CPU / `96Mi` memory and
  is capped at `200m` / `192Mi`. Tight limits keep the cluster stable on a
  laptop while still leaving headroom for the Python interpreter

## Manifest Files

| File | Description |
|------|-------------|
| `deployment.yml` | Primary `devops-info` Deployment: 5 replicas, probes, resources, rolling-update strategy |
| `service.yml` | NodePort Service exposing the Pods on port 30080 |
| `deployment-app2.yml` | Second app variant (Deployment + ClusterIP Service) used by the Ingress bonus |
| `ingress.yml` | nginx Ingress with path-based routing (`/app1`, `/app2`) and TLS |
| `tls-secret.yml` | Generated `kubernetes.io/tls` Secret for the Ingress |

### Configuration choices

- **Replicas = 5** — gives a meaningful demo for scaling and rolling updates
  while staying cheap on a single-node cluster.
- **`maxUnavailable: 0`** — guarantees the Service always has at least N Pods
  available during a rollout (no downtime).
- **Probes hit `/health`** — the Flask app already exposes a JSON
  health endpoint, reused for both liveness and readiness. Liveness has a
  longer `initialDelaySeconds` to avoid restart loops on slow startup.
- **NodePort `30080`** — predictable port for local testing without a cloud LB.

## Deployment Evidence

All raw outputs are captured under [`evidence/`](./evidence):

- `01-initial.txt` — `cluster-info`, `get nodes`, `get all`, `describe deployment`
- `02-scaling.txt` — pods after `kubectl scale --replicas=5`
- `03-rolling-update.txt` — rollout status + history after image bump to `v1`
- `04-rollback.txt` — `rollout undo` + history
- `05-ingress.txt` — deployments / services / ingress / pods overview
- `06-curl-tls.txt` — `curl` against HTTPS Ingress for `/app1` and `/app2`,
  plus HTTP→HTTPS 308 redirect

## Operations Performed

```bash
# 1. Cluster
minikube start --driver=docker --memory=4096 --cpus=2
kubectl cluster-info
kubectl get nodes

# 2. Build image into minikube's Docker
eval $(minikube docker-env)
docker build -t merkulovlr05/devops-info:latest -t merkulovlr05/devops-info:v1 ../app_python

# 3. Deploy
kubectl apply -f deployment.yml -f service.yml
kubectl rollout status deployment/devops-info

# 4. Scale
kubectl scale deployment/devops-info --replicas=5
kubectl rollout status deployment/devops-info

# 5. Rolling update + rollback
kubectl apply -f deployment.yml          # image tag bumped to :v1
kubectl rollout history deployment/devops-info
kubectl rollout undo deployment/devops-info

# 6. Bonus: ingress + TLS
minikube addons enable ingress
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=local.example.com/O=local.example.com"
kubectl create secret tls tls-secret --key tls.key --cert tls.crt \
  --dry-run=client -o yaml > tls-secret.yml
kubectl apply -f tls-secret.yml -f deployment-app2.yml -f ingress.yml

# Access (macOS Docker driver — port-forward the controller)
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8443:443 &
curl -k --resolve local.example.com:8443:127.0.0.1 https://local.example.com:8443/app1
curl -k --resolve local.example.com:8443:127.0.0.1 https://local.example.com:8443/app2
```

## Production Considerations

- **Health checks.** Liveness restarts a stuck container; readiness keeps
  half-initialised Pods out of the Service endpoints — separating these two
  signals is what enables true zero-downtime rolling updates.
- **Resource limits.** Requests drive the scheduler and HPA; limits stop a
  runaway process from starving its neighbours. Even modest values are far
  better than no value (the default is "unbounded", which kills cluster
  stability under load).
- **Improvements for production:**
  - Move from `:latest` to immutable, digest-pinned image tags.
  - Add a `PodDisruptionBudget` so node drains don't kill the last replica.
  - Add an `HorizontalPodAutoscaler` based on CPU / RPS metrics.
  - Use a real TLS certificate (cert-manager + Let's Encrypt), not a
    self-signed one.
  - Push manifests through a GitOps tool (Argo CD — see Lab 13).
- **Observability strategy:** the app already emits structured JSON logs and
  Prometheus metrics (Lab 8); on top of that I would add:
  - Per-Pod `kube-state-metrics` + cAdvisor scraping.
  - Liveness / readiness restart counters as alerts.
  - Distributed tracing via OpenTelemetry once there is more than one service.

## Challenges & Solutions

- **`ImagePullBackOff` on first apply.** The Docker Hub image was pushed only
  for `linux/amd64`, but minikube on Apple Silicon needs `arm64`. Fix: build
  the image inside minikube's daemon (`eval $(minikube docker-env)` + `docker
  build`) so the cluster picks it up locally without needing a registry.
- **Ingress unreachable on macOS.** With the Docker driver, minikube's IP is
  not routable from the host. Fix: `kubectl port-forward` the
  `ingress-nginx-controller` Service and use `--resolve` in `curl` to hit the
  host name.
- **Self-signed TLS.** Used `-k` in `curl` for testing; the 308 redirect
  output proves nginx is correctly forcing HTTPS.

## Bonus — Ingress with TLS

- **Why Ingress over NodePort?** A single TLS-terminating entry point with
  L7 routing (path / host based) is much closer to a production setup than
  one NodePort per Service. It also frees applications from caring about
  certificates.
- **Routing**
  - `https://local.example.com/app1` → `devops-info` (5 replicas)
  - `https://local.example.com/app2` → `devops-info-v2` (2 replicas)
- **TLS** — self-signed certificate stored in the `tls-secret` Secret of type
  `kubernetes.io/tls`; `nginx.ingress.kubernetes.io/ssl-redirect: "true"`
  forces HTTP → HTTPS (308). See `evidence/06-curl-tls.txt`.

> The `tls.key` / `tls.crt` files are git-ignored — regenerate locally with
> the `openssl` command above.
