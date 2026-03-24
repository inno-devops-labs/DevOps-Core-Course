# LAB09 - Kubernetes Fundamentals

## 0. Local Kubernetes Setup (Task 1)

### Tool choice: `minikube` (Docker driver)

I used **minikube** because it is simple for local single-node development and gives a full Kubernetes control plane quickly.

- Driver: Docker
- Kubernetes version: `v1.33.1`
- Cluster type: single-node local cluster

Cluster startup command used:

```bash
minikube start --driver=docker --kubernetes-version=v1.33.1
```


### Cluster verification evidence

```bash
$ kubectl cluster-info
Kubernetes control plane is running at https://192.168.49.2:8443
CoreDNS is running at https://192.168.49.2:8443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```

```bash
$ kubectl get nodes -o wide
NAME       STATUS   ROLES           AGE     VERSION   INTERNAL-IP    EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION     CONTAINER-RUNTIME
minikube   Ready    control-plane   9m26s   v1.33.1   192.168.49.2   <none>        Ubuntu 22.04.5 LTS   6.8.0-58-generic   docker://28.1.1
```

```bash
$ kubectl get namespaces
NAME              STATUS   AGE
default           Active   9m25s
kube-node-lease   Active   9m25s
kube-public       Active   9m25s
kube-system       Active   9m25s
```

## 1. Architecture Overview

### Deployment architecture

```text
                            +---------------------------------------------+
                            |                 minikube node               |
                            |               (192.168.49.2)               |
                            |                                             |
Client curl                 |   NodePort Service: devops-info-service     |
http://192.168.49.2:30080   ---> 80/TCP -> targetPort 5000               |
                            |            |                                |
                            |            v                                |
                            |   EndpointSlice (selected by label)         |
                            |   app=devops-info                           |
                            |      -> 10.244.0.13:5000                    |
                            |      -> 10.244.0.14:5000                    |
                            |      -> 10.244.0.15:5000                    |
                            |                                             |
                            |   Deployment devops-info (3 replicas)       |
                            |   Pods run image j0cos/devops-info-service:lab02
                            +---------------------------------------------+
```

### Networking flow explained

1. Each Pod receives a **Pod IP** from the cluster CNI network (`10.244.0.x` here).
2. The Service (`devops-info-service`) gets a stable **ClusterIP** (`10.109.86.63`) and selects Pods by label `app=devops-info`.
3. Kubernetes creates an **EndpointSlice** that stores current Pod endpoints behind the Service.
4. Because Service type is **NodePort**, Kubernetes exposes port `30080` on the node (`192.168.49.2`).
5. Traffic hitting `192.168.49.2:30080` is forwarded by kube-proxy rules to one healthy Pod endpoint (`:5000`).
6. **Readiness probe** controls endpoint membership, so only ready Pods receive traffic.

### Resource allocation strategy

Per Pod in Deployment:
- Requests: `100m CPU`, `128Mi memory`
- Limits: `200m CPU`, `256Mi memory`

This guarantees minimum resources for scheduler placement and prevents single Pod overconsumption.

## 2. Manifest Files

### `k8s/deployment.yml`

Main choices:
- `replicas: 3` (high availability for local lab)
- `strategy: RollingUpdate` with:
  - `maxSurge: 1`
  - `maxUnavailable: 0` (no intentional downtime during updates)
- Image from Lab 2 lineage: `j0cos/devops-info-service:lab02`
- Container port: `5000`
- Probes:
  - readiness: `GET /health`
  - liveness: `GET /health`
- Resources: requests + limits
- Labels for service selection and organization

### `k8s/service.yml`

Main choices:
- `type: NodePort`
- Service port `80` -> container port `5000` (named target port `http`)
- Fixed node port `30080` for predictable local access
- Selector `app: devops-info` matches Deployment Pod labels exactly

## 3. Deployment Evidence

Apply manifests:

```bash
$ kubectl apply -f k8s/deployment.yml
deployment.apps/devops-info created

$ kubectl apply -f k8s/service.yml
service/devops-info-service created

$ kubectl rollout status deployment/devops-info --timeout=240s
deployment "devops-info" successfully rolled out
```

Current cluster resources:

```bash
$ kubectl get all
NAME                               READY   STATUS    RESTARTS   AGE
pod/devops-info-5df7548dd9-cp79b   1/1     Running   0          2m16s
pod/devops-info-5df7548dd9-fsjb8   1/1     Running   0          2m8s
pod/devops-info-5df7548dd9-llnpl   1/1     Running   0          2m

NAME                          TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service   NodePort    10.109.86.63   <none>        80:30080/TCP   6m2s
service/kubernetes            ClusterIP   10.96.0.1      <none>        443/TCP        9m50s

NAME                          READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info   3/3     3            3           6m2s
```

Detailed Pods + Service:

```bash
$ kubectl get pods,svc -o wide
NAME                               READY   STATUS    RESTARTS   AGE     IP            NODE
pod/devops-info-5df7548dd9-cp79b   1/1     Running   0          2m16s   10.244.0.13   minikube
pod/devops-info-5df7548dd9-fsjb8   1/1     Running   0          2m8s    10.244.0.14   minikube
pod/devops-info-5df7548dd9-llnpl   1/1     Running   0          2m      10.244.0.15   minikube

NAME                          TYPE       CLUSTER-IP     PORT(S)        SELECTOR
service/devops-info-service   NodePort   10.109.86.63   80:30080/TCP   app=devops-info
```

