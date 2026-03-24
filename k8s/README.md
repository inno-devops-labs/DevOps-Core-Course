# Lab 9 — Kubernetes Deployment Documentation

## Architecture Overview

```
                        ┌──────────────────────────────────┐
                        │         Kubernetes Cluster       │
                        │         (minikube v1.38.1)       │
                        │                                  │
  External Traffic      │  NodePort :30080                 │
  ──────────────────►   │  ┌──────────────────────┐        │
                        │  │   Service (NodePort) │        │
                        │  │   python-app-service │        │
                        │  │   ClusterIP:         │        │
                        │  │   10.111.229.248:80  │        │
                        │  └──────────┬───────────┘        │
                        │             │ selector: app=python-app
                        │  ┌──────────▼───────────┐        │
                        │  │    Deployment        │        │
                        │  │    python-app        │        │
                        │  │  ┌───┐ ┌───┐ ┌───┐   │        │
                        │  │  │Pod│ │Pod│ │Pod│   │        │
                        │  │  │:50│ │:50│ │:50│   │        │
                        │  │  │00 │ │00 │ │00 │   │        │
                        │  │  └───┘ └───┘ └───┘   │        │
                        │  └──────────────────────┘        │
                        └──────────────────────────────────┘
```

**Components:**
- **Deployment** `python-app`: manages replicas of `aliyasag/devops-info-service`
- **Service** `python-app-service`: NodePort, exposes port 30080 outside the cluster
- **Pods**: each instance listens on port 5000 (Flask)

**Resource Allocation per Pod:**
- CPU: 100m request / 200m limit
- Memory: 128Mi request / 256Mi limit
- With 3 replicas: ~300m CPU and ~384Mi RAM total requests

---

## Manifest Files

### `deployment.yml`

Main manifest responsible for running the application.

| Parameter | Value | Reason |
|---|---|---|
| `replicas: 3` | 3 replicas | Fault tolerance and high availability |
| `strategy: RollingUpdate` | Update one Pod at a time | Zero-downtime deployment |
| `maxUnavailable: 0` | No Pods go down during update | Guarantees availability |
| `maxSurge: 1` | +1 extra Pod during update | Speeds up the rollout |
| `runAsNonRoot: true` | Non-root user | Security best practice |
| `livenessProbe` | HTTP GET /health every 5s | Restarts a hung container |
| `readinessProbe` | HTTP GET /health every 3s | Removes Pod from load balancing if not ready |
| `resources.requests` | 100m CPU, 128Mi | Guaranteed resources for the scheduler |
| `resources.limits` | 200m CPU, 256Mi | Protects cluster from resource starvation |

### `service.yml`

Exposes Pods to traffic from outside the cluster.

| Parameter | Value | Reason |
|---|---|---|
| `type: NodePort` | NodePort | Suitable for local development without a cloud provider |
| `port: 80` | Service port inside the cluster | Standard HTTP |
| `targetPort: 5000` | Container port | Matches the Flask application port |
| `nodePort: 30080` | External port | Fixed value in the 30000–32767 range |

---

## Deployment Evidence

### Task 1 — Cluster Setup

```
PS> kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:53239
CoreDNS is running at https://127.0.0.1:53239/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

PS> kubectl get nodes
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   59s   v1.35.1

PS> kubectl get namespaces
NAME              STATUS   AGE
default           Active   65s
kube-node-lease   Active   65s
kube-public       Active   65s
kube-system       Active   66s
```

**Tool choice:** minikube — a full-featured local cluster that runs inside a Docker container. It is easy to install on Windows and is well suited for development and learning.

### Task 2 & 3 — Deployment and Service

