# Kubernetes Deployment Report (Lab 09)

## 1. Architecture Overview

### Deployment Architecture

The application is deployed in a local Kubernetes cluster created with **minikube**.  
The final architecture contains:

- **1 Deployment**: `app-python`
- **5 Pods** managed by the Deployment
- **1 Service**: `app-python-service` of type `NodePort`
- **1 Kubernetes control plane node**: `minikube`

### Networking Flow

Client → `NodePort Service` → label selector `app=app-python` → one of the running Pods → Flask app on port `5000`

### Resource Allocation Strategy

Each container in the Deployment uses the following resource settings:

- **requests**
  - CPU: `100m`
  - Memory: `128Mi`
- **limits**
  - CPU: `200m`
  - Memory: `256Mi`

These values were chosen because the application is small and lightweight, but it still needs:
- guaranteed minimum resources for stable scheduling
- upper limits to prevent one container from consuming too much cluster capacity

---

## 2. Manifest Files

### `k8s/deployment.yml`

This manifest defines the main application Deployment.

#### Main configuration choices
- **replicas: 3** initially, later scaled to **5**
- image: `app-python:latest`
- `imagePullPolicy: Never`
- container port: `5000`
- liveness probe on `/health`
- readiness probe on `/health`
- resource requests and limits
- labels:
  - `app: app-python`

#### Why these values were chosen
- **3 replicas** satisfy the lab requirement and provide basic redundancy
- **5 replicas** were later used to demonstrate horizontal scaling
- **port 5000** matches the Flask application
- **/health** was used for both liveness and readiness because the app already exposes a working health endpoint
- **RollingUpdate** is the default and is appropriate for safe updates
- **imagePullPolicy: Never** was used because the image was built locally inside the minikube Docker environment

### `k8s/service.yml`

This manifest defines the Service exposing the application.

#### Main configuration choices
- type: `NodePort`
- service port: `80`
- target port: `5000`
- fixed nodePort: `30007`
- selector: `app=app-python`

#### Why these values were chosen
- **NodePort** is required by the lab for local cluster access
- **port 80** is convenient for external access
- **targetPort 5000** matches the application container port
- **selector** matches the Deployment label so traffic is routed correctly to the Pods

---

## 3. Deployment Evidence

### `kubectl get all`

```text
NAME                             READY   STATUS    RESTARTS   AGE
pod/app-python-856658699-5q5sm   1/1     Running   0          19m
pod/app-python-856658699-cl2jx   1/1     Running   0          19m
pod/app-python-856658699-gmtb2   1/1     Running   0          10m
pod/app-python-856658699-h4lqf   1/1     Running   0          16m
pod/app-python-856658699-z9xjw   1/1     Running   0          19m

NAME                         TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/app-python-service   NodePort    10.105.164.193   <none>        80:30007/TCP   18m
service/kubernetes           ClusterIP   10.96.0.1        <none>        443/TCP        44h

NAME                         READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/app-python   5/5     5            5           19m

NAME                                    DESIRED   CURRENT   READY   AGE
replicaset.apps/app-python-668c6d8f6d   0         0         0       14m
replicaset.apps/app-python-856658699    5         5         5       19m
```

### `kubectl get pods -o wide`

```text
NAME                         READY   STATUS    RESTARTS   AGE   IP            NODE       NOMINATED NODE   READINESS GATES
app-python-856658699-5q5sm   1/1     Running   0          19m   10.244.0.5    minikube   <none>           <none>
app-python-856658699-cl2jx   1/1     Running   0          19m   10.244.0.3    minikube   <none>           <none>
app-python-856658699-gmtb2   1/1     Running   0          11m   10.244.0.16   minikube   <none>           <none>
app-python-856658699-h4lqf   1/1     Running   0          16m   10.244.0.6    minikube   <none>           <none>
app-python-856658699-z9xjw   1/1     Running   0          19m   10.244.0.4    minikube   <none>           <none>
```

### `kubectl get svc -o wide`

