# Lab 9 - Kubernetes Fundamentals

This submission implements the required Kubernetes resources for deploying a Python web application using declarative manifests, health checks, resource constraints, scaling, rolling updates.

## 1. Architecture Overview

### Base architecture
- **Deployment:** `python-app`
- **Replicas:** 3 initially, later scaled to 5
- **Service:** `python-app-service` of type `NodePort`
- **Networking flow:** Client -> NodePort Service -> selected Pods -> container port `8000`
- **Resource policy:** Each Pod requests `100m CPU` and `128Mi memory`, with limits of `250m CPU` and `256Mi memory`

### Why this design
- `Deployment` gives self-healing, declarative desired state, and rolling updates.
- `Service` provides a stable endpoint even when Pods are recreated.
- Readiness and liveness probes improve reliability during startup and runtime.
- Resource requests and limits help the scheduler place Pods safely and prevent noisy-neighbor issues.

---

## 2. Manifest Files

### `k8s/deployment.yml`
Defines the main application Deployment.
Key choices:
- `replicas: 3` to satisfy the lab requirement and demonstrate high availability.
- Rolling update strategy with:
  - `maxSurge: 1`
  - `maxUnavailable: 0`
- Readiness and liveness probes on `/health`
- Resource requests and limits for predictable scheduling and cluster protection

### `k8s/service.yml`
Defines a `NodePort` Service for local cluster access.
Key choices:
- `port: 80` for a friendly service port
- `targetPort: http` mapped to container port `8000`
- `nodePort: 30080` for deterministic local testing
---

## 3. Deployment Evidence

Paste your real command output below after running the manifests locally.

### Cluster setup evidence
```bash
$ kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:55551
CoreDNS is running at https://127.0.0.1:55551/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.

$ kubectl get nodes
NAME       STATUS   ROLES           AGE    VERSION
minikube   Ready    control-plane   115s   v1.32.0
# paste output here
```

### Deployment evidence
```bash
$ kubectl get all
NAME                              READY   STATUS    RESTARTS   AGE
pod/python-app-5d8876899b-dwfkf   1/1     Running   0          2m1s
pod/python-app-5d8876899b-fp4j7   1/1     Running   0          2m1s
pod/python-app-5d8876899b-tnwkw   1/1     Running   0          2m1s

NAME                         TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/kubernetes           ClusterIP   10.96.0.1        <none>        443/TCP        4m36s
service/python-app-service   NodePort    10.111.219.228   <none>        80:30080/TCP   117s

NAME                         READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/python-app   3/3     3            3           2m1s

NAME                                    DESIRED   CURRENT   READY   AGE
replicaset.apps/python-app-5d8876899b   3         3         3       2m1s
```

```bash
$ kubectl get pods,svc -o wide
NAME                              READY   STATUS    RESTARTS   AGE     IP           NODE       NOMINATED NODE   READINESS GATES
pod/python-app-5d8876899b-dwfkf   1/1     Running   0          2m30s   10.244.0.5   minikube   <none>           <none>
pod/python-app-5d8876899b-fp4j7   1/1     Running   0          2m30s   10.244.0.3   minikube   <none>           <none>
pod/python-app-5d8876899b-tnwkw   1/1     Running   0          2m30s   10.244.0.4   minikube   <none>           <none>

NAME                         TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE     SELECTOR
service/kubernetes           ClusterIP   10.96.0.1        <none>        443/TCP        5m5s    <none>
service/python-app-service   NodePort    10.111.219.228   <none>        80:30080/TCP   2m26s   app=python-app
```

```bash
$ kubectl describe deployment python-app
Name:                   python-app
Namespace:              default
CreationTimestamp:      Tue, 24 Mar 2026 22:19:55 +0300
Labels:                 app=python-app
Annotations:            deployment.kubernetes.io/revision: 1
Selector:               app=python-app
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Pod Template:
  Labels:  app=python-app
  Containers:
   python-app:
    Image:      s1mphonia/devops-core-course-python-app
    Port:       8000/TCP
    Host Port:  0/TCP
    Limits:
      cpu:     250m
      memory:  256Mi
    Requests:
      cpu:      100m
      memory:   128Mi
    Liveness:   http-get http://:http/health delay=15s timeout=2s period=10s #success=1 #failure=3
    Readiness:  http-get http://:http/health delay=5s timeout=2s period=5s #success=1 #failure=3
    Environment:
      APP_ENV:     production
      PORT:        8000
    Mounts:        <none>
  Volumes:         <none>
  Node-Selectors:  <none>
  Tolerations:     <none>
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing    True    NewReplicaSetAvailable
OldReplicaSets:  <none>
NewReplicaSet:   python-app-5d8876899b (3/3 replicas created)
Events:
  Type    Reason             Age    From                   Message
  ----    ------             ----   ----                   -------
  Normal  ScalingReplicaSet  3m47s  deployment-controller  Scaled up replica set python-app-5d8876899b from 0 to 3
```

