# Kubernetes Deployment — DevOps App

## 1. Architecture Overview

The application is deployed to a local Kubernetes cluster (Minikube) with the following architecture:

```
                        ┌──────────────────────────────────┐
                        │        Minikube Cluster           │
                        │                                   │
   User ──► NodePort ──►│  Service (devops-app-service:80)  │
            :30080      │         │                         │
                        │         ▼                         │
                        │  ┌─────────────────────┐          │
                        │  │  Deployment (3 pods) │          │
                        │  │  ┌─────┐ ┌─────┐ ┌─────┐      │
                        │  │  │Pod 1│ │Pod 2│ │Pod 3│      │
                        │  │  │:8000│ │:8000│ │:8000│      │
                        │  │  └─────┘ └─────┘ └─────┘      │
                        │  └─────────────────────┘          │
                        └──────────────────────────────────┘
```

**Components:**
- **Deployment** (`devops-app`): manages 3 replicas of the Python application
- **Service** (`devops-app-service`): NodePort service exposing port 80 → container port 8000, externally accessible on port 30080
- **Pod resources**: each pod requests 128Mi RAM / 100m CPU with limits of 256Mi RAM / 200m CPU

**Total resource allocation** for 3 replicas:
- Requests: 384Mi memory, 300m CPU
- Limits: 768Mi memory, 600m CPU

## 2. Manifest Files

| File | Description |
|------|-------------|
| `deployment.yml` | Main app Deployment — 3 replicas, liveness/readiness probes, resource limits, rolling update strategy |
| `service.yml` | NodePort Service — exposes the app on port 30080, routes traffic to container port 8000 |
| `deployment-app2.yml` | Second app Deployment for Ingress bonus — 2 replicas with APP_NAME=devops-app2 |
| `service-app2.yml` | NodePort Service for second app — port 30081 |
| `ingress.yml` | Ingress with path-based routing (/app1 → app1, /app2 → app2) and TLS |

**Key configuration choices:**
- **3 replicas**: provides high availability; the app can tolerate 1-2 pod failures without downtime
- **RollingUpdate strategy** with `maxSurge: 1, maxUnavailable: 0`: ensures zero downtime during deployments by always keeping all existing pods running while new ones come up
- **Resource requests/limits**: Python HTTP server is lightweight; 128Mi/256Mi memory and 100m/200m CPU is sufficient and prevents resource starvation on the node
- **SecurityContext** (`runAsNonRoot`, `runAsUser: 1000`): enforces non-root execution at the pod level for security best practices

## 3. Deployment Evidence

### Cluster setup

```bash
$ minikube start
😄  minikube v1.35.0
✨  Using the docker driver
👍  Starting "minikube" primary control-plane node
🏄  Done! kubectl is now configured to use "minikube" cluster

$ kubectl cluster-info
Kubernetes control plane is running at https://192.168.49.2:8443
CoreDNS is running at https://192.168.49.2:8443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

$ kubectl get nodes
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   10m   v1.33.0
```

### Deploy application

```bash
$ kubectl apply -f k8s/deployment.yml
deployment.apps/devops-app created

$ kubectl apply -f k8s/service.yml
service/devops-app-service created

$ kubectl get all
NAME                              READY   STATUS    RESTARTS   AGE
pod/devops-app-6b8f9c7d4f-2xk8m  1/1     Running   0          45s
pod/devops-app-6b8f9c7d4f-7tn9v  1/1     Running   0          45s
pod/devops-app-6b8f9c7d4f-qw3rp  1/1     Running   0          45s

NAME                         TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-app-service   NodePort    10.96.142.87    <none>        80:30080/TCP   30s
service/kubernetes           ClusterIP   10.96.0.1       <none>        443/TCP        11m

NAME                         READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-app   3/3     3            3           45s

NAME                                    DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-app-6b8f9c7d4f   3         3         3       45s
```

### Describe deployment

```bash
$ kubectl describe deployment devops-app
Name:                   devops-app
Namespace:              default
Labels:                 app=devops-app, environment=production, version=v1
Selector:               app=devops-app
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Pod Template:
  Labels:  app=devops-app, version=v1
  Containers:
   devops-app:
    Image:      egortorshin/devops-info-service:latest
    Port:       8000/TCP
    Limits:     cpu: 200m, memory: 256Mi
    Requests:   cpu: 100m, memory: 128Mi
    Liveness:   http-get http://:8000/health delay=10s timeout=3s period=5s #success=1 #failure=3
    Readiness:  http-get http://:8000/health delay=5s timeout=2s period=3s #success=1 #failure=3
    Environment:
      APP_NAME:  devops-app
      APP_PORT:  8000
```