```text
NAME                 TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE   SELECTOR
app-python-service   NodePort    10.105.164.193   <none>        80:30007/TCP   18m   app=app-python
kubernetes           ClusterIP   10.96.0.1        <none>        443/TCP        44h   <none>
```

### `kubectl describe deployment app-python`

```text
Name:                   app-python
Namespace:              default
CreationTimestamp:      Fri, 20 Mar 2026 11:20:22 +0700
Labels:                 app=app-python
Annotations:            deployment.kubernetes.io/revision: 5
Selector:               app=app-python
Replicas:               5 desired | 5 updated | 5 total | 5 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  25% max unavailable, 25% max surge
Pod Template:
  Labels:  app=app-python
  Containers:
   app-python:
    Image:      app-python:latest
    Port:       5000/TCP
    Host Port:  0/TCP
    Limits:
      cpu:     200m
      memory:  256Mi
    Requests:
      cpu:         100m
      memory:      128Mi
    Liveness:      http-get http://:5000/health delay=10s timeout=1s period=5s #success=1 #failure=3
    Readiness:     http-get http://:5000/health delay=5s timeout=1s period=3s #success=1 #failure=3
    Environment:   <none>
    Mounts:        <none>
  Volumes:         <none>
  Node-Selectors:  <none>
  Tolerations:     <none>
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing    True    NewReplicaSetAvailable
OldReplicaSets:  app-python-668c6d8f6d (0/0 replicas created)
NewReplicaSet:   app-python-856658699 (5/5 replicas created)
Events:
  Type    Reason             Age                From                   Message
  ----    ------             ----               ----                   -------
  Normal  ScalingReplicaSet  20m                deployment-controller  Scaled up replica set app-python-856658699 from 0 to 3
  Normal  ScalingReplicaSet  17m                deployment-controller  Scaled up replica set app-python-856658699 from 3 to 5
  Normal  ScalingReplicaSet  12m (x2 over 15m)  deployment-controller  Scaled up replica set app-python-668c6d8f6d from 0 to 2
  Normal  ScalingReplicaSet  12m (x2 over 15m)  deployment-controller  Scaled down replica set app-python-856658699 from 5 to 4
  Normal  ScalingReplicaSet  12m (x2 over 15m)  deployment-controller  Scaled up replica set app-python-668c6d8f6d from 2 to 3
  Normal  ScalingReplicaSet  11m (x2 over 14m)  deployment-controller  Scaled down replica set app-python-668c6d8f6d from 3 to 0
  Normal  ScalingReplicaSet  11m (x2 over 14m)  deployment-controller  Scaled up replica set app-python-856658699 from 4 to 5
```

### Evidence that the application works

The application was opened through the Service and returned JSON successfully. 
![[07-service-access-response.png]]
Screenshots collected during the lab:
- `k8s/screenshots/lab09/01-cluster-nodes.png`
- `k8s/screenshots/lab09/02-deployments.png`
- `k8s/screenshots/lab09/03-pods-running.png`
- `k8s/screenshots/lab09/04-service.png`
- `k8s/screenshots/lab09/05-rolling-update-error.png`
- `k8s/screenshots/lab09/06-rollback-final.png`
- `k8s/screenshots/lab09/07-service-access-response.png`

---

## 4. Operations Performed

### Commands used to deploy

```bash
minikube start --driver=docker
eval $(minikube docker-env)
docker build -t app-python:latest ./app_python
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
```

### Scaling demonstration

The Deployment was scaled from 3 replicas to 5 replicas.

```bash
kubectl scale deployment app-python --replicas=5
kubectl get pods
```

Result:
- Kubernetes created 2 additional Pods
- after readiness probes passed, all 5 Pods became `1/1 Running`

### Rolling update demonstration

A rolling update was intentionally triggered with a non-existent image:

```bash
kubectl set image deployment/app-python app-python=app-python:v2
kubectl get pods -w
```

Observed result:
- new Pods were created
- the new Pods entered `ErrImageNeverPull`
- existing working Pods were still kept alive during the rollout attempt

This demonstrated how Kubernetes performs rolling updates and prevents immediate total outage.

### Rollback demonstration

The failed rollout was reverted with:

