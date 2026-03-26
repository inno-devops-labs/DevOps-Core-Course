# Lab 9 — Kubernetes Fundamentals

## 1. Architecture Overview

### System Architecture

```
                    ┌────────────────────────────────────┐
                    │        Kubernetes Cluster          │
                    │                                    │
  Client ─────────► │  Service (NodePort)                │
        :8080       │  :80 → 5000                        │
                    │        │                           │
                    │        ▼                           │
                    │  Deployment (5 replicas)           │
                    │  devops-info-service               │
                    │        │                           │
                    │        ▼                           │
                    │  Pods (FastAPI app, port 5000)     │
                    │                                    │
                    │  Ingress (local.example.com)       │
                    │  ├─ /app1 → devops-info-service    │
                    │  └─ /app2 → go-app-service         │
                    │                                    │
                    │  go-app-service (ClusterIP)        │
                    │        │                           │
                    │        ▼                           │
                    │  Deployment (3 replicas)           │
                    │  go-app                            │
                    │        │                           │
                    │        ▼                           │
                    │  Pods (Go app, port 5000)          │
                    └────────────────────────────────────┘
```

---

### Description

* **Primary application**: `devops-info-service`

  * 5 replicas
  * Port: 5000
  * Exposed via NodePort and Ingress

* **Second application (bonus)**:

  * 3 replicas
  * Used to demonstrate Ingress routing

* **Networking**:

  * NodePort for direct access
  * Ingress for HTTP routing and TLS

---

### Resource Allocation

| Application         | Replicas | CPU       | Memory      |
| ------------------- | -------- | --------- | ----------- |
| devops-info-service | 5        | 100m–500m | 128Mi–256Mi |
| second-app (bonus)  | 3        | 50m–200m  | 64Mi–128Mi  |

---

## 2. Manifest Files

### `deployment.yml`

Defines the main application:

* 5 replicas for high availability
* Rolling updates with zero downtime:

  * `maxSurge: 1`
  * `maxUnavailable: 0`
* Health checks:

  * startupProbe
  * livenessProbe
  * readinessProbe
* Resource limits and requests
* Secure container configuration (non-root)

---

### `service.yml`

* Type: NodePort
* Port: 80 → 5000
* Exposes application externally

---

### `ingress.yml` (Bonus)

Provides HTTP routing:

* `/app1` → main service
* `/app2` → second service
* TLS enabled via self-signed certificate

---

## 3. Deployment Evidence

### Cluster info

```bash
kubectl cluster-info
kubectl get nodes
```

#### Output:

```
$ kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:32776
CoreDNS is running at https://127.0.0.1:32776/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
```
```
$ kubectl get nodes
NAME   STATUS   ROLES           AGE     VERSION
lab9   Ready    control-plane   3m46s   v1.35.1
```
---

### All resources

```bash
kubectl get all
```

#### Output:

```
$ kubectl get all
NAME                                       READY   STATUS    RESTARTS   AGE
pod/devops-info-service-6b89b45d48-76m2h   1/1     Running   0          83s
pod/devops-info-service-6b89b45d48-7s2g4   1/1     Running   0          83s
pod/devops-info-service-6b89b45d48-jghsx   1/1     Running   0          83s
pod/devops-info-service-6b89b45d48-jssgc   1/1     Running   0          83s
pod/devops-info-service-6b89b45d48-ndn5z   1/1     Running   0          83s
pod/go-app-547678887d-jv7rk                1/1     Running   0          83s
pod/go-app-547678887d-pv6dz                1/1     Running   0          83s
pod/go-app-547678887d-tgmxm                1/1     Running   0          83s

NAME                          TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service   NodePort    10.109.56.112   <none>        80:32276/TCP   83s
service/go-app-service        ClusterIP   10.108.22.78    <none>        80/TCP         83s
service/kubernetes            ClusterIP   10.96.0.1       <none>        443/TCP        3m46s

NAME                                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service   5/5     5            5           83s
deployment.apps/go-app                3/3     3            3           83s

NAME                                             DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-info-service-6b89b45d48   5         5         5       83s
replicaset.apps/go-app-547678887d                3         3         3       83s
```

---

### Pods and Services

```bash
kubectl get pods,svc -o wide
```

#### Output:

```
$ kubectl get pods,svc -o wide
NAME                                       READY   STATUS    RESTARTS   AGE   IP            NODE   NOMINATED NODE   READINESS GATES
pod/devops-info-service-6b89b45d48-76m2h   1/1     Running   0          84s   10.244.0.14   lab9   <none>           <none>
pod/devops-info-service-6b89b45d48-7s2g4   1/1     Running   0          84s   10.244.0.12   lab9   <none>           <none>
pod/devops-info-service-6b89b45d48-jghsx   1/1     Running   0          84s   10.244.0.18   lab9   <none>           <none>
pod/devops-info-service-6b89b45d48-jssgc   1/1     Running   0          84s   10.244.0.16   lab9   <none>           <none>
pod/devops-info-service-6b89b45d48-ndn5z   1/1     Running   0          84s   10.244.0.13   lab9   <none>           <none>
pod/go-app-547678887d-jv7rk                1/1     Running   0          84s   10.244.0.17   lab9   <none>           <none>
pod/go-app-547678887d-pv6dz                1/1     Running   0          84s   10.244.0.15   lab9   <none>           <none>
pod/go-app-547678887d-tgmxm                1/1     Running   0          84s   10.244.0.11   lab9   <none>           <none>

NAME                          TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE     SELECTOR
service/devops-info-service   NodePort    10.109.56.112   <none>        80:32276/TCP   84s     app=devops-info-service
service/go-app-service        ClusterIP   10.108.22.78    <none>        80/TCP         84s     app=go-app
service/kubernetes            ClusterIP   10.96.0.1       <none>        443/TCP        3m47s   <none>
```

---

### Deployment details

```bash
kubectl describe deployment devops-info-service
```

#### Output:

```
$ kubectl describe deployment devops-info-service
Name:                   devops-info-service
Namespace:              default
CreationTimestamp:      Thu, 26 Mar 2026 19:07:58 +0300
Labels:                 app=devops-info-service
Annotations:            deployment.kubernetes.io/revision: 1
Selector:               app=devops-info-service
Replicas:               5 desired | 5 updated | 5 total | 5 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Pod Template:
  Labels:  app=devops-info-service
  Containers:
   devops-info-service:
    Image:      devops-info-service:lab9
    Port:       5000/TCP
    Host Port:  0/TCP
    Limits:
      cpu:     500m
      memory:  256Mi
    Requests:
      cpu:         100m
      memory:      128Mi
    Liveness:      http-get http://:http/health delay=10s timeout=2s period=10s #success=1 #failure=3
    Readiness:     http-get http://:http/health delay=5s timeout=2s period=5s #success=1 #failure=3
    Startup:       http-get http://:http/health delay=0s timeout=1s period=2s #success=1 #failure=30
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
OldReplicaSets:  <none>
NewReplicaSet:   devops-info-service-6b89b45d48 (5/5 replicas created)
Events:
  Type    Reason             Age   From                   Message
  ----    ------             ----  ----                   -------
  Normal  ScalingReplicaSet  85s   deployment-controller  Scaled up replica set devops-info-service-6b89b45d48 from 0 to 5
```

---

### Application test

```bash
curl http://localhost:8080/health
```

#### Output:

```json
{"status":"healthy","timestamp":"2026-03-26T16:09:35.464096+00:00","uptime_seconds":86}
```

---

### Ingress test (Bonus)

```bash
curl -k https://local.example.com/app1
curl -k https://local.example.com/app2
```

#### Output:

```json
# /app1 — routed to devops-info-service
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"devops-info-service-6b89b45d48-6559r","platform":"Linux","platform_version":"#1 SMP PREEMPT Thu Nov 20 09:34:02 UTC 2025","architecture":"aarch64","cpu_count":12,"python_version":"3.13.12"},"runtime":{"uptime_seconds":56,"uptime_human":"0 hours, 0 minutes","current_time":"2026-03-26T16:12:14.628155+00:00","timezone":"UTC"},"request":{"client_ip":"10.244.0.21","user_agent":"curl/8.7.1","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}

# /app2 — routed to go-app-service
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"go-app-547678887d-jv7rk","platform":"Linux","platform_version":"#1 SMP PREEMPT Thu Nov 20 09:34:02 UTC 2025","architecture":"aarch64","cpu_count":12,"python_version":"3.13.12"},"runtime":{"uptime_seconds":245,"uptime_human":"0 hours, 4 minutes","current_time":"2026-03-26T16:12:16.119192+00:00","timezone":"UTC"},"request":{"client_ip":"10.244.0.21","user_agent":"curl/8.7.1","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}
```

---

## 4. Operations Performed

### Deployment

```bash
kubectl apply -f k8s/
```

---

### Scaling

```bash
kubectl scale deployment/devops-info-service --replicas=5
kubectl get pods
```

#### Output:

```
$ kubectl scale deployment/devops-info-service --replicas=5
deployment.apps/devops-info-service scaled

$ kubectl get pods
NAME                                   READY   STATUS    RESTARTS   AGE
devops-info-service-6b89b45d48-7s2g4   1/1     Running   0          2m7s
devops-info-service-6b89b45d48-872n7   1/1     Running   0          17s
devops-info-service-6b89b45d48-jghsx   1/1     Running   0          2m7s
devops-info-service-6b89b45d48-ndn5z   1/1     Running   0          2m7s
devops-info-service-6b89b45d48-t675s   1/1     Running   0          17s
go-app-547678887d-jv7rk                1/1     Running   0          2m7s
go-app-547678887d-pv6dz                1/1     Running   0          2m7s
go-app-547678887d-tgmxm                1/1     Running   0          2m7s
```

---

### Rolling Update

