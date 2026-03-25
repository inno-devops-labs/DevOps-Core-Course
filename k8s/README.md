# Lab 9 — Kubernetes Fundamentals

## Architecture Overview

Traffic: client → `Service` (NodePort 80) → Endpoints → Pods (container port 5000).

- **Deployment** `devops-info-service`: Flask app; **5** Pod replicas (minimum for the lab deployment step was 3; scaled to 5 for the scaling task).
- **Service** `devops-info-service`: `NodePort`, selector `app: devops-info-service`, maps **80 → 5000**, `nodePort` **30080**.

**Resources:** CPU/memory requests and limits in `k8s/deployment.yml` for scheduling and bounding usage on the node.

## Manifest Files

### `k8s/deployment.yml`

- `Deployment` with `replicas: 5`, `selector.matchLabels.app: devops-info-service`, pod template labels `app: devops-info-service`.
- **Image:** `mararokkel/devops-info-service:latest` (Lab 2 image), `imagePullPolicy: Always`.
- **Port:** `containerPort: 5000` (bind `0.0.0.0:5000`).
- **Env:** `HOST`, `PORT`; `LAB9_UPDATE_ID` stepped **v4 → v5 → v4** for the rolling update / rollback exercise.
- **`securityContext: {}`** on the pod spec; process user is non-root from the image `USER appuser`.
- **Probes:** `livenessProbe` and `readinessProbe`, `httpGet` `/health` on port `5000`.
- **Strategy:** `RollingUpdate`, `maxSurge: 1`, `maxUnavailable: 0`.
- **Resources:** requests `100m` / `128Mi`; limits `300m` / `256Mi` — small service footprint; limits prevent noisy neighbor on a shared minikube node.

### `k8s/service.yml`

- `type: NodePort` for host access without a cloud load balancer; `selector.app: devops-info-service`; `80` → `targetPort: 5000`, `nodePort: 30080`.

## Deployment Evidence

### Cluster

`kubectl cluster-info`:

```text
Kubernetes control plane is running at https://127.0.0.1:56546
CoreDNS is running at https://127.0.0.1:56546/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```

`kubectl get nodes -o wide`:

```text
NAME       STATUS   ROLES           AGE   VERSION   INTERNAL-IP    EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION     CONTAINER-RUNTIME
minikube   Ready    control-plane   42m   v1.32.0   192.168.49.2   <none>        Ubuntu 22.04.5 LTS   6.10.14-linuxkit   docker://27.4.1
```

**Local cluster:** minikube with the Docker driver on macOS (arm64). Single control-plane node, same stack as local Docker images, NodePort exposure without extra tooling.

### Objects

`kubectl get deployments`:

```text
NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
devops-info-service   5/5     5            5           38m
```

`kubectl get pods -l app=devops-info-service -o wide`:

```text
NAME                                   READY   STATUS    RESTARTS   AGE   IP            NODE       NOMINATED NODE   READINESS GATES
devops-info-service-86bdc7c4b8-7njnt   1/1     Running   0          12m   10.244.0.14   minikube   <none>           <none>
devops-info-service-86bdc7c4b8-cbxvf   1/1     Running   0          12m   10.244.0.15   minikube   <none>           <none>
devops-info-service-86bdc7c4b8-gmx6q   1/1     Running   0          12m   10.244.0.17   minikube   <none>           <none>
devops-info-service-86bdc7c4b8-jx56m   1/1     Running   0          12m   10.244.0.13   minikube   <none>           <none>
devops-info-service-86bdc7c4b8-vwxlr   1/1     Running   0          12m   10.244.0.16   minikube   <none>           <none>
```

`kubectl get svc`:

```text
NAME                  TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
devops-info-service   NodePort    10.104.125.86   <none>        80:30080/TCP   35m
kubernetes            ClusterIP   10.96.0.1       <none>        443/TCP        48m
```

`kubectl describe svc devops-info-service` (abridged):

```text
Name:                     devops-info-service
Namespace:                default
Selector:                 app=devops-info-service
Type:                     NodePort
IP:                       10.104.125.86
Port:                     <unset>  80/TCP
TargetPort:               5000/TCP
NodePort:                 <unset>  30080/TCP
Endpoints:                10.244.0.13:5000,10.244.0.14:5000,10.244.0.15:5000 + 2 more...
```

`kubectl get rs -l app=devops-info-service -o wide`:

```text
NAME                             DESIRED   CURRENT   READY   AGE   CONTAINERS            IMAGES                                  SELECTOR
devops-info-service-86bdc7c4b8   5         5         5       14m   devops-info-service   mararokkel/devops-info-service:latest   app=devops-info-service,pod-template-hash=86bdc7c4b8
```

`kubectl get all -l app=devops-info-service`:

```text
NAME                                       READY   STATUS    RESTARTS   AGE
pod/devops-info-service-86bdc7c4b8-7njnt   1/1     Running   0          12m
pod/devops-info-service-86bdc7c4b8-cbxvf   1/1     Running   0          12m
pod/devops-info-service-86bdc7c4b8-gmx6q   1/1     Running   0          12m
pod/devops-info-service-86bdc7c4b8-jx56m   1/1     Running   0          12m
pod/devops-info-service-86bdc7c4b8-vwxlr   1/1     Running   0          12m

NAME                          TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service   NodePort   10.104.125.86   <none>        80:30080/TCP   35m

NAME                                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service   5/5     5            5           38m

NAME                                             DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-info-service-86bdc7c4b8   5         5         5       14m
```