Service endpoints (network mapping proof):

```bash
$ kubectl get endpointslices -l kubernetes.io/service-name=devops-info-service -o wide
NAME                        ADDRESSTYPE   PORTS   ENDPOINTS
devops-info-service-8vcl2   IPv4          5000    10.244.0.13,10.244.0.14,10.244.0.15
```

Deployment details (replicas + strategy + probes):

```bash
$ kubectl describe deployment devops-info
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  0 max unavailable, 1 max surge
...
Liveness:   http-get http://:http/health delay=15s timeout=2s period=10s
Readiness:  http-get http://:http/health delay=5s timeout=2s period=5s
...
Image:      j0cos/devops-info-service:lab02
```

Application reachability via NodePort:

```bash
$ MINIKUBE_HOME=/tmp/minikube minikube service devops-info-service --url
http://192.168.49.2:30080

$ curl -sS http://192.168.49.2:30080/health
{"status":"healthy","timestamp":"2026-03-24T14:07:55.571Z","uptime_seconds":129}
```

## 4. Operations Performed (Task 4)

### 4.1 Scaling to 5 replicas

```bash
$ kubectl scale deployment/devops-info --replicas=5
deployment.apps/devops-info scaled

$ kubectl rollout status deployment/devops-info --timeout=240s
deployment "devops-info" successfully rolled out

$ kubectl get deployment devops-info
NAME          READY   UP-TO-DATE   AVAILABLE   AGE
devops-info   5/5     5            5           2m41s
```

### 4.2 Rolling update demonstration

I changed Deployment configuration by updating an env var (`RELEASE_VERSION=v2`). This triggers a new ReplicaSet and rolling replacement.

```bash
$ kubectl set env deployment/devops-info RELEASE_VERSION=v2
deployment.apps/devops-info env updated

$ kubectl rollout status deployment/devops-info --timeout=240s
deployment "devops-info" successfully rolled out

$ kubectl rollout history deployment/devops-info
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
```

ReplicaSet transition evidence:

```bash
$ kubectl get rs -l app=devops-info
NAME                     DESIRED   CURRENT   READY   AGE
devops-info-5df7548dd9   0         0         0       3m33s
devops-info-7956d55994   5         5         5       39s
```

### 4.3 Zero downtime verification

During rollout, I continuously called `/health` 20 times (1 request/sec).

```text
01 200
02 200
03 200
04 200
05 200
06 200
07 200
08 200
09 200
10 200
11 200
12 200
13 200
14 200
15 200
16 200
17 200
18 200
19 200
20 200
```

Result: no failed responses observed while Pods were being replaced.

### 4.4 Rollback demonstration

```bash
$ kubectl rollout undo deployment/devops-info
deployment.apps/devops-info rolled back

$ kubectl rollout status deployment/devops-info --timeout=240s
deployment "devops-info" successfully rolled out

$ kubectl rollout history deployment/devops-info
REVISION  CHANGE-CAUSE
2         <none>
3         <none>

$ kubectl get deployment devops-info -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="RELEASE_VERSION")].value}'
v1
```

Rollback restored previous template configuration (`RELEASE_VERSION=v1`).

### 4.5 Return to declarative baseline

After demos, I reapplied manifest state (`3 replicas`).

```bash
$ kubectl apply -f k8s/deployment.yml
$ kubectl get deployment devops-info
NAME          READY   UP-TO-DATE   AVAILABLE
devops-info   3/3     3            3
```

## 5. Production Considerations

### Health checks

- **Readiness probe** (`/health`) prevents new Pod from receiving traffic until it is ready.
- **Liveness probe** (`/health`) restarts stuck containers automatically.
- Using both reduces bad traffic routing and supports self-healing.

### Resource limits rationale

- Requests ensure scheduler places Pods only when enough CPU/memory exist.
- Limits cap usage to protect node stability.
- Chosen values are conservative for a lightweight Flask service.

### Improvements for real production

1. Add dedicated Namespace (`devops`) and ResourceQuota/LimitRange.
2. Add HorizontalPodAutoscaler (CPU and/or request-based metrics).
3. Add PodDisruptionBudget for safer voluntary disruptions.
4. Add Ingress/Gateway for L7 routing instead of NodePort.
5. Add TLS, cert-manager, and external DNS.
6. Add NetworkPolicy to restrict east-west traffic.
7. Add CI pipeline validation (`kubectl apply --dry-run=server`, policy checks).

### Monitoring and observability strategy

- Reuse Lab 8 metrics stack (Prometheus + Grafana).
- Scrape Pod metrics via ServiceMonitor/PodMonitor (or static scrape in local lab).
- Keep structured logs from app and ship via Promtail/Loki (Lab 7).
- Add alerts for:
  - Pod restarts
  - Unavailable replicas
  - p95 latency and 5xx ratio

