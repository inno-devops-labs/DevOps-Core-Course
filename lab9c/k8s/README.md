# Lab 9 — Kubernetes Fundamentals

This lab is complete for all **required** tasks (bonus not included).

## 1) Architecture Overview

I used **kind** (Kubernetes in Docker) because it is quick to run locally on Windows and good for repeatable tests.

- Deployment: `devops-info-python` (3 replicas)
- Service: `devops-info-python-service` (`NodePort`, `80 -> 5000`, nodePort `30080`)
- Update strategy: RollingUpdate (`maxSurge: 1`, `maxUnavailable: 0`)
- Resources per pod:
  - requests: `100m` CPU, `128Mi` memory
  - limits: `300m` CPU, `256Mi` memory

Traffic path used for local verification:
`kubectl port-forward` -> Service -> Pods.

## 2) Manifest Files

### `deployment.yml`

Contains:

- 3 replicas
- labels/selectors
- image `tsixphoenix/devops-info-python:lab9`
- readiness + liveness probes on `/health`
- resource requests/limits
- non-root security context
- rolling update strategy

### `service.yml`

Contains:

- `type: NodePort`
- selector `app: devops-info-python`
- `port: 80`, `targetPort: 5000`, `nodePort: 30080`

## 3) Deployment Evidence

### Cluster setup

```bash
kubectl cluster-info --context kind-lab9
kubectl get nodes -o wide
```

```text
Kubernetes control plane is running at https://127.0.0.1:...
lab9-control-plane   Ready   control-plane   v1.32.2
```

### Deployed resources

```bash
kubectl get all
kubectl get pods,svc -o wide
kubectl describe deployment devops-info-python
```

Observed:

- deployment `devops-info-python` is `3/3 READY`
- service `devops-info-python-service` is `NodePort 80:30080/TCP`
- probes and rolling strategy are visible in `describe`

### App is reachable

```bash
kubectl port-forward service/devops-info-python-service 8080:80
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/
```

Example health response:

```text
{"status":"healthy","timestamp":"...","uptime_seconds":...}
```

## 4) Operations Performed

### Deploy

```bash
kubectl apply -f lab9c/k8s/deployment.yml -f lab9c/k8s/service.yml
kubectl rollout status deployment/devops-info-python
```

### Scale to 5 replicas

```bash
kubectl scale deployment/devops-info-python --replicas=5
kubectl rollout status deployment/devops-info-python
kubectl get deployment/devops-info-python
```

Result: `READY 5/5, AVAILABLE 5`.

### Rolling update

Updated `RELEASE_ID` in deployment and applied again:

```bash
kubectl apply -f lab9c/k8s/deployment.yml
kubectl rollout status deployment/devops-info-python
kubectl rollout history deployment/devops-info-python
```

Result: rollout completed successfully, revision history updated.

### Zero-downtime check during update

I called `/health` repeatedly during rollout. All responses were HTTP 200.

### Rollback

```bash
kubectl rollout undo deployment/devops-info-python
kubectl rollout status deployment/devops-info-python
kubectl rollout history deployment/devops-info-python
```

Result: rollback completed and previous revision was restored.

### Service verification

```bash
kubectl describe service devops-info-python-service
kubectl get endpoints devops-info-python-service
```

Result: service endpoints matched running pod IPs on port 5000.

## 5) Production Considerations

- Readiness probe keeps not-ready pods out of traffic.
- Liveness probe restarts broken pods.
- Requests/limits prevent noisy-neighbor issues and help scheduling.
- For real production, I would add:
  - namespace isolation + network policies
  - HPA
  - ConfigMaps/Secrets
  - PodDisruptionBudget
  - Ingress with TLS
- Observability plan:
  - metrics in Prometheus
  - logs in Loki/Grafana
  - alerts for 5xx rate, restarts, and pod availability

## 6) Challenges & Solutions

### No local cluster available initially

- `kubectl` existed, but no running cluster.
- Fixed by creating a local `kind` cluster (`kind-lab9`).

### First app rollout failed (CrashLoopBackOff)

- Cause: old image/tag mismatch.
- Fix: built fresh image `tsixphoenix/devops-info-python:lab9`, loaded it into kind, and used that tag in deployment.

### NodePort access from host in kind setup

- Direct node IP access was unreliable in this environment.
- Used `kubectl port-forward` for stable local verification.
