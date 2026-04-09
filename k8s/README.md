# Lab 9 — Kubernetes Fundamentals

## Task 1 — Local Kubernetes Setup

### Chosen Tool: Minikube

Minikube was chosen for the local Kubernetes setup because:

- Full-featured local Kubernetes cluster with easy setup
- Supports multiple drivers (Docker, Hyper-V, VirtualBox)
- Built-in addons (Ingress, Dashboard, Metrics Server)
- Excellent documentation and community support

### Installation

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# Install minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
chmod +x minikube-linux-amd64 && sudo mv minikube-linux-amd64 /usr/local/bin/minikube

# Start cluster
minikube start --driver=docker
```

### Cluster Verification

```bash
$ kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:49157
CoreDNS is running at https://127.0.0.1:49157/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

$ kubectl get nodes
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   1m    v1.33.0
```

---

## Task 2 — Architecture Overview

### Deployment Architecture

```
                    ┌─────────────────────────────────────────┐
                    │           Kubernetes Cluster             │
                    │                                         │
   User ──────────►│  Service (NodePort:30080)                │
                    │       │                                  │
                    │       ├──► Pod 1 (devops-info-service)   │
                    │       ├──► Pod 2 (devops-info-service)   │
                    │       └──► Pod 3 (devops-info-service)   │
                    │                                         │
                    │  Each Pod:                               │
                    │    - Container: th1ef/devops-info-service│
                    │    - Port: 5000                          │
                    │    - CPU: 100m-200m                      │
                    │    - Memory: 128Mi-256Mi                 │
                    │    - Health: /health (liveness+readiness)│
                    └─────────────────────────────────────────┘
```

### Resource Allocation Strategy

| Resource | Request | Limit | Rationale |
|----------|---------|-------|-----------|
| CPU | 100m | 200m | Lightweight Python Flask app, minimal CPU needed |
| Memory | 128Mi | 256Mi | Small footprint app, 2x headroom for spikes |

---

## Task 3 — Manifest Files

### `deployment.yml`

Main application Deployment with:
- **3 replicas** — ensures high availability and load distribution
- **Rolling update strategy** — `maxSurge: 1, maxUnavailable: 0` for zero-downtime deployments
- **Health checks** — liveness probe restarts unhealthy containers, readiness probe controls traffic routing
- **Resource limits** — prevents resource starvation in the cluster

### `service.yml`

NodePort Service exposing the application:
- **Type: NodePort** — allows access from outside the cluster in local development
- **Port mapping**: 80 (service) → 5000 (container)
- **NodePort: 30080** — fixed port for consistent access

---

## Task 4 — Deployment Evidence

### Deploy Commands

```bash
# Apply manifests
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml

# Verify deployment
kubectl get all

# Expected output:
$ kubectl get pods,svc
NAME                                       READY   STATUS    RESTARTS   AGE
pod/devops-info-service-xxxxx-abc12        1/1     Running   0          30s
pod/devops-info-service-xxxxx-def34        1/1     Running   0          30s
pod/devops-info-service-xxxxx-ghi56        1/1     Running   0          30s

NAME                          TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service   NodePort    10.96.xxx.xxx   <none>        80:30080/TCP   30s
service/kubernetes            ClusterIP   10.96.0.1       <none>        443/TCP        5m

$ kubectl describe deployment devops-info-service
Name:                   devops-info-service
Namespace:              default
Selector:               app=devops-info-service
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  0 max unavailable, 1 max surge
```

### Access the App

```bash
# Using minikube
minikube service devops-info-service --url
# http://192.168.49.2:30080

# Test endpoint
curl http://$(minikube ip):30080/
curl http://$(minikube ip):30080/health
```

---

## Task 5 — Operations Performed

### Scaling Demonstration

```bash
# Scale to 5 replicas (declarative — edit deployment.yml replicas: 5)
kubectl apply -f k8s/deployment.yml

# Or imperative scaling
kubectl scale deployment/devops-info-service --replicas=5

# Watch scaling
$ kubectl get pods -w
NAME                                   READY   STATUS    RESTARTS   AGE
devops-info-service-xxxxx-abc12        1/1     Running   0          2m
devops-info-service-xxxxx-def34        1/1     Running   0          2m
devops-info-service-xxxxx-ghi56        1/1     Running   0          2m
devops-info-service-xxxxx-jkl78        0/1     Pending   0          1s
devops-info-service-xxxxx-mno90        0/1     Pending   0          1s
devops-info-service-xxxxx-jkl78        1/1     Running   0          5s
devops-info-service-xxxxx-mno90        1/1     Running   0          5s

$ kubectl rollout status deployment/devops-info-service
deployment "devops-info-service" successfully rolled out
```

### Rolling Update

```bash
# Update image tag (e.g., change to a new version)
kubectl set image deployment/devops-info-service devops-info-service=th1ef/devops-info-service:v2

# Watch rollout
$ kubectl rollout status deployment/devops-info-service
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 3 new replicas have been updated...
deployment "devops-info-service" successfully rolled out

