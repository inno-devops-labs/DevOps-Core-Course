# Lab 09 — Kubernetes Fundamentals

## 1. Architecture Overview

This lab deploys a Python FastAPI application to a local Kubernetes cluster created with Minikube.

The final architecture includes:
- one `Deployment` named `python-app`
- one `Service` named `python-app-service`
- multiple replicated Pods managed by the Deployment
- external access through a `NodePort` Service

Traffic flow:

`Client -> NodePort Service -> Python application Pods`

The Service selects Pods using the label:

```yaml
app: python-app
```

The application image was built locally and loaded into Minikube, then deployed from Kubernetes manifests.

---

## 2. Manifest Files

### `deployment.yml`

The Deployment manifest defines the main application workload.

Key configuration choices:
- `replicas: 3` as the initial highly available setup
- `RollingUpdate` strategy for zero-downtime style updates
- container image based on the Python FastAPI application
- `readinessProbe` and `livenessProbe` on `/health`
- CPU and memory `requests` / `limits`
- exposed container port `5000`

This configuration ensures that:
- the application is replicated
- Kubernetes can detect unhealthy containers
- Pods only receive traffic after they become ready
- updates are performed gradually instead of stopping all Pods at once

### `service.yml`

The Service manifest exposes the application through Kubernetes networking.

Key configuration choices:
- `type: NodePort`
- service port `80`
- target container port `5000`
- selector `app: python-app`

This allowed external access to the application from the local machine.

---

## 3. Deployment Evidence

### Cluster setup

```bash
kubectl cluster-info
kubectl get nodes
kubectl get namespaces
```

Cluster status showed:
- running Kubernetes control plane
- one ready node (`minikube`)
- default system namespaces present

### Initial deployment

```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl get deployments
kubectl get pods
kubectl get svc
```

Initial deployment result:
- Deployment `python-app` successfully created
- 3 Pods reached `Running` state
- Service `python-app-service` created as `NodePort`

### Application verification

The application was accessed through the NodePort URL provided by Minikube:

```bash
minikube service python-app-service --url
```

Returned URL example:

```text
http://127.0.0.1:59869
```

Endpoint verification:

```bash
curl http://127.0.0.1:59869/health
curl http://127.0.0.1:59869/
```

Health endpoint response:

```json
{"status":"healthy","timestamp":"2026-03-25T07:19:09.795930+00:00","uptime_seconds":788}
```

Root endpoint response confirmed:
- service name `python-app`
- version information
- FastAPI runtime details
- available endpoints `/`, `/health`, `/metrics`

Note: on macOS with Minikube Docker driver, `minikube service --url` keeps a local tunnel process active in the terminal. This is expected behavior.

---

## 4. Operations Performed

### 4.1 Scaling

Scaling was demonstrated with:

```bash
kubectl scale deployment/python-app --replicas=5
kubectl rollout status deployment/python-app
kubectl get deployments
kubectl get pods
```

Command output showed:

```text
deployment.apps/python-app scaled
Waiting for deployment "python-app" rollout to finish: 3 of 5 updated replicas are available...
Waiting for deployment "python-app" rollout to finish: 4 of 5 updated replicas are available...
deployment "python-app" successfully rolled out
```

Deployment state after scaling:

```text
NAME         READY   UP-TO-DATE   AVAILABLE   AGE
python-app   5/5     5            5           20m
```

Pod state after scaling:

```text
NAME                          READY   STATUS    RESTARTS   AGE
python-app-6cf789bbf8-8mw2g   1/1     Running   0          3m59s
python-app-6cf789bbf8-ctnc4   1/1     Running   0          4m6s
python-app-6cf789bbf8-fdsls   1/1     Running   0          7s
python-app-6cf789bbf8-r4p66   1/1     Running   0          7s
python-app-6cf789bbf8-zwzd5   1/1     Running   0          4m13s
```

This confirmed successful horizontal scaling from 3 to 5 replicas.

### 4.2 Rolling Update

A rolling update was demonstrated by changing the environment variable:

```yaml
- name: APP_VERSION
  value: "lab09"
```

to:

```yaml
- name: APP_VERSION
  value: "lab09-v2"
```

Then applying the updated manifest:

```bash
kubectl apply -f k8s/deployment.yml
kubectl rollout status deployment/python-app
kubectl rollout history deployment/python-app
```

Verification:

```bash
curl http://127.0.0.1:59869/
```

The response showed:

```json
"version":"lab09-v2"
```

This confirmed that Kubernetes replaced old Pods gradually and deployed the new revision successfully.

### 4.3 Rollback

Rollback was demonstrated with:

```bash
kubectl rollout undo deployment/python-app
kubectl rollout status deployment/python-app
kubectl rollout history deployment/python-app
```

Verification:

```bash
curl http://127.0.0.1:59869/
```

The response showed:

```json
"version":"lab09"
```

This confirmed that Kubernetes successfully restored the previous stable revision.

### 4.4 Zero-Downtime Verification

Zero downtime was verified during a rolling update by sending continuous health-check requests while the deployment was being updated.

Commands used:

```bash
kubectl port-forward service/python-app-service 8080:80
```

In another terminal:

```bash
while true; do curl -s http://127.0.0.1:8080/health; echo; sleep 1; done
```

During the rollout, health responses continued without interruption. This confirmed that the rolling update strategy with readiness checks maintained service availability throughout the deployment process.

---

## 5. Production Considerations

Several production-oriented Kubernetes practices were included even in this local lab:

### Health checks
- `readinessProbe` ensures traffic is sent only to ready Pods
- `livenessProbe` allows automatic restart of unhealthy containers

### Resource management
- CPU and memory requests improve scheduler decisions
- CPU and memory limits prevent uncontrolled container resource usage

### Rolling deployment strategy
- `RollingUpdate` reduces downtime during updates
- `maxUnavailable: 0` helps preserve availability during rollout

### Potential future improvements
For a production environment, the following should be added:
- `Ingress` instead of direct `NodePort`
- TLS termination
- `HorizontalPodAutoscaler`
- `ConfigMap` and `Secret` resources
- monitoring and alerting integration
- persistent centralized logging
- dedicated image registry and CI/CD pipeline

---

## 6. Challenges and Solutions

### Challenge 1 — image pull failure
Initially, Pods failed with `ErrImagePull`.

Cause:
- Kubernetes could not access the required image directly

Solution:
- the application image was built locally
- the image was loaded into Minikube
- Deployment was configured to use the local image

### Challenge 2 — architecture mismatch risk on Apple Silicon
The work was performed on macOS Apple Silicon (`aarch64` / ARM64), while some existing Docker images were built for `amd64`.

Solution:
- rebuild and use a local image compatible with the current machine architecture

### Challenge 3 — local service access on macOS
With Minikube Docker driver on macOS, `minikube service --url` keeps the terminal session occupied because it runs a tunnel.

Solution:
- keep that terminal open while testing
- use another terminal window for `curl` requests

### Challenge 4 — path confusion during manifest apply
At one point, manifests were not found because commands were executed from the `app_python/` directory instead of the repository root.

Solution:
- return to the project root before running:

```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
```

---

## 7. Learning Outcomes

This lab demonstrated the core Kubernetes workflow:
- creating a local cluster with Minikube
- deploying an application with `Deployment`
- exposing it with `Service`
- verifying availability
- scaling replicas
- performing rolling updates
- using rollback to restore a previous revision

The lab also showed the practical relationship between:
- Docker images
- Kubernetes Pods
- Deployments
- Services
- health probes
- rollout management