# Lab 9 — Kubernetes Fundamentals

## Architecture Overview

This lab deploys the Python DevOps Info Service from Lab 2 as the primary workload and uses the Go service as the bonus second application for Ingress routing.

```text
                         +-----------------------------------+
                         |          local.example.com        |
                         |           80 / 443 on host        |
                         +----------------+------------------+
                                          |
                                          v
                                +-------------------+
                                | Ingress NGINX     |
                                | ingressClass=nginx|
                                +-----+---------+---+
                                      |         |
                              /app1   |         |   /app2
                                      |         |
                                      v         v
                           +--------------+   +--------------+
                           | Service      |   | Service      |
                           | Python       |   | Go           |
                           | NodePort     |   | ClusterIP    |
                           +------+-------+   +------+-------+
                                  |                  |
                                  v                  v
                         +----------------+   +----------------+
                         | 3 Python Pods  |   | 2 Go Pods      |
                         | port 3000      |   | port 8080      |
                         +----------------+   +----------------+
```

Resource strategy:
- Python app: `100m/128Mi` requests and `250m/256Mi` limits.
- Go app: `50m/64Mi` requests and `200m/128Mi` limits.
- Both workloads use HTTP health probes and rolling updates with `maxUnavailable: 0`.

## Local Kubernetes Setup

Chosen local cluster tool: `kind`.

Why `kind`:
- It runs directly on Docker and is well-suited for repeatable local testing.
- It supports `kind load docker-image`, which is convenient for the local Go bonus image.
- The included [kind-config.yml](/Users/pepega/Developer/learning/DevOps-Core-Course/k8s/kind-config.yml) maps host ports `80` and `443`, making the Ingress bonus straightforward to test.

Recommended setup sequence:

```bash
curl -Lo /tmp/kind https://github.com/kubernetes-sigs/kind/releases/download/v0.31.0/kind-darwin-arm64
chmod +x /tmp/kind

docker build -t pepegx/devops-info-service:lab02 app_python
docker build -t devops-info-go:lab02 app_go

/tmp/kind create cluster \
  --name devops-lab9 \
  --config k8s/kind-config.yml \
  --image kindest/node:v1.34.3@sha256:08497ee19eace7b4b5348db5c6a1591d7752b164530a36f855cb0f2bdcbadd48

/tmp/kind load docker-image pepegx/devops-info-service:lab02 --name devops-lab9
/tmp/kind load docker-image devops-info-go:lab02 --name devops-lab9
```

Cluster verification commands:

```bash
kubectl cluster-info
kubectl get nodes -o wide
kubectl get namespaces
```

Validated locally on March 23, 2026:

```text
$ kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:52576
CoreDNS is running at https://127.0.0.1:52576/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

$ kubectl get nodes -o wide
NAME                        STATUS   ROLES           AGE   VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE                         KERNEL-VERSION     CONTAINER-RUNTIME
devops-lab9-control-plane   Ready    control-plane   25m   v1.34.3   172.19.0.2    <none>        Debian GNU/Linux 12 (bookworm)   6.12.72-linuxkit   containerd://2.2.0
devops-lab9-worker          Ready    <none>          25m   v1.34.3   172.19.0.3    <none>        Debian GNU/Linux 12 (bookworm)   6.12.72-linuxkit   containerd://2.2.0
```

## Manifest Files

### [deployment.yml](/Users/pepega/Developer/learning/DevOps-Core-Course/k8s/deployment.yml)

Primary Python Deployment.

Key choices:
- `replicas: 3` satisfies the lab requirement and demonstrates high availability.
- `image: pepegx/devops-info-service:lab02` reuses the Lab 2 image.
- `livenessProbe` and `readinessProbe` both use `/health`, which already exists in the Flask app.
- `runAsUser: 100` and `runAsGroup: 101` make `runAsNonRoot: true` verifiable for the image user `app`.
- `allowPrivilegeEscalation: false`, dropped Linux capabilities, and `RuntimeDefault` seccomp improve runtime security.
- `LOG_LEVEL=INFO` is intentionally explicit so a later change to `DEBUG` can trigger a rolling update for Task 4.

### [service.yml](/Users/pepega/Developer/learning/DevOps-Core-Course/k8s/service.yml)

Primary NodePort Service.

Key choices:
- `type: NodePort` matches the lab requirement for local access.
- `port: 80` presents a conventional HTTP service port.
- `targetPort: http` maps to container port `3000`.
- `nodePort: 30080` keeps the external port deterministic for testing.

