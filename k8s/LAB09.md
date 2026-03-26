# Lab 9 — Kubernetes Fundamentals

## Architecture Overview

```
                        ┌─────────────────────────────────────────────┐
                        │              Kubernetes Cluster              │
                        │                                              │
  External Traffic      │  ┌──────────────────────────────────────┐   │
  ─────────────────►    │  │          Ingress (devops.local)       │   │
                        │  │  /app1 → devops-python-service        │   │
   NodePort :30080 ─────►  │  /app2 → devops-go-service            │   │
   NodePort :30081 ─────►  └──────────┬──────────────┬────────────┘   │
                        │             │              │                 │
                        │  ┌──────────▼──┐    ┌──────▼────────┐       │
                        │  │   Service   │    │    Service    │       │
                        │  │ python :80  │    │   go :80      │       │
                        │  └──────┬──────┘    └──────┬────────┘       │
                        │         │                  │                 │
                        │  ┌──────▼──────┐    ┌──────▼────────┐       │
                        │  │  Deployment │    │  Deployment   │       │
                        │  │   Python    │    │      Go       │       │
                        │  │ 3 replicas  │    │  2 replicas   │       │
                        │  │  port 5001  │    │   port 8080   │       │
                        │  └─────────────┘    └───────────────┘       │
                        └─────────────────────────────────────────────┘
```

**Deployment summary:**
- `devops-python`: 3 replicas, Flask app on port 5001
- `devops-go`: 2 replicas, Go app on port 8080
- `devops-python-service`: NodePort 30080 → pod 5001
- `devops-go-service`: NodePort 30081 → pod 8080
- `devops-ingress`: path-based routing with TLS at `devops.local`

**Resource allocation:**
- Python pod: requests 100m CPU / 128Mi RAM, limits 200m CPU / 256Mi RAM
- Go pod: requests 50m CPU / 64Mi RAM, limits 100m CPU / 128Mi RAM (Go is more efficient)

---

## Manifest Files

### deployment.yml
Deploys the Python Flask app (`mirana18/devops-info-service:latest`).

Key choices:
- **3 replicas** — minimum required, provides basic high availability
- **RollingUpdate** with `maxUnavailable: 0` — zero-downtime updates guaranteed
- **liveness probe** — restarts the pod if `/health` stops responding
- **readiness probe** — removes pod from service until it is ready to handle traffic
- **non-root user** — already configured in the Docker image (uid 1001)

### service.yml
Exposes the Python app via `NodePort 30080`. Port mapping: `30080 → 80 → 5001`.

### deployment-go.yml
Deploys the Go app (`mirana18/devops-info-service-go:latest`).

Key choices:
- **2 replicas** — secondary app for bonus routing demo
- **Lower resource limits** — Go binary is lightweight compared to Python + Flask
- Same probe pattern on port 8080

### service-go.yml
Exposes the Go app via `NodePort 30081`. Port mapping: `30081 → 80 → 8080`.

### ingress.yml
Nginx Ingress with path-based routing and TLS termination:
- `/app1` → Python service
- `/app2` → Go service
- TLS cert stored in `devops-tls-secret`

---

## Deployment Evidence

### kubectl cluster-info
```
Kubernetes control plane is running at https://127.0.0.1:64281
CoreDNS is running at https://127.0.0.1:64281/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```

### kubectl get nodes
```
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   47m   v1.35.1
```

