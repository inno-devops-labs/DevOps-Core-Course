# Lab 09 Kubernetes Deployment

## Architecture Overview

This lab deploys two containerized applications into the `devops-lab09` namespace:

- `devops-info-service`: FastAPI application from Lab 2, exposed through a `NodePort` service for direct local-cluster access.
- `devops-info-service-go`: Go bonus application, exposed internally as a `ClusterIP` service for Ingress routing.
- `devops-lab09` Ingress: path-based routing for `https://local.example.com/app1` and `https://local.example.com/app2`.

Traffic flow:

1. External request reaches the cluster through either:
   - `NodePort` service `devops-info-service` on port `30080`
   - Ingress `devops-lab09` on host `local.example.com`
2. Kubernetes Service selects Pods by `app.kubernetes.io/name` and `app.kubernetes.io/component`.
3. Deployment-managed Pods serve application traffic on container port `5000` (Python) or `8080` (Go).

Replica and resource strategy:

- Python app starts with `3` replicas to satisfy the lab requirement and demonstrate HA.
- Go app starts with `2` replicas for the bonus multi-app setup.
- Requests/limits are intentionally small for local clusters:
  - Python: `100m/128Mi` requests, `250m/256Mi` limits
  - Go: `100m/64Mi` requests, `250m/128Mi` limits

## Manifest Files

- [`namespace.yml`](/home/nodo/DevOps-Core-Course/k8s/namespace.yml): creates isolated namespace `devops-lab09`.
- [`deployment.yml`](/home/nodo/DevOps-Core-Course/k8s/deployment.yml): main FastAPI Deployment with:
  - `3` replicas
  - rolling update strategy with `maxSurge: 1` and `maxUnavailable: 0`
  - non-root execution
  - readiness probe on `/ready`
  - liveness probe on `/health`
- [`service.yml`](/home/nodo/DevOps-Core-Course/k8s/service.yml): `NodePort` service exposing the Python app on port `80` and node port `30080`.
- [`bonus-app2-deployment.yml`](/home/nodo/DevOps-Core-Course/k8s/bonus-app2-deployment.yml): bonus Go Deployment with probes on `/health`.
- [`bonus-app2-service.yml`](/home/nodo/DevOps-Core-Course/k8s/bonus-app2-service.yml): internal service for the Go application.
- [`ingress.yml`](/home/nodo/DevOps-Core-Course/k8s/ingress.yml): NGINX Ingress with:
  - `/app1` -> `devops-info-service`
  - `/app2` -> `devops-info-service-go`
  - TLS secret `local-example-com-tls`

Key configuration choices:

- Labels use the `app.kubernetes.io/*` convention for cleaner selectors and future observability tooling.
- Rolling updates keep service availability during image/config changes.
- Probes map directly to real application endpoints already implemented in:
  - [`app.py`](/home/nodo/DevOps-Core-Course/app_python/app.py)
  - [`main.go`](/home/nodo/DevOps-Core-Course/app_go/main.go)

## Local Kubernetes Setup

Chosen local cluster tool: `kind`

Why `kind`:

- Runs Kubernetes nodes as Docker containers, which is lightweight for lab work.
- Easy to recreate for repeatable testing.
- Common choice for CI-style local validation.

Tool installation used during verification:

```bash
curl -fsSLo ./kubectl https://dl.k8s.io/release/v1.33.0/bin/linux/amd64/kubectl
curl -fsSLo ./kind https://kind.sigs.k8s.io/dl/v0.27.0/kind-linux-amd64
chmod +x ./kubectl ./kind

./kind create cluster --name devops-lab09 --image kindest/node:v1.33.1
./kubectl cluster-info
./kubectl get nodes -o wide
```

The host environment had proxy settings that interfered with host-side `kubectl`, so live verification was performed from inside the running kind control-plane container using `/etc/kubernetes/admin.conf`.

## Deployment Steps

Build images first so the local cluster can use the app versions defined in the manifests:

```bash
docker build -t devops-info-service:lab09 ./app_python
docker build -t devops-info-service-go:lab09 ./app_go
kind load docker-image devops-info-service:lab09 --name devops-lab09
kind load docker-image devops-info-service-go:lab09 --name devops-lab09
```

Apply manifests:

```bash
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl apply -f k8s/bonus-app2-deployment.yml
kubectl apply -f k8s/bonus-app2-service.yml
kubectl apply -f k8s/ingress.yml
```

Basic verification:

```bash
kubectl get all -n devops-lab09
kubectl get pods,svc,ingress -n devops-lab09 -o wide
kubectl describe deployment devops-info-service -n devops-lab09
kubectl describe deployment devops-info-service-go -n devops-lab09
kubectl get endpoints -n devops-lab09
```

## Service Access

Direct service access for Task 3:

```bash
kubectl port-forward -n devops-lab09 service/devops-info-service 8080:80
curl http://127.0.0.1:8080/
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/ready
```

Alternative `kind` access:

```bash
kubectl port-forward -n devops-lab09 service/devops-info-service 8080:80
curl http://127.0.0.1:8080/
```

Expected endpoints:

- `/` returns service, system, runtime, and request metadata.
- `/health` returns liveness status.
- `/ready` returns readiness status.

## Scaling, Updates, and Rollback

Scale the main deployment to `5` replicas:

```bash
kubectl scale deployment/devops-info-service -n devops-lab09 --replicas=5
kubectl rollout status deployment/devops-info-service -n devops-lab09
kubectl get pods -n devops-lab09 -l app.kubernetes.io/name=devops-info-service
```

Declarative scaling alternative:

```bash
# edit spec.replicas in k8s/deployment.yml to 5
kubectl apply -f k8s/deployment.yml
```

Rolling update demonstration:

```bash
kubectl set image deployment/devops-info-service \
  -n devops-lab09 \
  devops-info-service=devops-info-service:lab09-v2

kubectl rollout status deployment/devops-info-service -n devops-lab09
kubectl rollout history deployment/devops-info-service -n devops-lab09
```

Rollback:

```bash
kubectl rollout undo deployment/devops-info-service -n devops-lab09
kubectl rollout history deployment/devops-info-service -n devops-lab09
```

Zero-downtime rationale:

- `maxUnavailable: 0` keeps all current replicas available until replacement Pods become ready.
- Readiness probes prevent traffic from reaching Pods before the application is ready to serve.

## Bonus: Ingress with TLS

Enable an Ingress controller.

For `kind`, install ingress-nginx:

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s
```

Generate a self-signed certificate:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key \
  -out tls.crt \
  -subj "/CN=local.example.com/O=local.example.com"
```

Create the TLS secret referenced by [`ingress.yml`](/home/nodo/DevOps-Core-Course/k8s/ingress.yml):

```bash
kubectl create secret tls local-example-com-tls \
  -n devops-lab09 \
  --key tls.key \
  --cert tls.crt
```

Add the host entry for local testing:

```bash
echo "127.0.0.1 local.example.com" | sudo tee -a /etc/hosts
```

Verify routing:

```bash
curl -k https://local.example.com/app1
curl -k https://local.example.com/app1/health
curl -k https://local.example.com/app2
curl -k https://local.example.com/app2/health
```

Ingress benefits over direct NodePort exposure:

- Single HTTP entrypoint for multiple apps
- Path-based routing
- Central TLS termination
- Cleaner local and production migration path

## Deployment Evidence

Runtime evidence captured from the running `devops-lab09` kind cluster:

```text
$ docker exec devops-lab09-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf cluster-info
Kubernetes control plane is running at https://devops-lab09-control-plane:6443
CoreDNS is running at https://devops-lab09-control-plane:6443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

$ docker exec devops-lab09-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf get nodes -o wide
NAME                         STATUS   ROLES           AGE    VERSION   INTERNAL-IP    EXTERNAL-IP   OS-IMAGE                         KERNEL-VERSION                     CONTAINER-RUNTIME
devops-lab09-control-plane   Ready    control-plane   2d4h   v1.33.1   192.168.16.2   <none>        Debian GNU/Linux 12 (bookworm)   6.6.87.2-microsoft-standard-WSL2   containerd://2.1.1

$ docker exec devops-lab09-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf get all -n devops-lab09
NAME                                          READY   STATUS    RESTARTS   AGE
pod/devops-info-service-6fd5fcc4dc-7k4mx      1/1     Running   0          14m
pod/devops-info-service-6fd5fcc4dc-8jdhh      1/1     Running   0          14m
pod/devops-info-service-6fd5fcc4dc-9jk77      1/1     Running   0          15m
pod/devops-info-service-6fd5fcc4dc-k6zvp      1/1     Running   0          15m
pod/devops-info-service-6fd5fcc4dc-x49s5      1/1     Running   0          15m
pod/devops-info-service-go-56dcbd7c77-f2d6h   1/1     Running   0          15m
pod/devops-info-service-go-56dcbd7c77-ncrq7   1/1     Running   0          15m

NAME                             TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service      NodePort    10.96.73.63     <none>        80:30080/TCP   26m
service/devops-info-service-go   ClusterIP   10.96.191.110   <none>        80/TCP         24m

NAME                                     READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service      5/5     5            5           26m
deployment.apps/devops-info-service-go   2/2     2            2           24m

$ docker exec devops-lab09-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf get pods,svc,ingress -n devops-lab09 -o wide
NAME                                          READY   STATUS    RESTARTS   AGE   IP            NODE                         NOMINATED NODE   READINESS GATES
pod/devops-info-service-6fd5fcc4dc-7k4mx      1/1     Running   0          14m   10.244.0.34   devops-lab09-control-plane   <none>           <none>
pod/devops-info-service-6fd5fcc4dc-8jdhh      1/1     Running   0          14m   10.244.0.33   devops-lab09-control-plane   <none>           <none>
pod/devops-info-service-6fd5fcc4dc-9jk77      1/1     Running   0          15m   10.244.0.28   devops-lab09-control-plane   <none>           <none>
pod/devops-info-service-6fd5fcc4dc-k6zvp      1/1     Running   0          15m   10.244.0.32   devops-lab09-control-plane   <none>           <none>
pod/devops-info-service-6fd5fcc4dc-x49s5      1/1     Running   0          15m   10.244.0.31   devops-lab09-control-plane   <none>           <none>
pod/devops-info-service-go-56dcbd7c77-f2d6h   1/1     Running   0          15m   10.244.0.30   devops-lab09-control-plane   <none>           <none>
pod/devops-info-service-go-56dcbd7c77-ncrq7   1/1     Running   0          15m   10.244.0.29   devops-lab09-control-plane   <none>           <none>

NAME                             TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE   SELECTOR
service/devops-info-service      NodePort    10.96.73.63     <none>        80:30080/TCP   26m   app.kubernetes.io/component=api,app.kubernetes.io/name=devops-info-service
service/devops-info-service-go   ClusterIP   10.96.191.110   <none>        80/TCP         24m   app.kubernetes.io/component=api,app.kubernetes.io/name=devops-info-service-go

NAME                                     CLASS   HOSTS               ADDRESS     PORTS     AGE
ingress.networking.k8s.io/devops-lab09   nginx   local.example.com   localhost   80, 443   21m

$ docker exec devops-lab09-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf rollout history deployment/devops-info-service -n devops-lab09
deployment.apps/devops-info-service
REVISION  CHANGE-CAUSE
2         <none>
3         <none>
4         <none>

$ docker exec devops-lab09-control-plane curl -sS http://10.96.73.63/health
{"status":"healthy","timestamp":"2026-03-26T13:11:07.720723+00:00","uptime_seconds":951}

$ docker exec devops-lab09-control-plane curl -sS http://10.96.191.110/health
{"status":"healthy","timestamp":"2026-03-26T13:11:07Z","uptime_seconds":931}

$ docker exec devops-lab09-control-plane curl -k -sS -H 'Host: local.example.com' https://10.96.2.82/app1/health
{"status":"healthy","timestamp":"2026-03-26T13:11:25.192436+00:00","uptime_seconds":978}

$ docker exec devops-lab09-control-plane curl -k -sS -H 'Host: local.example.com' https://10.96.2.82/app2/health
{"status":"healthy","timestamp":"2026-03-26T13:11:25Z","uptime_seconds":955}
```

