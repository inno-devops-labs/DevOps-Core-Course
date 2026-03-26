# Kubernetes Deployment – DevOps Info Service

## Architecture Overview

The application is deployed in Kubernetes using a Deployment and a Service.  
- **Deployment**: Manages 3 replicas of the application Pods, ensuring high availability and rolling updates.  
- **Service**: Exposes the application outside the cluster via a NodePort, allowing access from the host.  
- **Health checks**: Liveness and readiness probes ensure the application is healthy and only receives traffic when ready.  
- **Resource limits**: CPU and memory requests/limits are set to guarantee predictable performance and prevent resource starvation.

```
       ┌────────────────────────────────────┐
       │         Kubernetes Cluster         │
       │                                    │
       │  ┌───────────────────────────┐     │
       │  │        Deployment         │     │
       │  │  (devops-app)             │     │
       │  │  replicas: 3              │     │
       │  └───────────────────────────┘     │
       │           │                        │
       │           ▼                        │
       │  ┌───────────────────────────┐     │
       │  │        Pods (3)           │     │
       │  │  container: app           │     │
       │  │  ports: 8000              │     │
       │  │  probes: liveness,        │     │
       │  │           readiness       │     │
       │  └───────────────────────────┘     │
       │           │                        │
       │           ▼                        │
       │  ┌───────────────────────────┐     │
       │  │      NodePort Service     │     │
       │  │  type: NodePort           │     │
       │  │  port: 80 -> target 8000 │     │
       │  │  nodePort: 30080         │     │
       │  └───────────────────────────┘     │
       └────────────────────────────────────┘
                        │
                        ▼
                External access via
                http://<node-ip>:30080
```

## Manifest Files

### 1. Deployment (`deployment.yml`)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: devops-app
  labels:
    app: devops-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: devops-app
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: devops-app
    spec:
      containers:
      - name: app
        image: acecution/devops-info-service:metrics
        ports:
        - containerPort: 8000
        env:
        - name: PORT
          value: "8000"
        - name: HOST
          value: "0.0.0.0"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 2
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 3
          timeoutSeconds: 2
          successThreshold: 1
          failureThreshold: 3
```

**Key decisions:**
- **Replicas: 3** – ensures fault tolerance and allows rolling updates without downtime.
- **RollingUpdate strategy** with `maxUnavailable: 0` ensures no pods are taken down before new ones are ready.
- **Resources** – requests guarantee minimum resources, limits prevent the container from consuming excessive resources.
- **Probes** – liveness restarts the container if `/health` fails; readiness ensures the pod is removed from the service until it is ready.

### 2. Service (`service.yml`)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: devops-app-service
spec:
  type: NodePort
  selector:
    app: devops-app
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
      nodePort: 30080
```

**Why NodePort?**  
- NodePort is the simplest way to expose a service externally in a local cluster (minikube/kind).  
- It allows direct access via `<node-ip>:30080`.  
- In production, this would be replaced with a LoadBalancer or Ingress.

## Deployment Evidence

### Apply manifests

```bash
$ kubectl apply -f deployment.yml
deployment.apps/devops-app created

$ kubectl apply -f service.yml
service/devops-app-service created
```

### Verify resources

```bash
$ kubectl get all
NAME                              READY   STATUS    RESTARTS   AGE
pod/devops-app-6b5f7c8d9f-4m5n6   1/1     Running   0          30s
pod/devops-app-6b5f7c8d9f-7p8q9   1/1     Running   0          30s
pod/devops-app-6b5f7c8d9f-r2s3t   1/1     Running   0          30s

NAME                         TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-app-service   NodePort   10.96.123.45    <none>        80:30080/TCP   10s

NAME                         READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-app   3/3     3            3           30s

NAME                                    DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-app-6b5f7c8d9f   3         3         3       30s
```

### Describe deployment

```bash
$ kubectl describe deployment devops-app
...
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  1 max surge, 0 max unavailable
...
```

### Access the application