```
PS> kubectl get all
NAME                              READY   STATUS    RESTARTS   AGE
pod/python-app-7c986cd5db-47d62   1/1     Running   0          3m21s
pod/python-app-7c986cd5db-6c69q   1/1     Running   0          3m21s
pod/python-app-7c986cd5db-zlz7q   1/1     Running   0          3m21s

NAME                         TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/kubernetes           ClusterIP   10.96.0.1        <none>        443/TCP        17m
service/python-app-service   NodePort    10.111.229.248   <none>        80:30080/TCP   3m10s

NAME                         READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/python-app   3/3     3            3           3m21s

NAME                                    DESIRED   CURRENT   READY   AGE
replicaset.apps/python-app-7c986cd5db   3         3         3       3m21s
```

```
PS> kubectl describe deployment python-app
Name:                   python-app
Namespace:              default
CreationTimestamp:      Tue, 24 Mar 2026 17:55:57 +0300
Labels:                 app=python-app
                        version=1.0
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  0 max unavailable, 1 max surge
  Containers:
   python-app:
    Image:      aliyasag/devops-info-service:latest
    Port:       5000/TCP
    Limits:     cpu: 200m, memory: 256Mi
    Requests:   cpu: 100m, memory: 128Mi
    Liveness:   http-get http://:5000/health delay=10s timeout=1s period=5s #failure=3
    Readiness:  http-get http://:5000/health delay=5s timeout=1s period=3s #failure=3
```

### Application accessible via Service

```
PS> minikube service python-app-service --url

# Application responded in the browser:
{
  "endpoints": [
    {"description": "Service information", "method": "GET", "path": "/"},
    {"description": "Health check", "method": "GET", "path": "/health"}
  ],
  "service": {
    "name": "devops-info-service",
    "framework": "Flask",
    "version": "1.0.0"
  },
  "system": {
    "hostname": "python-app-7c986cd5db-6c69q",
    "platform": "Linux",
    "cpu_count": 12
  }
}
```

---

## Operations Performed

### Deploy

```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
```

### Task 4 — Scaling

Scaled deployment to 5 replicas:

```
PS> kubectl scale deployment/python-app --replicas=5
deployment.apps/python-app scaled

PS> kubectl get pods
NAME                          READY   STATUS    RESTARTS   AGE
python-app-7c986cd5db-47d62   1/1     Running   0          3h18m
python-app-7c986cd5db-6c69q   1/1     Running   0          3h18m
python-app-7c986cd5db-9gczh   1/1     Running   0          3h14m
python-app-7c986cd5db-j986r   1/1     Running   0          3h14m
python-app-7c986cd5db-zlz7q   1/1     Running   0          3h18m
```

All 5 replicas in Running status ✅

### Task 4 — Rolling Update

Updated image from `latest` to `v1.0.0`:

```
PS> kubectl set image deployment/python-app python-app=aliyasag/devops-info-service:v1.0.0
deployment.apps/python-app image updated

PS> kubectl rollout status deployment/python-app
Waiting for deployment "python-app" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "python-app" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "python-app" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "python-app" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "python-app" rollout to finish: 1 old replicas are pending termination...
deployment "python-app" successfully rolled out

PS> kubectl get pods
NAME                          READY   STATUS        RESTARTS   AGE
python-app-78cf4c5f76-2kwzl   1/1     Running       0          37s
python-app-78cf4c5f76-4qhnq   1/1     Running       0          20s
python-app-78cf4c5f76-9927j   1/1     Running       0          44s
python-app-78cf4c5f76-t44cx   1/1     Running       0          2m7s
python-app-78cf4c5f76-zfnxj   1/1     Running       0          27s
python-app-7c986cd5db-6c69q   1/1     Terminating   0          3h21m
```

Zero-downtime confirmed: new Pods reached Running state before old ones were terminated ✅

### Task 4 — Rollback