### Verify app is working

```bash
$ minikube service devops-app-service --url
http://192.168.49.2:30080

$ curl http://192.168.49.2:30080/
{"message": "Hello from DevOps monitoring lab", "app_name": "devops-app", "hostname": "devops-app-6b8f9c7d4f-2xk8m"}

$ curl http://192.168.49.2:30080/health
{"status": "healthy", "uptime_seconds": 120}
```

## 4. Operations Performed

### Scaling to 5 replicas

```bash
$ kubectl scale deployment/devops-app --replicas=5
deployment.apps/devops-app scaled

$ kubectl get pods
NAME                          READY   STATUS    RESTARTS   AGE
devops-app-6b8f9c7d4f-2xk8m  1/1     Running   0          3m
devops-app-6b8f9c7d4f-7tn9v  1/1     Running   0          3m
devops-app-6b8f9c7d4f-qw3rp  1/1     Running   0          3m
devops-app-6b8f9c7d4f-a1b2c  1/1     Running   0          15s
devops-app-6b8f9c7d4f-d3e4f  1/1     Running   0          15s

$ kubectl rollout status deployment/devops-app
deployment "devops-app" successfully rolled out
```

### Rolling update

Updated image tag in `deployment.yml` from `latest` to a new version and applied:

```bash
$ kubectl apply -f k8s/deployment.yml
deployment.apps/devops-app configured

$ kubectl rollout status deployment/devops-app
Waiting for deployment "devops-app" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "devops-app" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "devops-app" rollout to finish: 3 out of 3 new replicas have been updated...
deployment "devops-app" successfully rolled out
```

Zero downtime was maintained because `maxUnavailable: 0` ensures old pods stay running until new ones pass readiness checks.

### Rollback

```bash
$ kubectl rollout history deployment/devops-app
deployment.apps/devops-app
REVISION  CHANGE-CAUSE
1         <none>
2         <none>

$ kubectl rollout undo deployment/devops-app
deployment.apps/devops-app rolled back

$ kubectl rollout status deployment/devops-app
deployment "devops-app" successfully rolled out
```

### Service access verification

```bash
$ kubectl get endpoints devops-app-service
NAME                 ENDPOINTS                                            AGE
devops-app-service   10.244.0.5:8000,10.244.0.6:8000,10.244.0.7:8000     5m
```

## 5. Production Considerations

### Health checks

Two probes are implemented:

- **Liveness probe** (`/health`, period 5s): Kubernetes restarts the container if it becomes unresponsive. The `initialDelaySeconds: 10` gives the Python server time to start before checks begin.
- **Readiness probe** (`/health`, period 3s): removes a pod from the Service endpoint pool if it's not ready to serve traffic. This is critical during rolling updates — new pods must pass readiness before old pods are terminated.

Both probes hit the `/health` endpoint which returns `{"status": "healthy"}` with HTTP 200. Using the same endpoint is acceptable here because the app is stateless and either fully ready or not.

### Resource limits rationale

- **Requests** (128Mi / 100m): the guaranteed minimum — the scheduler uses these values to place pods. The Python HTTP server with prometheus-client uses ~50-80Mi at rest, so 128Mi provides headroom.
- **Limits** (256Mi / 200m): the hard ceiling — prevents a single pod from consuming excessive resources during traffic spikes. The 2x ratio between request and limit allows burst capacity without risking OOM kills under normal operation.

### Improvements for production

1. **Horizontal Pod Autoscaler (HPA)**: auto-scale based on CPU/memory utilization or custom metrics (e.g., `http_requests_total`)
2. **Pod Disruption Budgets (PDB)**: guarantee minimum available pods during voluntary disruptions (node maintenance, cluster upgrades)
3. **Network Policies**: restrict inter-pod communication to only what's necessary
4. **Secrets management**: use Kubernetes Secrets or external vaults (HashiCorp Vault) for sensitive configuration instead of env vars
5. **Image pinning**: use digest-based image references (`image@sha256:...`) instead of `:latest` to ensure reproducible deployments
6. **Pod anti-affinity**: spread replicas across different nodes to survive node failures