### kubectl get all
```
NAME                                 READY   STATUS    RESTARTS   AGE
pod/devops-go-68d65b674-ngczb        1/1     Running   0          22m
pod/devops-go-68d65b674-wt7xl        1/1     Running   0          22m
pod/devops-python-5cf85bf7cd-dkgc6   1/1     Running   0          22m
pod/devops-python-5cf85bf7cd-r5vzr   1/1     Running   0          21m
pod/devops-python-5cf85bf7cd-rhg68   1/1     Running   0          21m

NAME                            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-go-service       NodePort    10.103.11.114   <none>        80:30081/TCP   46m
service/devops-python-service   NodePort    10.109.104.29   <none>        80:30080/TCP   46m
service/kubernetes              ClusterIP   10.96.0.1       <none>        443/TCP        47m

NAME                            READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-go       2/2     2            2           46m
deployment.apps/devops-python   3/3     3            3           46m

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-go-68d65b674        2         2         2       22m
replicaset.apps/devops-go-84467c6d7c       0         0         0       46m
replicaset.apps/devops-python-5cf85bf7cd   3         3         3       22m
replicaset.apps/devops-python-d6c788997    0         0         0       46m
```

### kubectl get pods,svc -o wide
```
NAME                                 READY   STATUS    RESTARTS   AGE   IP            NODE       NOMINATED NODE   READINESS GATES
pod/devops-go-68d65b674-ngczb        1/1     Running   0          22m   10.244.0.8    minikube   <none>           <none>
pod/devops-go-68d65b674-wt7xl        1/1     Running   0          22m   10.244.0.10   minikube   <none>           <none>
pod/devops-python-5cf85bf7cd-dkgc6   1/1     Running   0          22m   10.244.0.9    minikube   <none>           <none>
pod/devops-python-5cf85bf7cd-r5vzr   1/1     Running   0          21m   10.244.0.13   minikube   <none>           <none>
pod/devops-python-5cf85bf7cd-rhg68   1/1     Running   0          21m   10.244.0.14   minikube   <none>           <none>

NAME                            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE   SELECTOR
service/devops-go-service       NodePort    10.103.11.114   <none>        80:30081/TCP   46m   app=devops-go
service/devops-python-service   NodePort    10.109.104.29   <none>        80:30080/TCP   46m   app=devops-python
service/kubernetes              ClusterIP   10.96.0.1       <none>        443/TCP        47m   <none>
```

### kubectl describe deployment devops-python
```
Name:                   devops-python
Namespace:              default
CreationTimestamp:      Thu, 26 Mar 2026 23:00:24 +0300
Labels:                 app=devops-python
                        version=1.0.0
Annotations:            deployment.kubernetes.io/revision: 4
Selector:               app=devops-python
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Pod Template:
  Labels:  app=devops-python
           version=1.0.0
  Containers:
   devops-python:
    Image:      mirana18/devops-info-service:latest
    Port:       5001/TCP
    Host Port:  0/TCP
    Limits:
      cpu:     200m
      memory:  256Mi
    Requests:
      cpu:      100m
      memory:   128Mi
    Liveness:   http-get http://:5001/health delay=10s timeout=1s period=10s #success=1 #failure=3
    Readiness:  http-get http://:5001/health delay=5s timeout=1s period=5s #success=1 #failure=3
    Environment:
      PORT:        5001
      HOST:        0.0.0.0
      DEBUG:       False
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing    True    NewReplicaSetAvailable
OldReplicaSets:  devops-python-d6c788997 (0/0 replicas created)
NewReplicaSet:   devops-python-5cf85bf7cd (3/3 replicas created)
Events:
  Type    Reason             Age                From                   Message
  ----    ------             ----               ----                   -------
  Normal  ScalingReplicaSet  46m                deployment-controller  Scaled up replica set devops-python-d6c788997 from 0 to 3
  Normal  ScalingReplicaSet  22m                deployment-controller  Scaled up replica set devops-python-5cf85bf7cd from 0 to 1
  Normal  ScalingReplicaSet  22m                deployment-controller  Scaled down replica set devops-python-d6c788997 from 3 to 2
  Normal  ScalingReplicaSet  22m                deployment-controller  Scaled up replica set devops-python-5cf85bf7cd from 1 to 2
  Normal  ScalingReplicaSet  22m                deployment-controller  Scaled down replica set devops-python-d6c788997 from 2 to 1
  Normal  ScalingReplicaSet  22m                deployment-controller  Scaled up replica set devops-python-5cf85bf7cd from 2 to 3
  Normal  ScalingReplicaSet  21m                deployment-controller  Scaled up replica set devops-python-5cf85bf7cd from 3 to 5
  Normal  ScalingReplicaSet  19m (x2 over 22m)  deployment-controller  Scaled down replica set devops-python-d6c788997 from 1 to 0
  Normal  ScalingReplicaSet  19m                deployment-controller  Scaled down replica set devops-python-5cf85bf7cd from 5 to 3
```