```bash
kubectl rollout undo deployment app-python
kubectl rollout status deployment app-python
kubectl get pods
```

Result:
- Kubernetes restored the previous healthy ReplicaSet
- all Pods returned to the `Running` state

### Service access method and verification

The application was accessed with:

```bash
minikube service app-python-service
```

This opened the service URL in the browser and returned the application JSON response successfully.

---

## 5. Production Considerations

### Health checks implemented

Two HTTP probes were configured:

- **livenessProbe** on `/health`
- **readinessProbe** on `/health`

#### Why they were implemented
- **Liveness probe** ensures Kubernetes restarts a container if the app becomes unhealthy
- **Readiness probe** ensures traffic is only sent to Pods that are ready to serve requests

This is important because a running container is not always a healthy or ready container.

### Resource limits rationale

Configured values:
- requests: `100m` CPU, `128Mi` memory
- limits: `200m` CPU, `256Mi` memory

These limits are reasonable for a small Flask application. They protect the cluster from resource overuse and give the scheduler enough information to place Pods correctly.

### How this could be improved for production

For a more production-ready setup, I would improve the deployment by adding:

- **Ingress** instead of NodePort
- **Horizontal Pod Autoscaler (HPA)** for automatic scaling
- **ConfigMaps** and **Secrets** for configuration management
- container image from a real registry instead of local minikube build
- separate namespaces for environments
- PodDisruptionBudget
- stronger security settings such as read-only filesystem and dropped capabilities
- startup probe if the application startup time increases

### Monitoring and observability strategy

A production version of this deployment should include:

- **Prometheus** for collecting metrics
- **Grafana** for dashboards and visualization
- centralized logs using **Loki** or another logging stack
- alerts for:
  - pod restarts
  - failed rollouts
  - readiness/liveness failures
  - CPU and memory saturation
  - service unavailability

This connects well with the monitoring work already done in the previous lab.

---

## 6. Challenges & Solutions

### Issue 1 — New Pods were not immediately ready
At first, new Pods showed `0/1 Running` instead of `1/1 Running`.

**Cause:**  
The readiness probe had not passed yet.

**How it was handled:**  
I waited and watched the Pods with:

```bash
kubectl get pods -w
```

After the readiness probe succeeded, the Pods became fully ready.

### Issue 2 — Failed rolling update (`ErrImageNeverPull`)
During the rolling update test, the Deployment was changed to `app-python:v2`, which did not exist.

**Cause:**  
The image tag was not available, and `imagePullPolicy: Never` prevented Kubernetes from pulling it from a registry.

**How it was debugged:**  
I used:
- `kubectl get pods -w`
- rollout status
- Deployment history visible in `kubectl describe deployment app-python`

**Solution:**  
I rolled back the Deployment:

```bash
kubectl rollout undo deployment app-python
```

This restored the previous healthy ReplicaSet.

### Issue 3 — Understanding what Kubernetes actually updates
A first attempt to set the image to the same tag did not visibly recreate Pods.

**What I learned:**  
Kubernetes only performs an actual rollout when there is a real change in the Pod template. Re-applying the same image does not necessarily trigger new Pods.

### What I learned about Kubernetes

This lab helped me understand several important Kubernetes ideas:

- Kubernetes manages **desired state**, not just one-time commands
- Deployments provide safe updates and rollback support
- Services give stable networking in front of changing Pods
- Probes are essential for reliability
- Resource requests and limits are important even for small services
- Rolling updates and rollback are critical production features
- Watching resources with `kubectl get ... -w` is very useful during debugging
- `kubectl describe` gives much more context than `kubectl get`

---

## 7. Conclusion

In this lab, I successfully deployed the Python application to Kubernetes using declarative manifests and production-oriented configuration.

The final implementation included:
- local cluster setup with minikube
- Deployment with probes and resource limits
- NodePort Service for access
- horizontal scaling from 3 to 5 replicas
- rolling update test
- rollback after failed rollout
- verification through `kubectl get`, `kubectl describe`, and application response output

Overall, the lab demonstrated the core Kubernetes workflow:
**deploy → expose → verify → scale → update → rollback**.
