# Lab 9 — Kubernetes Fundamentals

In this lab, I deployed my DevOps Info Service to a local Kubernetes cluster, exposed it with a `NodePort` service, demonstrated scaling and rolling updates, and completed the bonus task with Ingress path-based routing and TLS.

## 1. Architecture Overview

### Why I chose `kind`

I chose `kind` instead of `minikube` because I already had Docker running through OrbStack on this machine. That made `kind` the simplest option for creating a lightweight and reproducible local Kubernetes cluster without needing an additional VM.

I used the following tools:

```bash
brew install kind
kubectl version --client
kind version
```

I created and selected the cluster with:

```bash
kind create cluster --config k8s/kind-config.yml --name lab9
kubectl config use-context kind-lab9
```

I verified the cluster with:

```text
Kubernetes control plane is running at https://127.0.0.1:58360
CoreDNS is running at https://127.0.0.1:58360/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.

---
NAME                 STATUS   ROLES           AGE    VERSION
lab9-control-plane   Ready    control-plane   4m5s   v1.35.0

---
NAME                 STATUS   AGE
default              Active   4m6s
devops-lab9          Active   3m26s
ingress-nginx        Active   3m45s
kube-node-lease      Active   4m6s
kube-public          Active   4m6s
kube-system          Active   4m6s
local-path-storage   Active   4m2s
```

Screenshot:

![Cluster setup](/Users/pavorkmert/studying/DevOps/DevOps-Core-Course/k8s/screenshots/8-1.png)

### Deployment architecture

I ended up with the following architecture:

```text
Client
  |
  |-- NodePort 30080 ------------------------------> Service/devops-info-service
  |                                                  -> 3 Flask Pods
  |
  |-- HTTPS 8443 (Ingress host: local.example.com) -> Ingress NGINX
                                                     |-> /app1 -> Service/devops-info-service
                                                     |-> /app2 -> Service/devops-info-service-alt
```

In the final steady state, I had:

- `Deployment/devops-info-service` with 3 replicas
- `Service/devops-info-service` of type `NodePort` on `80:30080`
- `Deployment/devops-info-service-alt` with 2 replicas
- `Service/devops-info-service-alt` of type `ClusterIP`
- `Ingress/devops-lab9-ingress` for `local.example.com` with TLS
- `Namespace/devops-lab9` for isolation

### Resource allocation strategy

For each Flask pod, I configured:

- `requests.cpu: 100m`
- `requests.memory: 128Mi`
- `limits.cpu: 250m`
- `limits.memory: 256Mi`

I used these values because the application is lightweight, but I still wanted explicit resource management, predictable scheduling, and protection against unbounded memory usage.

## 2. Manifest Files

### `k8s/kind-config.yml`

In this file, I configured the local `kind` cluster:

- I created a cluster named `lab9`
- I published host ports:
  - `30080` for the main `NodePort` service
  - `8081` for HTTP Ingress
  - `8443` for HTTPS Ingress
- I labeled the node with `ingress-ready=true` so the `kind` Ingress NGINX deployment could run correctly

I used `8081` and `8443` instead of `80` and `443` because port `80` was already occupied on my host machine.

### `k8s/namespace.yml`

In this file, I created the `devops-lab9` namespace and added labels so all Lab 9 resources would stay grouped in their own isolated namespace.

### `k8s/deployment.yml`

In the main deployment manifest, I:

- deployed the image `devops-info-service:lab9-v1`
- set `replicas: 3`
- used a `RollingUpdate` strategy
- set:
  - `maxSurge: 1`
  - `maxUnavailable: 0`
- exposed container port `5000`
- configured `livenessProbe` and `readinessProbe` against `/health`
- added CPU and memory requests and limits

I chose 3 replicas because that satisfies the lab requirements and allows safe rolling updates. I used `maxUnavailable: 0` because I wanted the service to remain available during updates. I used `/health` for both probes because that endpoint already existed in my application and returned a stable `200 OK` response.

### `k8s/service.yml`

In this file, I exposed the main deployment with a `NodePort` service:

- service port: `80`
- target port: `5000`
- fixed node port: `30080`

This allowed me to access the application directly from my local machine for validation.

### `k8s/bonus-deployment.yml`

For the bonus task, I deployed a second application instance using the same container image, but I changed its metadata through environment variables:

- `SERVICE_NAME=devops-info-service-alt`
- `SERVICE_VERSION=1.0.0-alt`
- `SERVICE_DESCRIPTION=Alternate DevOps course info service behind Ingress`

I used this approach so the second deployment would behave like a distinct application in the responses without requiring a completely separate codebase.

### `k8s/bonus-service.yml`

