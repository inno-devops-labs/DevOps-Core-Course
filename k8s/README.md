# Lab 9 — Kubernetes Fundamentals

## Architecture Overview

The application is deployed to a local Kubernetes cluster (kind).

Flow:
User → Service (NodePort) → Pods (Deployment)

* Deployment manages 3–5 replicas of the application
* Service exposes the application to external traffic
* Pods run a Flask application on port 8080

## Manifest Files

### deployment.yml

* Defines Deployment with 3 replicas
* Uses Docker image: ray326sq/devops-info-python:lab03
* Configured RollingUpdate strategy
* Resource requests and limits set:

  * CPU: 100m–200m
  * Memory: 128Mi–256Mi
* Liveness and Readiness probes configured on /health endpoint
* Container runs on port 8080

### service.yml

* Type: NodePort
* Exposes application externally
* Maps port 80 → 8080
* Uses label selector app=devops-app

## Deployment Evidence

### Cluster Info

```
$ kubectl get nodes
NAME                 STATUS   ROLES           AGE     VERSION
kind-control-plane   Ready    control-plane   9m52s   v1.35.1
```

```
$ kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:50266
CoreDNS is running at https://127.0.0.1:50266/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
```

### Resources

```
kubectl get all
kubectl get pods,svc
kubectl describe deployment devops-app
```

### Application Test

```
curl http://localhost:8080
curl http://localhost:8080/health
```

Application returns JSON with service info and health status.

## Operations Performed

### Deployment

```
kubectl apply -f k8s/deployment.yml
kubectl get deployments
kubectl get pods
```

### Service

```
kubectl apply -f k8s/service.yml
kubectl port-forward service/devops-app-service 8080:80
```

### Scaling

```
kubectl scale deployment/devops-app --replicas=5
kubectl get pods
```

### Rolling Update

```
kubectl apply -f k8s/deployment.yml
kubectl rollout status deployment/devops-app
```

### Rollback

```
kubectl rollout history deployment/devops-app
kubectl rollout undo deployment/devops-app
```

## Production Considerations

* Health checks ensure container reliability and automatic restarts
* Resource limits prevent resource exhaustion
* Rolling updates ensure zero downtime deployments
* Horizontal scaling improves availability

Future improvements:

* Use Ingress instead of NodePort
* Add monitoring (Prometheus, Grafana)
* Use CI/CD for automated deployments

## Challenges & Solutions

### Issue 1: CrashLoopBackOff

Cause: Incorrect container port (8000 instead of 8080)
Solution: Updated containerPort and probes to 8080

### Issue 2: ImagePullBackOff

Cause: Image not available inside kind cluster
Solution: Loaded image using:

```
kind load docker-image ray326sq/devops-info-python:lab03
```

### Issue 3: Health checks failing

Cause: Probes pointing to wrong port
Solution: Fixed probe configuration to correct port

## Learnings

* Kubernetes uses declarative configuration
* Debugging requires kubectl logs and describe
* Health checks are critical for stability
* Rolling updates prevent downtime

---

Kubernetes deployment successfully completed.
