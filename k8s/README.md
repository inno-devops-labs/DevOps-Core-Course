# Lab 9 — Kubernetes Fundamentals (Manifests + Operations)

This folder contains the Kubernetes manifests to deploy the course Python app to a local Kubernetes cluster (minikube or kind) using best practices: replicas, resource requests/limits, probes, and rolling updates.

---

## Architecture Overview

- **Deployment**: `devops-python` (default namespace)
  - **Replicas**: 3 (scale to 5 for Task 4)
  - **Container port**: 5000
  - **Health endpoint**: `/health`
  - **Resources**: requests/limits set
  - **Strategy**: rolling update with `maxUnavailable: 0`
- **Service**: `devops-python` (NodePort)
  - Service port **80** → Pod port **5000**
  - NodePort: **30080**

Traffic flow:

`Client → NodeIP:30080 → Service(devops-python:80) → Pods(devops-python:5000)`

---

## Manifest Files

- **`deployment.yml`**
  - `replicas: 3`
  - `readinessProbe`, `livenessProbe`, `startupProbe` on `/health`
  - resource requests/limits
  - securityContext: `runAsNonRoot`, drop caps, `readOnlyRootFilesystem`
- **`service.yml`**
  - NodePort service exposing the app locally on port `30080`

---

## Task 1 — Local Kubernetes Setup (Evidence)

Pick one:
- **minikube** (recommended for local dev UX)
- **kind** (lightweight; good for CI-like environments)

Evidence commands (paste outputs into your report):

```bash
kubectl cluster-info
kubectl get nodes -o wide
kubectl get namespaces
```

---

## Task 2 & 3 — Deploy and Expose the App

Apply manifests:

```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
```

Verify:

```bash
kubectl get deployments
kubectl get pods -o wide
kubectl get svc -o wide
kubectl describe deployment devops-python
kubectl get endpoints devops-python
```

### Accessing the service

#### Option A: minikube

```bash
minikube service devops-python --url
curl "$(minikube service devops-python --url)/"
curl "$(minikube service devops-python --url)/health"
```

#### Option B: kind / generic cluster (port-forward)

```bash
kubectl port-forward service/devops-python 8080:80
curl http://localhost:8080/
curl http://localhost:8080/health
```

---

## Task 4 — Scaling, Rolling Updates, Rollback

### Scaling to 5 replicas

**Declarative** (edit `replicas` in `k8s/deployment.yml` then apply) OR do quick imperative scaling:

```bash
kubectl scale deployment/devops-python --replicas=5
kubectl get pods -w
kubectl rollout status deployment/devops-python
```

Capture evidence:

```bash
kubectl get deployment devops-python -o wide
kubectl get pods -l app=devops-python
```

### Rolling update

Update the image (example: change tag):

```bash
kubectl set image deployment/devops-python app=jambulancia/devops-info-service:latest
kubectl rollout status deployment/devops-python
kubectl rollout history deployment/devops-python
```

Watch pods during rollout:

```bash
kubectl get pods -l app=devops-python -w
```

### Rollback

```bash
kubectl rollout undo deployment/devops-python
kubectl rollout status deployment/devops-python
kubectl rollout history deployment/devops-python
```

---

## Production Considerations

- **Health checks**: `startupProbe` avoids killing slow-start containers; `readinessProbe` prevents traffic until ready; `livenessProbe` restarts unhealthy Pods.
- **Resources**: requests ensure scheduling; limits prevent noisy-neighbor issues.
- **Security**: non-root, runtime default seccomp, drop Linux capabilities, read-only filesystem.
- **Improvements for real prod**:
  - Use **Ingress / Gateway API** instead of NodePort
  - Add **HPA** (autoscaling) based on CPU/RPS
  - Add **PodDisruptionBudget** and anti-affinity
  - Use ConfigMaps/Secrets for config
  - Add metrics/logging/alerting (Labs 7–8 already)

---

## Challenges & Solutions (Fill In)

Common debugging commands:

```bash
kubectl describe pod <pod>
kubectl logs <pod>
kubectl get events --sort-by=.metadata.creationTimestamp
```

Write what you hit (image pull, probes, port mismatch, etc.) and how you fixed it.

---

## Lab 11 — Secrets & Vault (Helm chart)

The Helm chart under `k8s/devops-python/` supports Kubernetes Secrets (`templates/secrets.yaml`), a dedicated ServiceAccount for Vault Kubernetes auth, and optional Vault Agent Injector annotations.

Documentation and commands: **`k8s/SECRETS.md`**.