In this file, I created an internal `ClusterIP` service for the second application. I only needed it behind Ingress, so I did not expose it directly with a `NodePort`.

### `k8s/ingress.yml`

In this file, I configured path-based routing for `local.example.com`:

- `/app1` routes to the main service
- `/app2` routes to the alternate service

I also enabled TLS with the secret `local-example-tls`.

To install the Ingress controller, I ran:

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl -n ingress-nginx rollout status deployment/ingress-nginx-controller --timeout=180s
```

To create the TLS certificate and secret, I ran:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /tmp/lab9-tls/tls.key \
  -out /tmp/lab9-tls/tls.crt \
  -subj "/CN=local.example.com/O=local.example.com"

kubectl -n devops-lab9 create secret tls local-example-tls \
  --key /tmp/lab9-tls/tls.key \
  --cert /tmp/lab9-tls/tls.crt
```

## 3. Deployment Evidence

### Build and load image

I built the application image locally and loaded it into the `kind` cluster:

```bash
cd app_python
docker build -t devops-info-service:lab9-v1 .
kind load docker-image devops-info-service:lab9-v1 --name lab9
```

### Apply manifests

I applied the manifests with:

```bash
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl apply -f k8s/bonus-deployment.yml
kubectl apply -f k8s/bonus-service.yml
kubectl apply -f k8s/ingress.yml
```

### `kubectl get all`

After deployment, I verified all resources with:

```text
NAME                                           READY   STATUS    RESTARTS   AGE
pod/devops-info-service-7d49fb9f8-7qssw        1/1     Running   0          95s
pod/devops-info-service-7d49fb9f8-khkrl        1/1     Running   0          88s
pod/devops-info-service-7d49fb9f8-nrplf        1/1     Running   0          81s
pod/devops-info-service-alt-57dfdccd9f-4rsmf   1/1     Running   0          3m24s
pod/devops-info-service-alt-57dfdccd9f-82fcg   1/1     Running   0          3m24s

NAME                              TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service       NodePort    10.96.68.213   <none>        80:30080/TCP   3m24s
service/devops-info-service-alt   ClusterIP   10.96.87.127   <none>        80/TCP         3m24s

NAME                                      READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service       3/3     3            3           3m25s
deployment.apps/devops-info-service-alt   2/2     2            2           3m24s

NAME                                                 DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-info-service-7d49fb9f8        3         3         3       3m25s
replicaset.apps/devops-info-service-alt-57dfdccd9f   2         2         2       3m24s
replicaset.apps/devops-info-service-fd4fc8d5d        0         0         0       2m23s
```

Screenshot:

![kubectl get all](/Users/pavorkmert/studying/DevOps/DevOps-Core-Course/k8s/screenshots/8-2.png)

### `kubectl get pods,svc,ingress -o wide`

I used a more detailed resource listing to confirm pod IPs, node placement, service selectors, and Ingress status:

```text
NAME                                           READY   STATUS    RESTARTS   AGE     IP            NODE                 NOMINATED NODE   READINESS GATES
pod/devops-info-service-7d49fb9f8-7qssw        1/1     Running   0          95s     10.244.0.20   lab9-control-plane   <none>           <none>
pod/devops-info-service-7d49fb9f8-khkrl        1/1     Running   0          88s     10.244.0.21   lab9-control-plane   <none>           <none>
pod/devops-info-service-7d49fb9f8-nrplf        1/1     Running   0          81s     10.244.0.22   lab9-control-plane   <none>           <none>
pod/devops-info-service-alt-57dfdccd9f-4rsmf   1/1     Running   0          3m24s   10.244.0.11   lab9-control-plane   <none>           <none>
pod/devops-info-service-alt-57dfdccd9f-82fcg   1/1     Running   0          3m24s   10.244.0.12   lab9-control-plane   <none>           <none>

NAME                              TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE     SELECTOR
service/devops-info-service       NodePort    10.96.68.213   <none>        80:30080/TCP   3m24s   app.kubernetes.io/component=web,app.kubernetes.io/name=devops-info-service
service/devops-info-service-alt   ClusterIP   10.96.87.127   <none>        80/TCP         3m24s   app.kubernetes.io/component=web,app.kubernetes.io/name=devops-info-service-alt

NAME                                            CLASS   HOSTS               ADDRESS     PORTS     AGE
ingress.networking.k8s.io/devops-lab9-ingress   nginx   local.example.com   localhost   80, 443   41s
```

Screenshot:

![Pods, services and ingress](/Users/pavorkmert/studying/DevOps/DevOps-Core-Course/k8s/screenshots/8-3.png)

### `kubectl describe deployment devops-info-service`

I inspected the main deployment to confirm the replica count, rolling update strategy, health checks, image, and resource settings:

```text
Name:                   devops-info-service
Namespace:              devops-lab9
Labels:                 app.kubernetes.io/component=web
                        app.kubernetes.io/name=devops-info-service
                        app.kubernetes.io/part-of=devops-core-course
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Containers:
 app:
  Image:      devops-info-service:lab9-v1
  Port:       5000/TCP (http)
  Limits:
    cpu:     250m
    memory:  256Mi
  Requests:
    cpu:      100m
    memory:   128Mi
  Liveness:   http-get http://:http/health delay=10s timeout=2s period=10s #success=1 #failure=3
  Readiness:  http-get http://:http/health delay=5s timeout=2s period=5s #success=1 #failure=3
  Environment:
    HOST:                 0.0.0.0
    PORT:                 5000
    SERVICE_NAME:         devops-info-service
    SERVICE_VERSION:      1.0.0
    SERVICE_DESCRIPTION:  DevOps course info service on Kubernetes
    RELEASE_TRACK:        stable
```

Screenshot:

![Describe deployment](/Users/pavorkmert/studying/DevOps/DevOps-Core-Course/k8s/screenshots/8-4.png)

### Application reachable via NodePort

I confirmed that the main application was reachable from outside the cluster with:

```bash
curl http://127.0.0.1:30080/ | python3 -m json.tool
```

Observed response excerpt:

```json
{
  "service": {
    "description": "DevOps course info service on Kubernetes",
    "framework": "Flask",
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "system": {
    "hostname": "devops-info-service-7d49fb9f8-z9b4t",
    "platform": "Linux"
  }
}
```

Screenshot:

![NodePort curl](/Users/pavorkmert/studying/DevOps/DevOps-Core-Course/k8s/screenshots/8-5.png)

## 4. Operations I Performed

### Initial deployment

After applying the manifests, I confirmed that both deployments rolled out successfully:

```bash
kubectl -n devops-lab9 rollout status deployment/devops-info-service --timeout=180s
kubectl -n devops-lab9 rollout status deployment/devops-info-service-alt --timeout=180s
```

Result:

```text
deployment "devops-info-service" successfully rolled out
deployment "devops-info-service-alt" successfully rolled out
```

### Scaling to 5 replicas

To demonstrate scaling, I increased the main deployment to 5 replicas:

```bash
kubectl -n devops-lab9 scale deployment/devops-info-service --replicas=5
kubectl -n devops-lab9 rollout status deployment/devops-info-service --timeout=180s
kubectl -n devops-lab9 get deployment devops-info-service
kubectl -n devops-lab9 get pods -l app.kubernetes.io/name=devops-info-service
```

Observed output:

```text
deployment.apps/devops-info-service scaled
deployment "devops-info-service" successfully rolled out
NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
devops-info-service   5/5     5            5           48s

---
NAME                                  READY   STATUS    RESTARTS   AGE
devops-info-service-7d49fb9f8-8fgd4   1/1     Running   0          47s
devops-info-service-7d49fb9f8-bhlcd   1/1     Running   0          47s
devops-info-service-7d49fb9f8-hk2rw   1/1     Running   0          8s
devops-info-service-7d49fb9f8-l5stb   1/1     Running   0          8s
devops-info-service-7d49fb9f8-z9b4t   1/1     Running   0          47s
```

### Rolling update

To demonstrate a rolling update, I changed environment variables in the deployment, which created a new revision:

```bash
kubectl -n devops-lab9 set env deployment/devops-info-service \
  SERVICE_VERSION=1.1.0 \
  RELEASE_TRACK=canary

kubectl -n devops-lab9 rollout status deployment/devops-info-service --timeout=180s
kubectl -n devops-lab9 rollout history deployment/devops-info-service
```

Observed output:

```text
deployment.apps/devops-info-service env updated
deployment "devops-info-service" successfully rolled out

---
deployment.apps/devops-info-service
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
```

I then verified that the application reported the new version:

```json
{
  "description": "DevOps course info service on Kubernetes",
  "framework": "Flask",
  "name": "devops-info-service",
  "version": "1.1.0"
}
```

### Zero-downtime verification

While the rolling update was in progress, I repeatedly sent requests to the service and kept receiving `200 OK` responses:

```text
200
200
200
200
200
200
200
```

This matched the behavior I expected from `maxUnavailable: 0`.

### Rollback

To demonstrate rollback, I ran:

```bash
kubectl -n devops-lab9 rollout undo deployment/devops-info-service
kubectl -n devops-lab9 rollout status deployment/devops-info-service --timeout=180s
kubectl -n devops-lab9 rollout history deployment/devops-info-service
```

Observed output:

```text
deployment.apps/devops-info-service rolled back
deployment "devops-info-service" successfully rolled out

---
deployment.apps/devops-info-service
REVISION  CHANGE-CAUSE
2         <none>
3         <none>
```