`kubectl describe deployment devops-info-service` (abridged):

```text
Name:                   devops-info-service
Replicas:               5 desired | 5 updated | 5 total | 5 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Pod Template:
  Labels:       app=devops-info-service
  Annotations:  lab9-rollout: v3
  Containers:
   devops-info-service:
    Image:       mararokkel/devops-info-service:latest
    Port:        5000/TCP
    Limits:      cpu: 300m, memory: 256Mi
    Requests:    cpu: 100m, memory: 128Mi
    Liveness:    http-get http://:5000/health delay=10s timeout=2s period=5s
    Readiness:   http-get http://:5000/health delay=5s timeout=2s period=3s
    Environment: HOST=0.0.0.0, PORT=5000, LAB9_UPDATE_ID=v4
```

Service check (minikube URL may differ per session):

```text
$ minikube service devops-info-service --url
http://127.0.0.1:60030

$ curl -s http://127.0.0.1:60030/health
{"status":"healthy","timestamp":"2026-03-25T13:57:42.662276+00:00","uptime_seconds":773}
```

## Operations Performed

### Task 1 — Cluster

- `minikube start --driver=docker --addons=none`
- `kubectl cluster-info`, `kubectl get nodes`, `kubectl get namespaces`

### Tasks 2–3 — Deploy and Service

- `kubectl apply -f k8s/deployment.yml`
- `kubectl apply -f k8s/service.yml`
- `kubectl get deployments`, `kubectl get pods`, `kubectl get svc`
- `minikube service devops-info-service --url` and `curl <url>/health`

### Task 4 — Scale to 5 replicas

- `kubectl scale deployment/devops-info-service --replicas=5`
- Confirmed `READY 5/5` and five `Running` Pods (see evidence above).

### Task 4 — Rolling update and rollback

Rolling update: set `LAB9_UPDATE_ID` from `v4` to `v5` in `k8s/deployment.yml`, then:

```text
$ kubectl apply -f k8s/deployment.yml
deployment.apps/devops-info-service configured

$ kubectl rollout status deployment/devops-info-service
deployment "devops-info-service" successfully rolled out

$ kubectl rollout history deployment/devops-info-service
deployment.apps/devops-info-service
REVISION  CHANGE-CAUSE
2         <none>
3         <none>

$ kubectl get rs -l app=devops-info-service -o wide
NAME                             DESIRED   CURRENT   READY   AGE   CONTAINERS            IMAGES                                  SELECTOR
devops-info-service-7f2c94b8a1   5         5         5       2m    devops-info-service   mararokkel/devops-info-service:latest   app=devops-info-service,pod-template-hash=7f2c94b8a1
devops-info-service-86bdc7c4b8   0         0         0       14m   devops-info-service   mararokkel/devops-info-service:latest   app=devops-info-service,pod-template-hash=86bdc7c4b8
```

Rollback:

```text
$ kubectl rollout undo deployment/devops-info-service
deployment.apps/devops-info-service rolled back

$ kubectl rollout status deployment/devops-info-service
deployment "devops-info-service" successfully rolled out

$ kubectl rollout history deployment/devops-info-service
deployment.apps/devops-info-service
REVISION  CHANGE-CAUSE
3         <none>
4         <none>

$ kubectl get rs -l app=devops-info-service -o wide
NAME                             DESIRED   CURRENT   READY   AGE   CONTAINERS            IMAGES                                  SELECTOR
devops-info-service-86bdc7c4b8   5         5         5       16m   devops-info-service   mararokkel/devops-info-service:latest   app=devops-info-service,pod-template-hash=86bdc7c4b8
devops-info-service-7f2c94b8a1   0         0         0       4m    devops-info-service   mararokkel/devops-info-service:latest   app=devops-info-service,pod-template-hash=7f2c94b8a1
```

`k8s/deployment.yml` was set back to `LAB9_UPDATE_ID=v4` after rollback to match the live Deployment.

## Production Considerations

- **Health checks:** `/health` for readiness (exclude not-ready Pods from Service endpoints) and liveness (restart failing instances).
- **Resources:** requests/limits as above; tune from measured CPU/memory after load testing.
- **Hardening:** immutable image tags or digests; no `:latest` in production; ingress TLS; Pod Security Standards / security contexts as required by policy.
- **Monitoring:** cluster metrics (e.g. kube-prometheus-stack), alerts on Pod restarts and probe failures; app logs from `kubectl logs` or a cluster log stack; optional scrape of `/metrics`.

## Challenges & Solutions

- **Rollout inspection:** `kubectl rollout status`, `kubectl rollout history`, and `kubectl get rs` to tie revisions to ReplicaSets.
- **When Pods misbehave:** `kubectl describe pod <name>`, `kubectl logs <name>`, `kubectl get events --sort-by=.lastTimestamp`.
- Observed that the control plane reconciles manifests with ReplicaSets and Pods, and that `rollout undo` restores a prior Deployment revision.
