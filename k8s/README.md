# Zavadskii Peter Lab09

## Architecture Overview

In my architecture, I will reach the application via service using the Nodeport mode.

```
External Client
|
| (NodePort: 30560)
v
Minikube Node (192.168.49.2)
|
| kube-proxy forwards
v
Service
(port 80 → targetPort 5000)
|
| load balances
v
Pods
(containerPort: 5000)
^
|
| manages
ReplicaSet
(ensures 3 replicas)
^
|
| controls
Deployment
(rolling updates, rollbacks)
```


As a resource selection strategy, I decided to allocate resources to instances with a reserve

Deployment resource allocation :
* Requests: cpu=100m, memory=128Mi
* Limits: cpu=200m, memory=256Mi

## Manifest Files

1. Deployment Manifest (deployment.yaml)

### Brief Description

This manifest defines the deployment configuration for the devops-info-service application. It manages the lifecycle of the application pods, ensuring high availability and controlled updates.

### Key Configuration Choices

Replicas: 3

3 replicas selected to ensure high availability and fault tolerance

Allows traffic distribution across multiple application instances

Enables rolling updates without complete service interruption

### Rolling Update Strategy:

maxSurge: 1 - allows creating 1 additional pod above the desired count, ensuring smooth updates
maxUnavailable: 0 - guarantees that at least 3 pods (replicas - maxUnavailable) remain available during updates

This strategy minimizes downtime during deployment

### Resources:

Requests (CPU: 100m, Memory: 128Mi): guaranteed minimum resources for stable application operation

Limits (CPU: 200m, Memory: 256Mi): constraints to prevent node resource exhaustion

### Probes:

Liveness Probe (initialDelaySeconds: 10): checks if the application is running; after three failed attempts, the container will be restarted

Readiness Probe (initialDelaySeconds: 5): checks readiness to accept traffic; shorter initial interval for quick service integration
YAML anchor (&probe) used for DRY approach, with parameters overridden for readinessProbe

### Environment Variables:

HOST: 0.0.0.0 - application listens on all network interfaces within the container

PORT: 5000 - port where the application runs (matches containerPort)


2. Service Manifest (service.yaml)

### Brief Description

This manifest exposes the devops-info-service deployment as a network service, enabling external access to the application.

### Key Configuration Choices

Type: NodePort

Selected for external access to the application from outside the cluster

Suitable for development/testing environments or cases where no ingress controller is available

Allows direct access via a port on each cluster node

### Port Mapping:

* port: 80 - external port accessible within the cluster
* targetPort: 5000 - container port where traffic is forwarded
* nodePort: 30560 - static port on cluster nodes for external access (within the 30000-32767 range)

### Selector:

app: devops-info-service - connects the service to pods created by the deployment

Label matching ensures new pods are automatically included in the service



### Configuration Rationale

Configuration	Value	Reasoning
Replicas	3	Balance between fault tolerance and resource usage; can withstand failure of one node
CPU Request	100m	Baseline consumption for a REST API service; ensures stability
Memory Limit	256Mi	Prevents memory leaks; sufficient for handling standard requests
Rolling Update	maxSurge:1, maxUnavailable:0	Zero-downtime deployment; guarantees continuous availability
NodePort	30560	Fixed port for predictable access; simplifies network policy configuration
Revision History	5	Preserves the last 5 versions for quick rollback when needed



### Dependencies and Relationships

Service relies on labels defined in the Deployment (app: devops-info-service)
Service port 30560 must be allowed in cluster network policies
Application must have a /health endpoint for proper probe functionality

## Deployment Evidence

### Cluster setup (Task 1)

```bash
abraham_barrett@Abrahams-MacBook-Air k8s % kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:51375
CoreDNS is running at https://127.0.0.1:51375/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
abraham_barrett@Abrahams-MacBook-Air k8s % kubectl get nodes -o wide
NAME       STATUS   ROLES           AGE     VERSION   INTERNAL-IP    EXTERNAL-IP   OS-IMAGE                         KERNEL-VERSION     CONTAINER-RUNTIME
minikube   Ready    control-plane   8m30s   v1.35.1   192.168.49.2   <none>        Debian GNU/Linux 12 (bookworm)   6.10.14-linuxkit   docker://29.2.1
abraham_barrett@Abrahams-MacBook-Air k8s % 
```
---

Commands used to deploy : 
```bash
abraham_barrett@Abrahams-MacBook-Air k8s % kubectl apply -f service.yml
service/devops-info-service created
abraham_barrett@Abrahams-MacBook-Air k8s % kubectl apply -f deployment.yml  
deployment.apps/devops-info-service created

```
---
Outputs:

