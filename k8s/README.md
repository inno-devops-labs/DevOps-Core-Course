#  Kubernetes Deployment — DevOps Info Service

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Minikube Cluster                      │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │              default namespace                   │   │
│  │                                                  │   │
│  │   ┌─────────────────────────────────────────┐    │   │
│  │   │   Deployment: devops-info-service       │    │   │
│  │   │   Replicas: 5                           │    │   │
│  │   │                                         │    │   │
│  │   │   ┌────────┐ ┌────────┐ ┌────────┐      │    │   │
│  │   │   │  Pod 1 │ │  Pod 2 │ │  Pod 3 │ ...  │    │   │
│  │   │   │ :5000  │ │ :5000  │ │ :5000  │      │    │   │
│  │   │   └────────┘ └────────┘ └────────┘      │    │   │
│  │   └─────────────────────────────────────────┘    │   │
│  │                        │                         │   │
│  │   ┌────────────────────▼──────────────────┐      │   │
│  │   │   Service: devops-info-service        │      │   │
│  │   │   Type: NodePort                      │      │   │
│  │   │   ClusterIP:80 → Pod:5000             │      │   │
│  │   │   NodePort: 30080                     │      │   │
│  │   └───────────────────────────────────────┘      │   │
│  └──────────────────────────────────────────────────┘   │
│                        │                                │
│           Node IP: 192.168.49.2:30080                   │
└─────────────────────────────────────────────────────────┘
                         │
               External curl / browser
```

**Deployment summary:**

- **Pods:** 5 replicas of `devops-info-service` (FastAPI, port 5000)
- **Service:** NodePort exposing port 30080 → container port 5000
- **Resource allocation:** 100m CPU / 128Mi RAM request; 200m CPU / 256Mi RAM limit per pod

---

## 2. Manifest Files

### `deployment.yml`

Deploys the FastAPI `devops-info-service` (Docker image: `lanebo1/devops-info-service:latest`).


| Field                | Value                                        | Rationale                                  |
| -------------------- | -------------------------------------------- | ------------------------------------------ |
| `replicas`           | 3 (initial)                                  | Minimum for HA; scaled to 5 in lab         |
| `strategy`           | RollingUpdate (maxSurge=1, maxUnavailable=0) | Zero-downtime updates                      |
| `resources.requests` | 100m CPU, 128Mi memory                       | Baseline for scheduler; app is lightweight |
| `resources.limits`   | 200m CPU, 256Mi memory                       | Caps to prevent noisy-neighbour issues     |
| `livenessProbe`      | `GET /health` every 10s, 15s delay           | Restarts truly unhealthy containers        |
| `readinessProbe`     | `GET /health` every 5s, 5s delay             | Removes pod from LB while it starts up     |
| `securityContext`    | runAsNonRoot=true, runAsUser=999             | Follows principle of least privilege       |


### `service.yml`

Exposes the Deployment to external traffic via NodePort.


| Field        | Value                      | Rationale                                     |
| ------------ | -------------------------- | --------------------------------------------- |
| `type`       | NodePort                   | Sufficient for local cluster without cloud LB |
| `port`       | 80                         | Standard HTTP port on the service             |
| `targetPort` | 5000                       | Port the container listens on                 |
| `nodePort`   | 30080                      | Fixed port for predictable access             |
| `selector`   | `app: devops-info-service` | Matches all Deployment pods                   |


---

## 3. Deployment Evidence

### `kubectl cluster-info`

```
Kubernetes control plane is running at https://192.168.49.2:8443
CoreDNS is running at https://192.168.49.2:8443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```

### `kubectl get nodes`

```
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   56s   v1.34.0
```

### `kubectl get all`