Repository-side validation also completed:

```text
$ /tmp/lab09-bin/kubectl version --client --output=yaml
clientVersion.gitVersion: v1.33.0

$ KUBECONFIG=/tmp/lab09-kubeconfig /tmp/lab09-bin/kind version
kind v0.27.0

$ python3 - <<'PY'
import pathlib, yaml
for path in sorted(pathlib.Path('k8s').glob('*.yml')):
    with path.open() as f:
        list(yaml.safe_load_all(f))
    print(f"validated {path}")
PY
validated k8s/bonus-app2-deployment.yml
validated k8s/bonus-app2-service.yml
validated k8s/deployment.yml
validated k8s/ingress.yml
validated k8s/namespace.yml
validated k8s/service.yml

$ GOCACHE=/tmp/go-build-cache go test ./...
ok  	github.com/devops-course/devops-info-service-go	0.004s
```

## Production Considerations

Health checks:

- Python app uses separate readiness and liveness endpoints so Kubernetes can distinguish "ready for traffic" from "needs restart".
- Go app uses `/health` for both probes because the service is simple and stateless.

Resource limits:

- Requests guarantee scheduler placement even on small local clusters.
- Limits prevent a single Pod from consuming disproportionate local resources.

Recommended production improvements:

- Pin immutable image digests instead of mutable tags.
- Use `readOnlyRootFilesystem: true` after verifying app write paths.
- Add PodDisruptionBudgets and anti-affinity rules.
- Add HPA based on CPU or request latency.
- Manage TLS and DNS with cert-manager and external-dns.
- Move runtime configuration into ConfigMaps and Secrets.

Monitoring and observability:

- Collect Pod logs with Promtail/Loki from previous labs.
- Add Prometheus scraping for HTTP metrics.
- Track rollout events, probe failures, restart counts, and latency percentiles in Grafana.

## Challenges and Solutions

Issues encountered in this environment:

- `kubectl`, `kind`, and `minikube` were not preinstalled.
- `pytest` is not installed for the Python app test suite.
- Host proxy variables interfered with host-side `kubectl` access to the kind API server.
- Host ports `443` and direct NodePort access were not suitable for verification from this shell, so Service and Ingress checks were executed from inside the kind control-plane container.

Debugging and mitigation:

- Downloaded portable `kubectl` and `kind` binaries to `/tmp`.
- Validated all Kubernetes YAML manifests with `python3` and `PyYAML`.
- Ran the Go test suite with `GOCACHE=/tmp/go-build-cache` to avoid the read-only home cache.
- Used `docker exec ... kubectl --kubeconfig=/etc/kubernetes/admin.conf` inside the kind node to collect authoritative cluster output.

What this lab reinforced:

- Kubernetes manifests are only the starting point; runtime verification depends on cluster and image plumbing.
- Readiness probes and rolling update settings are the main controls that make zero-downtime updates realistic.
- Standard labels and clear namespace isolation make troubleshooting and future automation much easier.