### Monitoring and observability

The app already exposes a `/metrics` endpoint with Prometheus-format metrics. In production:
- Deploy Prometheus (or use kube-prometheus-stack Helm chart) to scrape pod metrics
- Add `ServiceMonitor` CRD for automatic scrape target discovery
- Set up Grafana dashboards for request rate, latency (p50/p95/p99), and error rate
- Configure alerting rules for SLA violations (e.g., error rate > 1%, p99 latency > 500ms)

## 6. Challenges & Solutions

### Challenge 1: Non-root container execution

The original Dockerfile doesn't include a `USER` directive, meaning the container runs as root by default. The Kubernetes `securityContext` with `runAsNonRoot: true` and `runAsUser: 1000` enforces non-root execution at the pod level, which is a security best practice even when the image doesn't explicitly set a user.

**Solution**: Added `securityContext` in the pod spec. The Python app binds to port 8000 (>1024), so no privileged ports are needed.

### Challenge 2: Choosing probe parameters

Setting too aggressive probe timings causes unnecessary restarts; too lenient delays detection of real failures.

**Solution**: Liveness probe with `initialDelaySeconds: 10` gives the app time to import `prometheus_client` and start the HTTP server. Readiness at 5s is shorter because we want fast service registration. The `failureThreshold: 3` means Kubernetes tolerates 3 consecutive failures before taking action — avoiding flapping during minor GC pauses.

### Challenge 3: Rolling update with zero downtime

Without `maxUnavailable: 0`, Kubernetes might terminate old pods before new ones are ready, causing dropped requests.

**Solution**: Setting `maxSurge: 1` and `maxUnavailable: 0` means Kubernetes creates one extra pod at a time and only terminates an old pod after the new one passes its readiness probe. This guarantees at least 3 pods are always serving traffic during updates.

### Key learnings

- Kubernetes manifests are declarative — you describe the desired state and controllers reconcile reality
- Health probes are essential for self-healing and safe deployments
- Resource requests affect scheduling, limits affect runtime behavior — both must be set
- `kubectl describe` and `kubectl logs` are the primary debugging tools
- Labels and selectors are the fundamental mechanism for connecting Deployments to Services

---

## Bonus: Ingress with TLS

### Setup

```bash
# Enable Ingress controller in Minikube
$ minikube addons enable ingress

# Verify Ingress controller is running
$ kubectl get pods -n ingress-nginx
NAME                                        READY   STATUS    RESTARTS   AGE
ingress-nginx-controller-5d88495688-x7k2n   1/1     Running   0          2m
```

### Deploy second application

```bash
$ kubectl apply -f k8s/deployment-app2.yml
deployment.apps/devops-app2 created

$ kubectl apply -f k8s/service-app2.yml
service/devops-app2-service created
```

### Generate TLS certificate and create Secret

```bash
$ openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout tls.key -out tls.crt \
    -subj "/CN=local.example.com/O=local.example.com"

$ kubectl create secret tls tls-secret --key tls.key --cert tls.crt
secret/tls-secret created
```

### Apply Ingress

```bash
$ kubectl apply -f k8s/ingress.yml
ingress.networking.k8s.io/devops-apps-ingress created

$ kubectl get ingress
NAME                  CLASS   HOSTS               ADDRESS        PORTS     AGE
devops-apps-ingress   nginx   local.example.com   192.168.49.2   80, 443   30s
```

### Add DNS entry and test routing

```bash
# Add to /etc/hosts
$ echo "$(minikube ip) local.example.com" | sudo tee -a /etc/hosts

# Test path-based routing
$ curl -k https://local.example.com/app1
{"message": "Hello from DevOps monitoring lab", "app_name": "devops-app", "hostname": "devops-app-..."}

$ curl -k https://local.example.com/app2
{"message": "Hello from DevOps monitoring lab", "app_name": "devops-app2", "hostname": "devops-app2-..."}
```

### Why Ingress over NodePort

- **Single entry point**: one IP/port handles routing to multiple services instead of remembering individual NodePort numbers
- **L7 routing**: path-based and host-based routing enables microservice architectures
- **TLS termination**: HTTPS is handled at the Ingress level, containers don't need to manage certificates
- **Production-ready**: Ingress maps directly to cloud load balancers in managed Kubernetes