### App working evidence
```bash
$ minikube service python-app-service --url
http://127.0.0.1:55887
$ curl http://127.0.0.1:55887/health
{"status":"healthy","timestamp":"2026-03-24T19:32:56.978169+00:00","uptime_seconds":765}
```

---

## 4. Operations Performed

### Deploy resources
```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl get deployments,pods,svc
```

### Scale to 5 replicas
```bash
$ kubectl scale deployment/python-app --replicas=5
deployment.apps/python-app scaled
$ kubectl rollout status deployment/python-app
Waiting for deployment "python-app" rollout to finish: 3 of 5 updated replicas are available...
Waiting for deployment "python-app" rollout to finish: 4 of 5 updated replicas are available...
deployment "python-app" successfully rolled out
$ kubectl get pods
NAME                          READY   STATUS    RESTARTS   AGE
python-app-5d8876899b-dwfkf   1/1     Running   0          14m
python-app-5d8876899b-fndbm   1/1     Running   0          12s
python-app-5d8876899b-fp4j7   1/1     Running   0          14m
python-app-5d8876899b-tnwkw   1/1     Running   0          14m
python-app-5d8876899b-x66jp   1/1     Running   0          12s
```

### Perform rolling update
```bash
kubectl set image deployment/python-app python-app=s1mphonia/devops-core-course-python-app
kubectl rollout status deployment/python-app
kubectl rollout history deployment/python-app
```

### Roll back deployment
```bash
kubectl rollout undo deployment/python-app
kubectl rollout status deployment/python-app
```

### Access method
```bash
$ kubectl port-forward service/python-app-service 8080:80
Forwarding from 127.0.0.1:8080 -> 8000
Forwarding from [::1]:8080 -> 8000
```

Verification:
```bash
$ curl http://127.0.0.1:8080/health
{"status":"healthy","timestamp":"2026-03-24T19:35:59.837506+00:00","uptime_seconds":950}
```

---

## 5. Production Considerations

### Health checks
Both readiness and liveness probes use `GET /health`.

**Why readiness?**
- Prevents traffic from reaching Pods before they are ready.

**Why liveness?**
- Restarts stuck containers automatically.

For slower-starting applications, a `startupProbe` could be added to avoid premature restarts.

### Resource limits rationale
The selected values are intentionally conservative for a small Python web service:
- Requests:
  - `100m` CPU
  - `128Mi` memory
- Limits:
  - `250m` CPU
  - `256Mi` memory

This is enough for a lightweight API while still demonstrating good production hygiene.

### Improvements for real production
- Use `ConfigMap` and `Secret` objects instead of hardcoded env vars
- Pin immutable image digests instead of mutable tags
- Add `PodDisruptionBudget`
- Add `HorizontalPodAutoscaler`
- Add `NetworkPolicy`
- Use `Ingress` or `Gateway API` instead of NodePort
- Add centralized logging, tracing, and metrics

### Monitoring and observability
Recommended stack:
- Metrics: Prometheus + Grafana
- Logs: Loki or EFK stack
- Traces: OpenTelemetry
- Alerting: Alertmanager

Useful debug commands:
```bash
kubectl logs <pod-name>
kubectl describe pod <pod-name>
kubectl get events --sort-by=.metadata.creationTimestamp
```

---

## 6. Challenges and Solutions

### Possible issue: Service unreachable
**Cause:** selector labels do not match Pod labels  
**Fix:** verify:
```bash
kubectl get pods --show-labels
kubectl describe service python-app-service
```

### What I learned
- Kubernetes works best when using declarative manifests and `kubectl apply`
- Deployments manage rollout strategy and desired state
- Services decouple networking from Pod lifecycle
- Probes and resource constraints are essential, not optional extras

---

## 8. Tool Choice for Local Cluster

I would choose **minikube** for this lab because:
- it is beginner-friendly
- Ingress setup is straightforward with built-in addons
- it closely mimics a real single-node Kubernetes environment
- service exposure with `minikube service` is convenient

`kind` is also a strong choice, especially for CI/CD and fast ephemeral clusters, but Minikube is slightly simpler for local learning and demo screenshots.

---

## 9. Files Included

- `k8s/deployment.yml`
- `k8s/service.yml`

