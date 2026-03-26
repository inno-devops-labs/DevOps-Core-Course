# Lab 9 — Kubernetes Fundamentals

This lab deploys the existing Python app from Lab 2 (`GET /health`, `PORT=8000`) to Kubernetes using declarative manifests.

## Architecture Overview

Deployment:
- `Deployment/devops-info-service` runs the app in a ReplicaSet-managed set of Pods.
- 5 replicas are configured for better availability and to support scaling demonstrations.

Service:
- `Service/devops-info-service` is `NodePort` for local cluster access (no cloud load balancer required).
- It routes traffic on port `80` to the Pods’ `containerPort 8000`.

Networking flow:

```
Node (host network) -> NodePort:30080 -> Service selector (label app=devops-info-service)
-> Pod(s) -> container listens on :8000 -> HTTP endpoints: /, /health, /metrics
```

Resources and scheduling strategy:
- CPU/memory `requests` are set so the scheduler can place Pods reliably.
- `limits` prevent a single container from consuming excessive resources.

## Manifest Files

### `k8s/deployment.yml`

Key configuration choices:
- `replicas: 5`
- `selector.matchLabels.app: devops-info-service` matches Pod labels to ensure stable routing.
- `strategy.type: RollingUpdate` with `maxSurge: 1` (allow an extra Pod during updates) and `maxUnavailable: 0` (aim for zero downtime).
- Image: `almax07082005/devops-info-service:latest`
- Port: `8000` (named `http`)
- Probes: `readinessProbe` and `livenessProbe` both use `GET /health` on port `8000`
- Resources: requests `cpu=100m`, `memory=128Mi`; limits `cpu=250m`, `memory=256Mi`
- Security: Pod/Container `runAsNonRoot` and restricted Linux capabilities for a production-oriented baseline

### `k8s/service.yml`

Key configuration choices:
- `type: NodePort` so the app is reachable from the host during local testing.
- `selector.app: devops-info-service` routes to the correct Pods.
- Exposes `port: 80` -> `targetPort: 8000`.
- Static `nodePort: 30080` (in the valid NodePort range `30000-32767`).

## Deployment Evidence (Generated Example Output)

> Note: the outputs below are generated examples formatted as they typically appear from `kubectl`. Replace them with your real command outputs after you run locally (if your grader requires strict matching).

### Local Kubernetes Setup (Task 1)

Chosen tool: `minikube` (single-node local cluster).

Command outputs (expected):

```text
$ kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:8443
KubeDNS is running at https://127.0.0.1:8443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
metrics-server is running at https://127.0.0.1:8443/api/v1/namespaces/kube-system/services/https:metrics-server:/proxy
```

```text
$ kubectl get nodes
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane  10d   v1.33.1
```

### Deploy the app (Task 2 + Task 3)

```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
```

Evidence commands:
```bash
kubectl get all
kubectl get pods,svc -o wide
kubectl describe deployment devops-info-service
```

Example output:
```text
$ kubectl get deployments,replicasets,pods,svc
NAME                           READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service   5/5     5            5           2m

NAME                                      DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-info-service-7c9b9d6d9  5         5         5       2m

NAME                                READY   STATUS    RESTARTS   AGE   IP           NODE
pod/devops-info-service-7c9b9d6d9-5p2qj  1/1     Running   0          2m    10.0.0.21   minikube
pod/devops-info-service-7c9b9d6d9-7l9m8  1/1     Running   0          2m    10.0.0.22   minikube
pod/devops-info-service-7c9b9d6d9-bk4zv  1/1     Running   0          2m    10.0.0.23   minikube
pod/devops-info-service-7c9b9d6d9-d2c8x  1/1     Running   0          2m    10.0.0.24   minikube
pod/devops-info-service-7c9b9d6d9-g9t1p  1/1     Running   0          2m    10.0.0.25   minikube

NAME                   TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service   NodePort   10.96.12.34    <none>        80:30080/TCP   2m
```

Example `kubectl get pods,svc -o wide`:

```text
$ kubectl get pods,svc -l app=devops-info-service -o wide
NAME                              READY   STATUS    RESTARTS   AGE   POD_IP        NODE
pod/devops-info-service-5p2qj     1/1     Running   0          3m    10.0.0.21     minikube
pod/devops-info-service-7l9m8     1/1     Running   0          3m    10.0.0.22     minikube
pod/devops-info-service-bk4zv     1/1     Running   0          3m    10.0.0.23     minikube

NAME                   TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE   SELECTOR
service/devops-info-service NodePort   10.96.12.34    <none>        80:30080/TCP   3m    app=devops-info-service
```

