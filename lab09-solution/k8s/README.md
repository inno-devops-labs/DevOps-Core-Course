# Lab 9 — Kubernetes (Task 5)

**Task 1 (setup):** Install `kubectl` and **minikube** or **kind** (`kind` is lightweight for CI; **minikube** is a fuller single-node dev cluster). Start the cluster, then capture `kubectl cluster-info` and `kubectl get nodes` for your lab report.

## 1. Architecture overview

- **Namespace:** `lab09`
- **App 1:** `Deployment` `devops-info-service` (Lab 2 FastAPI image), **Service** `NodePort` (cluster port 80 → container 8000, node port 30080)
- **App 2 (bonus):** `Deployment` `app2-nginx` (`nginx:1.27-alpine`), **Service** `ClusterIP` port 80
- **Ingress (bonus):** Single `Ingress` host `local.example.com`, TLS via `tls-secret`; paths `/app1` → app1, `/app2` → app2 (NGINX rewrite to backend root)
- **Resources:** CPU/memory requests + limits on both apps so the scheduler can place pods and noisy neighbors are capped

## 2. Manifest files

| File | Purpose |
|------|---------|
| `namespace.yaml` | Isolates resources |
| `deployment.yml` | 3 replicas, RollingUpdate (`maxUnavailable: 0`), probes on `/health`, resources |
| `service.yml` | `NodePort` for local access to app1 |
| `deployment-app2.yml` / `service-app2.yml` | Second app for Ingress bonus |
| `ingress.yml` | Path routing + TLS (needs controller + secret) |

**Choices:** 3 replicas (lab minimum); limits 2× requests for headroom; liveness vs readiness both on `/health` (Lab 2 already exposes it; readiness gates traffic, liveness restarts stuck pods).

## 3. Deployment evidence

Run after a successful apply and paste output for your report:

```bash
kubectl get all -n lab09
kubectl get pods,svc -n lab09 -o wide
kubectl describe deployment devops-info-service -n lab09
```

**App check (NodePort):** `minikube service devops-info-service -n lab09 --url` or `kubectl port-forward -n lab09 svc/devops-info-service 8080:80` then `curl -s http://127.0.0.1:8080/health`

## 4. Operations performed

**Deploy**

```bash
kubectl apply -f namespace.yaml
kubectl apply -f deployment.yml -f service.yml
# bonus: kubectl apply -f deployment-app2.yml -f service-app2.yml
```

**Scale to 5**

```bash
kubectl scale deployment/devops-info-service --replicas=5 -n lab09
kubectl get pods -n lab09 -w
```

**Rolling update** (example: new image tag)

```bash
kubectl set image deployment/devops-info-service devops-info-service=your-dockerhub-username/devops-info-service:v2 -n lab09
kubectl rollout status deployment/devops-info-service -n lab09
```

**Rollback**

```bash
kubectl rollout history deployment/devops-info-service -n lab09
kubectl rollout undo deployment/devops-info-service -n lab09
```

**Service access:** NodePort as above; **Ingress:** add hosts entry, create TLS secret (`../scripts/create-tls-secret.ps1` or `.sh`), apply `ingress.yml`, then `curl -k https://local.example.com/app1/` and `/app2/`.

## 5. Production considerations

- **Probes:** HTTP `/health` — readiness delays routing until the app responds; liveness recovers from deadlocks without killing during slow start (`initialDelaySeconds`).
- **Limits:** Small but non-zero requests so Guaranteed/Burstable QoS behavior is defined; tune from metrics.
- **Improvements:** HPA, PodDisruptionBudgets, NetworkPolicies, real TLS certs, external secrets, separate `/ready` if dependencies exist, resource quotas per namespace.
- **Observability:** Prometheus metrics from ingress and apps, structured logs, traces (OpenTelemetry), alerts on probe failures and 5xx.

## 6. Challenges and solutions

- **Image pull errors:** Build/push Lab 2 image under your name, or `minikube image load` / `kind load docker-image` for local tags.
- **Ingress not ready:** Wait until ingress controller pods are Running; `kubectl describe ingress -n lab09` for events.
- **TLS / curl errors:** Self-signed cert requires `-k`; trust CA in production.
- **Debug:** `kubectl logs`, `kubectl describe pod`, `kubectl get events -n lab09`.
