# Kubernetes deployment — DevOps Info Service

## Architecture Overview

```
                    ┌────────────────────┐
                    │  nodePort: 30080   │
                    └─────────┬──────────┘
                              │ 
                              │   selector: app: devops-info-service
                              │ 
            ┌─────────────────┼───────────────────────┐
            ▼                 ▼                       ▼
       ┌─────────┐         ┌─────────┐           ┌─────────┐
       │  Pod    │         │  Pod    │           │  Pod    │
       │  :5000  │         │  :5000  │           │  :5000  │
       └─────────┘         └─────────┘           └─────────┘
```

3 replicas. 
Exposed via NodePort 30080. Conteiner port 5000.

### Resources:
```
    requests:
        memory: "128Mi"
        cpu: "100m"
    limits:
        memory: "256Mi"
        cpu: "300m"
```

---

## Manifest Files

- **deployment.yml**:
    - 3 replicas
    - resource requests/limits (100m/128Mi plus 300m/256Mi)
    - liveness/readiness `/health` on port 5000
    - rolling update strategy with maxSurge 1 and maxUnavailable 0

- **service.yml**:
    - NodePort service
    - selector `app: devops-info-service`
    - service port 80 -> targetPort 5000, nodePort 30080

---

## Deployment Evidence

Commands and expected outputs:

```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl get all
NAME                                         READY   STATUS    RESTARTS   AGE
pod/devops-info-service-87555b7b6-47jvs      1/1     Running   0          12m
pod/devops-info-service-87555b7b6-d4jwl      1/1     Running   0          12m
pod/devops-info-service-87555b7b6-qsndw      1/1     Running   0          12m

NAME                          TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service   NodePort    10.109.235.249   <none>        80:30080/TCP   12m
service/kubernetes            ClusterIP   10.96.0.1        <none>        443/TCP        15m

NAME                                     READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service      3/3     3            3           12m

NAME                                               DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-info-service-87555b7b6      3         3         3       12m
```


```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl get pods,deploy,svc
NAME                                         READY   STATUS    RESTARTS   AGE
pod/devops-info-service-87555b7b6-47jvs      1/1     Running   0          15m
pod/devops-info-service-87555b7b6-d4jwl      1/1     Running   0          15m
pod/devops-info-service-87555b7b6-qsndw      1/1     Running   0          15m

NAME                                     READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service      3/3     3            3           15m

NAME                          TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service   NodePort    10.109.235.249   <none>        80:30080/TCP   14m
service/kubernetes            ClusterIP   10.96.0.1        <none>        443/TCP        17m
```


```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl describe deployment devops-info-service
Name:                   devops-info-service
Namespace:              default
CreationTimestamp:      Thu, 26 Mar 2026 16:35:26 +0300
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
    Image:      chaleshka/devops-info-service:latest
    Port:       5000/TCP
    Host Port:  0/TCP
    Limits:
      cpu:     300m
      memory:  256Mi
    Requests:
      cpu:      100m
      memory:   128Mi
    Liveness:   http-get http://:5000/health delay=15s timeout=3s period=10s #success=1 #failure=3
    Readiness:  http-get http://:5000/health delay=5s timeout=3s period=5s #success=1 #failure=3
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
NewReplicaSet:   devops-info-service-87555b7b6 (5/5 replicas created)
Events:
  Type    Reason             Age   From                   Message
  ----    ------             ----  ----                   -------
  Normal  ScalingReplicaSet  22m   deployment-controller  Scaled up replica set devops-info-service-87555b7b6 from 0 to 3
```

## Operations Performed

### Installation
```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

### Deploy
```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
```

### Scaling
```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl scale deployment/devops-info-service --replicas=0
deployment.apps/devops-info-service scaled

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl get all
NAME                                         READY   STATUS    RESTARTS   AGE
pod/devops-info-service-87555b7b6-47jvs      1/1     Running   0          12m
pod/devops-info-service-87555b7b6-d4jwl      1/1     Running   0          12m
pod/devops-info-service-87555b7b6-gs825      1/1     Running   0          28s
pod/devops-info-service-87555b7b6-qsndw      1/1     Running   0          12m
pod/devops-info-service-87555b7b6-wdtkl      1/1     Running   0          28s

NAME                          TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service   NodePort    10.109.235.249   <none>        80:30080/TCP   12m
service/kubernetes            ClusterIP   10.96.0.1        <none>        443/TCP        15m

NAME                                     READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service      5/5     5            5           12m

NAME                                               DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-info-service-87555b7b6      5         5         5       12m
```

### Rolling update
```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl apply -f k8s/deployment.yml
deployment.apps/devops-info-service configured

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl rollout status deployment/devops-info-service
deployment "devops-info-service" successfully rolled out
```

### Service Access and Verification
```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl -i http://192.168.49.2:30080/
HTTP/1.1 200 OK
Server: Werkzeug/3.1.5 Python/3.12.12
Date: Thu, 26 Mar 2026 14:26:59 GMT
Content-Type: application/json
Content-Length: 691
Connection: close

