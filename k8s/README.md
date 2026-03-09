# Kubernetes Deployment — DevOps Info Service

## Architecture Overview

The deployment architecture consists of the following components:

```
                    ┌──────────────────────────────────────────────┐
                    │              Kubernetes Cluster               │
                    │                                              │
  User ──► Ingress (NGINX) ──┬──► Service (app1:80)               │
            (TLS termination) │    └──► Pod 1 (:5000)              │
                              │    └──► Pod 2 (:5000)              │
                              │    └──► Pod 3 (:5000)              │
                              │                                    │
                              └──► Service (app2:80)               │
                                   └──► Pod 1 (:5678)              │
                                   └──► Pod 2 (:5678)              │
                    └──────────────────────────────────────────────┘
```

**Primary application (devops-info-service):**
- 3 replicas (scalable to 5+)
- Exposed via NodePort (30080) and Ingress (`/app1`)
- Health checks on `/health`

**Secondary application (devops-info-service-v2) — Bonus:**
- 2 replicas
- Exposed via ClusterIP and Ingress (`/app2`)
- Simple HTTP echo service

**Resource Allocation Strategy:**
- Requests: guarantee minimum CPU/memory for scheduling
- Limits: cap maximum usage to protect cluster stability
- App 1: 100m–200m CPU, 128Mi–256Mi RAM per pod
- App 2: 50m–100m CPU, 64Mi–128Mi RAM per pod

---

## Manifest Files

| File | Description |
|------|-------------|
| `deployment.yml` | Primary app Deployment — 3 replicas, health probes, resource limits, rolling update strategy |
| `service.yml` | NodePort Service exposing the primary app on port 30080 |
| `deployment-app2.yml` | Secondary app Deployment (bonus) — 2 replicas of http-echo |
| `service-app2.yml` | ClusterIP Service for the secondary app (bonus) |
| `ingress.yml` | Ingress with path-based routing + TLS (bonus) |

### Key Configuration Choices

- **3 replicas**: ensures high availability — survives at least 1 pod failure
- **RollingUpdate with maxUnavailable: 0**: guarantees zero downtime during updates
- **maxSurge: 1**: creates one extra pod at a time, conservative resource use
- **NodePort 30080**: predictable port for local development access
- **Resource requests/limits**: prevents resource starvation and OOMKills; values are based on light Python/FastAPI footprint
- **livenessProbe initialDelaySeconds: 10**: gives FastAPI enough time to start up
- **readinessProbe initialDelaySeconds: 5**: starts checking readiness earlier to add pod to service quickly

---

## Deployment Evidence

### Cluster Setup

```
$ kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:60829
CoreDNS is running at https://127.0.0.1:60829/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

$ kubectl get nodes
NAME       STATUS   ROLES           AGE   VERSION   INTERNAL-IP    OS-IMAGE
minikube   Ready    control-plane   17m   v1.35.1   192.168.49.2   Debian GNU/Linux 12 (bookworm)
```

### Deploying the Application

```
$ kubectl apply -f k8s/deployment.yml
deployment.apps/devops-info-service created

$ kubectl apply -f k8s/service.yml
service/devops-info-service created

$ kubectl rollout status deployment/devops-info-service
deployment "devops-info-service" successfully rolled out
```

### kubectl get all

```
$ kubectl get all
NAME                                       READY   STATUS    RESTARTS   AGE
pod/devops-info-service-6754977cfd-b2p72   1/1     Running   0          36s
pod/devops-info-service-6754977cfd-ggkwp   1/1     Running   0          27s
pod/devops-info-service-6754977cfd-hpwjr   1/1     Running   0          49s

NAME                          TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service   NodePort    10.105.244.215   <none>        80:30080/TCP   14m
service/kubernetes            ClusterIP   10.96.0.1        <none>        443/TCP        17m

NAME                                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service   3/3     3            3           15m

NAME                                             DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-info-service-6754977cfd   3         3         3       49s
```

