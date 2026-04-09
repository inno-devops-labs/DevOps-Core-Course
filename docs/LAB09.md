# Kubernetes Deployment Documentation

## 1. Architecture Overview

### Deployment Architecture

```
Internet / Host
     │
     ▼
┌─────────────────────────────────────┐
│  Ingress Controller (nginx)         │
│  local.example.com                  │
│  /app1 → app-python-service:80      │
│  /app2 → myapp-go-app-go:80         │
│  TLS termination (self-signed cert) │
└────────────┬────────────────────────┘
             │
     ┌───────┴───────┐
     ▼               ▼
┌─────────┐     ┌──────────┐
│ Service │     │ Service  │
│ NodePort│     │ NodePort │
│ :30080  │     │ :32065   │
└────┬────┘     └────┬─────┘
     │               │
     ▼               ▼
┌─────────┐     ┌──────────┐
│  Pod x3 │     │  Pod x2  │
│ FastAPI │     │  Gin/Go  │
│ :8000   │     │  :8080   │
└─────────┘     └──────────┘
```

### Resource Summary

| Resource | Count | Notes |
|----------|-------|-------|
| Pods (app-python) | 3 | Replicas, spread across nodes |
| Pods (app-go) | 2 | From lab 10 Helm chart |
| Services | 2 | NodePort type |
| Ingress | 1 | nginx, path-based routing, TLS |

### Resource Allocation per Pod

| | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-|-------------|-----------|----------------|--------------|
| app-python | 100m | 200m | 128Mi | 256Mi |

---

## 2. Manifest Files

### `deployment.yml`

Deploys the FastAPI Python app with 3 replicas, rolling update strategy, liveness and readiness probes, and CPU/memory limits.

Key configuration choices:
- **3 replicas** — minimum for HA; losing one pod still leaves two serving traffic
- **`maxUnavailable: 0`** — zero-downtime deploys; old pods are not removed until new ones are ready
- **`maxSurge: 1`** — only one extra pod created at a time, limits resource spike during update
- **`imagePullPolicy: Never`** — uses the image loaded into minikube locally (no Docker Hub required)
- **Probes on `/health`** — the FastAPI app exposes a dedicated health endpoint that returns `{"status":"healthy"}`

### `service.yml`

Exposes the Deployment as a `NodePort` service on port `30080`.

Key choices:
- **NodePort** — allows direct host access on minikube without running `minikube tunnel`
- **Fixed `nodePort: 30080`** — predictable URL for local development
- **`port: 80 → targetPort: 8000`** — standard HTTP port outside, app port inside

### `ingress.yml`

Path-based routing from a single hostname to both applications, with TLS.

Key choices:
- **`rewrite-target: /`** — strips the `/app1` or `/app2` prefix before forwarding to the backend, so the apps receive requests at `/` as normal
- **Self-signed TLS** — sufficient for local development; demonstrates the TLS termination pattern
- **Single Ingress resource** — both routing rules in one object, sharing the same TLS certificate

---

## 3. Deployment Evidence

### `kubectl cluster-info`

```
Kubernetes control plane is running at https://127.0.0.1:55990
CoreDNS is running at https://127.0.0.1:55990/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```

### `kubectl get nodes`

```
NAME       STATUS   ROLES           AGE     VERSION
minikube   Ready    control-plane   6d19h   v1.33.1
```

### `kubectl get all -l app=app-python`

```
NAME                              READY   STATUS    RESTARTS   AGE
pod/app-python-6d99b79d85-8lpmw   1/1     Running   0          4m56s
pod/app-python-6d99b79d85-fmjl8   1/1     Running   0          5m1s
pod/app-python-6d99b79d85-vbzq6   1/1     Running   0          5m9s

NAME                         TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/app-python-service   NodePort   10.100.92.104   <none>        80:30080/TCP   9m5s

NAME                         READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/app-python   3/3     3            3           9m5s

NAME                                    DESIRED   CURRENT   READY   AGE
replicaset.apps/app-python-6d99b79d85   3         3         3       5m9s
```

### `kubectl get pods,svc -l app=app-python -o wide`