After the rollback, I verified that the service reported version `1.0.0` again:

```json
{
  "description": "DevOps course info service on Kubernetes",
  "framework": "Flask",
  "name": "devops-info-service",
  "version": "1.0.0"
}
```

### Return to manifest-declared steady state

After the scaling, update, and rollback demonstration, I re-applied the main deployment manifest so that the cluster state matched the committed YAML again:

```bash
kubectl apply -f k8s/deployment.yml
kubectl -n devops-lab9 rollout status deployment/devops-info-service --timeout=180s
kubectl -n devops-lab9 get deployment devops-info-service
```

Observed output:

```text
deployment.apps/devops-info-service configured
deployment "devops-info-service" successfully rolled out
NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
devops-info-service   3/3     3            3           2m26s
```

## 5. Bonus — Ingress with TLS

### Ingress resource

For the bonus task, I first confirmed that the Ingress resource existed:

```bash
kubectl -n devops-lab9 get ingress devops-lab9-ingress -o wide
```

Output:

```text
NAME                  CLASS   HOSTS               ADDRESS   PORTS     AGE
devops-lab9-ingress   nginx   local.example.com             80, 443   0s
```

### HTTPS routing test

Because my `kind` node published HTTPS on host port `8443`, I tested both routes with `curl --resolve`:

```bash
curl -ksS --resolve local.example.com:8443:127.0.0.1 \
  https://local.example.com:8443/app1

curl -ksS --resolve local.example.com:8443:127.0.0.1 \
  https://local.example.com:8443/app2
```

Observed `/app1` response excerpt:

```json
{
  "description": "DevOps course info service on Kubernetes",
  "framework": "Flask",
  "name": "devops-info-service",
  "version": "1.0.0"
}
```

Screenshot:

![Ingress app1](/Users/pavorkmert/studying/DevOps/DevOps-Core-Course/k8s/screenshots/8-6.png)

Observed `/app2` response excerpt:

```json
{
  "description": "Alternate DevOps course info service behind Ingress",
  "framework": "Flask",
  "name": "devops-info-service-alt",
  "version": "1.0.0-alt"
}
```

Screenshot:

![Ingress app2](/Users/pavorkmert/studying/DevOps/DevOps-Core-Course/k8s/screenshots/8-7.png)

### Why I consider Ingress better than multiple NodePorts

I consider Ingress a better solution than exposing every application with its own `NodePort` because:

- I can use a single HTTP/HTTPS entry point
- I can route traffic by path instead of by port
- I can terminate TLS at the Ingress layer
- it is much closer to a real production setup

## 6. Production Considerations

### Health checks

I configured both deployments with:

- `readinessProbe` on `/health`
- `livenessProbe` on `/health`

I did this so Kubernetes would only send traffic to ready pods and would restart pods that became unhealthy.

### Resource limits rationale

I set CPU and memory requests and limits because I wanted:

- predictable scheduling
- protection from excessive resource consumption
- behavior closer to production best practices

For this small Flask application, the chosen values were intentionally conservative.

### Monitoring and observability strategy

If I were to extend this toward production, I would integrate it with the Lab 7 and Lab 8 observability stack:

- scrape `/metrics` from the Python application with Prometheus
- collect logs with Promtail
- visualize traffic, latency, errors, and pod health in Grafana
- alert on downtime, elevated errors, or restart spikes

### What I would improve for real production

- use immutable CI-published image tags
- move configuration to Helm values or Kustomize overlays
- add a `PodDisruptionBudget`
- add topology spread constraints or anti-affinity
- add an HPA
- manage certificates with cert-manager
- eventually move toward Gateway API

## 7. Challenges and Solutions

### Host port `80` was already occupied

When I first tried to create the `kind` cluster, it failed because host port `80` was already in use.

To fix that, I changed the host port mappings in `k8s/kind-config.yml` to use `8081` and `8443` instead.

### I needed the second app to look different in the bonus task

Because I reused the same image for the second deployment, both applications would have looked identical by default.

To solve that, I updated `app_python/app.py` so the service metadata could be read from environment variables while preserving the original defaults. That allowed me to keep the same image and still make the second deployment visibly distinct.

### My local Python environment was missing packages

While validating the project locally, I found that my `venv` did not yet include `python-json-logger` and `prometheus-client`.

I fixed that by installing dependencies from `app_python/requirements.txt` and then re-running the tests.

## 8. Verification

I verified the Python application tests with:

```bash
cd app_python
venv/bin/python -m pytest -q
```

The result was:

```text
20 passed in 1.16s
Required test coverage of 70% reached. Total coverage: 94.12%
```