### Describe Deployment

```
$ kubectl describe deployment devops-info-service
Name:                   devops-info-service
Namespace:              default
Labels:                 app=devops-info-service
                        environment=development
                        managed-by=kubectl
Selector:               app=devops-info-service
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Pod Template:
  Labels:  app=devops-info-service
           version=latest
  Containers:
   devops-info-service:
    Image:      vladimirzhidkov/devops-info-service:lab02
    Port:       5000/TCP
    Limits:     cpu: 200m, memory: 256Mi
    Requests:   cpu: 100m, memory: 128Mi
    Liveness:   http-get http://:http/health delay=10s timeout=3s period=10s #failure=3
    Readiness:  http-get http://:http/health delay=5s timeout=2s period=5s #failure=3
Conditions:
  Available      True    MinimumReplicasAvailable
  Progressing    True    NewReplicaSetAvailable
```

### Access and Test the Application

```
$ kubectl port-forward service/devops-info-service 8080:80
Forwarding from 127.0.0.1:8080 -> 5000

$ curl http://localhost:8080/health
{"status":"healthy","timestamp":"2026-03-09T19:31:16.591Z","uptime_seconds":121}

$ curl http://localhost:8080/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"devops-info-service-6754977cfd-hpwjr","platform":"Linux","architecture":"x86_64","cpu_count":16,"python_version":"3.13.11"},"runtime":{"uptime_seconds":130,"uptime_human":"2 minutes, 10 seconds","current_time":"2026-03-09T19:31:25.127Z","timezone":"UTC"}}
```

---

## Operations Performed

### 1. Initial Deploy

```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl rollout status deployment/devops-info-service
# deployment "devops-info-service" successfully rolled out
```

### 2. Scaling to 5 Replicas

```
$ kubectl scale deployment/devops-info-service --replicas=5
deployment.apps/devops-info-service scaled

$ kubectl rollout status deployment/devops-info-service
Waiting for deployment "devops-info-service" rollout to finish: 3 of 5 updated replicas are available...
Waiting for deployment "devops-info-service" rollout to finish: 4 of 5 updated replicas are available...
deployment "devops-info-service" successfully rolled out

$ kubectl get pods
NAME                                   READY   STATUS    RESTARTS   AGE
devops-info-service-6754977cfd-b2p72   1/1     Running   0          69s
devops-info-service-6754977cfd-ggkwp   1/1     Running   0          60s
devops-info-service-6754977cfd-hpwjr   1/1     Running   0          82s
devops-info-service-6754977cfd-jdj2d   1/1     Running   0          13s
devops-info-service-6754977cfd-vkbfd   1/1     Running   0          13s
```

### 3. Rolling Update

```bash
# Update image tag in deployment.yml, then:
kubectl apply -f k8s/deployment.yml
kubectl rollout status deployment/devops-info-service
# Waiting for deployment "devops-info-service" rollout to finish: 1 out of 3 new replicas have been updated...
# ...
# deployment "devops-info-service" successfully rolled out

# Check history
$ kubectl rollout history deployment/devops-info-service
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
```

### 4. Rollback

```
$ kubectl rollout undo deployment/devops-info-service
deployment.apps/devops-info-service rolled back

$ kubectl rollout status deployment/devops-info-service
deployment "devops-info-service" successfully rolled out

$ kubectl rollout history deployment/devops-info-service
REVISION  CHANGE-CAUSE
2         <none>
3         <none>
```

---

## Production Considerations

### Health Checks

| Probe | Path | Purpose |
|-------|------|---------|
| Liveness | `/health` | Restarts the container if the app becomes unresponsive (deadlock, crash loop) |
| Readiness | `/health` | Removes the pod from the Service endpoints if it's not ready to handle traffic |

Both probes use the same `/health` endpoint which returns `{"status": "healthy", ...}` with uptime info. The liveness probe has a longer `initialDelaySeconds` (10s) to avoid killing pods during startup; readiness uses 5s to quickly detect ready state.