### [go-deployment.yml](/Users/pepega/Developer/learning/DevOps-Core-Course/k8s/go-deployment.yml)

Bonus Deployment for the Go application.

Key choices:
- Uses `devops-info-go:lab02`, built from the multi-stage Dockerfile in `app_go`.
- `replicas: 2` keeps the bonus setup realistic without unnecessary resource usage.
- `runAsUser: 65532` and `runAsGroup: 65532` make the distroless `nonroot` user explicit for Kubernetes.
- Same production controls as the primary workload: resource boundaries, probes, and security context.

### [go-service.yml](/Users/pepega/Developer/learning/DevOps-Core-Course/k8s/go-service.yml)

ClusterIP Service for the bonus Go app.

Key choices:
- `ClusterIP` is sufficient because external traffic arrives through Ingress.
- Port `80` keeps the Ingress backend simple and consistent.

### [ingress.yml](/Users/pepega/Developer/learning/DevOps-Core-Course/k8s/ingress.yml)

Bonus Ingress with TLS.

Key choices:
- `ingressClassName: nginx` targets the community ingress controller explicitly.
- Regex paths plus `rewrite-target: /$2` allow both `/app1` and `/app2` and also support subpaths like `/app1/health`.
- TLS is terminated at Ingress with secret `tls-secret`.

### [kind-config.yml](/Users/pepega/Developer/learning/DevOps-Core-Course/k8s/kind-config.yml)

Local cluster bootstrap config.

Key choices:
- Host port mappings expose `80` and `443` for Ingress testing.
- `ingress-ready=true` label matches the standard kind + ingress-nginx local deployment pattern.

### [ingress-nginx-kind-patch.yml](/Users/pepega/Developer/learning/DevOps-Core-Course/k8s/ingress-nginx-kind-patch.yml)

Merge patch for the upstream ingress-nginx controller Deployment in a local kind environment.

Key choice:
- Forces the controller onto the node labeled `ingress-ready=true`, which is the same node that receives host port mappings from [kind-config.yml](/Users/pepega/Developer/learning/DevOps-Core-Course/k8s/kind-config.yml).

## Deployment Evidence

The commands below are the exact evidence set needed for the lab report:

```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl apply -f k8s/go-deployment.yml
kubectl apply -f k8s/go-service.yml

kubectl get all
kubectl get pods,svc -o wide
kubectl describe deployment devops-info-python
kubectl describe deployment devops-info-go
kubectl get endpoints
kubectl get endpointslice
```

Observed output from the validated local run:

```text
$ kubectl get all
NAME                                      READY   STATUS    RESTARTS   AGE
pod/devops-info-go-84f4f6c68b-4g82m       1/1     Running   0          16m
pod/devops-info-go-84f4f6c68b-wbx4c       1/1     Running   0          16m
pod/devops-info-python-7c4f5b8b58-887cb   1/1     Running   0          8m53s
pod/devops-info-python-7c4f5b8b58-fntwg   1/1     Running   0          9m17s
pod/devops-info-python-7c4f5b8b58-m9czk   1/1     Running   0          9m30s

NAME                         TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-info-go       ClusterIP   10.96.219.251   <none>        80/TCP         19m
service/devops-info-python   NodePort    10.96.255.141   <none>        80:30080/TCP   19m
service/kubernetes           ClusterIP   10.96.0.1       <none>        443/TCP        25m

NAME                                 READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-go       2/2     2            2           19m
deployment.apps/devops-info-python   3/3     3            3           19m

$ kubectl get pods,svc -o wide
NAME                                      READY   STATUS    RESTARTS   AGE     IP            NODE                 NOMINATED NODE   READINESS GATES
pod/devops-info-go-84f4f6c68b-4g82m       1/1     Running   0          17m     10.244.1.10   devops-lab9-worker   <none>           <none>
pod/devops-info-go-84f4f6c68b-wbx4c       1/1     Running   0          17m     10.244.1.8    devops-lab9-worker   <none>           <none>
pod/devops-info-python-7c4f5b8b58-887cb   1/1     Running   0          9m39s   10.244.1.24   devops-lab9-worker   <none>           <none>
pod/devops-info-python-7c4f5b8b58-fntwg   1/1     Running   0          10m     10.244.1.22   devops-lab9-worker   <none>           <none>
pod/devops-info-python-7c4f5b8b58-m9czk   1/1     Running   0          10m     10.244.1.21   devops-lab9-worker   <none>           <none>

NAME                         TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE   SELECTOR
service/devops-info-go       ClusterIP   10.96.219.251   <none>        80/TCP         20m   app.kubernetes.io/name=devops-info-go
service/devops-info-python   NodePort    10.96.255.141   <none>        80:30080/TCP   20m   app.kubernetes.io/name=devops-info-python
service/kubernetes           ClusterIP   10.96.0.1       <none>        443/TCP        26m   <none>

$ kubectl get endpoints
NAME                 ENDPOINTS                                          AGE
devops-info-go       10.244.1.10:8080,10.244.1.8:8080                   4m47s
devops-info-python   10.244.1.11:3000,10.244.1.7:3000,10.244.1.9:3000   4m47s
kubernetes           172.19.0.2:6443                                    10m
```

