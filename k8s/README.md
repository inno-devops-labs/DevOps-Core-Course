# LAB09 — Kubernetes Fundamentals

## 1. Architecture Overview

This lab deploys two existing course applications to a local Kubernetes cluster.

- **App 1:** Python service (`devops-info-python`) in a Deployment with 3 replicas.
- **App 2 (bonus):** Go service (`devops-info-go`) in a Deployment with 2 replicas.
- **Service exposure:**
  - `devops-info-python-service` as `NodePort` for direct local access.
  - `devops-info-go-service` as `ClusterIP` for Ingress routing.
- **Ingress (bonus):** path routing with TLS:
  - `/app1` -> Python service
  - `/app2` -> Go service

Traffic flow:

```text
Client -> NodePort (app1) -> Python Pods (x3)
Client -> Ingress (TLS) -> /app1 -> Python Service -> Python Pods
Client -> Ingress (TLS) -> /app2 -> Go Service -> Go Pods
```

Resource strategy:
- Python app: requests `100m/128Mi`, limits `300m/256Mi`
- Go app: requests `100m/64Mi`, limits `300m/128Mi`

---

## 2. Manifest Files

- `k8s/deployment.yml`  
  Main Deployment for Python app. Includes rolling update strategy, probes, and resources.

- `k8s/service.yml`  
  NodePort Service for Python app (`30080`) for local direct testing.

- `k8s/deployment-app2.yml`  
  Bonus Deployment for Go app with probes and resources.

- `k8s/service-app2.yml`  
  ClusterIP Service for Go app used by Ingress.

- `k8s/ingress.yml`  
  Bonus Ingress with path-based routing and TLS termination.

Why these values:
- **3 replicas** for main app to satisfy lab minimum and show HA basics.
- **maxUnavailable: 0** to keep service available during updates.
- **Health checks on `/health`** because both applications already expose it.
- **NodePort for Task 3** (required for local external access).

---

## 3. Deployment Evidence

Run and capture:

```bash
kubectl get all
kubectl get pods,svc -o wide
kubectl describe deployment devops-info-python
curl -s http://127.0.0.1:8080/health
```

Screenshots placeholders:

![kubectl get all](screenshots/lab09-kubectl-get-all.png)
![pods and services](screenshots/lab09-pods-services.png)
![describe deployment](screenshots/lab09-describe-deployment.png)
![service response](screenshots/lab09-service-response.png)

---

## 4. Operations Performed

### Deploy

```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl get deployments
kubectl get pods -o wide
kubectl get svc
```

### Scaling demonstration

```bash
kubectl scale deployment/devops-info-python --replicas=5
kubectl rollout status deployment/devops-info-python
kubectl get pods -l app=devops-info-python
```

### Rolling update demonstration

```bash
kubectl set image deployment/devops-info-python \
  devops-info-python=olesianov/devops-info-python:lab04
kubectl rollout status deployment/devops-info-python
kubectl rollout history deployment/devops-info-python
```

### Rollback demonstration

```bash
kubectl rollout undo deployment/devops-info-python
kubectl rollout status deployment/devops-info-python
kubectl rollout history deployment/devops-info-python
```

### Service access

For local testing:

```bash
kubectl port-forward service/devops-info-python-service 8080:80
```

Then:

```bash
curl -s http://127.0.0.1:8080/
curl -s http://127.0.0.1:8080/health
```

---

## 5. Production Considerations

- **Health checks:** liveness + readiness on `/health` to restart unhealthy pods and route traffic only to ready pods.
- **Resource limits:** prevent noisy-neighbor effects and improve scheduler decisions.
- **Security:** container images run as non-root users (already configured in Dockerfiles).
- **Improvements for real production:**
  - Use HPA/VPA and metrics-server.
  - Add PodDisruptionBudget.
  - Use dedicated namespace, NetworkPolicies, and secrets manager.
  - Use GitOps (Argo CD) and CI policy checks.
- **Monitoring/observability:** keep Prometheus/Grafana from previous labs; scrape app metrics and add Kubernetes dashboards/alerts.

---

## 6. Challenges & Solutions

- **Port mismatch risk:** Python app defaults to port 5000 while Dockerfile exposes 8000; fixed by setting `PORT=5000` in manifest and matching Service/Probes.
- **Ingress path routing:** app endpoints are rooted at `/`, so regex rewrite is used for `/app1` and `/app2`.
- **Debugging approach:** `kubectl describe`, `kubectl logs`, `kubectl get events --sort-by=.metadata.creationTimestamp`.

What I learned:
- Declarative manifests are easy to re-apply and version.
- Probes and rollout strategy are key for safer updates.
- Ingress gives cleaner routing than many NodePort services.

