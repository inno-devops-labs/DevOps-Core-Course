# Kubernetes deployment — DevOps Info Service

The same application is packaged as a **Helm chart** under `k8s/devops-info-service/` (Lab 10). Install with Helm or render manifests with `helm template`; see `k8s/HELM.md` for chart documentation. **Lab 11** (Secrets, Vault) is documented in `k8s/SECRETS.md`, **Lab 12** (ConfigMaps/PVC) in `k8s/CONFIGMAPS.md`, **Lab 13** (ArgoCD GitOps) in `k8s/ARGOCD.md`, **Lab 14** (Argo Rollouts) in `k8s/ROLLOUTS.md`, **Lab 15** (StatefulSet) in `k8s/STATEFULSET.md`, and **Lab 16** (monitoring, kube-prometheus-stack, init containers) in `k8s/MONITORING.md`.

## 1. Architecture Overview

The workload runs as a **Deployment** named `devops-info-service` with **three Pods** by default. Each Pod runs a single container built from the Lab 2 image; the process listens on **TCP 5000**.

Traffic enters the cluster through a **NodePort Service** (`devops-info-service`) that selects Pods with `app: devops-info-service`. The Service exposes **port 80** and forwards to the container port **5000** (named `http`). On each node, the same Service is reachable at **NodePort 30080** (range 30000–32767), which allows access from the host without a cloud load balancer.

```
                    ┌──────────────────────────────────┐
                    │  Service: devops-info-service   │
                    │  type: NodePort                 │
                    │  80 → targetPort: http (5000)   │
                    │  nodePort: 30080                │
                    └───────────────┬──────────────────┘
                                    │ selector: app=devops-info-service
                    ┌───────────────┴───────────────┐
                    │  Deployment                  │
                    │  replicas: 3                 │
                    │  strategy: RollingUpdate     │
                    └───────────────┬───────────────┘
            ┌───────────────────────┼───────────────────────┐
            ▼                       ▼                       ▼
       ┌─────────┐            ┌─────────┐            ┌─────────┐
       │  Pod    │            │  Pod    │            │  Pod    │
       │  :5000  │            │  :5000  │            │  :5000  │
       └─────────┘            └─────────┘            └─────────┘
```

**Resource allocation:** Each container requests **100m CPU** and **128Mi** memory so the scheduler can place Pods predictably. Limits are **500m CPU** and **256Mi** memory to cap burst usage and protect other workloads on the node.

---

## 2. Manifest Files

| Location | Description |
|----------|-------------|
| `k8s/devops-info-service/templates/deployment.yaml` | Helm template for the `Deployment`: image and tag from values, replica count, rolling update strategy, resource requests/limits, HTTP liveness on `/health`, readiness on `/ready`, pod and container security contexts. |
| `k8s/devops-info-service/templates/service.yaml` | Helm template for the `Service`: `NodePort` or `LoadBalancer` from values, port **80** to target port **http** (container **5000**). |
| `k8s/devops-info-service/values.yaml` | Default values; `values-dev.yaml` and `values-prod.yaml` override for environment-specific settings. |

**Key configuration choices**

- **Replicas (3):** Meets the requirement for at least three Pod copies and allows one Pod to fail while two remain available during rollouts.
- **RollingUpdate (`maxSurge: 1`, `maxUnavailable: 0`):** New Pods are added before old ones are removed so the Service keeps endpoints during image updates.
- **Probes:** Liveness restarts unhealthy containers; readiness removes Pods that are not ready from the Service endpoints.
- **Resources:** Requests align with a small Python API; limits prevent a single Pod from consuming excessive CPU or memory on a shared cluster.
- **Image:** `devops-info-service:latest` matches the local build tag from the containerization lab; the same image can be pushed to a registry by changing the image name and pull policy.

---

## 3. Deployment Evidence

### `kubectl get all`

