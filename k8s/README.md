# Kubernetes Deployment — DevOps Info Service

Related docs:
- `k8s/HELM.md`
- `k8s/SECRETS.md`
- `k8s/CONFIGMAPS.md`
- `k8s/ARGOCD.md`

## 1. Architecture Overview

```
                        ┌─────────────────────────────────────────────┐
                        │              minikube cluster                │
                        │                                              │
  External traffic      │  ┌──────────────────────────────────────┐   │
  ─────────────────────►│  │  Ingress (nginx) — devops.local       │   │
   HTTPS :443           │  │  /app1 ──► devops-info-service        │   │
                        │  │  /app2 ──► devops-info-service-v2     │   │
                        │  └──────────────────────────────────────┘   │
                        │           │                    │             │
  External traffic      │  ┌────────▼──────┐  ┌─────────▼──────────┐ │
  ─────────────────────►│  │ Service        │  │ Service            │ │
   NodePort :30080      │  │ NodePort 30080 │  │ ClusterIP          │ │
                        │  └────────┬──────┘  └─────────┬──────────┘ │
                        │           │                    │             │
                        │  ┌────────▼──────┐  ┌─────────▼──────────┐ │
                        │  │  Deployment   │  │  Deployment        │ │
                        │  │  3 replicas   │  │  2 replicas        │ │
                        │  │  app v1       │  │  app v2            │ │
                        │  └───────────────┘  └────────────────────┘ │
                        └─────────────────────────────────────────────┘
```

**Resource allocation:**
- App v1: 3 replicas × (100m CPU / 64Mi RAM) requests, (200m CPU / 128Mi RAM) limits
- App v2: 2 replicas × same resource profile
- Rolling update: `maxSurge: 1`, `maxUnavailable: 0` — zero downtime guaranteed

---

## 2. Manifest Files

### `deployment.yml`
Main application Deployment. Key choices:
- **3 replicas** — minimum for high availability; one pod can be lost without downtime
- **`runAsNonRoot: true` + `runAsUser: 1000`** — matches the `appuser` from the Dockerfile, prevents container escape privilege escalation
- **Liveness probe on `/health`** — restarts the container if the Flask app becomes unresponsive
- **Readiness probe on `/ready`** — removes the pod from the Service load balancer during startup or degradation, preventing traffic to unready instances
- **`maxUnavailable: 0`** — during rolling updates, never reduce capacity below current; new pods must be ready before old ones terminate

### `service.yml`
NodePort Service for app v1. Key choices:
- **NodePort 30080** — fixed port for predictable local access; range 30000–32767
- **`port: 80 → targetPort: 5001`** — external callers use standard HTTP port 80, traffic is translated to the container's actual port 5001
- Doubles as the Ingress backend for `/app1` — no separate ClusterIP Service needed

### `deployment-app2.yml`
Second application Deployment + ClusterIP Service in one file. Identical image with `APP_INSTANCE=v2` env var to distinguish instances. Uses ClusterIP only — it's only reachable through the Ingress, not directly.

### `ingress.yml`
NGINX Ingress with path-based routing and TLS termination. Routes `/app1` and `/app2` to their respective services. The `rewrite-target: /` annotation strips the path prefix so the upstream Flask app receives requests at `/` rather than `/app1`.

---

## 3. Deployment Evidence

### Cluster setup
```
$ kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:61501
CoreDNS is running at https://127.0.0.1:61501/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

$ kubectl get nodes
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   43s   v1.35.1
```

### Pods coming up (readiness probes in action)
```
$ kubectl get pods -w
NAME                                   READY   STATUS              RESTARTS   AGE
devops-info-service-6f6c86c964-4j2kn   0/1     ContainerCreating   0          8s
devops-info-service-6f6c86c964-6x4wm   0/1     ContainerCreating   0          8s
devops-info-service-6f6c86c964-vkllh   0/1     ContainerCreating   0          8s
devops-info-service-6f6c86c964-vkllh   0/1     Running             0          24s
devops-info-service-6f6c86c964-6x4wm   0/1     Running             0          25s
devops-info-service-6f6c86c964-4j2kn   0/1     Running             0          28s
devops-info-service-6f6c86c964-vkllh   1/1     Running             0          36s
devops-info-service-6f6c86c964-6x4wm   1/1     Running             0          37s
devops-info-service-6f6c86c964-4j2kn   1/1     Running             0          39s
```
Note the `0/1 Running` → `1/1 Running` transition: the pod is running but the readiness probe hasn't passed yet — it's not sent traffic until `1/1`.

