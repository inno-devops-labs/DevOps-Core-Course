# Lab 09 - Kubernetes Fundamentals

## 1. Architecture Overview

I used **Minikube** with the **Docker driver** because this repository already uses Docker, the setup works well on local WSL-based development machines, and `minikube service` makes NodePort access straightforward without needing a cloud load balancer.

Current deployment shape:

```text
Client (curl/browser)
  -> minikube service devops-info-service --url
  -> Service/devops-info-service (NodePort 80 -> 30080)
  -> Deployment/devops-info-service
  -> 3 Flask Pods listening on port 5000
```

Resource and rollout strategy:

- `replicas: 3` in the declarative manifest
- CPU request/limit: `100m` / `250m`
- Memory request/limit: `128Mi` / `256Mi`
- Rolling update strategy: `maxSurge: 1`, `maxUnavailable: 0`
- `minReadySeconds: 5` to avoid marking pods available too early
- Pod security: non-root numeric UID/GID `10001`, dropped capabilities, `RuntimeDefault` seccomp

## 2. Cluster Setup Evidence

Tooling used:

- `kubectl v1.35.3`
- `minikube v1.38.1`
- Docker driver with Kubernetes `v1.35.1`

Cluster startup:

```bash
minikube start --driver=docker
```

`kubectl cluster-info`:

```text
Kubernetes control plane is running at https://127.0.0.1:32771
CoreDNS is running at https://127.0.0.1:32771/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```

`kubectl get nodes -o wide`:

```text
NAME       STATUS   ROLES           AGE   VERSION   INTERNAL-IP    EXTERNAL-IP   OS-IMAGE                         KERNEL-VERSION                     CONTAINER-RUNTIME
minikube   Ready    control-plane   12s   v1.35.1   192.168.49.2   <none>        Debian GNU/Linux 12 (bookworm)   6.6.87.2-microsoft-standard-WSL2   docker://29.2.1
```

## 3. Manifest Files

### `k8s/deployment.yml`

This manifest creates the main application Deployment:

- Uses the local image `devops-info-service:lab09`
- Sets `imagePullPolicy: IfNotPresent` for local Minikube use
- Starts with `3` replicas
- Exposes container port `5000`
- Configures readiness and liveness probes against `GET /health`
- Adds requests and limits for CPU and memory
- Uses a rolling update strategy suitable for zero-downtime local demos
- Adds basic hardening with `runAsNonRoot`, explicit UID/GID, dropped capabilities, and `seccompProfile`

### `k8s/service.yml`

This manifest exposes the Deployment through a NodePort service:

- Service name: `devops-info-service`
- Service port: `80`
- Target port: named container port `http` (`5000`)
- NodePort: `30080`
- Selector: `app=devops-info-service`

### Supporting Changes

I also fixed two image/runtime issues that blocked Kubernetes deployment:

- Added [`app_python/app.py`](../app_python/app.py) as the top-level entrypoint used by Docker and local runs
- Updated [`app_python/Dockerfile`](../app_python/Dockerfile) to:
  - create a numeric non-root user (`UID 10001`)
  - use `/bin/sh` instead of invalid `sh`
  - copy only the runtime files required by the container

## 4. Deployment Evidence

Build, load, and apply:

```bash
docker build -t devops-info-service:lab09 ./app_python
minikube image load devops-info-service:lab09
kubectl apply -f k8s/deployment.yml -f k8s/service.yml
kubectl rollout status deployment/devops-info-service --timeout=180s
```

Final `kubectl get all`:

```text
NAME                                       READY   STATUS    RESTARTS   AGE
pod/devops-info-service-5cc99549bf-h6b6s   1/1     Running   0          102s
pod/devops-info-service-5cc99549bf-jf2qc   1/1     Running   0          113s
pod/devops-info-service-5cc99549bf-q5ggz   1/1     Running   0          2m8s

NAME                          TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service   NodePort    10.99.84.30   <none>        80:30080/TCP   6m21s
service/kubernetes            ClusterIP   10.96.0.1     <none>        443/TCP        8m11s

NAME                                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service   3/3     3            3           6m21s
```

