## Architecture Overview

```
                      ┌─────────────────────────────────────┐
                      │           Kubernetes Cluster        │
                      │                                     │
  External Traffic    │  ┌──────────────────────────────┐   │
  ─────────────────► ─┼─►│  NodePort Service (:30080)   │   │
                      │  └──────────────┬───────────────┘   │
                      │                 │ routes to         │
                      │  ┌──────────────▼───────────────┐   │
                      │  │        Deployment            │   │
                      │  │  ┌──────┐ ┌──────┐ ┌──────┐  │   │
                      │  │  │ Pod  │ │ Pod  │ │ Pod  │  │   │
                      │  │  │ :80  │ │ :80  │ │ :80  │  │   │
                      │  └──┴──────┴─┴──────┴─┴──────┴──┘   │
                      └─────────────────────────────────────┘
```

**Resources:**
- **Deployment**: `devops-info-service` - 3 replicas (default), up to 5 during scaling tests
- **Service**: `devops-info-service` - NodePort, port 80 → NodePort 30080
- **Image**: `andiazdi/lab02:latest` (FastAPI Python application)
- **Resource per pod**: 100m CPU / 128Mi memory (requests), 200m CPU / 256Mi memory (limits)

---

## Manifest Files

### `deployment.yml`

Production-ready Deployment manifest with:
- **3 replicas** - ensures high availability and load distribution
- **RollingUpdate strategy** with `maxSurge: 1` and `maxUnavailable: 0` - guarantees zero downtime updates
- **Liveness probe** on `/health` - restarts unhealthy containers automatically
- **Readiness probe** on `/health` - removes pods from load balancing until they are ready
- **Resource requests & limits** - enables proper scheduling and prevents resource starvation
- **Non-root security context** - runs as user 999 (app), dropping all Linux capabilities

Key configuration choices:
- `replicas: 3` - minimum for high availability in production
- `memory: 128Mi/256Mi` - based on observed FastAPI idle (~80MB) and peak usage
- `cpu: 100m/200m` - Python web service is mostly I/O bound, 0.1 cores is sufficient at idle
- `initialDelaySeconds: 15` for liveness - gives app time to start before health checks begin

### `service.yml`

NodePort Service manifest:
- **Type: NodePort** - provides access from outside the cluster for local development
- **port: 80** - Service port (internal cluster communication)
- **targetPort: 80** - Container port (matches APP_PORT env var)
- **nodePort: 30080** - Fixed external port for predictable access URL

---

## Deployment Evidence

### `kubectl get all`

```
NAME                                       READY   STATUS    RESTARTS   AGE
pod/devops-info-service-5c57555b65-7prgs   1/1     Running   0          46s
pod/devops-info-service-5c57555b65-vngfr   1/1     Running   0          55s
pod/devops-info-service-5c57555b65-vznrm   1/1     Running   0          38s

NAME                          TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service   NodePort    10.108.251.194   <none>        80:30080/TCP   4m14s
service/kubernetes            ClusterIP   10.96.0.1        <none>        443/TCP        5m10s

NAME                                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service   3/3     3            3           4m6s

NAME                                             DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-info-service-5c57555b65   3         3         3       4m6s
replicaset.apps/devops-info-service-7f5bb987f5   0         0         0       81s
```

### `kubectl get pods,svc -o wide`

```
NAME                                       READY   STATUS    RESTARTS   AGE   IP            NODE
pod/devops-info-service-5c57555b65-7prgs   1/1     Running   0          46s   10.244.0.13   minikube
pod/devops-info-service-5c57555b65-vngfr   1/1     Running   0          55s   10.244.0.12   minikube
pod/devops-info-service-5c57555b65-vznrm   1/1     Running   0          38s   10.244.0.14   minikube

NAME                          TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE     SELECTOR
service/devops-info-service   NodePort    10.108.251.194   <none>        80:30080/TCP   4m14s   app=devops-info-service
```

### `kubectl describe deployment devops-info-service` (key fields)

```
Name:                   devops-info-service
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Liveness:   http-get http://:80/health delay=15s timeout=5s period=10s #failure=3
Readiness:  http-get http://:80/health delay=5s timeout=3s period=5s #failure=3
```

### App working - curl output via port-forward

```
StatusCode        : 200
Content           : {"status":"healthy","timestamp":"2026-03-26T09:58:19.065020","uptime_seconds":68}
```

---

## Operations Performed

### Initial Deployment

```bash
# Install minikube
Invoke-WebRequest -Uri "https://storage.googleapis.com/minikube/releases/latest/minikube-windows-amd64.exe" -OutFile "$env:USERPROFILE\minikube.exe"

# Start cluster
minikube start --driver=docker

# Apply manifests
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
```

### Verify Cluster Setup