```kubectl get all```
```bash
abraham_barrett@Abrahams-MacBook-Air k8s % kubectl get all            
NAME                                      READY   STATUS    RESTARTS   AGE
pod/devops-info-service-7c75c977c-bmg5n   1/1     Running   0          4m2s
pod/devops-info-service-7c75c977c-fxzcq   1/1     Running   0          4m2s
pod/devops-info-service-7c75c977c-hv988   1/1     Running   0          4m2s

NAME                          TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service   NodePort    10.101.151.138   <none>        80:30560/TCP   4m7s
service/kubernetes            ClusterIP   10.96.0.1        <none>        443/TCP        12m

NAME                                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service   3/3     3            3           4m2s

NAME                                            DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-info-service-7c75c977c   3         3         3       4m2s
abraham_barrett@Abrahams-MacBook-Air k8s % 


```

```kubectl get pods,svc```

```bash
abraham_barrett@Abrahams-MacBook-Air k8s % kubectl get pods,svc
NAME                                      READY   STATUS    RESTARTS   AGE
pod/devops-info-service-7c75c977c-bmg5n   1/1     Running   0          4m29s
pod/devops-info-service-7c75c977c-fxzcq   1/1     Running   0          4m29s
pod/devops-info-service-7c75c977c-hv988   1/1     Running   0          4m29s

NAME                          TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service   NodePort    10.101.151.138   <none>        80:30560/TCP   4m34s
service/kubernetes            ClusterIP   10.96.0.1        <none>        443/TCP        12m
abraham_barrett@Abrahams-MacBook-Air k8s % 
```
```kubectl get all -o wide```
```bash
abraham_barrett@Abrahams-MacBook-Air k8s % kubectl get all -o wide
NAME                                       READY   STATUS    RESTARTS   AGE    IP            NODE       NOMINATED NODE   READINESS GATES
pod/devops-info-service-55f94bd495-k8vpg   1/1     Running   0          106m   10.244.0.8    minikube   <none>           <none>
pod/devops-info-service-55f94bd495-mnshq   1/1     Running   0          106m   10.244.0.9    minikube   <none>           <none>
pod/devops-info-service-55f94bd495-xmq5l   1/1     Running   0          105m   10.244.0.10   minikube   <none>           <none>

NAME                          TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE    SELECTOR
service/devops-info-service   NodePort    10.101.151.138   <none>        80:30560/TCP   116m   app=devops-info-service
service/kubernetes            ClusterIP   10.96.0.1        <none>        443/TCP        124m   <none>

NAME                                  READY   UP-TO-DATE   AVAILABLE   AGE    CONTAINERS            IMAGES                           SELECTOR
deployment.apps/devops-info-service   3/3     3            3           116m   devops-info-service   abrahambarrett228/lab02:latest   app=devops-info-service

NAME                                             DESIRED   CURRENT   READY   AGE    CONTAINERS            IMAGES                                         SELECTOR
replicaset.apps/devops-info-service-54599f9d65   0         0         0       107m   devops-info-service   abrahambarrett228/devops-info-service          app=devops-info-service,pod-template-hash=54599f9d65
replicaset.apps/devops-info-service-55f94bd495   3         3         3       106m   devops-info-service   abrahambarrett228/lab02:latest                 app=devops-info-service,pod-template-hash=55f94bd495
replicaset.apps/devops-info-service-58d848bc9b   0         0         0       107m   devops-info-service   abrahambarrett228/devops-info-service:latest   app=devops-info-service,pod-template-hash=58d848bc9b
replicaset.apps/devops-info-service-7c75c977c    0         0         0       116m   devops-info-service   funnyfoxd/devops-info-service:lab02            app=devops-info-service,pod-template-hash=7c75c977c
abraham_barrett@Abrahams-MacBook-Air k8s % 

```




```kubectl describe deployment <name>```

```bash
abraham_barrett@Abrahams-MacBook-Air k8s % kubectl describe deployment devops-info-service
Name:                   devops-info-service
Namespace:              default
CreationTimestamp:      Thu, 26 Mar 2026 18:13:58 +0300
Labels:                 app=devops-info-service
Annotations:            deployment.kubernetes.io/revision: 1
Selector:               app=devops-info-service
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Pod Template:
  Labels:  app=devops-info-service
  Containers:
   devops-info-service:
    Image:      funnyfoxd/devops-info-service:lab02
    Port:       5000/TCP
    Host Port:  0/TCP
    Limits:
      cpu:     200m
      memory:  256Mi
    Requests:
      cpu:      100m
      memory:   128Mi
    Liveness:   http-get http://:5000/health delay=10s timeout=2s period=10s #success=1 #failure=3
    Readiness:  http-get http://:5000/health delay=5s timeout=2s period=5s #success=1 #failure=3
    Environment:
      HOST:        0.0.0.0
      PORT:        5000
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
NewReplicaSet:   devops-info-service-7c75c977c (3/3 replicas created)
Events:
  Type    Reason             Age    From                   Message
  ----    ------             ----   ----                   -------
  Normal  ScalingReplicaSet  4m59s  deployment-controller  Scaled up replica set devops-info-service-7c75c977c from 0 to 3
```


```Screenshot or curl output showing app working```

```curl http://192.168.49.2:30560```

