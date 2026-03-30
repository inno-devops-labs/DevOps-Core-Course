# Kubernetes Lab Documentation

## 1. Architecture Overview

I deployed the application to a local Kubernetes cluster running on **minikube**. The setup uses a standard Kubernetes pattern:

- **Deployment**: manages the application Pods
- **Service**: exposes the Pods inside and outside the cluster
- **Pods**: run the Flask-based application container
- **Replica count**: scaled from 3 to 5 replicas using a declarative manifest update

### Traffic Flow

`Browser / curl` → `NodePort Service` → `Pod IPs` → `Flask application`

### Resource Allocation Strategy

The Deployment includes:
- **CPU request:** `100m`
- **CPU limit:** `200m`
- **Memory request:** `128Mi`
- **Memory limit:** `256Mi`

This gives the app enough resources for normal operation while protecting the cluster from excessive usage.

---

## 2. Manifest Files

### `k8s/deployment.yml`
This file defines the application Deployment.

Key choices:
- **Replicas:** `5`
- **Strategy:** `RollingUpdate`
- **Max surge:** `1`
- **Max unavailable:** `0`
- **Container port:** `8000`
- **Liveness probe:** `/health`
- **Readiness probe:** `/health`
- **Resources:** requests and limits are defined
- **Environment variable:** `PORT=8000`

The app image used is:

```yaml
image: danielambda/devops-app:latest
```

### `k8s/service.yml`
This file defines the Service used to expose the Deployment.

Key choices:
- **Type:** `NodePort`
- **Service port:** `80`
- **Target port:** `8000`
- **NodePort:** `30080`
- **Selector:** matches the Deployment label `app: devops-core-course`

This allowed access to the app from outside the cluster on the local minikube IP.

---

## 3. Deployment Evidence

### Cluster Setup
`kubectl cluster-info`
```bash
Kubernetes control plane is running at https://192.168.49.2:8443
CoreDNS is running at https://192.168.49.2:8443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
```

`kubectl get nodes`
```bash
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   66s   v1.35.1
```

### Deployment Status
`kubectl apply -f k8s/deployment.yml`
```bash
deployment.apps/devops-core-course created
```

`kubectl get deployments`
```bash
NAME                 READY   UP-TO-DATE   AVAILABLE   AGE
devops-core-course   0/3     3            0           9s
```

`kubectl describe deployment devops-core-course`
```bash
Name:                   devops-core-course
Namespace:              default
CreationTimestamp:      Tue, 31 Mar 2026 01:23:45 +0300
Labels:                 app=devops-core-course
Annotations:            deployment.kubernetes.io/revision: 1
Selector:               app=devops-core-course
Replicas:               3 desired | 3 updated | 3 total | 2 available | 1 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Pod Template:
  Labels:  app=devops-core-course
  Containers:
   devops-core-course:
    Image:      danielambda/devops-app:latest
    Port:       8000/TCP (http)
    Host Port:  0/TCP (http)
    Limits:
      cpu:     200m
      memory:  256Mi
    Requests:
      cpu:      100m
      memory:   128Mi
    Liveness:   http-get http://:http/health delay=10s timeout=2s period=5s #success=1 #failure=3
    Readiness:  http-get http://:http/health delay=5s timeout=2s period=3s #success=1 #failure=3
    Environment:
      PORT:        8000
    Mounts:        <none>
  Volumes:         <none>
  Node-Selectors:  <none>
  Tolerations:     <none>
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      False   MinimumReplicasUnavailable
  Progressing    True    ReplicaSetUpdated
OldReplicaSets:  <none>
NewReplicaSet:   devops-core-course-db7bd75dd (3/3 replicas created)
Events:
  Type    Reason             Age   From                   Message
  ----    ------             ----  ----                   -------
  Normal  ScalingReplicaSet  25s   deployment-controller  Scaled up replica set devops-core-course-db7bd75dd from 0 to 3
```

---

## 4. Service Verification

`kubectl apply -f k8s/service.yml`

`minikube service --all`
```bash
┌───────────┬────────────────────────────┬─────────────┬───────────────────────────┐
│ NAMESPACE │            NAME            │ TARGET PORT │            URL            │
├───────────┼────────────────────────────┼─────────────┼───────────────────────────┤
│ default   │ devops-core-course-service │ 80          │ http://192.168.49.2:30080 │
└───────────┴────────────────────────────┴─────────────┴───────────────────────────┘
```

`kubectl get services`
```bash
NAME                         TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
devops-core-course-service   NodePort    10.109.110.248   <none>        80:30080/TCP   16m
kubernetes                   ClusterIP   10.96.0.1        <none>        443/TCP        27m
```

`kubectl describe service devops-core-course-service`
```bash
Name:                     devops-core-course-service
Namespace:                default
Labels:                   app=devops-core-course
Annotations:              <none>
Selector:                 app=devops-core-course
Type:                     NodePort
IP Family Policy:         SingleStack
IP Families:              IPv4
IP:                       10.109.110.248
IPs:                      10.109.110.248
Port:                     <unset>  80/TCP
TargetPort:               8000/TCP
NodePort:                 <unset>  30080/TCP
Endpoints:                10.244.0.3:8000,10.244.0.5:8000,10.244.0.4:8000
Session Affinity:         None
External Traffic Policy:  Cluster
Internal Traffic Policy:  Cluster
Events:                   <none>
```

`kubectl get endpoints`
```bash
NAME                         ENDPOINTS                                         AGE
devops-core-course-service   10.244.0.3:8000,10.244.0.4:8000,10.244.0.5:8000   16m
kubernetes                   192.168.49.2:8443
```

