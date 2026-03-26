# LAB09 — Kubernetes Fundamentals

## 1. Task 1 — Local Kubernetes Setup

### Chosen tool and reason
I used **minikube** because it is simple for local learning and has easy built-in Ingress support (`minikube addons enable ingress`).

### Kubernetes fundamentals (brief)
- **Pod:** smallest runnable unit, one or more containers.
- **Deployment:** manages replicas and rolling updates.
- **Service:** stable network endpoint for Pods.
- **Namespace:** logical isolation boundary inside cluster.
- **Declarative approach:** define desired state in YAML, apply with `kubectl apply`.

### Evidence placeholders
- `kubectl cluster-info` output: `screenshots/lab09-cluster-info.png`
- `kubectl get nodes` output: `screenshots/lab09-get-nodes.png`

---

## 2. Task 2 — Application Deployment

Created manifest:
- `k8s/deployment.yml`

Implemented requirements:
- Uses Docker image from earlier labs (`olesianov/devops-info-python:lab03`)
- `replicas: 3`
- Requests/limits configured
- Liveness and readiness probes on `/health`
- Rolling update strategy with `maxUnavailable: 0`, `maxSurge: 1`
- Labels/selectors configured
- Container runs non-root (already set in image Dockerfile)

Evidence placeholders:
- `kubectl get deployments`: `screenshots/lab09-get-deployments.png`
- `kubectl get pods`: `screenshots/lab09-get-pods.png`
- `kubectl describe deployment devops-info-python`: `screenshots/lab09-describe-python-deploy.png`

---

## 3. Task 3 — Service Configuration

Created manifest:
- `k8s/service.yml`

Implemented requirements:
- Service type `NodePort`
- Correct selector (`app: devops-info-python`)
- Exposes service port 80 to container port 5000
- Fixed `nodePort: 30080` for predictable local testing

Access and verification:
- `kubectl port-forward service/devops-info-python-service 8080:80`
- `curl` to `/` and `/health`

Evidence placeholders:
- `kubectl get services`: `screenshots/lab09-get-services.png`
- `kubectl describe service devops-info-python-service`: `screenshots/lab09-describe-service.png`
- app response: `screenshots/lab09-app-response.png`

---

## 4. Task 4 — Scaling and Updates

### Scaling
- Scaled deployment from 3 to 5 replicas with `kubectl scale`.
- Verified running pods and rollout status.

### Rolling update
- Updated image tag to simulate new version.
- Watched rollout status and rollout history.
- Strategy keeps availability during update (`maxUnavailable: 0`).

### Rollback
- Executed `kubectl rollout undo`.
- Verified revision history and stable status.

Evidence placeholders:
- scaling output: `screenshots/lab09-scale-to-5.png`
- rollout status/history: `screenshots/lab09-rollout-history.png`
- rollback output: `screenshots/lab09-rollback.png`

---

## 5. Task 5 — Documentation Checklist Coverage

This repository includes:
- `k8s/README.md` with architecture, manifests, evidence, operations, production notes, and challenges.
- `k8s/LAB09.md` (this file) as concise task-by-task submission notes.

---

## 6. Bonus — Ingress with TLS

Implemented files:
- `k8s/deployment-app2.yml`
- `k8s/service-app2.yml`
- `k8s/ingress.yml`

### Bonus requirements coverage
1. **Second app deployment:** Go app deployed with its own Deployment and Service.
2. **Ingress controller:** use minikube ingress addon.
3. **Path routing:**  
   - `/app1` -> `devops-info-python-service`  
   - `/app2` -> `devops-info-go-service`
4. **TLS:** self-signed cert + Kubernetes TLS secret `devops-lab09-tls`.

Ingress benefit vs NodePort:
- One entry point for many services.
- Path/host routing at HTTP layer.
- Centralized TLS termination.

Evidence placeholders:
- ingress controller pods: `screenshots/lab09-ingress-controller.png`
- ingress resource: `screenshots/lab09-ingress-get.png`
- TLS secret: `screenshots/lab09-tls-secret.png`
- curl routing app1/app2: `screenshots/lab09-ingress-routing.png`
- curl HTTPS (`-k`): `screenshots/lab09-https-test.png`

---

## 7. Commands to Collect Evidence (Git Bash / WSL)

Run from `DevOps-Core-Course` root unless noted.

### 7.1 Cluster setup evidence

```bash
kubectl version --client
minikube version
minikube start --driver=docker
kubectl cluster-info
kubectl get nodes -o wide
kubectl get namespaces
```

### 7.2 Deploy app1 (Task 2 + 3)

```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl get deployments
kubectl get pods -o wide
kubectl get svc
kubectl describe deployment devops-info-python
kubectl describe service devops-info-python-service
kubectl get endpoints devops-info-python-service
```

### 7.3 Verify app1 works

```bash
kubectl port-forward service/devops-info-python-service 8080:80
```

In another terminal:

```bash
curl -s http://127.0.0.1:8080/ | head -c 400 && echo
curl -s http://127.0.0.1:8080/health
```

### 7.4 Scaling + rolling update + rollback (Task 4)

```bash
kubectl scale deployment/devops-info-python --replicas=5
kubectl rollout status deployment/devops-info-python
kubectl get pods -l app=devops-info-python

kubectl set image deployment/devops-info-python devops-info-python=olesianov/devops-info-python:lab04
kubectl rollout status deployment/devops-info-python
kubectl rollout history deployment/devops-info-python

kubectl rollout undo deployment/devops-info-python
kubectl rollout status deployment/devops-info-python
kubectl rollout history deployment/devops-info-python
```

### 7.5 Bonus: deploy app2 + ingress + TLS

```bash
kubectl apply -f k8s/deployment-app2.yml
kubectl apply -f k8s/service-app2.yml
minikube addons enable ingress
kubectl get pods -n ingress-nginx

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout k8s/tls.key -out k8s/tls.crt \
  -subj "/CN=local.devops.lab/O=local.devops.lab"

kubectl create secret tls devops-lab09-tls \
  --key k8s/tls.key \
  --cert k8s/tls.crt

kubectl apply -f k8s/ingress.yml
kubectl get ingress
kubectl describe ingress devops-info-ingress
kubectl get all
```

### 7.6 Bonus route checks

```bash
MINIKUBE_IP=$(minikube ip)
echo "$MINIKUBE_IP local.devops.lab"
```

Add that line to `/etc/hosts` (WSL) or `C:\Windows\System32\drivers\etc\hosts` (Windows), then test:

```bash
curl -s http://local.devops.lab/app1/health
curl -s http://local.devops.lab/app2/health
curl -k -s https://local.devops.lab/app1/health
curl -k -s https://local.devops.lab/app2/health
```

### 7.7 Helpful debug commands

```bash
kubectl get events --sort-by=.metadata.creationTimestamp
kubectl logs deployment/devops-info-python --tail=100
kubectl logs deployment/devops-info-go --tail=100
```

### 7.8 If you run via Ansible in WSL

Use this inventory flag in commands:

```bash
ansible-playbook -i inventory/hosts.ini <playbook>.yml
```