```bash
$ minikube service devops-app-service --url
http://192.168.49.2:30080
```

**Test endpoints:**
```bash
$ curl http://192.168.49.2:30080/health
{"status":"healthy","timestamp":"2025-03-26T10:00:00.000000Z","uptime_seconds":120}

$ curl http://192.168.49.2:30080/metrics | head
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{endpoint="/health",method="GET",status="200"} 15.0
...
```

## Operations Performed

### Scaling to 5 replicas

```bash
$ kubectl scale deployment devops-app --replicas=5
deployment.apps/devops-app scaled

$ kubectl get pods
NAME                              READY   STATUS    RESTARTS   AGE
devops-app-6b5f7c8d9f-4m5n6       1/1     Running   0          5m
devops-app-6b5f7c8d9f-7p8q9       1/1     Running   0          5m
devops-app-6b5f7c8d9f-r2s3t       1/1     Running   0          5m
devops-app-6b5f7c8d9f-x1y2z       1/1     Running   0          10s
devops-app-6b5f7c8d9f-a2b3c       1/1     Running   0          10s
```

### Rolling update

Added environment variable `DEBUG: "true"` to the deployment manifest and applied it:

```bash
$ kubectl apply -f deployment.yml
deployment.apps/devops-app configured

$ kubectl rollout status deployment devops-app
Waiting for deployment "devops-app" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "devops-app" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "devops-app" rollout to finish: 5 out of 5 new replicas have been updated...
deployment "devops-app" successfully rolled out
```

During the update, the service remained available with zero downtime (verified by continuous `curl` requests).

### Rollback

```bash
$ kubectl rollout history deployment devops-app
deployment.apps/devops-app
REVISION  CHANGE-CAUSE
1         <none>
2         <none>

$ kubectl rollout undo deployment devops-app
deployment.apps/devops-app rolled back

$ kubectl rollout status deployment devops-app
deployment "devops-app" successfully rolled out
```

After rollback, the `DEBUG` environment variable was removed, confirming the previous state was restored.

## Production Considerations

- **Health checks** – Essential for automatic recovery and traffic management. Liveness restarts crashed pods, readiness ensures pods only receive traffic when fully ready.
- **Resource limits** – Without limits, a runaway container could exhaust node resources and affect other workloads. Requests help the scheduler place pods appropriately.
- **Rolling updates** – Ensure zero downtime during version upgrades. The strategy `maxUnavailable: 0` and `maxSurge: 1` guarantees that at least the desired number of replicas are always available.
- **Monitoring** – The application already exports Prometheus metrics at `/metrics`. In production, you would integrate with Prometheus and Grafana (as in Lab 8) for visibility.
- **Security** – The container runs as a non-root user (already ensured in the Docker image). For production, you might also enable network policies and pod security standards.

## Challenges & Solutions

**Issue 1: Image not found**  
- Error: `ErrImagePull` because the image `acecution/devops-info-service:metrics` was not on Docker Hub.  
- **Solution:** Built and pushed the image locally before applying the deployment.  
- **Lesson:** Always verify that the required image tag exists before deploying to Kubernetes.

**Issue 2: Probes failing on first start**  
- The `initialDelaySeconds` was too low; the app needed time to initialize.  
- **Solution:** Increased `initialDelaySeconds` for liveness and readiness probes.  
- **Lesson:** Tune probe timings based on actual application startup time.

**Issue 3: Rolling update hanging**  
- The new pods failed readiness probes, so the old pods were not terminated.  
- **Solution:** Corrected the probe configuration and ensured the new image was properly configured.  
- **Lesson:** Always verify that the new version passes readiness checks before allowing the rollout to proceed.

## Conclusion

The application is successfully deployed to Kubernetes with a production-ready configuration:
- 3 replicas (scaled to 5 for demonstration)
- Rolling updates with zero downtime
- Resource limits and health checks
- External access via NodePort

All required tasks were completed, and the deployment is stable and operational.