{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"10.244.0.1","method":"GET","path":"/","user_agent":"curl/8.5.0"},"runtime":{"current_time":"2026-03-26T14:26:59.840762+00:00","timezone":"UTC","uptime_human":"0.0h 10.0m","uptime_seconds":621.963426},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":12,"hostname":"devops-info-service-78c7795667-sdrnr","platform":"Linux","platform_version":"#1 SMP Tue Nov 5 00:21:55 UTC 2024","python_version":"3.12.12"}}


andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl -i http://192.168.49.2:30080/health
HTTP/1.1 200 OK
Server: Werkzeug/3.1.5 Python/3.12.12
Date: Thu, 26 Mar 2026 14:33:42 GMT
Content-Type: application/json
Content-Length: 97
Connection: close

{"status":"healthy","timestamp":"2026-03-26T14:33:42.622811+00:00","uptime_seconds":1024.745475}


andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl -i http://192.168.49.2:30080/health
HTTP/1.1 200 OK
Server: Werkzeug/3.1.5 Python/3.12.12
Date: Thu, 26 Mar 2026 14:33:46 GMT
Content-Type: application/json
Content-Length: 97
Connection: close

{"status":"healthy","timestamp":"2026-03-26T14:33:46.019084+00:00","uptime_seconds":1028.141748}


andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl -i http://192.168.49.2:30080/health
HTTP/1.1 200 OK
Server: Werkzeug/3.1.5 Python/3.12.12
Date: Thu, 26 Mar 2026 14:33:46 GMT
Content-Type: application/json
Content-Length: 97
Connection: close

{"status":"healthy","timestamp":"2026-03-26T14:33:46.470234+00:00","uptime_seconds":1028.592898}


andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl -i http://192.168.49.2:30080/health
HTTP/1.1 200 OK
Server: Werkzeug/3.1.5 Python/3.12.12
Date: Thu, 26 Mar 2026 14:33:46 GMT
Content-Type: application/json
Content-Length: 97
Connection: close

{"status":"healthy","timestamp":"2026-03-26T14:33:46.783296+00:00","uptime_seconds":1020.813187}


andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl -i http://192.168.49.2:30080/health
HTTP/1.1 200 OK
Server: Werkzeug/3.1.5 Python/3.12.12
Date: Thu, 26 Mar 2026 14:33:47 GMT
Content-Type: application/json
Content-Length: 97
Connection: close

{"status":"healthy","timestamp":"2026-03-26T14:33:47.087022+00:00","uptime_seconds":1035.408622}


andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl -i http://192.168.49.2:30080/health
HTTP/1.1 200 OK
Server: Werkzeug/3.1.5 Python/3.12.12
Date: Thu, 26 Mar 2026 14:33:47 GMT
Content-Type: application/json
Content-Length: 97
Connection: close

{"status":"healthy","timestamp":"2026-03-26T14:33:47.356393+00:00","uptime_seconds":1021.386284}
```


---

## Production Considerations

### What health checks did you implement and why?

Implemented health checks in deployment:
- livenessProbe (HTTP GET /health on port 5000)
  - initialDelaySeconds: 15, timeoutSeconds: 3, periodSeconds: 10, failureThreshold: 3
- readinessProbe (HTTP GET /health on port 5000)
  - initialDelaySeconds: 5, timeoutSeconds: 3, periodSeconds: 5, failureThreshold: 3

### Resource limits rationale

Deployment uses resources:
- requests: cpu 100m, memory 128Mi
- limits: cpu 300m, memory 256Mi

Rationale:
- Prevents a single Pod from consuming all node resources.
- Gives scheduler correct assumption of resource usage.
- Provides application protection against noisy neighbors in shared cluster.
- Supports predictable performance on local Minikube environment.

### How would you improve this for production?

- Use specific image tag instead of `latest` (e.g. `1.0.0`, `1.0.1`) and use immutable tags for reproducible deployments.
- Add HorizontalPodAutoscaler (HPA) to scale based on CPU/memory/requests.
- Add PodDisruptionBudget (PDB) to maintain availability during node maintenance.
- Use ConfigMap for non-sensitive config values and Secret for credentials, avoiding bake-in environment variables.
- Expose service through Ingress controller with TLS, not NodePort, for production-grade external access.
- Use a private registry with image scanning and signing (e.g., GCR/ECR/ACR + Notary/OCI sig).
- Enable resource quotas and limit ranges in namespace for multi-tenant safety.
- Add network policies (e.g., allow only app <-> db flow) for pod network segmentation.
- Add liveness/readiness startup probe tuning based on real app cold-start times.

### Monitoring and observability strategy

- App contains `/metrics` path for Prometheus.
- App can be used with grafana (as it was into Labs 7 and 8).

---

## Challenges & Solutions

No Challenges