### Resource Limits Rationale

- **CPU 100m request / 200m limit**: FastAPI + uvicorn is lightweight; 0.1 core is enough for normal load, 0.2 core handles traffic spikes
- **Memory 128Mi request / 256Mi limit**: Python baseline memory ~60–80Mi; 128Mi gives safe headroom; 256Mi limit prevents memory leaks from consuming node resources

### Production Improvements

1. **Horizontal Pod Autoscaler (HPA)** — auto-scale based on CPU/memory metrics
2. **Pod Disruption Budget (PDB)** — ensure minimum availability during voluntary disruptions
3. **Network Policies** — restrict pod-to-pod traffic
4. **Secrets management** — use Kubernetes Secrets or external vault for sensitive config
5. **Namespace isolation** — deploy to a dedicated namespace instead of `default`
6. **Image pinning** — use specific image SHA digests instead of `latest` tag
7. **Pod anti-affinity** — spread replicas across nodes for true HA

### Monitoring & Observability

- The app exposes `/metrics` endpoint (Prometheus format) — can be scraped by Prometheus
- Structured JSON logging — can be collected by Fluentd/Promtail
- Health endpoints enable Kubernetes-native monitoring
- For production: add ServiceMonitor (Prometheus Operator) and Grafana dashboards

---

## Bonus: Ingress with TLS

### Setup Ingress Controller

```bash
# Minikube
minikube addons enable ingress

# Verify
kubectl get pods -n ingress-nginx
```

### Deploy Second Application

```bash
kubectl apply -f k8s/deployment-app2.yml
kubectl apply -f k8s/service-app2.yml
```

### Generate TLS Certificate and Create Secret

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=local.example.com/O=local.example.com"

kubectl create secret tls tls-secret \
  --key tls.key \
  --cert tls.crt
```

### Deploy Ingress

```bash
kubectl apply -f k8s/ingress.yml

# Verify
kubectl get ingress
kubectl describe ingress apps-ingress
```

### Test Routing

```bash
# Add to hosts file:
# <minikube-ip> local.example.com

curl -k https://local.example.com/app1   # → devops-info-service
curl -k https://local.example.com/app2   # → "Hello from App 2!"
```

### Ingress Benefits over NodePort

- **Path-based routing**: single entry point routes to multiple services
- **TLS termination**: HTTPS handled centrally, backend pods use plain HTTP
- **Host-based routing**: virtual hosting for different domains
- **Centralized configuration**: one place for routing rules, rate limiting, rewrites

---

## Challenges & Solutions

### Common Issues and Debugging

| Issue | Cause | Solution |
|-------|-------|---------|
| ImagePullBackOff | Image not found on DockerHub | Verify image name/tag; `kubectl describe pod <name>` for details |
| CrashLoopBackOff | App crashes on startup | Check logs: `kubectl logs <pod-name>`; fix app or probe config |
| Readiness probe failing | Wrong port or path | Verify containerPort matches probe port; test `/health` endpoint |
| Service has no endpoints | Label mismatch | Compare `kubectl get ep` with `kubectl get pods --show-labels` |

### Debugging Commands

```bash
kubectl describe pod <pod-name>     # Events, conditions, probe status
kubectl logs <pod-name>             # Application stdout/stderr
kubectl logs <pod-name> --previous  # Logs from crashed container
kubectl get events --sort-by='.lastTimestamp'  # Cluster events
kubectl exec -it <pod-name> -- /bin/sh         # Shell into container
```

### Key Learnings

1. **Declarative > imperative** — `kubectl apply` is idempotent and tracks changes
2. **Labels are critical** — Service selectors must exactly match Pod labels
3. **Probes prevent downtime** — readiness probes ensure traffic only goes to healthy pods
4. **Resource limits matter** — without them, a single pod can starve the entire node
5. **Rolling updates are graceful** — combined with `maxUnavailable: 0`, users experience zero downtime
