# LAB 09 — Kubernetes Fundamentals

## Overview

In this lab, we deployed a containerized application to Kubernetes using declarative manifests.  
The goal was to understand Kubernetes fundamentals and apply production-ready practices.

## Architecture

Application deployed as:

- Deployment (3 replicas)
- Service (NodePort)

Flow:

Client → Service → Pods (Deployment)

## Task 1 — Cluster Setup

### Commands used

```
minikube start --driver=docker
kubectl cluster-info
kubectl get nodes
```

### Screenshot

`screenshots/9-1-nodes.png`

## Task 2 — Deployment

### Manifest

File: `k8s/deployment.yml`

Key features:
- 3 replicas
- resource limits
- liveness & readiness probes

### Commands

```
kubectl apply -f k8s/deployment.yml
kubectl get deployments
kubectl get pods
```

### Screenshot

`screenshots/9-2-pods.png`

## Task 3 — Service

### Manifest

File: `k8s/service.yml`

Type: NodePort

### Commands

```
kubectl apply -f k8s/service.yml
kubectl get services
```

### Access app

```
minikube service devops-service --url
curl http://<url>
```

### Screenshot

`screenshots/9-3-curl.png`

## Task 4 — Scaling

### Command

```
kubectl scale deployment/devops-app --replicas=5
kubectl get pods
```

### Screenshot

`screenshots/9-4-pods5.png`

## Task 5 — Rolling Update

### Update image

(edit deployment.yml)

```
kubectl apply -f k8s/deployment.yml
kubectl rollout status deployment/devops-app
```

### Screenshot

`screenshots/9-5-rollout.png`

## Task 6 — Rollback

```
kubectl rollout undo deployment/devops-app
kubectl rollout history deployment/devops-app
```

### Screenshot

`screenshots/9-6-rollback.png`

## Deployment Evidence

### Commands

```
kubectl get all
kubectl get pods,svc
kubectl describe deployment devops-app
```

### Screenshot

`screenshots/9-7-evidence.png`

## Production Considerations

- Liveness & readiness probes for reliability
- Resource limits for stability
- Rolling updates for zero downtime
- Scaling for load handling

## Challenges

### 1. ImagePullBackOff
Fix: push image to DockerHub

### 2. Service not working
Fix: correct labels

### 3. Pod crash
Fix: check logs

```
kubectl logs <pod>
```

## Conclusion

Successfully:

- Deployed application to Kubernetes
- Exposed it via Service
- Implemented scaling and updates
- Applied production best practices

Kubernetes provides automated management and scalability for containerized applications.