```
NAME                                       READY   STATUS    RESTARTS   AGE
pod/devops-info-service-6678487559-5klnq   1/1     Running   0          24s
pod/devops-info-service-6678487559-7z2lx   1/1     Running   0          32s
pod/devops-info-service-6678487559-dj4lj   1/1     Running   0          15s
pod/devops-info-service-6678487559-sbfmb   1/1     Running   0          40s
pod/devops-info-service-6678487559-w2v5j   1/1     Running   0          48s

NAME                          TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service   NodePort    10.99.31.119   <none>        80:30080/TCP   2m41s
service/kubernetes            ClusterIP   10.96.0.1      <none>        443/TCP        3m18s

NAME                                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service   5/5     5            5           2m45s

NAME                                             DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-info-service-6678487559   5         5         5       2m45s
replicaset.apps/devops-info-service-846944df8b   0         0         0       99s
```

### `kubectl get pods,svc -o wide`

```
NAME                                       READY   STATUS    RESTARTS   AGE   IP            NODE       NOMINATED NODE   READINESS GATES
pod/devops-info-service-6678487559-5klnq   1/1     Running   0          29s   10.244.0.16   minikube   <none>           <none>
pod/devops-info-service-6678487559-7z2lx   1/1     Running   0          37s   10.244.0.15   minikube   <none>           <none>
pod/devops-info-service-6678487559-dj4lj   1/1     Running   0          20s   10.244.0.17   minikube   <none>           <none>
pod/devops-info-service-6678487559-sbfmb   1/1     Running   0          45s   10.244.0.14   minikube   <none>           <none>
pod/devops-info-service-6678487559-w2v5j   1/1     Running   0          53s   10.244.0.13   minikube   <none>           <none>

NAME                          TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE     SELECTOR
service/devops-info-service   NodePort    10.99.31.119   <none>        80:30080/TCP   2m46s   app=devops-info-service
service/kubernetes            ClusterIP   10.96.0.1      <none>        443/TCP        3m23s   <none>
```

### `kubectl describe deployment devops-info-service`

```
Name:                   devops-info-service
Namespace:              default
Labels:                 app=devops-info-service
                        version=1.0.0
Replicas:               5 desired | 5 updated | 5 total | 5 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Pod Template:
  Containers:
   devops-info-service:
    Image:      lanebo1/devops-info-service:latest
    Port:       5000/TCP
    Limits:     cpu: 200m, memory: 256Mi
    Requests:   cpu: 100m, memory: 128Mi
    Liveness:   http-get http://:5000/health delay=15s timeout=5s period=10s #failure=3
    Readiness:  http-get http://:5000/health delay=5s timeout=3s period=5s #failure=3
Conditions:
  Available      True    MinimumReplicasAvailable
  Progressing    True    NewReplicaSetAvailable
```

### App working (curl output)

```bash
$ curl http://192.168.49.2:30080/health
{"status":"healthy","timestamp":"2026-03-26T18:46:00.907238+00:00","uptime_seconds":15}

$ curl http://192.168.49.2:30080/
{
  "service": {"name": "devops-info-service", "version": "1.0.0", ...},
  "system": {"hostname": "devops-info-service-6678487559-t6mj9", "platform": "Linux", ...},
  ...
}
```

---

## 4. Operations Performed

### Deploy

```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl rollout status deployment/devops-info-service
```

### Scale to 5 Replicas

```bash
kubectl scale deployment/devops-info-service --replicas=5
kubectl rollout status deployment/devops-info-service
# Output:
# Waiting for deployment "devops-info-service" rollout to finish: 3 of 5 updated replicas are available...
# Waiting for deployment "devops-info-service" rollout to finish: 4 of 5 updated replicas are available...
# deployment "devops-info-service" successfully rolled out
```

### Rolling Update

```bash
kubectl set env deployment/devops-info-service APP_VERSION=v1.1.0
kubectl rollout status deployment/devops-info-service
# Output (rolling, 1 pod at a time, maxUnavailable=0):
# Waiting for deployment "devops-info-service" rollout to finish: 1 out of 5 new replicas have been updated...
# Waiting for deployment "devops-info-service" rollout to finish: 2 out of 5 new replicas have been updated...
# ...
# deployment "devops-info-service" successfully rolled out
```

### Rollback