```
NAME                              READY   STATUS    RESTARTS   AGE     IP            NODE       NOMINATED NODE   READINESS GATES
pod/app-python-6d99b79d85-8lpmw   1/1     Running   0          4m56s   10.244.0.39   minikube   <none>           <none>
pod/app-python-6d99b79d85-fmjl8   1/1     Running   0          5m1s    10.244.0.38   minikube   <none>           <none>
pod/app-python-6d99b79d85-vbzq6   1/1     Running   0          5m9s    10.244.0.37   minikube   <none>           <none>

NAME                         TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE    SELECTOR
service/app-python-service   NodePort   10.100.92.104   <none>        80:30080/TCP   9m5s   app=app-python
```

### `kubectl describe deployment app-python`

```
Name:                   app-python
Namespace:              default
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Pod Template:
  Containers:
   app-python:
    Image:      polinanime/devops-info-service:latest
    Port:       8000/TCP
    Limits:     cpu: 200m, memory: 256Mi
    Requests:   cpu: 100m, memory: 128Mi
    Liveness:   http-get http://:8000/health delay=10s timeout=1s period=5s
    Readiness:  http-get http://:8000/health delay=5s timeout=1s period=3s
```

### Application Health Check

```
$ kubectl port-forward svc/app-python-service 8081:80
$ curl -s http://localhost:8081/health
{"status":"healthy","timestamp":"2026-04-09T16:03:31.196194+00:00","uptime_seconds":27}
```

---

## 4. Operations Performed

### Initial Deployment

```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
```

### Scaling to 5 Replicas

```bash
kubectl scale deployment/app-python --replicas=5
kubectl get pods -l app=app-python
```

Output:
```
NAME                          READY   STATUS    RESTARTS   AGE
app-python-6d99b79d85-7c98m   1/1     Running   0          33s
app-python-6d99b79d85-c2fkp   1/1     Running   0          38s
app-python-6d99b79d85-lwlgr   1/1     Running   0          10s
app-python-6d99b79d85-mwgj7   1/1     Running   0          10s
app-python-6d99b79d85-vg88n   1/1     Running   0          43s
```

### Rolling Update

Added `APP_VERSION: "1.1"` env var to trigger a new rollout:

```bash
kubectl apply -f k8s/deployment.yml
kubectl rollout status deployment/app-python
```

Output:
```
Waiting for deployment "app-python" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "app-python" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "app-python" rollout to finish: 1 old replicas are pending termination...
deployment "app-python" successfully rolled out
```

### Rollback

```bash
kubectl rollout undo deployment/app-python
kubectl rollout history deployment/app-python
```

Output:
```
deployment.apps/app-python
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
3         <none>
4         <none>
5         <none>
```

### Service Access

```bash
kubectl port-forward svc/app-python-service 8081:80
curl http://localhost:8081/health
```

---

## 5. Production Considerations

### Health Checks

Both liveness and readiness probes hit `/health` on port 8000:

- **Liveness** (`initialDelaySeconds: 10`, `periodSeconds: 5`) — restarts the container if it becomes unresponsive. The 10-second delay prevents premature restarts during app startup.
- **Readiness** (`initialDelaySeconds: 5`, `periodSeconds: 3`) — removes the pod from the service load balancer until it is ready to serve traffic. The shorter delay means traffic is accepted as soon as the app is up, but not before.

Using the same `/health` path for both is acceptable here because the Python app's startup time is short. For a slow-starting app (e.g. JVM), a separate `startupProbe` would prevent liveness from killing the pod before it finishes initializing.

### Resource Limits Rationale

| | Value | Reason |
|-|-------|--------|
| CPU request: `100m` | 0.1 core | Sufficient for idle FastAPI serving low traffic |
| CPU limit: `200m` | 0.2 core | Allows burst without starving other pods |
| Memory request: `128Mi` | | Python + FastAPI + prometheus_client baseline RSS |
| Memory limit: `256Mi` | | Headroom for concurrent requests; OOM-kill before node pressure |

### Production Improvements