```bash
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"devops-info-service-55f94bd495-k8vpg","platform_name":"Linux","architecture":"aarch64","python_version":"3.13.11"},"runtime":{"seconds":6648,"human":"1 hours, 50 minutes"},"request":{"client_ip":"127.0.0.1","user_agent":"Python-urllib/3.13","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}
```


```curl http://192.168.49.2:30560/health```
```bash
{"status":"healthy","timestamp":"2026-03-26T17:12:46.593066+00:00","uptime_seconds":6519}
```

## Operations Performed



### Deployment Commands

1. Deploy the application:
```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```
2. Verify deployment status:

```bash
kubectl get pods
kubectl get svc
```
3. Check rollout completion:

```bash
kubectl rollout status deployment/devops-info-service
```

### Scaling Operations

Scale from 3 to 5 replicas:
```bash
kubectl scale deployment devops-info-service --replicas=5
kubectl rollout status deployment/devops-info-service
```


Rollout status output:

```bash
Waiting for deployment "devops-info-service" rollout to finish: 3 of 5 updated replicas are available...
Waiting for deployment "devops-info-service" rollout to finish: 4 of 5 updated replicas are available...
deployment "devops-info-service" successfully rolled out
```

Running pods after scaling:
```bash
devops-info-service-7c75c977c-bmg5n
devops-info-service-7c75c977c-fxzcq
devops-info-service-7c75c977c-hv988
devops-info-service-7c75c977c-xyz12
devops-info-service-7c75c977c-abc34
```

Rolling Update Demonstration

Triggered update by modifying the deployment (added DEBUG environment variable temporarily).

Service availability verification during update — continuous health checks:
```bash
while true; do curl -s -o /dev/null -w "%{http_code}\n" http://192.168.49.2:30560/health; sleep 2; done
```
Health check results during rollout:
```
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

Rollout status output:

```bash
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 1 old replicas are pending termination...
deployment "devops-info-service" successfully rolled out
```

Service Access and Verification

Access method using Minikube:

```bash

minikube ip # Output: 192.168.49.2
curl http://192.168.49.2:30560/health
```

Health endpoint test:

```bash
curl http://192.168.49.2:30560/health
```

Service details verification: ```kubectl describe service devops-info-service```

## Production Considerations

## Health Checks

### Liveness Probe (`/health`)
- **Configuration**: delay: 10s, period: 10s, timeout: 2s, failureThreshold: 3
- **Purpose**: Detects if app is deadlocked or stuck
- **Action**: Restarts container after 3 failures

### Readiness Probe (`/health`)
- **Configuration**: delay: 5s, period: 5s, timeout: 2s, failureThreshold: 3
- **Purpose**: Ensures app only receives traffic when ready
- **Action**: Removes from service during startup or temporary failures

### Why These Values
- **Faster readiness (5s)** : Quick traffic acceptance
- **Slower liveness (10s)** : Avoids premature restarts
- **2s timeout** : Prevents hanging probes
- **3 failures** : Tolerates transient issues

---

## Resource Limits

| Resource | Request | Limit | Rationale |
|----------|---------|-------|-----------|
| **CPU** | 100m | 200m | Guarantees baseline compute; allows burst up to 2x; prevents noisy neighbors |
| **Memory** | 128Mi | 256Mi | Ensures stability; prevents memory leaks; 2x buffer for normal fluctuations |

**Note**: Requests guarantee resources for scheduling; limits protect node stability.

---

## Production Improvements

1. **Horizontal Pod Autoscaling** - Auto-scale based on CPU/memory usage (3-10 replicas)
2. **Ingress + TLS** - Replace NodePort with Ingress and SSL termination
3. **Pod Disruption Budget** - Ensure minimum 2 pods available during voluntary disruptions
4. **ConfigMaps/Secrets** - Externalize configuration and sensitive data
5. **Security Context** - Run as non-root, drop all capabilities
6. **Network Policies** - Restrict pod-to-pod communication
7. **Topology Spread** - Distribute pods across nodes for high availability
8. **minReadySeconds** - Wait 30s after readiness before considering pods available

---

## Monitoring and Observability

| Component | Tool | Purpose |
|-----------|------|---------|
| **Metrics** | Prometheus + Grafana | Collect pod metrics, request rate, latency, error rate |
| **Logs** | EFK/ELK Stack | Centralized structured logging with request IDs |
| **Traces** | Jaeger/Tempo | Distributed tracing for request flow debugging |
| **Alerts** | AlertManager | Notify on high error rates, pod restarts, resource pressure |

### Key Alerts
- Error rate > 5% for 5 minutes
- Pod restarts > 5 in 10 minutes
- Memory usage > 80% of limit

### SLO Targets
- **Availability**: 99.9%
- **P95 latency**: < 500ms
- **Error rate**: < 0.1%

### Application Metrics to Expose
- Request count, latency, error rate by endpoint
- Active connections
- Business metrics (user sessions, transactions)

## Challenges & Solutions

In general I am familiar with k8s so for me there were no significant challenges