### All resources
```
$ kubectl get all
NAME                                       READY   STATUS    RESTARTS   AGE
pod/devops-info-service-6f6c86c964-4j2kn   1/1     Running   0          67s
pod/devops-info-service-6f6c86c964-6x4wm   1/1     Running   0          67s
pod/devops-info-service-6f6c86c964-vkllh   1/1     Running   0          67s

NAME                          TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service   NodePort    10.98.141.56   <none>        80:30080/TCP   63s
service/kubernetes            ClusterIP   10.96.0.1      <none>        443/TCP        5m9s

NAME                                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service   3/3     3            3           67s

NAME                                             DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-info-service-6f6c86c964   3         3         3       67s
```

### App responding
```
$ curl http://127.0.0.1:61857/health
{"status":"healthy","timestamp":"2026-03-24T17:22:23.213915+00:00","uptime_seconds":212}
```

### Deployment details
```
$ kubectl describe deployment devops-info-service
Name:                   devops-info-service
Namespace:              default
CreationTimestamp:      Tue, 24 Mar 2026 20:18:22 +0300
Labels:                 app=devops-info-service
                        version=1.0
Annotations:            deployment.kubernetes.io/revision: 3
Selector:               app=devops-info-service
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Pod Template:
  Labels:  app=devops-info-service
           version=1.0
  Containers:
   devops-info-service:
    Image:      plaffyyy9/devops-info-service:lab9
    Port:       5001/TCP
    Host Port:  0/TCP
    Limits:
      cpu:     200m
      memory:  128Mi
    Requests:
      cpu:      100m
      memory:   64Mi
    Liveness:   http-get http://:5001/health delay=10s timeout=1s period=15s #success=1 #failure=3
    Readiness:  http-get http://:5001/ready delay=5s timeout=1s period=10s #success=1 #failure=3
    Environment:
      HOST:   0.0.0.0
      PORT:   5001
      DEBUG:  false
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing    True    NewReplicaSetAvailable
OldReplicaSets:  devops-info-service-65c757fbfc (0/0 replicas created)
NewReplicaSet:   devops-info-service-6f6c86c964 (3/3 replicas created)
Events:
  Normal  ScalingReplicaSet  17m    Scaled up   devops-info-service-6f6c86c964 from 0 to 3
  Normal  ScalingReplicaSet  13m    Scaled up   devops-info-service-6f6c86c964 from 3 to 5
  Normal  ScalingReplicaSet  10m    Scaled down devops-info-service-6f6c86c964 from 5 to 3
  Normal  ScalingReplicaSet  10m    Scaled up   devops-info-service-65c757fbfc from 0 to 1
  Normal  ScalingReplicaSet  9m11s  Scaled down devops-info-service-65c757fbfc from 1 to 0
```

### Ingress controller
```
$ kubectl get pods -n ingress-nginx
NAME                                        READY   STATUS      RESTARTS   AGE
ingress-nginx-admission-create-26l84        0/1     Completed   0          108s
ingress-nginx-admission-patch-f785m         0/1     Completed   0          108s
ingress-nginx-controller-596f8778bc-8xnxs   1/1     Running     0          108s
```

---

## 4. Operations Performed

### Deploy
```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
minikube service devops-info-service --url
```

### Scale to 5 replicas
```bash
$ kubectl scale deployment/devops-info-service --replicas=5
deployment.apps/devops-info-service scaled

$ kubectl get pods
NAME                                   READY   STATUS    RESTARTS   AGE
devops-info-service-6f6c86c964-4j2kn   1/1     Running   0          4m48s
devops-info-service-6f6c86c964-6t5cz   1/1     Running   0          19s
devops-info-service-6f6c86c964-6x4wm   1/1     Running   0          4m48s
devops-info-service-6f6c86c964-vkllh   1/1     Running   0          4m48s
devops-info-service-6f6c86c964-xpp8m   1/1     Running   0          19s
```

### Rolling update (image tag → lab9-temp)
```bash
# Edit deployment.yml image to :lab9-temp, then:
$ kubectl apply -f k8s/deployment.yml
$ kubectl rollout status deployment/devops-info-service
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 3 new replicas have been updated...

$ kubectl rollout history deployment/devops-info-service
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
```
The rollout stalled because `lab9-temp` does not exist on Docker Hub — the new pod failed to pull the image. Because `maxUnavailable: 0`, the old pods were never terminated — zero downtime was maintained.

