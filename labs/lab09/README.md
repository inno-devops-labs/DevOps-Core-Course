# Lab 09 — Kubernetes Fundamentals

## Architecture Overview

This lab demonstrates deployment of a containerized FastAPI application to a local Kubernetes cluster using declarative manifests.

Architecture:
- 1 Kubernetes Deployment: `devops-info-service`
- 1 Kubernetes Service: `devops-info-service`
- 3 replicas initially, later scaled to 5 replicas
- Service type: `NodePort`

Traffic flow:
Client -> Service -> Pods

The application container listens on port `5000`.
The Kubernetes Service exposes port `80` and forwards traffic to container port `5000`.

Resource allocation strategy:
- CPU request: `100m`
- CPU limit: `200m`
- Memory request: `128Mi`
- Memory limit: `256Mi`

This configuration provides basic resource isolation and helps Kubernetes schedule Pods properly.

## Manifest Files

### `k8s/deployment.yml`
This manifest defines the application Deployment.

Key configuration choices:
- `replicas: 3` for high availability
- `RollingUpdate` strategy with:
  - `maxSurge: 1`
  - `maxUnavailable: 0`
- container image: `fayzullin/devops-info-service:latest`
- container port: `5000`
- readiness and liveness probes using `/health`
- resource requests and limits
- labels for organization and selector matching

Why these values were chosen:
- 3 replicas satisfy the lab requirement and improve availability
- rolling update settings ensure zero downtime during updates
- resource limits protect the cluster from excessive resource usage
- `/health` is the dedicated endpoint for health checks

### `k8s/service.yml`
This manifest defines a Kubernetes Service for exposing the application.

Key configuration choices:
- Service type: `NodePort`
- Service port: `80`
- target port: `5000`
- selector: `app=devops-info-service`

Why this was chosen:
- `NodePort` is appropriate for local cluster access
- the selector matches Pods created by the Deployment

## Deployment Evidence

### Cluster setup
```bash
kubectl cluster-info
kubectl get nodes
kubectl get namespaces
```

Example output:

Kubernetes control plane is running at https://127.0.0.1:39539
CoreDNS is running at https://127.0.0.1:39539/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

NAME                 STATUS   ROLES           AGE   VERSION
lab9-control-plane   Ready    control-plane   28m   v1.33.1

NAME                 STATUS   AGE
default              Active   28m
kube-node-lease      Active   28m
kube-public          Active   28m
kube-system          Active   28m
local-path-storage   Active   27m

Current resources

```bash
kubectl get all
kubectl get pods,svc -o wide
kubectl describe deployment devops-info-service
```

Example output:

NAME                                       READY   STATUS    RESTARTS   AGE
pod/devops-info-service-7c94bcb745-dbdmp   1/1     Running   0          31s
pod/devops-info-service-7c94bcb745-h9248   1/1     Running   0          52s
pod/devops-info-service-7c94bcb745-rv99s   1/1     Running   0          43s

NAME                          TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service   NodePort    10.96.89.151   <none>        80:30080/TCP   7m1s

NAME                                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service   3/3     3            3           7m2s
Application verification

The application was tested using port forwarding:

```bash
kubectl port-forward service/devops-info-service 8080:80
curl http://localhost:8080
curl http://localhost:8080/health
```

Example output:

{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"devops-info-service-7c94bcb745-h9248","platform":"Linux","platform_version":"6.14.0-35-generic","architecture":"x86_64","cpu_count":6,"python_version":"3.12.13"},"runtime":{"uptime_seconds":71,"uptime_human":"0 hours, 1 minutes","current_time":"2026-03-27T17:31:04.829259+00:00","timezone":"UTC"},"request":{"client_ip":"127.0.0.1","user_agent":"curl/8.5.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}
{"status":"healthy","timestamp":"2026-03-27T17:31:04.956924+00:00","uptime_seconds":71}

## Operations Performed
Deployment

```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
Scaling demonstration
```

The Deployment was scaled from 3 replicas to 5 replicas.

Commands used:

```bash
kubectl scale deployment/devops-info-service --replicas=5
kubectl get pods
kubectl rollout status deployment/devops-info-service
kubectl get deployment devops-info-service
```

Result:

NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
devops-info-service   5/5     5            5           10m
Rolling update demonstration

A rolling update was demonstrated by applying an updated Deployment manifest with new probe configuration.

Commands used:

```bash
kubectl apply -f deployment.yml
kubectl rollout status deployment/devops-info-service
kubectl describe deployment devops-info-service
```

Observed behavior:

Kubernetes created a new ReplicaSet
old Pods were terminated gradually
new Pods became Ready before old Pods were fully removed
zero downtime was preserved because maxUnavailable: 0

## Rollback demonstration

Rollback was demonstrated using Deployment rollout undo.

Commands used:

```bash
kubectl rollout history deployment/devops-info-service
kubectl rollout undo deployment/devops-info-service
kubectl rollout status deployment/devops-info-service
kubectl rollout history deployment/devops-info-service
kubectl get pods
```

Example output:

REVISION  CHANGE-CAUSE
1         <none>
2         <none>

deployment.apps/devops-info-service rolled back

REVISION  CHANGE-CAUSE
2         <none>
3         <none>

Rollback result:

deployment was successfully rolled back
previous ReplicaSet became active again
Pods were recreated and reached Running state

## Production Considerations
Health checks

Both readiness and liveness probes were configured to use the /health endpoint.

Why:

readinessProbe ensures traffic is routed only to healthy Pods
livenessProbe allows Kubernetes to restart unhealthy containers automatically
Resource limits

CPU and memory requests/limits were defined to:

help Kubernetes scheduler place Pods correctly
prevent one container from consuming too many cluster resources
improve cluster stability
Production improvements

For a real production environment, I would additionally implement:

Ingress or Gateway API for HTTP routing
TLS termination
ConfigMaps and Secrets
Horizontal Pod Autoscaler
PodDisruptionBudget
centralized logging
monitoring with Prometheus and Grafana
CI/CD pipeline for automated deployments
separate namespaces for environments
Monitoring and observability strategy

A production setup should include:

metrics collection
application logs aggregation
Kubernetes events monitoring
alerting on failed Pods, restart loops, and probe failures
dashboarding for CPU, memory, and request latency

##Challenges & Solutions

Challenge 1: Docker image push failed

Initially, pushing the Docker image to Docker Hub failed due to insufficient token scopes.

Solution:

re-authenticated with Docker Hub
pushed the image successfully after fixing credentials
Challenge 2: Local Kubernetes tool setup

minikube was not installed on the system.

Solution:

installed kind
created a local cluster with kind create cluster --name lab9
Challenge 3: Initial Pod startup

At first, Pods were in ContainerCreating and one Pod briefly showed ErrImagePull.

Solution:

verified the image was available in Docker Hub
waited for image pull to complete
confirmed all Pods eventually reached Running
Challenge 4: Choosing correct health check endpoint

Initially probes were configured against /.

Solution:

updated both liveness and readiness probes to use /health
applied the updated Deployment
verified successful rollout

## What I Learned

In this lab I learned:

how to deploy a containerized application to Kubernetes using declarative YAML manifests
how Deployments manage desired state and rolling updates
how Services provide stable networking for Pods
how to configure health checks and resource limits
how to scale applications and perform rollback operations
how Kubernetes reconciles desired and actual cluster state