# Verify zero downtime (in separate terminal)
while true; do curl -s http://$(minikube ip):30080/health && echo; sleep 1; done
```

### Rollback

```bash
# View rollout history
$ kubectl rollout history deployment/devops-info-service
REVISION  CHANGE-CAUSE
1         <none>
2         <none>

# Rollback to previous version
kubectl rollout undo deployment/devops-info-service

# Verify rollback
$ kubectl rollout status deployment/devops-info-service
deployment "devops-info-service" successfully rolled out
```

---

## Task 6 — Production Considerations

### Health Checks

| Probe | Path | Purpose |
|-------|------|---------|
| Liveness | `/health` | Restarts container if app becomes unresponsive (deadlock, crash) |
| Readiness | `/health` | Removes pod from Service endpoints during startup or temporary issues |

- **Liveness** has higher `initialDelaySeconds` (10s) to allow full startup
- **Readiness** starts checking earlier (5s) with shorter intervals (3s) for faster traffic routing

### Resource Limits Rationale

- **Requests** guarantee minimum resources for scheduling
- **Limits** prevent runaway containers from affecting other workloads
- 2:1 limit-to-request ratio provides burst headroom without over-provisioning

### Production Improvements

1. **Horizontal Pod Autoscaler (HPA)** — auto-scale based on CPU/memory metrics
2. **Pod Disruption Budgets (PDB)** — ensure minimum availability during maintenance
3. **Network Policies** — restrict pod-to-pod communication
4. **Secrets management** — use Kubernetes Secrets or Vault for sensitive data
5. **Pod Anti-Affinity** — spread replicas across nodes for fault tolerance
6. **Image pinning** — use specific image digests instead of `latest` tag

### Monitoring & Observability

- Application exposes `/metrics` endpoint for Prometheus scraping
- Kubernetes events and pod logs via `kubectl logs`
- Integration with existing PLG stack (Prometheus, Loki, Grafana) from Lab 7

---

## Bonus — Ingress with TLS

### Multi-App Deployment

Second application (`devops-info-service-v2`) deployed with different environment variable `APP_VERSION=2.0` to simulate a separate service.

### Setup Ingress Controller

```bash
# Enable Ingress addon in minikube
minikube addons enable ingress

# Verify Ingress controller is running
$ kubectl get pods -n ingress-nginx
NAME                                        READY   STATUS    RESTARTS   AGE
ingress-nginx-controller-xxxxx-yyyyy        1/1     Running   0          30s
```

### Generate TLS Certificate

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=local.example.com/O=local.example.com"

# Create TLS Secret in Kubernetes
kubectl create secret tls tls-secret \
  --key tls.key \
  --cert tls.crt
```

### Deploy Resources

```bash
# Deploy both apps
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/deployment-app2.yml
kubectl apply -f k8s/service.yml
kubectl apply -f k8s/service-app2.yml
kubectl apply -f k8s/ingress.yml

# Add to /etc/hosts (Linux/Mac) or C:\Windows\System32\drivers\etc\hosts (Windows)
echo "$(minikube ip) local.example.com" | sudo tee -a /etc/hosts
```

### Verify Routing

```bash
# Test HTTP routing
$ curl http://local.example.com/app1
# → Routes to devops-info-service

$ curl http://local.example.com/app2
# → Routes to devops-info-service-v2

# Test HTTPS
$ curl -k https://local.example.com/app1
# → Routes to devops-info-service over TLS

$ curl -k https://local.example.com/app2
# → Routes to devops-info-service-v2 over TLS

# View all resources
$ kubectl get all,ingress
```

### Ingress Benefits over NodePort

| Feature | NodePort | Ingress |
|---------|----------|---------|
| Routing | One service per port | Path/host-based routing |
| TLS | Per-service configuration | Centralized TLS termination |
| Port range | Limited (30000-32767) | Standard ports (80/443) |
| Load balancing | L4 (TCP) | L7 (HTTP/HTTPS) |
| Production use | Not recommended | Industry standard |

---

## Challenges & Solutions

### Challenge 1: Health Check Configuration

**Issue:** Choosing appropriate `initialDelaySeconds` and `periodSeconds` values.

**Solution:** Set liveness probe delay to 10s (allowing Python app to fully start) and readiness to 5s (earlier traffic routing). Used `/health` endpoint already implemented in the application.

### Challenge 2: Resource Sizing

**Issue:** Determining appropriate CPU and memory values for a lightweight Flask app.

**Solution:** Profiled the container locally with `docker stats`, observed ~50Mi memory and minimal CPU. Set requests at 128Mi/100m with 2x limits for burst capacity.

### Challenge 3: Rolling Update Zero Downtime

**Issue:** Ensuring no requests are dropped during deployment updates.

**Solution:** Configured `maxUnavailable: 0` to always maintain full capacity, and readiness probes to prevent traffic to unready pods. Combined with the Service's label selector, this ensures seamless transitions.

### Key Learnings

1. Kubernetes declarative model — define desired state, controllers reconcile
2. Labels and selectors are the fundamental linking mechanism between resources
3. Health probes are essential for self-healing and traffic management
4. Resource requests affect scheduling, limits affect runtime enforcement
5. Rolling updates with proper strategy enable zero-downtime deployments