### Rollback
```bash
$ kubectl rollout undo deployment/devops-info-service
deployment.apps/devops-info-service rolled back

$ kubectl rollout status deployment/devops-info-service
deployment "devops-info-service" successfully rolled out

$ kubectl get pods
NAME                                   READY   STATUS    RESTARTS   AGE
devops-info-service-6f6c86c964-4j2kn   1/1     Running   0          9m9s
devops-info-service-6f6c86c964-6x4wm   1/1     Running   0          9m9s
devops-info-service-6f6c86c964-vkllh   1/1     Running   0          9m9s
```
Original three pods restored, running the original `lab9` image.

### Bonus — Ingress with TLS
```bash
# Enable Ingress controller
minikube addons enable ingress

# Deploy second app
kubectl apply -f k8s/deployment-app2.yml

# Apply Ingress
kubectl apply -f k8s/ingress.yml

# Generate self-signed TLS certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout k8s/tls.key -out k8s/tls.crt \
  -subj "/CN=devops.local/O=devops.local"

# Create TLS Secret
kubectl create secret tls devops-tls-secret \
  --key k8s/tls.key \
  --cert k8s/tls.crt

# Add minikube IP to /etc/hosts
echo "$(minikube ip) devops.local" | sudo tee -a /etc/hosts
# Result: 192.168.49.2 devops.local

# Test routing (requires minikube tunnel on macOS Docker driver)
minikube tunnel   # run in separate terminal
curl -k https://devops.local/app1
curl -k https://devops.local/app2
```

---

## 5. Production Considerations

### Health checks
Two separate probes serve distinct purposes:
- **Liveness (`/health`)** — detects a hung or crashed Flask process and triggers a container restart. `initialDelaySeconds: 10` gives the app time to boot before Kubernetes starts checking.
- **Readiness (`/ready`)** — prevents traffic from reaching pods that are starting up or temporarily degraded. The pod stays in the Service pool only while this probe passes.

### Resource limits
Requests and limits are both set deliberately small for a Python Flask app with minimal CPU work:
- `cpu: 100m` request — guarantees the scheduler places the pod on a node with spare capacity
- `memory: 128Mi` limit — prevents a memory leak from consuming the whole node; the OOM killer will restart the pod instead

For production, these values should be tuned from actual `kubectl top pods` measurements under load.

### Improvements for production
- Replace NodePort with a cloud LoadBalancer or Gateway API for proper external traffic management
- Add a `PodDisruptionBudget` to maintain minimum availability during node maintenance
- Use `HorizontalPodAutoscaler` to scale replicas automatically based on CPU/memory metrics
- Store the Docker image tag in a `ConfigMap` or use image digests (`sha256:...`) instead of mutable tags for reproducible deployments
- Add `NetworkPolicy` to restrict which pods can communicate with each other

### Monitoring and observability
The application already exposes `/metrics` in Prometheus format. In a production cluster this integrates with:
- **Prometheus Operator + ServiceMonitor** — auto-discovers services by label and scrapes metrics
- **Grafana** — the dashboard from Lab 8 works unchanged once Prometheus is pointed at the k8s service
- **Structured JSON logs** — already implemented; a Loki + Promtail stack (as in Lab 8) can collect them from pod stdout

---

## 6. Challenges & Solutions

### Ingress not reachable on macOS (Docker driver)
**Problem:** `curl -k https://devops.local/app1` hung indefinitely after adding the minikube IP to `/etc/hosts`.

**Cause:** minikube with the Docker driver on macOS runs inside a Docker network that is not directly routable from the host. The IP `192.168.49.2` is only reachable inside Docker's virtual network, not from the macOS network stack.

**Solution:** Run `minikube tunnel` in a separate terminal before testing. This creates a network route from the host into the minikube cluster and also assigns a routable IP to LoadBalancer-type services.

**Alternative:** Use `kubectl port-forward` to bypass the network issue entirely:
```bash
kubectl port-forward -n ingress-nginx \
  service/ingress-nginx-controller 8443:443
curl -k https://devops.local:8443/app1 --resolve devops.local:8443:127.0.0.1
```

### Readiness probe delay visible in pod watch
During the initial rollout, pods showed `0/1 Running` for ~10–30 seconds before becoming `1/1`. This is expected — the `initialDelaySeconds: 5` and the app's startup time mean the readiness probe takes a few cycles to pass. No action needed; this is the correct behaviour.

### Rolling update stalled on bad image tag
When the image was changed to `lab9-temp` (non-existent tag), the rollout stalled at "1 out of 3 new replicas updated" — the new pod entered `ErrImagePull`. Because `maxUnavailable: 0`, the old pods were never touched. This demonstrated the safety guarantee: a bad deployment cannot take down the running service. `kubectl rollout undo` restored the previous revision instantly.