```bash
kubectl rollout history deployment/devops-info-service
# REVISION  CHANGE-CAUSE
# 1         Initial deployment v1.0.0
# 2         Rolling update: added APP_VERSION=v1.1.0 env var

kubectl rollout undo deployment/devops-info-service
# deployment.apps/devops-info-service rolled back

kubectl rollout status deployment/devops-info-service
# deployment "devops-info-service" successfully rolled out
```

### Service Access

```bash
minikube service devops-info-service --url
# http://192.168.49.2:30080

curl http://192.168.49.2:30080/health
# {"status":"healthy",...}
```

---

## 5. Production Considerations

### Health Checks

- **Liveness probe** (`GET /health`, 15s delay, 10s period): Detects containers that are running but stuck in a bad state (deadlock, memory corruption). Kubernetes will restart them automatically.
- **Readiness probe** (`GET /health`, 5s delay, 5s period): Prevents premature traffic routing. The pod only enters the Service endpoint pool once it responds `200 OK`. This is critical during rolling updates — new pods must pass readiness before old ones are removed, ensuring zero downtime.

### Resource Limits Rationale

- **Requests (100m CPU, 128Mi):** The scheduler uses these to place pods on nodes. Set conservatively so the scheduler has accurate information.
- **Limits (200m CPU, 256Mi):** Cap resource consumption to prevent one misbehaving pod from starving others. The 2× multiplier allows CPU burst for occasional spikes without allowing runaway usage.

### Production Improvements

1. **Separate namespaces** per environment (dev/staging/prod) for isolation
2. **HorizontalPodAutoscaler** to scale replicas based on CPU/memory metrics automatically
3. **PodDisruptionBudget** to ensure minimum availability during node maintenance
4. **Image pinning** — use a specific digest instead of `:latest` for reproducible deployments
5. **ConfigMaps and Secrets** to manage configuration separately from the image
6. **NetworkPolicies** to restrict pod-to-pod communication
7. **Resource quotas** per namespace to prevent one team from consuming all cluster resources

### Monitoring and Observability

- The app already exposes **Prometheus metrics** at `/metrics`
- Deploy **Prometheus + Grafana** (e.g., via `kube-prometheus-stack` Helm chart) to scrape and visualize metrics
- Use **kubectl top pods** (requires metrics-server) for basic resource monitoring
- Centralize logs with **Loki** or an EFK stack (Elasticsearch + Fluentd + Kibana)
- Set up **alerting rules** in Prometheus for pod crash loops, high error rates, and resource exhaustion

---

## 6. Challenges & Solutions

### Challenge 1: Docker socket permissions

The user was not in the `docker` group, so `minikube start --driver=docker` failed with a socket permission error.

**Solution:** Added the user to the `docker` group (`usermod -aG docker`) and used `sg docker` to apply the group change in the current shell session without logout.

### Challenge 2: Choosing `minikube` vs `kind`

Both tools were installed. **Minikube** was chosen because:

- It provides a full VM-backed cluster that more closely resembles production node architecture
- Has built-in addon support (`minikube addons enable ingress`, metrics-server, etc.)
- `minikube service` command makes NodePort access trivial in local dev
- `kind` (Kubernetes in Docker) is excellent for CI/CD pipelines but requires extra port mapping for NodePort services

### Challenge 3: Non-root security context compatibility

The Dockerfile already creates a non-root user (`appuser`, uid 999). The pod security context (`runAsUser: 999`) was set to match, avoiding permission errors on the filesystem.

### Key Learnings

- **Declarative over imperative**: `kubectl apply -f` is idempotent and version-controlled; imperative commands are for quick testing only
- **Labels are the backbone**: The selector mechanism connecting Deployments → ReplicaSets → Pods → Services all relies on consistent label matching
- **Readiness ≠ Liveness**: Readiness controls traffic routing; liveness controls container restarts — both are needed in production
- **Rollout history requires change-cause annotation**: Without `kubernetes.io/change-cause`, history is opaque; always annotate deployments
- **maxUnavailable=0** is the key to zero-downtime: Kubernetes won't terminate old pods until new ones are ready