`kubectl get endpoints` still worked on the validated local run, but Kubernetes 1.34 warns that `Endpoints` is deprecated. For current clusters, prefer:

```text
$ kubectl get endpointslice
NAME                      ADDRESSTYPE   PORTS   ENDPOINTS                                  AGE
devops-info-go-7l9x9      IPv4          8080    10.244.1.8,10.244.1.10                     20m
devops-info-python-rk4m6  IPv4          3000    10.244.1.21,10.244.1.22,10.244.1.24       20m
kubernetes                IPv4          6443    172.19.0.2                                 26m
```

Python deployment description excerpt:

```text
$ kubectl describe deployment devops-info-python
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Environment:
  HOST:        0.0.0.0
  PORT:        3000
  LOG_LEVEL:   INFO
```

Primary Service access:

```bash
kubectl port-forward service/devops-info-python 8080:80
curl http://127.0.0.1:8080/
curl http://127.0.0.1:8080/health
```

Observed output:

```json
{"endpoints":[{"description":"Service and system information","method":"GET","path":"/"},{"description":"Health check endpoint","method":"GET","path":"/health"},{"description":"Prometheus metrics endpoint","method":"GET","path":"/metrics"}],"request":{"client_ip":"127.0.0.1","method":"GET","path":"/","user_agent":"curl/8.7.1"},"runtime":{"current_time":"2026-03-23T16:38:04.598291+00:00","timezone":"UTC","uptime_human":"0 hours, 10 minutes","uptime_seconds":600},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"aarch64","cpu_count":4,"hostname":"devops-info-python-7c4f5b8b58-m9czk","platform":"Linux","platform_version":"#1 SMP Mon Feb 16 11:19:07 UTC 2026","python_version":"3.13.12"}}
```

```json
{"status":"healthy","timestamp":"2026-03-23T16:38:04.599563+00:00","uptime_seconds":600}
```

If you are using a NodePort-aware local runtime instead of port-forward, the same service is also exposed on port `30080`.

Ingress controller installation for the bonus task:

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl patch deployment -n ingress-nginx ingress-nginx-controller \
  --type merge \
  --patch-file k8s/ingress-nginx-kind-patch.yml
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=180s
```

Observed final ingress state:

```text
$ kubectl get ingress -o wide
NAME                  CLASS   HOSTS               ADDRESS     PORTS     AGE
devops-info-ingress   nginx   local.example.com   localhost   80, 443   6m34s

$ kubectl get pods -n ingress-nginx -o wide
NAME                                        READY   STATUS    RESTARTS   AGE   IP           NODE                        NOMINATED NODE   READINESS GATES
ingress-nginx-controller-74864fb8d6-wbp6g   1/1     Running   0          46s   10.244.0.5   devops-lab9-control-plane   <none>           <none>
```

TLS secret creation:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout k8s/tls.key \
  -out k8s/tls.crt \
  -subj "/CN=local.example.com/O=local.example.com" \
  -addext "subjectAltName=DNS:local.example.com"

kubectl create secret tls tls-secret \
  --key k8s/tls.key \
  --cert k8s/tls.crt

kubectl apply -f k8s/ingress.yml
kubectl get ingress
```

Bonus routing verification:

```bash
curl -sk --noproxy '*' --resolve local.example.com:443:127.0.0.1 \
  https://local.example.com/app1 | jq '.service.framework'
curl -sk --noproxy '*' --resolve local.example.com:443:127.0.0.1 \
  https://local.example.com/app2 | jq '.service.framework'
curl -sk --noproxy '*' --resolve local.example.com:443:127.0.0.1 \
  https://local.example.com/app1/health
curl -sk --noproxy '*' --resolve local.example.com:443:127.0.0.1 \
  https://local.example.com/app2/health
```