### Application Response
`curl http://192.168.49.2:30080`
```json
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"10.244.0.1","method":"GET","path":"/","user_agent":"curl/8.18.0"},"runtime":{"current_time":"2026-03-30T22:52:08.064417+00:00","timezone":"UTC","uptime_human":"0 hours, 2 minutes","uptime_seconds":152},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":16,"hostname":"devops-core-course-db7bd75dd-5zjm9","platform":"Linux","platform_version":"#1-NixOS SMP PREEMPT_DYNAMIC Wed Mar 25 10:10:46 UTC 2026","python_version":"3.13.12"}}
```

`minikube service devops-core-course-service --url`
```bash
http://192.168.49.2:30080
```

---

## 5. Operations Performed

### Initial Deployment
Applied the Deployment manifest:
```bash
kubectl apply -f k8s/deployment.yml
```

### Scaling
I used the **declarative approach** for scaling by updating the `replicas` field in `k8s/deployment.yml` from `3` to `5`, then reapplying the manifest.

`kubectl get deployments`
```bash
NAME                 READY   UP-TO-DATE   AVAILABLE   AGE
devops-core-course   5/5     5            5           22m
```

`kubectl get pods`
```bash
NAME                                 READY   STATUS    RESTARTS   AGE
devops-core-course-db7bd75dd-2mtps   1/1     Running   0          38s
devops-core-course-db7bd75dd-5c6jq   1/1     Running   0          22m
devops-core-course-db7bd75dd-g9ghr   1/1     Running   0          22m
devops-core-course-db7bd75dd-xfzrz   1/1     Running   0          22m
devops-core-course-db7bd75dd-xqcpg   1/1     Running   0          38s
```

`kubectl rollout status deployment/devops-core-course`
```bash
deployment "devops-core-course" successfully rolled out
```

### Rolling Update
I updated the Deployment manifest and reapplied it to trigger a rolling update.

`kubectl rollout status deployment/devops-core-course`
```bash
Waiting for deployment "devops-core-course" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "devops-core-course" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "devops-core-course" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "devops-core-course" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "devops-core-course" rollout to finish: 1 old replicas are pending termination...
deployment "devops-core-course" successfully rolled out
```

`kubectl get pods -w`
```bash
devops-core-course-84b7cc9b87-24jmm   1/1     Running       0          30s
devops-core-course-84b7cc9b87-7rsdl   1/1     Running       0          23s
devops-core-course-84b7cc9b87-dr9t8   1/1     Running       0          36s
devops-core-course-84b7cc9b87-sclcq   1/1     Running       0          17s
devops-core-course-84b7cc9b87-sg5lc   1/1     Running       0          63s
devops-core-course-db7bd75dd-5c6jq    1/1     Terminating   0          25m
devops-core-course-db7bd75dd-g9ghr    1/1     Terminating   0          25m
devops-core-course-db7bd75dd-xfzrz    1/1     Terminating   0          25m
devops-core-course-db7bd75dd-xqcpg    0/1     Error         0          3m16s
```

### Rollback
I used rollout undo to restore the previous revision.

`kubectl rollout history deployment/devops-core-course`
```bash
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
```

`kubectl rollout undo deployment/devops-core-course`
```bash
deployment.apps/devops-core-course rolled back
```

After rollback, the deployment became healthy again.

`kubectl rollout history deployment/devops-core-course`
```bash
REVISION  CHANGE-CAUSE
2         <none>
3         <none>
```

`kubectl describe deployment devops-core-course`
```bash
Replicas:               5 desired | 5 updated | 5 total | 5 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  0 max unavailable, 1 max surge
```

---

## 6. Production Considerations

### Health Checks
I implemented both **liveness** and **readiness** probes against `/health`.

Why:
- **Liveness probe** restarts the container if it becomes unhealthy
- **Readiness probe** removes the Pod from service until it is ready to receive traffic

### Resource Limits
I defined requests and limits to:
- reserve enough CPU and memory for the app
- prevent one container from consuming too many resources
- help Kubernetes schedule Pods predictably

### Improvements for Production
If this were a production system, I would improve it by:
- using a pinned image tag instead of `latest`
- adding a separate `startupProbe` for slow boot times
- using ConfigMaps and Secrets for configuration
- adding autoscaling with HPA
- adding monitoring and alerting
- using Ingress instead of NodePort
- adding proper log aggregation and tracing

### Monitoring and Observability
Useful observability additions would include:
- Prometheus metrics
- Grafana dashboards
- centralized logs
- alerting on Pod restarts, readiness failures, and high resource usage

---

## 7. Challenges & Solutions

### Issues Encountered
- `kubectl apply` without a file argument returned an error because `-f` or `-k` is required.
- During rollout, some Pods briefly showed `Error` or `Terminating` states while Kubernetes replaced the old ReplicaSet with the new one.

### How I Debugged
I used:
- `kubectl get pods`
- `kubectl describe deployment devops-core-course`
- `kubectl get services`
- `kubectl describe service devops-core-course-service`
- `kubectl get endpoints`
- `kubectl rollout status deployment/devops-core-course`
- browser access and `curl`

### What I Learned
This lab reinforced:
- how declarative Kubernetes manifests work
- how Deployments manage Pod lifecycles
- how Services provide stable access to Pods
- how rolling updates and rollback keep applications available
- how probes and resource limits improve reliability

---

## 8. Summary

This Kubernetes setup successfully deployed the application to minikube using:
- a **Deployment** with 5 replicas
- a **NodePort Service**
- **health checks**
- **resource requests and limits**
- **rolling update support**
- **rollback capability**

The application is reachable from the browser and responds correctly through the Service endpoint.
