# Lab 9 — Kubernetes Fundamentals

## Architecture Overview

I used **Minikube** with the Docker driver because it was already available on the workstation, integrates cleanly with `kubectl`, and provides a built-in NGINX Ingress addon for the bonus task.

The deployment architecture is:

```text
Client
  |
  +--> NodePort service (devops-info-python) -> 3 Python Pods
  |
  +--> Ingress (local.example.com)
         +--> /app1 -> devops-info-python service -> Python Pods
         +--> /app2 -> devops-info-go service -> Go Pods
```

Resource strategy:
- Python app: `100m` CPU / `128Mi` memory requests, `250m` CPU / `256Mi` memory limits
- Go app: `100m` CPU / `64Mi` memory requests, `250m` CPU / `128Mi` memory limits
- Both deployments use `maxUnavailable: 0` and `maxSurge: 1` for safe rolling updates.

## Local Kubernetes Setup

Chosen tool: **Minikube**

Why:
- already installed locally
- works well with the Docker driver on macOS
- easy ingress enablement for the bonus task
- simple local service access with `minikube service --url`

Tool versions observed during the run:

```bash
kubectl version --client --output=yaml
```

```text
clientVersion:
  gitVersion: v1.32.2
  platform: darwin/arm64
```

```bash
minikube version
```

```text
minikube version: v1.35.0
```

Cluster startup:

```bash
minikube start -p lab9 --driver=docker --kubernetes-version=v1.32.0
minikube addons enable ingress -p lab9
kubectl cluster-info
kubectl get nodes -o wide
kubectl get pods -n ingress-nginx
```

```text
Kubernetes control plane is running at https://127.0.0.1:60400
CoreDNS is running at https://127.0.0.1:60400/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```

```text
NAME   STATUS   ROLES           AGE   VERSION   INTERNAL-IP    EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION     CONTAINER-RUNTIME
lab9   Ready    control-plane   85s   v1.32.0   192.168.49.2   <none>        Ubuntu 22.04.5 LTS   6.10.14-linuxkit   docker://27.4.1
```

```text
NAME                                        READY   STATUS      RESTARTS   AGE
ingress-nginx-admission-create-mmm7d        0/1     Completed   0          57s
ingress-nginx-admission-patch-sjx65         0/1     Completed   1          57s
ingress-nginx-controller-56d7c84fd4-pzzsp   1/1     Running     0          57s
```

## Manifest Files

Files created:

- `k8s/namespace.yml`
  Creates isolated namespace `devops-lab9`.
- `k8s/deployment.yml`
  Main Python deployment with 3 replicas, rolling update strategy, resource controls, and startup/readiness/liveness probes.
- `k8s/service.yml`
  NodePort service for external local access to the Python application on port `30080`.
- `k8s/bonus-go-deployment.yml`
  Bonus Go deployment for multi-application ingress routing.
- `k8s/bonus-go-service.yml`
  NodePort service for the Go application on port `30081`.
- `k8s/ingress.yml`
  NGINX ingress with regex path rewrites:
  `/app1(/|$)(.*)` -> Python service
  `/app2(/|$)(.*)` -> Go service
- `k8s/kustomization.yaml`
  Allows a single `kubectl apply -k k8s`.

Key configuration choices:

- 3 Python replicas satisfy the lab requirement while still being light enough for Minikube.
- Probes use `/health`, which both applications already expose.
- Numeric `runAsUser`, `runAsGroup`, and `fsGroup` are set to keep `runAsNonRoot: true` valid in Kubernetes.
- Fixed NodePorts make local testing deterministic.
- TLS is terminated at the ingress using a self-signed certificate stored as a Kubernetes TLS secret.

## Deployment Evidence

Deployment commands:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /tmp/devops-lab9-tls/tls.key \
  -out /tmp/devops-lab9-tls/tls.crt \
  -subj "/CN=local.example.com/O=local.example.com"

kubectl create namespace devops-lab9 --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret tls devops-lab9-tls \
  --namespace devops-lab9 \
  --key /tmp/devops-lab9-tls/tls.key \
  --cert /tmp/devops-lab9-tls/tls.crt \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl apply -k k8s
kubectl rollout status deployment/devops-info-python -n devops-lab9 --timeout=180s
kubectl rollout status deployment/devops-info-go -n devops-lab9 --timeout=180s
```

`kubectl get all -n devops-lab9`:

```text
NAME                                     READY   STATUS    RESTARTS   AGE
pod/devops-info-go-588c865797-8jjd4      1/1     Running   0          3m38s
pod/devops-info-go-588c865797-z7cgs      1/1     Running   0          4m34s
pod/devops-info-python-f788594f7-gpptm   1/1     Running   0          2m41s
pod/devops-info-python-f788594f7-pttqw   1/1     Running   0          4m34s
pod/devops-info-python-f788594f7-vdkdj   1/1     Running   0          3m48s

NAME                         TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-info-go       NodePort   10.108.72.148   <none>        80:30081/TCP   9m17s
service/devops-info-python   NodePort   10.97.112.209   <none>        80:30080/TCP   9m17s