```bash
kubectl apply -f k8s/deployment.yml
kubectl rollout status deployment/devops-info-service
```

#### Output:

```
$ kubectl apply -f k8s/deployment.yml
deployment.apps/devops-info-service configured

$ kubectl rollout status deployment/devops-info-service
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 1 old replicas are pending termination...
deployment "devops-info-service" successfully rolled out
```

---

### Rollback

```bash
kubectl rollout history deployment/devops-info-service
kubectl rollout undo deployment/devops-info-service
```

#### Output:

```
$ kubectl rollout history deployment/devops-info-service
deployment.apps/devops-info-service
REVISION  CHANGE-CAUSE
1         kubectl set image deployment/devops-info-service devops-info-service=devops-info-service:lab9 --record=true
2         kubectl set image deployment/devops-info-service devops-info-service=devops-info-service:lab9 --record=true

$ kubectl rollout undo deployment/devops-info-service
deployment.apps/devops-info-service rolled back

$ kubectl rollout status deployment/devops-info-service
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 1 old replicas are pending termination...
deployment "devops-info-service" successfully rolled out
```

---

### Service Access

```bash
kubectl port-forward service/devops-info-service 8080:80
```

---

## 5. Production Considerations

### Health Checks

* **startupProbe** prevents premature restarts
* **readinessProbe** ensures traffic only goes to ready pods
* **livenessProbe** restarts unhealthy containers

---

### Resource Management

Requests and limits:

* prevent resource starvation
* improve scheduling
* ensure cluster stability

---

### Improvements for Production

* Use **Ingress or Gateway API** instead of NodePort
* Add **Horizontal Pod Autoscaler**
* Implement **monitoring (Prometheus + Grafana)**
* Add **centralized logging**
* Use **NetworkPolicy**

---

### Monitoring Strategy

* `/metrics` endpoint for Prometheus
* Metrics collection via scraping
* Visualization with Grafana
* Alerts for failures and latency

---

## 6. Challenges & Solutions

### Non-root container issue

Problem:

* Pod failed due to security constraints

Solution:

* Explicit UID/GID:

```yaml
runAsUser: 999
runAsGroup: 999
```

---

### Port-forward instability

Problem:

* Connection dropped during rolling update

Solution:

* Restart port-forward after rollout

---

### Local Docker images

Problem:

* Cluster could not access local images

Solution:

```bash
minikube image load devops-info-service:lab9 --profile lab9
```

---

## 7. Bonus — Ingress with TLS

### Second Application Deployment

```bash
kubectl apply -f k8s/deployment-go.yml
kubectl apply -f k8s/service-go.yml
```

---

### Enable Ingress Controller

```bash
minikube addons enable ingress --profile lab9
kubectl get pods -n ingress-nginx
```

#### Output:

```
$ minikube addons enable ingress --profile lab9
* ingress is an addon maintained by Kubernetes.
* After the addon is enabled, please run "minikube tunnel" and your ingress resources would be available at "127.0.0.1"
  - Using image registry.k8s.io/ingress-nginx/controller:v1.14.3
  - Using image registry.k8s.io/ingress-nginx/kube-webhook-certgen:v1.6.7
  - Using image registry.k8s.io/ingress-nginx/kube-webhook-certgen:v1.6.7
* Verifying ingress addon...
* The 'ingress' addon is enabled

$ kubectl get pods -n ingress-nginx
NAME                                        READY   STATUS      RESTARTS   AGE
ingress-nginx-admission-create-nk9dh        0/1     Completed   0          3m48s
ingress-nginx-admission-patch-ddd2x         0/1     Completed   0          3m48s
ingress-nginx-controller-596f8778bc-8s5gw   1/1     Running     0          3m48s
```

---

### TLS Setup

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=local.example.com/O=local.example.com"

kubectl create secret tls tls-secret \
  --key tls.key \
  --cert tls.crt
```

---

### Ingress Apply

```bash
kubectl apply -f k8s/ingress.yml
kubectl get ingress
```

#### Output:

```
$ kubectl apply -f k8s/ingress.yml
ingress.networking.k8s.io/devops-ingress created

$ kubectl get ingress
NAME             CLASS   HOSTS               ADDRESS        PORTS     AGE
devops-ingress   nginx   local.example.com   192.168.49.2   80, 443   11s
```

---

### Hosts Configuration

```bash
echo "192.168.49.2 local.example.com" | sudo tee -a /etc/hosts
```

---

### Verification

```bash
curl -k https://local.example.com/app1
curl -k https://local.example.com/app2
```

---

### Why Ingress is Better than NodePort

* Supports **path-based routing**
* Provides **TLS termination**
* Works as **single entry point**
* More suitable for production environments

---

## Conclusion

In this lab:

* A Kubernetes cluster was configured using minikube
* A production-ready Deployment was created
* Service exposure and networking were implemented
* Scaling, rolling updates, and rollback were demonstrated
* Ingress with TLS was configured for advanced routing

This demonstrates core Kubernetes concepts and production practices.
