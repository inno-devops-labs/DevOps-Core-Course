# Lab 09 - Kubernetes Fundamentals

## Architecture Overview

The deployment runs 3 replicas of the `devops-info-service` Flask app behind a NodePort Service. Traffic enters through the Service on port 80 and is forwarded to container port 5000.

```
Client -> NodePort (30080) -> Service (port 80) -> Pods (port 5000) x3
```

Each pod requests 100m CPU / 128Mi memory with limits of 200m CPU / 256Mi memory. This keeps resource usage predictable without being too restrictive for a lightweight Flask app.

## Cluster Setup

Tool: minikube. It provides a full single-node cluster with addon support and is simple to set up on Linux.

```bash
minikube start
```

```
$ kubectl cluster-info
Kubernetes control plane is running at https://192.168.49.2:8443
CoreDNS is running at https://192.168.49.2:8443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

$ kubectl get nodes
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   19s   v1.35.1
```

## Manifest Files

### deployment.yml

Deployment for the Python app with:
- 3 replicas for availability
- RollingUpdate strategy with `maxSurge: 1` and `maxUnavailable: 0` for zero-downtime deploys
- Liveness probe on `/health` (restarts unhealthy containers)
- Readiness probe on `/health` (removes unready pods from service)
- Resource requests and limits

### service.yml

NodePort Service exposing the deployment:
- Selector matches `app: devops-info-service` labels from the Deployment
- Maps external port 80 to container port 5000
- NodePort 30080 for local access

## Deployment

```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
```

```
$ kubectl get all
NAME                                       READY   STATUS    RESTARTS   AGE
pod/devops-info-service-7d48dc69bc-b7b87   1/1     Running   0          69s
pod/devops-info-service-7d48dc69bc-frwp6   1/1     Running   0          69s
pod/devops-info-service-7d48dc69bc-vnkf7   1/1     Running   0          69s

NAME                          TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service   NodePort    10.98.62.61   <none>        80:30080/TCP   69s
service/kubernetes            ClusterIP   10.96.0.1     <none>        443/TCP        3m5s

NAME                                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service   3/3     3            3           69s

NAME                                             DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-info-service-7d48dc69bc   3         3         3       69s
```

```
$ kubectl get pods,svc -o wide
NAME                                       READY   STATUS    RESTARTS   AGE   IP           NODE       NOMINATED NODE   READINESS GATES
pod/devops-info-service-7d48dc69bc-b7b87   1/1     Running   0          71s   10.244.0.3   minikube   <none>           <none>
pod/devops-info-service-7d48dc69bc-frwp6   1/1     Running   0          71s   10.244.0.5   minikube   <none>           <none>
pod/devops-info-service-7d48dc69bc-vnkf7   1/1     Running   0          71s   10.244.0.4   minikube   <none>           <none>

NAME                          TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE    SELECTOR
service/devops-info-service   NodePort    10.98.62.61   <none>        80:30080/TCP   71s    app=devops-info-service
service/kubernetes            ClusterIP   10.96.0.1     <none>        443/TCP        3m7s   <none>
```

```
$ kubectl describe deployment devops-info-service
Name:                   devops-info-service
Namespace:              default
Labels:                 app=devops-info-service
Selector:               app=devops-info-service
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Pod Template:
  Labels:  app=devops-info-service
  Containers:
   devops-info-service:
    Image:      iucapstonead/devops-info-service:latest
    Port:       5000/TCP
    Limits:
      cpu:     200m
      memory:  256Mi
    Requests:
      cpu:         100m
      memory:      128Mi
    Liveness:      http-get http://:5000/health delay=10s timeout=1s period=5s #success=1 #failure=3
    Readiness:     http-get http://:5000/health delay=5s timeout=1s period=3s #success=1 #failure=3
```

Access:

```bash
$ minikube service devops-info-service --url
http://192.168.49.2:30080

$ curl http://192.168.49.2:30080/health
{"status":"healthy","timestamp":"2026-03-26T18:46:50.356469+00:00","uptime_seconds":119}
```

## Scaling

Scaled to 5 replicas by changing `replicas: 5` in deployment.yml:

```bash
kubectl apply -f k8s/deployment.yml
```

```
$ kubectl get pods
NAME                                   READY   STATUS    RESTARTS   AGE
devops-info-service-7d48dc69bc-2lbzb   1/1     Running   0          75s
devops-info-service-7d48dc69bc-9cq48   1/1     Running   0          75s
devops-info-service-7d48dc69bc-b7b87   1/1     Running   0          4m4s
devops-info-service-7d48dc69bc-frwp6   1/1     Running   0          4m4s
devops-info-service-7d48dc69bc-vnkf7   1/1     Running   0          4m4s
```

## Rolling Update

Updated image tag to `0.3.1` and applied:

```
$ kubectl set image deployment/devops-info-service devops-info-service=iucapstonead/devops-info-service:0.3.1
deployment.apps/devops-info-service image updated

$ kubectl rollout status deployment/devops-info-service
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 1 old replicas are pending termination...
deployment "devops-info-service" successfully rolled out
```

The `maxUnavailable: 0` setting ensures all existing pods stay running until new ones pass readiness checks.

## Rollback

```
$ kubectl rollout history deployment/devops-info-service
REVISION  CHANGE-CAUSE
1         <none>
2         <none>

$ kubectl rollout undo deployment/devops-info-service
deployment.apps/devops-info-service rolled back

$ kubectl rollout history deployment/devops-info-service
REVISION  CHANGE-CAUSE
2         <none>
3         <none>
```

Revision 1 became revision 3 after the rollback, confirming the original spec was restored.

## Production Considerations

### Health checks

Both liveness and readiness probes hit `/health`. The liveness probe has a longer `initialDelaySeconds` (10s) to give the app time to start. The readiness probe starts checking after 5s so pods are added to the service quickly once ready.

### Resource limits

Requests are set conservatively (100m CPU, 128Mi) since the Flask app is lightweight. Limits are 2x requests to allow short bursts without letting a pod consume excessive resources.

### Improvements for production

- Use a specific image tag instead of `latest` for reproducibility
- Add a HorizontalPodAutoscaler for dynamic scaling
- Use Ingress instead of NodePort for proper HTTP routing
- Add NetworkPolicies for pod-to-pod traffic control
- Set up PodDisruptionBudgets to maintain availability during node maintenance
- Use namespaces to isolate environments

### Monitoring

Prometheus metrics are already exposed at `/metrics` by the app. In production, deploy Prometheus with ServiceMonitor CRDs to scrape pods automatically. Grafana dashboards for request rates and latency.

## Challenges

- Initial pod crashes due to readiness probe hitting the app before it was fully started. Fixed by increasing `initialDelaySeconds`.
- NodePort access required `minikube service` command since the cluster IP is not directly reachable from the host network.
- Resource limits too low initially caused OOMKill on startup. Bumped memory limit from 128Mi to 256Mi.