NAME                                 READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-go       2/2     2            2           9m17s
deployment.apps/devops-info-python   3/3     3            3           9m17s
```

`kubectl get pods,svc -n devops-lab9 -o wide`:

```text
NAME                                     READY   STATUS    RESTARTS   AGE     IP            NODE   NOMINATED NODE   READINESS GATES
pod/devops-info-go-588c865797-8jjd4      1/1     Running   0          3m36s   10.244.0.15   lab9   <none>           <none>
pod/devops-info-go-588c865797-z7cgs      1/1     Running   0          4m32s   10.244.0.13   lab9   <none>           <none>
pod/devops-info-python-f788594f7-gpptm   1/1     Running   0          2m39s   10.244.0.16   lab9   <none>           <none>
pod/devops-info-python-f788594f7-pttqw   1/1     Running   0          4m32s   10.244.0.12   lab9   <none>           <none>
pod/devops-info-python-f788594f7-vdkdj   1/1     Running   0          3m46s   10.244.0.14   lab9   <none>           <none>

NAME                         TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE     SELECTOR
service/devops-info-go       NodePort   10.108.72.148   <none>        80:30081/TCP   9m15s   app.kubernetes.io/name=devops-info-go
service/devops-info-python   NodePort   10.97.112.209   <none>        80:30080/TCP   9m15s   app.kubernetes.io/name=devops-info-python
```

`kubectl describe deployment devops-info-python -n devops-lab9`:

```text
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Liveness:               http-get http://:http/health
Readiness:              http-get http://:http/health
Startup:                http-get http://:http/health
```

NodePort access:

```bash
minikube service devops-info-python -n devops-lab9 --url -p lab9
```

```text
http://127.0.0.1:62388
```

Application verification:

```bash
curl -fsS http://127.0.0.1:62388/health
curl -fsS http://127.0.0.1:62388/
```

```json
{"status":"healthy","timestamp":"2026-03-26T17:06:56.747641+00:00","uptime_seconds":431}
```

```json
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"10.244.0.1","method":"GET","path":"/","user_agent":"curl/8.7.1"},"runtime":{"current_time":"2026-03-26T17:06:56.483712+00:00","timezone":"UTC","uptime_human":"6 minutes","uptime_seconds":368},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"aarch64","cpu_count":10,"hostname":"devops-info-python-f788594f7-vdkdj","platform":"Linux","platform_version":"#1 SMP Thu Aug 14 19:26:13 UTC 2025","python_version":"3.13.11"}}
```

## Operations Performed

### Scaling

Commands:

```bash
kubectl scale deployment/devops-info-python -n devops-lab9 --replicas=5
kubectl rollout status deployment/devops-info-python -n devops-lab9 --timeout=180s
kubectl get deployment devops-info-python -n devops-lab9
kubectl get pods -n devops-lab9 -l app.kubernetes.io/name=devops-info-python
```

Output:

```text
deployment.apps/devops-info-python scaled
deployment "devops-info-python" successfully rolled out
```

```text
NAME                 READY   UP-TO-DATE   AVAILABLE   AGE
devops-info-python   5/5     5            5           13m
```

```text
NAME                                 READY   STATUS    RESTARTS   AGE
devops-info-python-f788594f7-gpptm   1/1     Running   0          7m19s
devops-info-python-f788594f7-jsbwb   1/1     Running   0          54s
devops-info-python-f788594f7-pttqw   1/1     Running   0          9m12s
devops-info-python-f788594f7-rbl2q   1/1     Running   0          54s
devops-info-python-f788594f7-vdkdj   1/1     Running   0          8m26s
```

After the demo, I restored the deployment back to the manifest-defined `3` replicas:

```bash
kubectl apply -f k8s/deployment.yml
kubectl rollout status deployment/devops-info-python -n devops-lab9 --timeout=180s
```

### Rolling Update

Commands:

```bash
kubectl rollout history deployment/devops-info-python -n devops-lab9
kubectl set env deployment/devops-info-python -n devops-lab9 RELEASE_TRACK=canary
kubectl rollout status deployment/devops-info-python -n devops-lab9 --timeout=180s
kubectl rollout history deployment/devops-info-python -n devops-lab9
kubectl get deployment devops-info-python -n devops-lab9 -o jsonpath='{.spec.template.spec.containers[0].env[3].value}'
```

Output:

```text
deployment.apps/devops-info-python 
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
```

```text
deployment.apps/devops-info-python env updated
deployment "devops-info-python" successfully rolled out
```

```text
deployment.apps/devops-info-python 
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
3         <none>
```

```text
canary
```

Zero-downtime check during the rolling update:

```bash
for i in $(seq 1 15); do
  curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:62388/health
  sleep 1
