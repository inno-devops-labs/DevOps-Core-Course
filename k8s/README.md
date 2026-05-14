## Local cluster verification

Minikube and kubectl verification outputs:

```bash
=== minikube status ===
minikube
type: Control Plane
host: Running
kubelet: Running
apiserver: Running
kubeconfig: Configured

=== kubectl cluster-info ===
Kubernetes control plane is running at https://192.168.49.2:8443
CoreDNS is running at https://192.168.49.2:8443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

=== kubectl get nodes ===
NAME       STATUS   ROLES           AGE   VERSION   INTERNAL-IP    EXTERNAL-IP  OS-IMAGE                         KERNEL-VERSION      CONTAINER-RUNTIME
minikube   Ready    control-plane   59s   v1.35.1   192.168.49.2   <none>       Debian GNU/Linux 12 (bookworm)   6.17.0-23-generic   docker://29.2.1

=== kubectl get namespaces ===
NAME              STATUS   AGE
default           Active   67s
kube-node-lease   Active   67s
kube-public       Active   67s
kube-system       Active   67s

=== minikube ip ===
192.168.49.2
```

## Notes
- Cluster was created with: `minikube start --driver=docker`.
- `kubectl` was configured by minikube; use `minikube kubectl -- <cmd>` if needed for version compatibility.

## Task 2 — Application Deployment

### Manifest files
- `k8s/deployment.yml`
	- Deployment name: `devops-python`
	- Replicas: `3`
	- Image: `devops-python:latest`
	- Container port: `5000`
	- Rolling update strategy: `maxSurge: 1`, `maxUnavailable: 0`
	- Resource requests: `cpu: 100m`, `memory: 128Mi`
	- Resource limits: `cpu: 250m`, `memory: 256Mi`
	- Probes:
		- Liveness: `GET /health` on port `5000`
		- Readiness: `GET /health` on port `5000`
	- Security context for runtime compatibility: `runAsUser: 1000`

- `k8s/service.yml`
	- Service name: `devops-python-service`
	- Type: `NodePort`
	- Port mapping: `80 -> 5000`, nodePort `30080`

### Commands used

```bash
cd /home/chupapupa/DevOps-Core-Course-v/lab_solutions/lab1/app_python
docker build -t devops-python:latest .
minikube image load devops-python:latest

kubectl apply -f /home/chupapupa/DevOps-Core-Course-v/k8s/deployment.yml
kubectl apply -f /home/chupapupa/DevOps-Core-Course-v/k8s/service.yml

kubectl rollout status deployment/devops-python --timeout=180s
kubectl get deployment devops-python -o wide
kubectl get pods -l app=devops-python -o wide
kubectl get svc devops-python-service -o wide
```

### Evidence (terminal output)

```bash
$ kubectl rollout status deployment/devops-python --timeout=180s
deployment "devops-python" successfully rolled out

$ kubectl get deployment devops-python -o wide
NAME            READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS      IMAGES                SELECTOR
devops-python   3/3     3            3           12m   devops-python   devops-python:latest  app=devops-python

$ kubectl get pods -l app=devops-python -o wide
NAME                             READY   STATUS    RESTARTS   AGE     IP           NODE       NOMINATED NODE   READINESS GATES
devops-python-64bbcbc858-6cjvw   1/1     Running   0          2m32s   10.244.0.10  minikube   <none>           <none>
devops-python-64bbcbc858-rbk8n   1/1     Running   0          2m47s   10.244.0.8   minikube   <none>           <none>
devops-python-64bbcbc858-t5fpl   1/1     Running   0          2m39s   10.244.0.9   minikube   <none>           <none>

$ kubectl get svc devops-python-service -o wide
NAME                    TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE   SELECTOR
devops-python-service   NodePort   10.103.198.46   <none>        80:30080/TCP   14m   app=devops-python
```

## Task 3 — Service Configuration and access

### Exposure method
- Service type: `NodePort`
- Exposed node port: `30080`
- Local Minikube URL: `http://192.168.49.2:30080`
- Fallback access used for testing: `kubectl port-forward service/devops-python-service 8080:80`

### Evidence (connectivity tests)

```bash
$ kubectl get endpoints devops-python-service -o wide
NAME                    ENDPOINTS                                            AGE
devops-python-service   10.244.0.11:5000,10.244.0.12:5000,10.244.0.13:5000   27s

$ curl -v --max-time 5 http://127.0.0.1:8080/health
> GET /health HTTP/1.1
< HTTP/1.1 200 OK
{"status":"healthy","timestamp":"2026-05-14T17:06:43.716721Z","uptime_seconds":2

$ curl -s http://127.0.0.1:8080/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"devops-python-866ff679fb-fmqq9"...

$ curl -s http://127.0.0.1:8080/metrics | head -n 10
# HELP python_gc_objects_collected_total Objects collected during gc
# TYPE python_gc_objects_collected_total counter
python_gc_objects_collected_total{generation="0"} 468.0
```

### What this proves
- The Service selects the correct Pods via `app=devops-python`.
- The application is reachable through a stable service endpoint.
- `/health`, `/`, and `/metrics` respond correctly through the exposed service.

## Next steps (suggested)
- Proceed to Task 3 connectivity validation (`minikube service devops-python-service --url` + `curl`).
- Add screenshots for deployment and service outputs.

## Task 4 — Scaling, rolling updates, and rollback

### Scaling demonstration

Commands used:

```bash
kubectl scale deployment/devops-python --replicas=5
kubectl rollout status deployment/devops-python --timeout=120s
kubectl get deployment devops-python -o wide
kubectl get pods -l app=devops-python -o wide
```

Evidence:

```bash
$ kubectl get deployment devops-python -o wide
NAME            READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS      IMAGES                SELECTOR
devops-python   5/5     5            5           14m   devops-python   devops-python:latest  app=devops-python
```

### Rolling update demonstration

Commands used:

```bash
cd /home/chupapupa/DevOps-Core-Course-v/lab_solutions/lab1/app_python
docker build -t devops-python:v2 .
minikube image load devops-python:v2

kubectl set image deployment/devops-python devops-python=devops-python:v2
kubectl rollout status deployment/devops-python --timeout=180s
kubectl rollout history deployment/devops-python
```

Evidence:

```bash
$ kubectl rollout history deployment/devops-python
deployment.apps/devops-python
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
```

### Rollback demonstration

Commands used:

```bash
kubectl rollout undo deployment/devops-python
kubectl rollout status deployment/devops-python --timeout=300s
kubectl get deployment devops-python -o wide
kubectl rollout history deployment/devops-python
```

Evidence:

```bash
$ kubectl rollout status deployment/devops-python --timeout=300s
deployment "devops-python" successfully rolled out

$ kubectl get deployment devops-python -o wide
NAME            READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS      IMAGES                SELECTOR
devops-python   5/5     5            5           16m   devops-python   devops-python:latest  app=devops-python
```

### Notes
- Scaling was performed to 5 replicas with `kubectl scale`.
- The rolling update was triggered by switching the image tag to `v2`.
- Rollback returned the Deployment to the previous revision and completed successfully.