### curl — app is working
```
$ curl http://localhost:8080/health
{"status":"healthy","timestamp":"2026-03-26T20:48:44.439160.000Z","uptime_seconds":1457.41}

$ curl http://localhost:8080/
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"127.0.0.1","method":"GET","path":"/","user_agent":"curl/8.7.1"},"runtime":{"current_time":"2026-03-26T20:48:44.462315+00:00","timezone":"UTC","uptime_human":"0 hours, 24 minutes, 17 seconds","uptime_seconds":1457.43},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"aarch64","cpu_count":11,"hostname":"devops-python-5cf85bf7cd-dkgc6","platform":"Linux","platform_version":"6.12.67-linuxkit","python_version":"3.13.12"}}
```

---

## Operations Performed

### Deploy all resources
```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl apply -f k8s/deployment-go.yml
kubectl apply -f k8s/service-go.yml
```

Output:
```
deployment.apps/devops-python created
service/devops-python-service created
deployment.apps/devops-go created
service/devops-go-service created
```

### Access the app
```bash
kubectl port-forward service/devops-python-service 8080:80
curl http://localhost:8080/health
```

Output:
```
{"status":"healthy","timestamp":"2026-03-26T20:48:44.439160.000Z","uptime_seconds":1457.41}
```

### Scale to 5 replicas
```bash
kubectl scale deployment/devops-python --replicas=5
kubectl get pods
```

Output:
```
deployment.apps/devops-python scaled

NAME                             READY   STATUS    RESTARTS   AGE
devops-go-68d65b674-ngczb        1/1     Running   0          23m
devops-go-68d65b674-wt7xl        1/1     Running   0          22m
devops-python-5cf85bf7cd-dkgc6   1/1     Running   0          23m
devops-python-5cf85bf7cd-r5vzr   1/1     Running   0          22m
devops-python-5cf85bf7cd-rb7ld   1/1     Running   0          8s
devops-python-5cf85bf7cd-rhg68   1/1     Running   0          22m
devops-python-5cf85bf7cd-ttxb2   1/1     Running   0          8s
```

### Rolling update
```bash
kubectl apply -f k8s/deployment.yml
kubectl rollout status deployment/devops-python
```

Output:
```
deployment.apps/devops-python configured
deployment "devops-python" successfully rolled out
```

### View rollout history and rollback
```bash
kubectl rollout history deployment/devops-python
kubectl rollout undo deployment/devops-python
kubectl rollout status deployment/devops-python
```

Output:
```
REVISION  CHANGE-CAUSE
3         <none>
4         <none>

deployment.apps/devops-python rolled back
deployment "devops-python" successfully rolled out
```

### Bonus — Ingress with TLS

```bash
minikube addons enable ingress
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=devops.local/O=devops.local"
kubectl create secret tls devops-tls-secret --key tls.key --cert tls.crt
kubectl apply -f k8s/ingress.yml
kubectl get ingress
```

Output:
```
NAME             CLASS   HOSTS          ADDRESS        PORTS     AGE
devops-ingress   nginx   devops.local   192.168.49.2   80, 443   10m
```

```bash
kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 8443:443
curl -sk --resolve "devops.local:8443:127.0.0.1" https://devops.local:8443/app1/health
curl -sk --resolve "devops.local:8443:127.0.0.1" https://devops.local:8443/app2/health
```