1. **Namespace isolation** — deploy to a dedicated namespace, not `default`
2. **HorizontalPodAutoscaler** — scale based on CPU/memory metrics instead of manual scaling
3. **PodDisruptionBudget** — guarantee at least 2 replicas available during node maintenance
4. **Non-root user** — already enforced in the Dockerfile (`USER appuser`)
5. **ImagePullPolicy: IfNotPresent** with a pinned digest tag — avoid `latest` and pulling on every restart
6. **Network Policy** — restrict pod-to-pod traffic to only what is needed
7. **Readiness gates** — use topology-aware hints for cross-zone traffic routing

### Monitoring and Observability

The FastAPI app exposes a `/metrics` endpoint in Prometheus format. In production:
- Deploy Prometheus to scrape `/metrics` from pods via `prometheus.io/scrape: "true"` pod annotations
- Add Grafana dashboards for request rate, error rate, and latency (RED method)
- Enable structured JSON logging (already implemented in the app) and ship to a log aggregator (Loki, ELK)

---

## 6. Challenges and Solutions

### Challenge 1 — Image not available in minikube after cluster restart

After restarting minikube, the multi-node setup reverted to single-node and the locally-cached image (`polinanime/devops-info-service:latest`) was lost. Pods entered `ImagePullBackOff` because the image is not published to Docker Hub.

**Solution:** Reload the image from the local Docker daemon into minikube:
```bash
minikube image load polinanime/devops-info-service:latest
```
And set `imagePullPolicy: Never` in the deployment to always use the local image.

**Lesson:** For production, always push images to a registry. For local development, `imagePullPolicy: Never` with `minikube image load` is the reliable workflow.

### Challenge 2 — Vault agent injector intercepting raw manifest pods

Pods created from `k8s/deployment.yml` were being intercepted by the Vault mutating webhook from lab 11, adding an init container that then failed authentication. This caused pods to stay in `Init:0/1`.

**Diagnosis:**
```bash
kubectl logs <pod> -c vault-agent-init
# Error: 403 permission denied on auth/kubernetes/login
```

**Solution:** The Vault K8s auth config was missing the CA cert and token reviewer JWT. After fixing the Vault config in lab 11, raw manifest pods without Vault annotations were no longer injected (the webhook only injects when `vault.hashicorp.com/agent-inject: "true"` is present).

**Lesson:** Mutating admission webhooks affect all pods in the namespace. Always check `kubectl describe pod` events and init container logs when a pod is stuck in `Pending` or `Init`.

---

## Bonus — Ingress with TLS

### Ingress Controller

Enabled the nginx ingress addon in minikube:

```bash
minikube addons enable ingress
kubectl get pods -n ingress-nginx
```

Output:
```
NAME                                       READY   STATUS      RESTARTS   AGE
ingress-nginx-admission-create-grx6t       0/1     Completed   0          2m4s
ingress-nginx-admission-patch-fmmpj        0/1     Completed   0          2m4s
ingress-nginx-controller-67c5cb88f-mqs5h   1/1     Running     0          2m4s
```

### TLS Certificate and Secret

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=local.example.com/O=local.example.com"

kubectl create secret tls tls-secret --key tls.key --cert tls.crt
```

### Ingress Resource

```bash
kubectl apply -f k8s/ingress.yml
kubectl get ingress
```

Output:
```
NAME           CLASS   HOSTS               ADDRESS        PORTS     AGE
apps-ingress   nginx   local.example.com   192.168.49.2   80, 443   23s
```

### Routing Verification

```bash
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8443:443

# app1 → FastAPI Python
curl -sk -H "Host: local.example.com" https://localhost:8443/app1/
# Returns: {"service":{"name":"devops-info-service","framework":"FastAPI"}, ...}

# app2 → Go Gin
curl -sk -H "Host: local.example.com" https://localhost:8443/app2/
# Returns: {"service":{"name":"devops-info-service","framework":"gin"}, ...}
```

### Ingress Benefits over NodePort

| | NodePort | Ingress |
|-|----------|---------|
| Routing | One port per service | Multiple services on same port (80/443) |
| TLS | Must be handled in-app | Terminated at the controller |
| URL paths | Not supported | Full path-based routing |
| Host-based routing | No | Yes (virtual hosting) |
| Certificates | Per-service | Centrally managed |

With Ingress, adding a new service requires only a new routing rule — no new port allocation or firewall rule. TLS certificates are managed in one place. This scales well as the number of services grows.