Expected distinction:
- `/app1` returns the Flask response with `"framework": "Flask"`.
- `/app2` returns the Go response with `"framework": "Go (http)"`.

Observed output:

```text
$ curl -s --noproxy '*' --resolve local.example.com:80:127.0.0.1 http://local.example.com/app1
<html>
<head><title>308 Permanent Redirect</title></head>
<body>
<center><h1>308 Permanent Redirect</h1></center>
<hr><center>nginx</center>
</body>
</html>
```

```json
{"endpoints":[{"description":"Service and system information","method":"GET","path":"/"},{"description":"Health check endpoint","method":"GET","path":"/health"},{"description":"Prometheus metrics endpoint","method":"GET","path":"/metrics"}],"request":{"client_ip":"10.244.0.5","method":"GET","path":"/","user_agent":"curl/8.7.1"},"runtime":{"current_time":"2026-03-23T16:36:29.302823+00:00","timezone":"UTC","uptime_human":"0 hours, 8 minutes","uptime_seconds":493},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"aarch64","cpu_count":4,"hostname":"devops-info-python-7c4f5b8b58-fntwg","platform":"Linux","platform_version":"#1 SMP Mon Feb 16 11:19:07 UTC 2026","python_version":"3.13.12"}}
```

```json
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"Go (http)"},"system":{"hostname":"devops-info-go-84f4f6c68b-4g82m","platform":"linux","platform_version":"go1.21.13","architecture":"arm64","cpu_count":4,"go_version":"1.21.13"},"runtime":{"uptime_seconds":955,"uptime_human":"0 hours, 15 minutes","current_time":"2026-03-23T16:36:45.443556716Z","timezone":"UTC"},"request":{"client_ip":"10.244.0.5","user_agent":"curl/8.7.1","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service and system information"},{"path":"/health","method":"GET","description":"Health check endpoint"}]}
```

```json
{"status":"healthy","timestamp":"2026-03-23T16:36:45.443296+00:00","uptime_seconds":485}
{"status":"healthy","timestamp":"2026-03-23T16:36:45.444469466Z","uptime_seconds":955}
```

## Operations Performed

### Initial deployment

```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl rollout status deployment/devops-info-python
```

### Scaling demonstration

Actual local demonstration used an imperative scale so the repository manifest could stay at the baseline `replicas: 3`:

```bash
kubectl scale deployment/devops-info-python --replicas=5
kubectl rollout status deployment/devops-info-python
kubectl get pods -l app.kubernetes.io/name=devops-info-python
```

Observed output:

```text
$ kubectl scale deployment/devops-info-python --replicas=5
deployment.apps/devops-info-python scaled

$ kubectl rollout status deployment/devops-info-python --timeout=180s
deployment "devops-info-python" successfully rolled out
```

After the demonstration, the live deployment was scaled back to `3` replicas so it matched the repository baseline again.

### Rolling update demonstration

This lab does not require a new image build. A Pod template configuration change is enough:

```bash
kubectl set env deployment/devops-info-python LOG_LEVEL=DEBUG
kubectl rollout status deployment/devops-info-python
kubectl rollout history deployment/devops-info-python
```

Observed output:

```text
$ kubectl set env deployment/devops-info-python LOG_LEVEL=DEBUG
deployment.apps/devops-info-python env updated

$ kubectl rollout status deployment/devops-info-python --timeout=180s
deployment "devops-info-python" successfully rolled out
```

Why this works:
- Changing an environment variable changes the Pod template hash.
- Kubernetes creates a new ReplicaSet and performs a rolling update using the strategy from the Deployment manifest.

### Rollback demonstration

```bash
kubectl rollout undo deployment/devops-info-python
kubectl rollout status deployment/devops-info-python
kubectl rollout history deployment/devops-info-python
```

Observed output:

```text
$ kubectl rollout undo deployment/devops-info-python
deployment.apps/devops-info-python rolled back

$ kubectl rollout status deployment/devops-info-python --timeout=180s
deployment "devops-info-python" successfully rolled out

$ kubectl rollout history deployment/devops-info-python
deployment.apps/devops-info-python 
REVISION  CHANGE-CAUSE
1         <none>
3         <none>
4         <none>
```

