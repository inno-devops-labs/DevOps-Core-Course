# Lab 09 — Kubernetes Fundamentals

## 1. Architecture Overview

Chosen local cluster tool: **kind**.

Why kind:
- Runs Kubernetes nodes as Docker containers (lightweight, fast startup).
- Good fit for local reproducible lab work.
- Easy local image loading (`kind load docker-image`) for images built in previous labs.

High-level architecture:

```text
Client (curl)
   |
   v
Service: devops-info-service (NodePort 80 -> targetPort 8080, nodePort 30080)
   |
   v
Deployment: devops-info-app (RollingUpdate: maxSurge=1, maxUnavailable=0)
   |
   +-- Pod 1 (Flask app)
   +-- Pod 2 (Flask app)
   +-- Pod 3 (Flask app)
```

Resource allocation strategy:
- Requests: `100m CPU`, `128Mi memory`.
- Limits: `250m CPU`, `256Mi memory`.
- Goal: guaranteed baseline resources with bounded max usage.

Cluster verification output:

```bash
$ kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:56810
CoreDNS is running at https://127.0.0.1:56810/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

$ kubectl get nodes -o wide
NAME                  STATUS   ROLES           AGE   VERSION   INTERNAL-IP   CONTAINER-RUNTIME
lab09-control-plane   Ready    control-plane   62s   v1.32.2   172.19.0.2    containerd://2.0.3
```

## 2. Manifest Files

### `k8s/deployment.yml`
- Deploys app as `Deployment/devops-info-app`.
- Initial replicas: `3` (task requirement).
- Labels/selectors: `app: devops-info`.
- Rolling update strategy: `maxSurge: 1`, `maxUnavailable: 0`.
- Health checks:
  - `livenessProbe` on `GET /health`.
  - `readinessProbe` on `GET /health`.
- Resource requests/limits included.
- Uses local image from Lab 2: `devops_lab02:cilc`.

### `k8s/service.yml`
- Creates `Service/devops-info-service` of type `NodePort`.
- Selects Pods via `app: devops-info`.
- Exposes service port `80` to container `8080`.
- NodePort fixed at `30080`.

### `k8s/deployment-v2.yml`
- Temporary manifest used for rolling update demonstration.
- Same as `deployment.yml`, but image tag changed to `devops_lab02:v2`.

Key value choices:
- Replicas `3`: baseline HA for lab objective.
- `maxUnavailable: 0`: keep service available during updates.
- Probe endpoint `/health`: already implemented in Flask app.

## 3. Deployment Evidence

```bash
$ kubectl apply -f k8s/deployment.yml
deployment.apps/devops-info-app created

$ kubectl apply -f k8s/service.yml
service/devops-info-service created

$ kubectl rollout status deployment/devops-info-app
deployment "devops-info-app" successfully rolled out

$ kubectl get deployments
NAME              READY   UP-TO-DATE   AVAILABLE
devops-info-app   3/3     3            3
```

`kubectl get all` excerpt:

```bash
NAME                              READY   UP-TO-DATE   AVAILABLE
deployment.apps/devops-info-app   3/3     3            3

NAME                          TYPE       CLUSTER-IP     PORT(S)
service/devops-info-service   NodePort   10.96.12.118   80:30080/TCP
```

`kubectl get pods,svc -o wide` (stable state):

```bash
$ kubectl get pods -l app=devops-info -o wide
NAME                               READY   STATUS    IP            NODE
devops-info-app-79679fc787-msptg   1/1     Running   10.244.0.15   lab09-control-plane
devops-info-app-79679fc787-nrlgs   1/1     Running   10.244.0.13   lab09-control-plane
devops-info-app-79679fc787-pfcnc   1/1     Running   10.244.0.14   lab09-control-plane

$ kubectl get svc devops-info-service -o wide
NAME                  TYPE       CLUSTER-IP     PORT(S)        SELECTOR
devops-info-service   NodePort   10.96.12.118   80:30080/TCP   app=devops-info
```

`kubectl describe deployment devops-info-app` confirms:
- Replicas: `3 desired | 3 updated | 3 total | 3 available | 0 unavailable`
- Strategy: `RollingUpdate` with `0 max unavailable, 1 max surge`
- Probes and resources configured on container.

Service verification with curl:

```bash
$ kubectl port-forward service/devops-info-service 18080:80

$ curl -s http://127.0.0.1:18080/health
{"status":"healthy","timestamp":"2026-03-26T17:55:37.461569+00:00","uptime_seconds":7}
```

## 4. Operations Performed

### Deploy commands

```bash
kind create cluster --name lab09 --image kindest/node:v1.32.2
kind load docker-image devops_lab02:cilc --name lab09
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl rollout status deployment/devops-info-app
```

### Scaling demonstration

```bash
$ kubectl scale deployment/devops-info-app --replicas=5
deployment.apps/devops-info-app scaled

$ kubectl rollout status deployment/devops-info-app
deployment "devops-info-app" successfully rolled out

$ kubectl get deployment devops-info-app
NAME              READY   UP-TO-DATE   AVAILABLE
devops-info-app   5/5     5            5
```

### Rolling update demonstration

```bash
$ kubectl apply -f k8s/deployment-v2.yml
deployment.apps/devops-info-app configured

$ kubectl rollout status deployment/devops-info-app
deployment "devops-info-app" successfully rolled out

$ kubectl rollout history deployment/devops-info-app
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
```

Zero-downtime verification during update (continuous health checks via Service):

```bash
availability_check ok=40 fail=0
```

### Rollback demonstration

```bash
$ kubectl rollout undo deployment/devops-info-app
deployment.apps/devops-info-app rolled back

$ kubectl rollout status deployment/devops-info-app
deployment "devops-info-app" successfully rolled out

$ kubectl rollout history deployment/devops-info-app
REVISION  CHANGE-CAUSE
2         <none>
3         <none>
```

Service access method used:
- `kubectl port-forward service/devops-info-service 18080:80`
- Verified endpoints: `/health`, `/`.

## 5. Production Considerations

Health checks:
- Implemented liveness and readiness probes using `/health`.
- Liveness restarts unhealthy containers.
- Readiness keeps unready Pods out of service load balancing.

Resource limits rationale:
- Requests reserve enough resources for steady app behavior.
- Limits cap burst usage to protect cluster stability.

How to improve for real production:
- Use separate startup probe if startup can be slow.
- Use HPA based on CPU/RPS.
- Add PodDisruptionBudget and anti-affinity.
- Pin immutable image digests instead of mutable tags.
- Add dedicated namespace, NetworkPolicies, and Secrets management.

Monitoring and observability strategy:
- Scrape `/metrics` with Prometheus.
- Dashboard in Grafana for latency/error-rate/resource usage.
- Centralize logs (e.g., Loki/ELK) and set alert rules.

## 6. Challenges & Solutions

Challenges encountered:
- No active Kubernetes context initially.
- Docker daemon was not running, which blocked local cluster/image workflows.

How it was solved:
- Started Docker Desktop.
- Installed `kind` and created local cluster.
- Loaded local Docker image into kind node using `kind load docker-image`.

Debugging approach used:
- `kubectl rollout status` for deployment progress.
- `kubectl get pods,svc,endpoints` for object state and networking.
- `kubectl describe deployment` for strategy/probe/resource verification.
- Service-level `curl` checks during rollout for availability.

What was learned:
- Declarative manifests keep state reproducible.
- RollingUpdate parameters directly control availability behavior.
- Probes and resources are baseline requirements, not optional extras.

---

Raw command output log collected during execution:
- `k8s/lab09-evidence.txt`