done
```

```text
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
200
200
200
200
200
```

### Rollback

Commands:

```bash
kubectl rollout undo deployment/devops-info-python -n devops-lab9
kubectl rollout status deployment/devops-info-python -n devops-lab9 --timeout=180s
kubectl rollout history deployment/devops-info-python -n devops-lab9
kubectl get deployment devops-info-python -n devops-lab9 -o jsonpath='{.spec.template.spec.containers[0].env[3].value}'
```

Output:

```text
deployment.apps/devops-info-python rolled back
deployment "devops-info-python" successfully rolled out
```

```text
deployment.apps/devops-info-python 
REVISION  CHANGE-CAUSE
1         <none>
3         <none>
4         <none>
```

```text
stable
```

## Bonus Task — Ingress with TLS

TLS generation and secret creation:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /tmp/devops-lab9-tls/tls.key \
  -out /tmp/devops-lab9-tls/tls.crt \
  -subj "/CN=local.example.com/O=local.example.com"

kubectl create secret tls devops-lab9-tls \
  --namespace devops-lab9 \
  --key /tmp/devops-lab9-tls/tls.key \
  --cert /tmp/devops-lab9-tls/tls.crt \
  --dry-run=client -o yaml | kubectl apply -f -
```

Ingress evidence:

```bash
kubectl get ingress -n devops-lab9
kubectl describe ingress devops-lab9-ingress -n devops-lab9
kubectl get secret devops-lab9-tls -n devops-lab9
```

```text
NAME                  CLASS   HOSTS               ADDRESS        PORTS     AGE
devops-lab9-ingress   nginx   local.example.com   192.168.49.2   80, 443   29m
```

```text
TLS:
  devops-lab9-tls terminates local.example.com
Rules:
  local.example.com
    /app1(/|$)(.*)   devops-info-python:80
    /app2(/|$)(.*)   devops-info-go:80
Annotations:
  nginx.ingress.kubernetes.io/rewrite-target: /$2
  nginx.ingress.kubernetes.io/use-regex: true
```

```text
NAME              TYPE                DATA   AGE
devops-lab9-tls   kubernetes.io/tls   2      33m
```

Because Minikube uses the Docker driver on macOS, I validated ingress through the local proxy created by:

```bash
minikube service ingress-nginx-controller -n ingress-nginx --url -p lab9
```

Output:

```text
http://127.0.0.1:53779
http://127.0.0.1:53780
```

HTTP requests show redirect-to-HTTPS behavior:

```bash
curl -fsS -H 'Host: local.example.com' http://127.0.0.1:53779/app1/health
curl -fsS -H 'Host: local.example.com' http://127.0.0.1:53779/app2/health
```

```html
<html>
<head><title>308 Permanent Redirect</title></head>
<body>
<center><h1>308 Permanent Redirect</h1></center>
<hr><center>nginx</center>
</body>
</html>
```

HTTPS requests succeed for both applications:

```bash
curl -kfsS -H 'Host: local.example.com' https://127.0.0.1:53780/app1/health
curl -kfsS -H 'Host: local.example.com' https://127.0.0.1:53780/app2/health
```

```json
{"status":"healthy","timestamp":"2026-03-26T17:25:29.835538+00:00","uptime_seconds":443}
```

```json
{"status":"healthy","timestamp":"2026-03-26T17:25:29Z","uptime_seconds":1535}
```

Ingress is better than exposing both apps with separate NodePorts because it provides:

- one HTTP/HTTPS entry point
- path-based routing
- TLS termination
- cleaner scaling to more services later

For long-term production traffic management, I would consider **Gateway API** instead of investing further in NGINX Ingress.

## Production Considerations

Health checks:
- `startupProbe` protects slow starts
- `readinessProbe` prevents traffic to unready Pods
- `livenessProbe` enables self-healing restarts

Resource rationale:
- requests are small enough for Minikube scheduling
- limits prevent a single Pod from monopolizing the node
- Go app gets lower memory because its runtime footprint is smaller

What I would improve for production:
- use immutable image tags instead of `latest`
- add `HorizontalPodAutoscaler`
- add `PodDisruptionBudget`
- add `NetworkPolicy`
- move TLS management to `cert-manager`
- use Gateway API or cloud load balancers
- add Prometheus scraping and Grafana dashboards from lab 8 into the cluster

Monitoring and observability strategy:
- keep `/health` for probes
- expose `/metrics` from the Python app to Prometheus
- collect container logs with Promtail or an OpenTelemetry pipeline
- add alerting on restart count, readiness failures, and latency

## Challenges & Solutions

Main issue encountered:

```text
Error: container has runAsNonRoot and image has non-numeric user (appuser), cannot verify user is non-root
```

Cause:
- both images use the symbolic user `appuser`
- Kubernetes could not verify that the user was non-root when `runAsNonRoot: true` was set

Fix:
- added explicit numeric security context fields in both deployments:
  - `runAsUser: 1000`
  - `runAsGroup: 1000`
  - `fsGroup: 1000`

How I debugged:
- `kubectl get pods -o wide`
- `kubectl describe pod ...`
- `kubectl describe deployment ...`
- rollout status and replica set inspection

What I learned:
- Kubernetes security settings can be stricter than Docker runtime defaults
- using numeric UIDs avoids ambiguity with non-root enforcement
- on macOS with the Docker driver, `minikube service --url` is the most reliable path for local validation
- ingress validation can be done cleanly with the Minikube proxy even when privileged ports are inconvenient