Zero-downtime verification during rollback:

```text
$ kubectl logs availability-check
1:200
2:200
3:200
4:200
5:200
6:200
7:200
8:200
9:200
10:200
11:200
12:200
13:200
14:200
15:200
16:200
17:200
18:200
19:200
20:200
```

## Production Considerations

Health checks:
- The Flask app already exposes `/health`, so it is reused for both liveness and readiness.
- The Go app also exposes `/health`, keeping the bonus setup consistent.
- In production, I would add a deeper readiness check if external dependencies existed.

Resource limits rationale:
- The services are small HTTP APIs with no heavy CPU work or local state.
- The Python app gets more memory than the Go app because its runtime overhead is naturally higher.
- Requests are set low enough for local clusters but still realistic enough for scheduler decisions.

Security choices:
- Non-root execution is enforced at the container level and already supported by both images.
- Privilege escalation is disabled.
- Linux capabilities are dropped.
- RuntimeDefault seccomp is enabled at the pod level.

Observability strategy:
- The Python app already exposes `/metrics`, so the next production step would be to add a `ServiceMonitor` or Prometheus scrape config in the cluster.
- Structured stdout logs from the Python app fit well with a Loki or ELK pipeline.
- Pod restarts, probe failures, and resource saturation should be monitored as baseline SRE signals.

Improvements for a real production environment:
- Replace local NodePort access with a cloud LoadBalancer or Gateway API.
- Store TLS material in cert-manager instead of generating self-signed certificates manually.
- Move environment configuration into ConfigMaps and Secrets.
- Add PodDisruptionBudgets, NetworkPolicies, and horizontal pod autoscaling.

## Challenges & Solutions

### Local image availability

Challenge:
- The bonus Go image is not published in the repository documentation as a remote registry artifact.

Solution:
- Build the image locally and load it into the kind cluster with `kind load docker-image`.

### Non-numeric users with `runAsNonRoot`

Challenge:
- Both application images used symbolic users (`app` and `nonroot`). Kubernetes refused to start the containers with `runAsNonRoot: true` because it could not prove they were non-root from the image metadata alone.

Observed error:

```text
Error: container has runAsNonRoot and image has non-numeric user (app), cannot verify user is non-root
Error: container has runAsNonRoot and image has non-numeric user (nonroot), cannot verify user is non-root
```

Solution:
- Added explicit numeric `runAsUser` and `runAsGroup` values in both Deployment manifests.

### Ingress path routing

Challenge:
- Both applications only expose `/` and `/health`, while the bonus task requires `/app1` and `/app2`.

Solution:
- Use ingress-nginx regex path matching and rewrite the request path back to `/` or `/health`.

### TLS for local development

Challenge:
- Browsers and CLI tools will not trust a self-signed certificate by default.

Solution:
- Use `curl --resolve ... -k` for functional verification during the lab and keep the key material out of Git via [k8s/.gitignore](/Users/pepega/Developer/learning/DevOps-Core-Course/k8s/.gitignore).

### kind-specific Ingress scheduling

Challenge:
- The upstream ingress-nginx Deployment may land on a worker node, while host ports `80/443` are mapped only to the labeled control-plane node in the local kind setup.

Solution:
- Apply [ingress-nginx-kind-patch.yml](/Users/pepega/Developer/learning/DevOps-Core-Course/k8s/ingress-nginx-kind-patch.yml) with `kubectl patch --patch-file` so the controller schedules onto the `ingress-ready=true` node.

### Port-forward as a misleading zero-downtime check

Challenge:
- A `kubectl port-forward service/...` session broke during rollout and produced connection failures even though the Service itself remained healthy.

Root cause:
- The port-forward stream was pinned to a pod that terminated during the rollout, so the client observed a broken forwarding tunnel rather than a real service outage.

Solution:
- Verified zero downtime from inside the cluster through the stable Service DNS name using a temporary BusyBox probe pod.

### Kubernetes debugging workflow

Primary debugging commands used for this lab:

```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
kubectl get events --sort-by=.lastTimestamp
kubectl describe ingress devops-info-ingress
kubectl describe service devops-info-python
```

Main learnings:
- Kubernetes rewards declarative thinking: edit manifests, apply, observe, and rollback when necessary.
- Labels and selectors are the glue between Deployments, Services, and Ingress.
- Probes and limits are not optional polish; they are part of the minimum safe baseline.