Final `kubectl get pods,svc -o wide`:

```text
NAME                                       READY   STATUS    RESTARTS   AGE    IP            NODE       NOMINATED NODE   READINESS GATES
pod/devops-info-service-5cc99549bf-h6b6s   1/1     Running   0          102s   10.244.0.18   minikube   <none>           <none>
pod/devops-info-service-5cc99549bf-jf2qc   1/1     Running   0          113s   10.244.0.17   minikube   <none>           <none>
pod/devops-info-service-5cc99549bf-q5ggz   1/1     Running   0          2m8s   10.244.0.16   minikube   <none>           <none>

NAME                          TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE     SELECTOR
service/devops-info-service   NodePort    10.99.84.30   <none>        80:30080/TCP   6m21s   app=devops-info-service
```

`kubectl describe deployment devops-info-service` excerpt:

```text
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        5
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Image:                  devops-info-service:lab09
Port:                   5000/TCP (http)
Limits:
  cpu:                  250m
  memory:               256Mi
Requests:
  cpu:                  100m
  memory:               128Mi
Liveness:               http-get http://:http/health delay=15s timeout=2s period=10s
Readiness:              http-get http://:http/health delay=5s timeout=2s period=5s
```

Service access:

```bash
minikube service devops-info-service --url
```

Sample output from this run:

```text
http://127.0.0.1:36269
! Because you are using a Docker driver on linux, the terminal needs to be open to run it.
```

`curl` verification:

```text
curl -s http://127.0.0.1:36269/
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"10.244.0.1","method":"GET","path":"/","user_agent":"curl/8.5.0"},"runtime":{"current_time":"2026-04-02T19:41:59.439442.000Z","human":"0 hours, 1 minutes","seconds":67,"timezone":"UTC"},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","hostname":"devops-info-service-5cc99549bf-cbvrr","platform":"Linux","python_version":"3.14.3"}}

curl -s http://127.0.0.1:36269/health
{"status":"healthy","timestamp":"2026-04-02T19:41:59.439872+00:00","uptime_seconds":67}
```

## 5. Operations Performed

### Scaling to 5 Replicas

Commands:

```bash
kubectl scale deployment/devops-info-service --replicas=5
kubectl wait --for=condition=available deployment/devops-info-service --timeout=180s
kubectl get deployment devops-info-service
kubectl get pods -l app=devops-info-service -o wide
```

Output:

```text
deployment.apps/devops-info-service scaled
deployment.apps/devops-info-service condition met

NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
devops-info-service   5/5     5            5           2m59s
```

```text
NAME                                   READY   STATUS    RESTARTS   AGE    IP            NODE
devops-info-service-5cc99549bf-cbvrr   1/1     Running   0          104s   10.244.0.6    minikube
devops-info-service-5cc99549bf-crslz   1/1     Running   0          77s    10.244.0.8    minikube
devops-info-service-5cc99549bf-gx8cv   1/1     Running   0          14s    10.244.0.10   minikube
devops-info-service-5cc99549bf-lhklq   1/1     Running   0          89s    10.244.0.7    minikube
devops-info-service-5cc99549bf-p26x8   1/1     Running   0          14s    10.244.0.9    minikube
```

### Rolling Update Demo

I triggered a rollout by changing a configuration value instead of changing the image tag:

```bash
kubectl set env deployment/devops-info-service RELEASE_TRACK=rollout-demo
kubectl rollout status deployment/devops-info-service --timeout=180s
kubectl rollout history deployment/devops-info-service
```

Key output:

```text
deployment.apps/devops-info-service env updated
deployment "devops-info-service" successfully rolled out
```

Rollout history after the update:

```text
deployment.apps/devops-info-service
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
3         <none>
```

ReplicaSet view during the update:

