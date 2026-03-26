# Lab 09: Kubernetes Fundamentals

## 1. Architecture Overview

```
                   ┌──────────────────────────────────┐
                   │        Minikube Cluster          │
                   │                                  │
                   │  ┌──────────────────────────┐    │
                   │  │   Deployment: pythonapp  │    │
                   │  │   replicas: 3 (→5)       │    │
                   │  │                          │    │
                   │  │  ┌─────┐ ┌─────┐ ┌─────┐ │    │
User ──► NodePort  │  │  │Pod 1│ │Pod 2│ │Pod 3│ │    │
   :30080   ──────►│  │  └─────┘ └─────┘ └─────┘ │    │
                   │  └──────────────────────────┘    │
                   │                                  │
                   │  Service: pythonapp-service      │
                   │  Type: NodePort (80 → 5000)      │
                   └──────────────────────────────────┘
```

- **3 replicas** of `aidarsarvartdinov/pythonapp:latest`, scalable to 5
- **NodePort Service** on port 30080 forwards to container port 5000
- **Resource limits**: 200m CPU / 256Mi memory per pod
- **Health checks**: liveness and readiness probes on `/health`

## 2. Manifest Files

### `k8s/deployment.yml`
- **Image**: `aidarsarvartdinov/pythonapp:latest`
- **Replicas**: 3 (chosen for availability while fitting minikube resources)
- **Strategy**: RollingUpdate with `maxSurge: 1, maxUnavailable: 0` for zero-downtime deployments
- **Resources**: requests 100m/128Mi, limits 200m/256Mi — lightweight Python app doesn't need much
- **Probes**: HTTP GET `/health` on port 5000 for both liveness (10s delay) and readiness (5s delay)

### `k8s/service.yml`
- **Type**: NodePort — allows external access from host machine without a cloud load balancer
- **Port mapping**: 80 (service) → 5000 (container), NodePort 30080

## 3. Deployment Evidence

### Cluster Setup
```
$ minikube start --driver=docker
😄  minikube v1.38.1 on Microsoft Windows 10 Pro 22H2
✨  Using the docker driver based on user configuration

$ kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:62261
CoreDNS is running at https://127.0.0.1:62261/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

$ kubectl get nodes
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   9s    v1.35.1
```

Tool choice: **minikube** with Docker

### Apply Manifests
```
$ kubectl apply -f k8s/deployment.yml
deployment.apps/pythonapp created

$ kubectl apply -f k8s/service.yml
service/pythonapp-service created
```

### Running Pods (3 replicas)
```
$ kubectl get pods
NAME                        READY   STATUS    RESTARTS   AGE
pythonapp-66f558849-9nt5d   1/1     Running   0          58s
pythonapp-66f558849-fmkdz   1/1     Running   0          58s
pythonapp-66f558849-wr7b7   1/1     Running   0          58s
```

### Services
```
$ kubectl get svc
NAME                TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
kubernetes          ClusterIP   10.96.0.1        <none>        443/TCP        65s
pythonapp-service   NodePort    10.105.195.156   <none>        80:30080/TCP   58s
```

### kubectl get all
```
$ kubectl get all
NAME                            READY   STATUS    RESTARTS   AGE
pod/pythonapp-66f558849-9nt5d   1/1     Running   0          59s
pod/pythonapp-66f558849-fmkdz   1/1     Running   0          59s
pod/pythonapp-66f558849-wr7b7   1/1     Running   0          59s

NAME                        TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/kubernetes          ClusterIP   10.96.0.1        <none>        443/TCP        66s
service/pythonapp-service   NodePort    10.105.195.156   <none>        80:30080/TCP   59s

NAME                        READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/pythonapp   3/3     3            3           59s

NAME                                  DESIRED   CURRENT   READY   AGE
replicaset.apps/pythonapp-66f558849   3         3         3       59s
```

### Describe Deployment
```
$ kubectl describe deployment pythonapp
Name:                   pythonapp
Namespace:              default
Replicas:               5 desired | 5 updated | 5 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Pod Template:
  Containers:
   pythonapp:
    Image:      aidarsarvartdinov/pythonapp:latest
    Port:       5000/TCP
    Limits:     cpu: 200m, memory: 256Mi
    Requests:   cpu: 100m, memory: 128Mi
    Liveness:   http-get http://:5000/health delay=10s timeout=1s period=5s
    Readiness:  http-get http://:5000/health delay=5s timeout=1s period=3s
    Environment:
      HOST:  0.0.0.0
      PORT:  5000
```

## 4. Operations Performed

### Scaling to 5 Replicas
```
$ kubectl scale deployment/pythonapp --replicas=5
deployment.apps/pythonapp scaled

$ kubectl get pods
NAME                        READY   STATUS    RESTARTS   AGE
pythonapp-66f558849-6fhtm   1/1     Running   0          14s
pythonapp-66f558849-9nt5d   1/1     Running   0          73s
pythonapp-66f558849-fmkdz   1/1     Running   0          73s
pythonapp-66f558849-ggp6l   1/1     Running   0          14s
pythonapp-66f558849-wr7b7   1/1     Running   0          73s
```
All 5 replicas running — 2 new pods created in ~14s.

### Rolling Update
```
$ kubectl set env deployment/pythonapp APP_VERSION=v2
deployment.apps/pythonapp env updated

$ kubectl rollout status deployment/pythonapp
Waiting for deployment "pythonapp" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "pythonapp" rollout to finish: 2 out of 5 new replicas have been updated...
...
deployment "pythonapp" successfully rolled out
```
Pods replaced one by one (maxSurge=1, maxUnavailable=0 → zero downtime).

### Rollback
```
$ kubectl rollout undo deployment/pythonapp
deployment.apps/pythonapp rolled back

$ kubectl rollout status deployment/pythonapp
deployment "pythonapp" successfully rolled out

$ kubectl rollout history deployment/pythonapp
REVISION  CHANGE-CAUSE
3         <none>
4         <none>
```

### Service Access
```
$ minikube service pythonapp-service --url
http://127.0.0.1:<port>
```
Or via port-forward:
```
$ kubectl port-forward service/pythonapp-service 8080:80
```

## 5. Production Considerations

- **Health checks**: Liveness probe restarts unhealthy containers; readiness probe removes from service during startup. Both use the `/health` endpoint.
- **Resource limits**: Prevent a single pod from consuming all node resources. Requests ensure pods are scheduled on nodes with enough capacity.
- **Rolling updates**: `maxUnavailable: 0` ensures all pods remain available during deployments.
- **Improvements for prod**: Add PodDisruptionBudgets, network policies, Horizontal Pod Autoscaler, and external Ingress with TLS.
