# lab 09: kubernetes fundamentals

## 1. architecture overview

### components

| component | purpose | port |
|-----------|---------|------|
| deployment | manages replicas and rolling updates | - |
| service (nodeport) | exposes app outside cluster | 30080 |
| pods | run application containers | 5000 |

### data flow

```
┌──────────────────────────────────────────────────────────────┐
│                     kubernetes cluster                       │
│                                                              │
│  external traffic                                            │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────────┐                                         │
│  │   nodeport      │  30080:80                               │
│  │   (external)    │                                         │
│  └────────┬────────┘                                         │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────┐                                         │
│  │   service       │  clusterip:80 → pod:5000                │
│  │   (clusterip)   │                                         │
│  └────────┬────────┘                                         │
│           │                                                  │
│     ┌─────┴─────┬─────────┐                                  │
│     ▼           ▼         ▼                                  │
│  ┌──────┐   ┌──────┐   ┌──────┐                              │
│  │ pod1 │   │ pod2 │   │ pod3 │                              │
│  │:5000 │   │:5000 │   │:5000 │                              │
│  └──────┘   └──────┘   └──────┘                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. project structure

```
k8s/
├── deployment.yml     # deployment manifest with probes and resources
├── service.yml        # nodeport service manifest
└── docs/
    ├── LAB09.md       # this documentation
    └── screenshots/   # deployment evidence screenshots
```

### configuration files

| file | purpose |
|------|---------|
| [deployment.yml](../deployment.yml) | deployment with 3 replicas, health checks, resource limits |
| [service.yml](../service.yml) | nodeport service exposing app on port 30080 |

---

## 3. deployment configuration

### key configuration concepts

**deployment:**

| concept | value | why |
|---------|-------|-----|
| `replicas: 3` | 3 pods | high availability minimum |
| `maxSurge: 1` | 1 extra pod | allows gradual rollout |
| `maxUnavailable: 0` | zero downtime | never go below desired replicas |
| `resources.requests` | 100m cpu, 128mi mem | guaranteed resources for scheduling |
| `resources.limits` | 200m cpu, 256mi mem | prevent resource starvation |

**health checks:**

| probe | endpoint | initial delay | period | purpose |
|-------|----------|---------------|--------|---------|
| liveness | /health | 10s | 5s | restart unhealthy container |
| readiness | /health | 5s | 3s | remove from service if not ready |

**container settings:**

| setting | value | why |
|---------|-------|-----|
| image | onemoreslacker/devops-info-service:v0 | existing docker hub image |
| containerport | 5000 | app default port |
| user | non-root (from dockerfile) | security best practice |

---

## 4. service configuration

### service type: nodeport

| concept | value | why |
|---------|-------|-----|
| type | nodeport | local cluster access without load balancer |
| nodeport | 30080 | fixed port for easy access |
| port | 80 | standard http port |
| targetport | 5000 | container port |
| selector | app=devops-info-service | routes to matching pods |

### access methods

**minikube:**
```bash
minikube service devops-info-service
minikube service devops-info-service --url
```

**port-forward (any cluster):**
```bash
kubectl port-forward service/devops-info-service 8080:80
```

---

## 5. cluster setup

### tools installed

| tool | version | purpose |
|------|---------|---------|
| kubectl | 1.32+ | kubernetes cli |
| minikube | 1.35+ | local kubernetes cluster |

### cluster startup

```bash
$ minikube start
😄  minikube v1.35.0 on Darwin 15.3 (arm64)
✨  Using the docker driver based on existing profile
👍  Starting "minikube" primary control-plane node in "minikube" cluster
🚜  Pulling base image ...
🔄  Restarting existing docker container for "minikube" ...
🐳  Preparing Kubernetes v1.32.0 on Docker 27.4.1 ...
🔎  Verifying Kubernetes components...
🌟  Enabled addons: storage-provisioner, default-storageclass
🏄  Done! kubectl is now configured to use "minikube" cluster
```

### cluster verification

[cluster setup output](screenshots/cluster-setup.png)

### why minikube

chose minikube over kind because:
- full-featured local kubernetes with addon support
- easy ingress enable with `minikube addons enable ingress`
- built-in docker driver for macos arm64
- `minikube service` command simplifies access

---

## 6. deployment

### apply manifests

```bash
$ kubectl apply -f k8s/deployment.yml
deployment.apps/devops-info-service created

$ kubectl apply -f k8s/service.yml
service/devops-info-service created
```

### verify deployment

[kubectl get all](screenshots/kubectl-get-all.png)

[kubectl get pod](screenshots/kubectl-get-pod.png)

[kubectl get svc](screenshots/kubectl-get-svc.png)

### deployment details

[kubectl describe deployment](screenshots/kubectl-describe-deployment.png)

### access application

[curl localhost:8080](screenshots/curl.png)

---

## 7. operations

### scaling

```bash
# scale to 5 replicas
$ kubectl scale deployment/devops-info-service --replicas=5
deployment.apps/devops-info-service scaled
```

[kubectl get pod after scaling](screenshots/kubectl-get-pod-scale.png)

### rolling update

```bash
# update image
$ kubectl set image deployment/devops-info-service \
    devops-info-service=onemoreslacker/devops-info-service:latest
deployment.apps/devops-info-service image updated
```

[kubectl rollout status](screenshots/kubectl-rollout-status.png)

---

## 8. production considerations

### resource management

| resource | request | limit | rationale |
|----------|---------|-------|-----------|
| cpu | 100m | 200m | python/fastapi not cpu-intensive, allows burst |
| memory | 128mi | 256mi | minimal footprint, headroom for gc |

### health checks

| probe | purpose | configuration |
|-------|---------|---------------|
| liveness | restart hung container | 10s delay, 5s period |
| readiness | remove from service | 5s delay, 3s period |

**why these values:**
- `initialdelayseconds: 10` - gives app time to start
- `periodseconds: 5` (liveness) - quick detection of hung processes
- `periodseconds: 3` (readiness) - fast response to traffic changes

### improvements for production

| improvement | description |
|-------------|-------------|
| hpa | horizontal pod autoscaler for automatic scaling |
| pdb | pod disruption budget for maintenance availability |
| network policies | restrict traffic between namespaces |
| secrets management | use external secrets or vault |
| multi-zone | spread pods across availability zones |
| pod anti-affinity | ensure pods on different nodes |

### observability

the app already exposes `/metrics` endpoint for prometheus:
- request count by method, endpoint, status
- request latency histogram
- active requests gauge

---

## 9. challenges

### image platform mismatch

**problem**: image built on arm64 mac may not run on amd64 cluster nodes.

**solution**: built multi-arch image:
```bash
docker buildx build --platform linux/amd64,linux/arm64 \
  -t onemoreslacker/devops-info-service:v0 --push .
```

### readiness probe timing

**problem**: pods marked ready before app fully initialized.

**solution**: set `initialdelayseconds: 5` which is sufficient for this fast-starting app.

### resource constraints

**problem**: pods pending due to insufficient cluster resources.

**solution**: check events with `kubectl describe pod <name>` and adjust resource requests.

---

## 10. key learnings

| concept | understanding |
|---------|---------------|
| declarative config | define desired state, kubernetes reconciles |
| self-healing | failed containers restart, failed nodes trigger rescheduling |
| rolling updates | zero-downtime with proper strategy |
| service discovery | stable endpoints regardless of pod ip changes |
| resource management | requests/limits essential for scheduling |