```text
NAME                             DESIRED   CURRENT   READY   AGE
devops-info-service-5cc99549bf   0         0         0       2m56s
devops-info-service-65c6fcf67b   5         5         5       68s
devops-info-service-bf6495c7f    0         0         0       4m11s
```

### Zero-Downtime Check

While the rolling update was running, I repeatedly queried `/health` through the service tunnel:

```bash
for i in $(seq 1 12); do curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:36269/health; sleep 1; done
```

Output:

```text
200
200
200
200
200
200
200
200
200
200
200
200
```

All requests returned `200`, which matches the deployment strategy of `maxUnavailable: 0`.

### Rollback Demo

Commands:

```bash
kubectl rollout undo deployment/devops-info-service
kubectl rollout status deployment/devops-info-service --timeout=180s
kubectl rollout history deployment/devops-info-service
```

Output:

```text
deployment.apps/devops-info-service rolled back
deployment "devops-info-service" successfully rolled out
```

Rollout history after rollback:

```text
deployment.apps/devops-info-service
REVISION  CHANGE-CAUSE
1         <none>
3         <none>
4         <none>
```

I then returned the live cluster to the declarative manifest state:

```bash
kubectl apply -f k8s/deployment.yml
kubectl get deployment devops-info-service
```

```text
deployment.apps/devops-info-service configured

NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
devops-info-service   3/3     3            3           5m32s
```

## 6. Production Considerations

### Health Checks

- **Readiness probe** uses `/health` to keep new pods out of service until they are actually responding.
- **Liveness probe** uses the same endpoint to restart unhealthy containers automatically.
- For this small Flask app, `/health` is enough. In a larger service, I would separate readiness from liveness and include downstream dependency checks only where appropriate.

### Resource Limits Rationale

- `100m` CPU and `128Mi` memory requests are enough for a small Flask API on a local cluster.
- `250m` CPU and `256Mi` memory limits give headroom while still preventing one pod from consuming excessive node resources.
- These values are conservative defaults for a lab cluster; real values should come from load testing and production telemetry.

### What I Would Improve for Production

- Use a dedicated namespace such as `devops-info`
- Push immutable images to a real registry and reference versioned tags instead of a local Minikube image
- Add `startupProbe` and separate readiness/liveness behavior if startup becomes slower
- Add Horizontal Pod Autoscaler and PodDisruptionBudget
- Add Ingress or Gateway API with TLS
- Add ConfigMaps and Secrets for configuration instead of hardcoding all runtime values
- Add NetworkPolicies and image scanning in CI

### Monitoring and Observability Strategy

- Keep application logs on stdout/stderr for container-native log collection
- Expose `/metrics` and scrape it with Prometheus
- Add Grafana dashboards for request rate, latency, restart count, and probe failures
- Watch Kubernetes events and ReplicaSet history during rollouts for fast debugging

## 7. Challenges and Solutions

### 1. Dockerfile Build Failure

Initial build error:

```text
useradd: invalid shell 'sh'
```

Fix:

- Changed the Dockerfile to use `/bin/sh`

### 2. `CreateContainerConfigError` on First Deployment

Initial Kubernetes error:

```text
Error: container has runAsNonRoot and image has non-numeric user (appuser), cannot verify user is non-root
```

Fix:

- Rebuilt the image with numeric user `UID 10001`
- Set `runAsUser: 10001` and `runAsGroup: 10001` in the Deployment

### 3. Local Python Test Runner Not Installed

The host shell did not have `pytest` installed, so I validated the lab with:

- successful Docker image builds
- successful Minikube deployment and rollout
- live `curl` checks through the Kubernetes service
- scale, update, and rollback verification via `kubectl`

## 8. What I Learned

- Kubernetes requires image/user configuration to match pod security expectations, especially with `runAsNonRoot`
- Rolling updates are easy to demonstrate with config changes, not just image changes
- `kubectl describe`, events, and ReplicaSet history are the fastest tools for debugging failed pod startups
- Declarative manifests are the source of truth, but imperative commands are very useful for day-two operations like scaling and rollback