```
PS> kubectl rollout history deployment/python-app
deployment.apps/python-app
REVISION  CHANGE-CAUSE
1         <none>
2         <none>

PS> kubectl rollout undo deployment/python-app
deployment.apps/python-app rolled back

PS> kubectl rollout status deployment/python-app
deployment "python-app" successfully rolled out

PS> kubectl get pods
NAME                          READY   STATUS    RESTARTS   AGE
python-app-7c986cd5db-6hvfv   1/1     Running   0          59s
python-app-7c986cd5db-6lh72   1/1     Running   0          67s
python-app-7c986cd5db-6xcvt   1/1     Running   0          85s
python-app-7c986cd5db-hjg2q   1/1     Running   0          53s
python-app-7c986cd5db-mlsh6   1/1     Running   0          76s
```

Rollback to revision 1 (latest) completed successfully ✅

---

## Production Considerations

### Health Checks

- **Liveness Probe** (`/health`, every 5s, `initialDelaySeconds: 10`): if the application hangs and stops responding, Kubernetes automatically restarts the Pod. The 10s delay gives Flask time to start up.
- **Readiness Probe** (`/health`, every 3s, `initialDelaySeconds: 5`): the Pod is removed from load balancing until it is ready to serve traffic. This is critical during Rolling Updates — traffic is only sent to Pods that have passed the readiness check, ensuring zero-downtime.

Both probes use the existing `/health` endpoint of the application, confirmed working in the browser.

### Resource Limits

- **Requests** (100m CPU, 128Mi): used by the scheduler to select a node. Guarantee minimum resources for the Pod.
- **Limits** (200m CPU, 256Mi): hard ceiling. Exceeding the Memory Limit causes OOMKill; exceeding the CPU Limit causes throttling.
- Values were chosen for a lightweight Flask application. For production, load testing with `kubectl top pods` should be performed to fine-tune these numbers.

### Improvements for Production

1. **Horizontal Pod Autoscaler (HPA)** — automatic scaling based on CPU/Memory load
2. **PodDisruptionBudget** — guarantees a minimum number of live Pods during node maintenance
3. **ConfigMap + Secrets** — move configuration and credentials out of the manifest
4. **Ingress + TLS** — replace NodePort with an Ingress controller and HTTPS
5. **NetworkPolicy** — restrict network access between Pods
6. **Dedicated namespace** — isolate the application from other cluster resources

### Monitoring & Observability

- **Prometheus + Grafana** — real-time CPU/Memory/RPS metrics
- **Loki** — centralized logs from all Pods
- **kubectl logs -f pod-name** — quick debugging of a specific Pod
- **kubectl top pods** — current resource consumption (requires metrics-server)
- **kubectl get events** — cluster events for diagnosing issues

---

## Challenges & Solutions

### Challenge 1: Linux commands do not work on Windows
**Symptom:** `curl -LO`, `chmod`, `sudo` are not recognized in PowerShell  
**Solution:** Use `Invoke-WebRequest` instead of `curl`; install tools via winget or manually through the browser

### Challenge 2: Registry access error when setting PATH
**Symptom:** `SecurityException` when calling `SetEnvironmentVariable`  
**Solution:** Run PowerShell as Administrator

### Challenge 3: Health endpoint requirement
**Symptom:** Without a working `/health` endpoint the Readiness probe would fail and the Pod would never receive traffic  
**Solution:** The `devops-info-service` application already exposes a `/health` endpoint, confirmed in the browser

### What I Learned About Kubernetes

- Kubernetes operates on the **desired state** principle: you describe the desired state in YAML and the control plane continuously works to achieve it through reconciliation loops
- **Labels and selectors** are the core mechanism for linking resources: the Service finds Pods via `selector: app=python-app`, and the Deployment manages Pods via `matchLabels`
- **Rolling Update** with `maxUnavailable: 0` guarantees zero-downtime: a new Pod must pass the Readiness probe before the old one is terminated
- `kubectl apply` (declarative) is preferred over `kubectl create` (imperative) — manifests can be stored in Git and reapplied without errors
- A rollback is essentially the same as a Rolling Update, just using the previous revision's configuration