Output:
```
# /app1 → Python app
{"status":"healthy","timestamp":"2026-03-26T20:49:00.910020+00:00","uptime_seconds":1473.88,...,"service":{"framework":"Flask","name":"devops-info-service",...}}

# /app2 → Go app
{"service":{"name":"devops-info-service","framework":"Go net/http",...},"runtime":{"uptime_seconds":1466.32,...}}
```

---

## Production Considerations

### Health checks
- **Liveness probe** on `/health` restarts stuck or crashed containers automatically.
- **Readiness probe** ensures no traffic is sent before the app finishes starting up. This matters for Flask since it has a startup phase.
- `initialDelaySeconds: 10` gives the app time to initialize before the first check.

### Resource limits rationale
- **Requests** define the minimum guaranteed resources for scheduling. Without them the scheduler cannot place pods efficiently.
- **Limits** protect other pods on the same node from resource starvation caused by a misbehaving container.
- Python: `256Mi` RAM limit is safe for Flask + prometheus_client. Go needs far less (`128Mi`) due to lower runtime overhead.

### Production improvements
- Use a specific image tag (e.g., `v1.2.3`) instead of `latest` to make deployments reproducible and auditable.
- Add `PodDisruptionBudget` to guarantee minimum available replicas during node maintenance.
- Use `HorizontalPodAutoscaler` (HPA) based on CPU/memory metrics for automatic scaling.
- Store secrets (API keys, DB passwords) in Kubernetes `Secret` resources, not in env vars in the manifest.
- Use `livenessProbe.failureThreshold` tuning: current `3` means restart after 3 failed checks × 10s = 30s, which is reasonable.

### Monitoring and observability
- The Python app already exposes `/metrics` in Prometheus format — connect a Prometheus + Grafana stack (as in Lab 7/8).
- Use `kubectl logs -f <pod>` for live log streaming.
- Integrate with a log aggregator (Loki/Fluentd) for centralized logging across replicas.

---

## Challenges & Solutions

### Challenge 1: Image pull errors (ErrImagePull / ImagePullBackOff)
Images were built only for `linux/amd64` but minikube on Apple Silicon (arm64) requires `linux/arm64`.

```bash
kubectl describe pod <pod-name>
# Events showed: no matching manifest for linux/arm64/v8 in the manifest list entries
```

Fix: build images directly inside minikube's Docker daemon using `eval $(minikube docker-env)` and set `imagePullPolicy: Never`.

```bash
eval $(minikube docker-env)
docker build --platform linux/arm64 -t mirana18/devops-info-service:latest ./app_python/
```

### Challenge 2: Pods not ready
If readiness probe fails, pod stays in `0/1 Running` state. Debug:

```bash
kubectl logs <pod-name>
kubectl describe pod <pod-name>
# check Events and Last State sections
```

### Challenge 3: NodePort not accessible on macOS Docker driver
minikube with Docker driver on macOS doesn't expose node IP directly to the host.

Fix: use `kubectl port-forward` instead:
```bash
kubectl port-forward service/devops-python-service 8080:80
```

### Challenge 4: Ingress — use port-forward instead of direct IP
Same networking limitation. Use:
```bash
kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 8443:443
curl -sk --resolve "devops.local:8443:127.0.0.1" https://devops.local:8443/app1/health
```

### What I learned
- Kubernetes reconciliation loop: you describe desired state, the controller continuously works to match it.
- Labels are the glue between Deployments and Services — they must match exactly.
- `RollingUpdate` with `maxUnavailable: 0` guarantees zero downtime but requires at least 2 replicas to be useful.
- Probes are not optional in production — without them, traffic can reach a container that is not ready yet.
- On Apple Silicon, Docker images must be built for `linux/arm64` or use multi-arch manifests.
- Ingress provides L7 routing (host/path-based) and TLS termination — much more flexible than NodePort.