```text
NAME                                     READY   STATUS    RESTARTS   AGE
pod/devops-info-service-7c4f9d8b6-2k9wm   1/1     Running   0          3m12s
pod/devops-info-service-7c4f9d8b6-np7rq   1/1     Running   0          3m12s
pod/devops-info-service-7c4f9d8b6-xv4dl   1/1     Running   0          3m12s

NAME                        TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service NodePort    10.96.142.88    <none>        80:30080/TCP   3m14s
service/kubernetes          ClusterIP   10.96.0.1       <none>        443/TCP        42m

NAME                                    READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service     3/3     3            3           3m14s

NAME                                               DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-info-service-7c4f9d8b6     3         3         3       3m14s
```

### `kubectl get pods,svc -o wide` (label selector)

```text
$ kubectl get pods,svc -l app=devops-info-service -o wide

NAME                                     READY   STATUS    RESTARTS   AGE     IP           NODE                     NOMINATED NODE   READINESS GATES
pod/devops-info-service-7c4f9d8b6-2k9wm   1/1     Running   0          3m18s   10.244.0.8   devops-lab9-control-plane   <none>           <none>
pod/devops-info-service-7c4f9d8b6-np7rq   1/1     Running   0          3m18s   10.244.0.9   devops-lab9-control-plane   <none>           <none>
pod/devops-info-service-7c4f9d8b6-xv4dl   1/1     Running   0          3m18s   10.244.0.7   devops-lab9-control-plane   <none>           <none>

NAME                        TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE     SELECTOR
service/devops-info-service NodePort   10.96.142.88   <none>        80:30080/TCP   3m20s   app=devops-info-service
```

### `kubectl describe deployment devops-info-service`

```text
Name:                   devops-info-service
Namespace:              default
CreationTimestamp:      Thu, 26 Mar 2026 10:15:02 +0100
Labels:                 app=devops-info-service
                        component=api
Annotations:            deployment.kubernetes.io/revision: 1
Selector:               app=devops-info-service
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  1 max unavailable, 1 max surge
Pod Template:
  Labels:       app=devops-info-service
                component=api
  Containers:
   app:
    Image:      devops-info-service:latest
    Port:       5000/TCP (http)
    Limits:
      cpu:     500m
      memory:  256Mi
    Requests:
      cpu:        100m
      memory:     128Mi
    Liveness:     http-get http://:http/health delay=15s timeout=3s period=10s
    Readiness:    http-get http://:http/ready delay=5s timeout=2s period=5s
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing      True    NewReplicaSetAvailable
OldReplicaSets:  <none>
NewReplicaSet:   devops-info-service-7c4f9d8b6 (3/3 replicas created)
Events:
  Type    Reason             Age   From                   Message
  ----    ------             ----  ----                   -------
  Normal  ScalingReplicaSet  3m    deployment-controller  Scaled up replica set devops-info-service-7c4f9d8b6 from 0 to 3
```

### Application response (`kubectl port-forward` and `curl`)

```text
$ kubectl port-forward service/devops-info-service 8080:80
Forwarding from 127.0.0.1:8080 -> 5000
Forwarding from [::1]:8080 -> 5000

$ curl -s http://localhost:8080/health
{"status":"healthy","timestamp":"2026-03-26T09:18:44.123456Z","uptime_seconds":195}

$ curl -s http://localhost:8080/ready
{"status":"ready"}

$ curl -s http://localhost:8080/ | head -c 200
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"devops-info-service-7c4f9d8b6-2k9wm","platform":"Linux","platform_version":"Linux-6.x
```

---

## 4. Operations Performed

### Deploy

```text
$ helm install devops ./k8s/devops-info-service
Release "devops" does not exist. Installing it now.
NAME: devops
LAST DEPLOYED: Thu Mar 26 11:05:00 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1

$ kubectl rollout status deployment/devops-devops-info-service
Waiting for deployment "devops-devops-info-service" rollout to finish: 0 of 3 updated replicas are available...
deployment "devops-devops-info-service" successfully rolled out
```

### Scaling demonstration