```bash
kubectl cluster-info
# Kubernetes control plane is running at https://127.0.0.1:24969

kubectl get nodes
# NAME       STATUS   ROLES           AGE   VERSION
# minikube   Ready    control-plane   14s   v1.35.1
```

### Scaling to 5 Replicas

```bash
kubectl scale deployment/devops-info-service --replicas=5

# Output:
# NAME                                   READY   STATUS    RESTARTS   AGE
# devops-info-service-5c57555b65-27wlg   1/1     Running   0          37s
# devops-info-service-5c57555b65-g7dzh   1/1     Running   0          2m15s
# devops-info-service-5c57555b65-k4gmk   1/1     Running   0          2m15s
# devops-info-service-5c57555b65-tgpm6   1/1     Running   0          37s
# devops-info-service-5c57555b65-v9cd9   1/1     Running   0          2m15s

kubectl rollout status deployment/devops-info-service
# deployment "devops-info-service" successfully rolled out
```

### Rolling Update

Changed image tag from `latest` to `1.0.0` in `deployment.yml`, then:

```bash
kubectl apply -f k8s/deployment.yml

# Output (rolling update in action):
# Waiting for deployment: 0 out of 3 new replicas have been updated...
# Waiting for deployment: 1 out of 3 new replicas have been updated...
# Waiting for deployment: 2 out of 3 new replicas have been updated...
# Waiting for deployment: 1 old replicas are pending termination...
# deployment "devops-info-service" successfully rolled out
```

### Rollback

```bash
kubectl rollout history deployment/devops-info-service
# REVISION  CHANGE-CAUSE
# 1         <none>
# 2         <none>

kubectl rollout undo deployment/devops-info-service
# deployment.apps/devops-info-service rolled back
# deployment "devops-info-service" successfully rolled out
```

### Service Access

```bash
# Via port-forward (Docker driver on Windows)
kubectl port-forward service/devops-info-service 8088:80

# Test
curl http://127.0.0.1:8088/health
# {"status":"healthy","timestamp":"2026-03-26T09:58:19.065020","uptime_seconds":68}

# Via minikube tunnel (alternative)
minikube service devops-info-service --url
# http://127.0.0.1:23283
```

## Production Considerations

### Health Checks

Two probes are configured:
- **Liveness probe**: Kubernetes restarts the container automatically if it becomes unresponsive or enters an error state. 
FastAPI's `/health` endpoint returns the current uptime and status, which verifies the app is actually processing requests.
- **Readiness probe**: Kubernetes removes the pod from the Service endpoints until it passes. 
This prevents traffic from being routed to a pod that is starting up or temporarily overloaded.

### Resource Limits Rationale

| Resource | Request | Limit | Reason                                                                                 |
|----------|---------|-------|----------------------------------------------------------------------------------------|
| CPU      | 100m    | 200m  | FastAPI + uvicorn is I/O-bound; 0.1 core is adequate at idle, 0.2 prevents CPU hogging |
| Memory   | 128Mi   | 256Mi | Python baseline ~80Mi, limit prevents OOM cascades                                     |

### Production Improvements

1. **Horizontal Pod Autoscaler (HPA)** - auto-scale based on CPU/memory metrics
2. **Pod Disruption Budget (PDB)** - guarantee minimum available replicas during voluntary disruptions
3. **ConfigMap & Secrets** - externalize configuration and sensitive values
4. **Ingress with TLS** - single entry point with HTTPS termination instead of NodePort
5. **NetworkPolicies** - restrict pod-to-pod communication
6. **Dedicated namespace** - isolate the app from other workloads
7. **Image pull policy** - use `IfNotPresent` with pinned digest tags instead of `latest`
8. **Pod anti-affinity** - spread replicas across different nodes

### Monitoring and Observability Strategy

The application already exposes `/metrics` (Prometheus format) and `/health` endpoints from Lab 8:
- **Prometheus** scrapes `/metrics` for request rates, latencies, and error counts
- **Grafana** visualizes dashboards (already configured in `monitoring/`)
- **Loki + Promtail** collects structured JSON logs


## Challenges & Solutions

### Challenge 1: minikube not in PATH on Windows
**Problem:** `minikube` command not found after download  
**Solution:** Downloaded binary to `$USERPROFILE` directory and prepended it to `$env:PATH` for the session

### Challenge 2: Docker driver requires open terminal for NodePort
**Problem:** On Windows with Docker driver, `minikube service` keeps the tunnel open only while the terminal is open  
**Solution:** Used `kubectl port-forward` as an alternative - it creates a local port binding directly through the Kubernetes API, no tunnel required.

### What I Learned

- Kubernetes reconciliation loop: declare desired state, the control plane continuously works to achieve it
- Labels and selectors are the glue connecting Deployments to Services - they must match exactly