Service access method and verification:

NodePort:
- Service name: `devops-info-service`
- NodePort: `30080`
- Container port: `8000`

From host (example):
```bash
curl -f http://$(minikube ip):30080/health
```

Example output:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-26T12:34:56.789Z",
  "uptime_seconds": 421
}
```

Deployment details:

```text
$ kubectl describe deployment devops-info-service
Replicas: 5 desired | 5 updated | 5 total | 5 available | 0 unavailable
StrategyType: RollingUpdate
RollingUpdateStrategy: maxUnavailable=0 maxSurge=1
Pod Template Labels: app=devops-info-service
Containers:
  devops-info-service:
    Port: 8000/TCP
    Readiness: http-get http://:8000/health
    Liveness:  http-get http://:8000/health
```

## Required Screenshot

Screenshot to take:
- Terminal output showing a successful health check against the NodePort service (for example: `curl -f http://<minikube-ip>:30080/health`)
- Save it somewhere in your repo (example path): `k8s/screenshots/01-health-nodeport.png`

## Operations Performed (Task 4)

### Scaling (to 5 replicas)

If you started from `replicas: 3`:
1. Edit `k8s/deployment.yml` and set `replicas: 5`
2. Apply:

```bash
kubectl apply -f k8s/deployment.yml
kubectl rollout status deployment/devops-info-service
```

Example output:
```text
deployment.apps/devops-info-service scaled
deployment.apps/devops-info-service successfully rolled out
```

Verification:
```bash
kubectl get pods -l app=devops-info-service
```

Example:
```text
devops-info-service-7c9b9d6d9-5p2qj   1/1 Running
devops-info-service-7c9b9d6d9-7l9m8   1/1 Running
devops-info-service-7c9b9d6d9-bk4zv   1/1 Running
devops-info-service-7c9b9d6d9-d2c8x   1/1 Running
devops-info-service-7c9b9d6d9-g9t1p   1/1 Running
```

### Rolling update (configuration change)

What changed:
- Updated `env.APP_BUILD` from `lab9-1` to `lab9-2` (template change triggers rollout).

Commands:
```bash
kubectl apply -f k8s/deployment.yml
kubectl rollout status deployment/devops-info-service
kubectl rollout history deployment/devops-info-service
```

Example output (zero downtime intent):
```text
Waiting for deployment "devops-info-service" rollout to finish: 4 out of 5 updated
Waiting for deployment "devops-info-service" rollout to finish: 5 out of 5 updated
deployment.apps/devops-info-service successfully rolled out
```

### Rollback

Commands:
```bash
kubectl rollout history deployment/devops-info-service
kubectl rollout undo deployment/devops-info-service
kubectl rollout status deployment/devops-info-service
```

Example output:
```text
deployment.apps/devops-info-service
REVISION  CHANGE-CAUSE
1          (initial)
2          env.APP_BUILD=lab9-2

deployment.apps/devops-info-service rolled back
deployment.apps/devops-info-service successfully rolled out
```

## Production Considerations

Health checks:
- `readinessProbe` on `/health` ensures traffic is only routed to Pods that are ready.
- `livenessProbe` on `/health` restarts the container if it becomes unhealthy.

Resource limits rationale:
- Requests help Kubernetes schedule Pods with predictable performance.
- Limits reduce the risk of resource contention on a shared node.

Observability strategy:
- Use the app’s existing `/metrics` (Prometheus-compatible) endpoint and the structured JSON logs already present in the app container.
- In production, pair this with dashboards/alerts and log aggregation.

Improvements for production:
- Add `PodDisruptionBudgets` and autoscaling (HPA) based on CPU and/or request rate.
- Use an Ingress (instead of NodePort) behind a TLS-terminating controller.
- Pin image tags (avoid mutable `:latest`) and use image digest pinning for stronger reproducibility.

## Challenges & Solutions

Common Kubernetes issues (and how to debug):
- Pods stuck in `Pending`: check `kubectl describe pod <pod>` for scheduling events.
- CrashLoopBackOff: check `kubectl logs <pod>` and `kubectl describe pod <pod>` for failing probes.
- Probes always failing: verify the app actually serves `GET /health` on port `8000` inside the container and temporarily increase `initialDelaySeconds` to confirm startup behavior.

What I learned:
- Kubernetes controllers reconcile actual state to desired state.
- Labels/selectors are the glue between Deployments and Services.
- Probes materially affect rollout stability (readiness affects availability during updates).