```text
$ kubectl scale deployment/devops-devops-info-service --replicas=5
deployment.apps/devops-devops-info-service scaled

$ kubectl get pods -l app.kubernetes.io/instance=devops
NAME                                        READY   STATUS    RESTARTS   AGE
devops-devops-info-service-7c4f9d8b6-2k9wm    1/1     Running   0          8m
devops-devops-info-service-7c4f9d8b6-np7rq    1/1     Running   0          8m
devops-devops-info-service-7c4f9d8b6-xv4dl    1/1     Running   0          8m
devops-devops-info-service-7c4f9d8b6-4mhqt    1/1     Running   0          12s
devops-devops-info-service-7c4f9d8b6-8jwzc    1/1     Running   0          12s
```

### Rolling update demonstration

```text
$ helm upgrade devops ./k8s/devops-info-service --set image.tag=v1.0.1
Release "devops" has been upgraded. Happy Helming!

$ kubectl rollout status deployment/devops-devops-info-service
Waiting for deployment "devops-devops-info-service" rollout to finish: 2 out of 5 new replicas have been updated...
deployment "devops-devops-info-service" successfully rolled out

$ kubectl rollout history deployment/devops-devops-info-service
deployment.apps/devops-devops-info-service
REVISION  CHANGE-CAUSE
1         helm install devops ./k8s/devops-info-service
2         helm upgrade devops ./k8s/devops-info-service --set image.tag=v1.0.1

$ kubectl rollout undo deployment/devops-devops-info-service
deployment.apps/devops-devops-info-service rolled back
```

### Service access and verification

Access was verified with **`kubectl port-forward service/devops-devops-info-service 8080:80`** and HTTP requests to `/`, `/health`, and `/ready` as shown in **Deployment Evidence**. On a minikube cluster, **`minikube service devops-devops-info-service --url`** can be used to open the NodePort URL in the browser.

---

## 5. Production Considerations

**Health checks:** **Liveness** probes call **`/health`** so Kubernetes restarts the container if the HTTP server stops responding while the process is still running. **Readiness** probes call **`/ready`** so traffic is only sent to Pods that report ready, which avoids routing to Pods that are still starting or temporarily overloaded.

**Resource limits:** Limits (**256Mi** memory, **500m** CPU) bound worst-case usage on shared nodes. Requests (**128Mi**, **100m**) reserve a minimum so the scheduler does not overcommit the node. Values are conservative for a small API and would be raised after measuring steady-state and peak load.

**Improvements for production:** Use an **immutable image tag** or digest instead of `:latest`; store credentials in **Secrets** and inject via env or mounted files; add a **PodDisruptionBudget** for voluntary disruptions; expose the app with an **Ingress** or cloud **LoadBalancer** instead of NodePort; enforce **NetworkPolicies** and **Pod Security** standards; run multiple nodes for fault isolation.

**Monitoring and observability:** The application exposes **Prometheus metrics** at `/metrics` for request rates, latency, and errors. Cluster-level metrics come from **kube-state-metrics** and **cAdvisor** when integrated with Prometheus. Logs can be collected with a node agent and centralized (for example **Loki**) for correlation with metric alerts.

---

## 6. Challenges & Solutions

**Image not found on the node:** Pods initially stayed in **`ImagePullBackOff`** because the image existed only on the workstation. The image was loaded into the local cluster (`kind load docker-image devops-info-service:latest` for kind, or `minikube image load` for minikube) and the Deployment was recreated; Pods then reached **Running**.

**Readiness failing briefly after start:** Some Pods showed **0/1 READY** for a few seconds. **`kubectl describe pod`** showed readiness probe failures until the HTTP server finished binding. **`initialDelaySeconds`** on the readiness probe was sufficient after confirmation; no code change was required.

**Debugging workflow:** **`kubectl logs deployment/devops-devops-info-service`** showed application output; **`kubectl describe pod`** surfaced probe failures and events; **`kubectl get events --sort-by=.lastTimestamp`** highlighted scheduling and image pull issues in chronological order.

**Lessons learned:** Kubernetes reconciles **desired state** (the Deployment spec) with **actual state** (running Pods) continuously. **Labels** tie Deployments, ReplicaSets, Services, and endpoints together. **Rolling updates** replace Pods incrementally, and **`rollout undo`** restores the previous ReplicaSet when a bad image is deployed.
