# Lab 10


## Chart Overview

The chart is named `simple-app-chart` and is located in `k8s/simple-app-chart/`. It packages the Kubernetes manifests (Deployment, Service) as templates, making them configurable via `values.yaml`.

### Chart Structure

```
simple-app-chart/
├── Chart.yaml # Metadata (name, version, appVersion)
├── values.yaml # Default configuration values
├── templates/
│ ├── deployment.yaml # Deployment template
│ ├── service.yaml # Service template
│ ├── _helpers.tpl # Helper functions for labels and names
│ └── hooks/ # Helm hook jobs
│ ├── pre-install-job.yaml
│ └── post-install-job.yaml
└── charts/ # (empty, for dependencies)
```

### Key Template Files
- **deployment.yaml**: Defines the Deployment with replicas, image, resources, and probes, all parameterized.
- **service.yaml**: Defines a NodePort Service, also configurable.
- **_helpers.tpl**: Provides consistent naming and label generation across resources.

### Values Organization Strategy
Values are structured logically:
- `replicaCount` – top‑level scalar.
- `image` – nested object with repository, tag, pullPolicy.
- `service` – nested object with type, port, targetPort, nodePort.
- `resources` – nested object with requests and limits.
- `livenessProbe` / `readinessProbe` – full probe definitions, allowing them to be overridden or disabled.

This structure keeps related settings together and makes it easy to override specific parts.

---

## Configuration Guide

The chart exposes configuration through `values.yaml`. The most important parameters are:

| Value | Description | Default |
|-------|-------------|---------|
| `replicaCount` | Number of pod replicas | `3` |
| `image.repository` | Docker image repository | `thevex/simple-app` |
| `image.tag` | Image tag | `2026.03.09` |
| `service.type` | Service type (`NodePort` or `LoadBalancer`) | `NodePort` |
| `service.port` | Service port | `80` |
| `service.targetPort` | Container port | `8000` |
| `resources` | CPU/memory requests and limits | `requests.cpu=100m`, `requests.memory=128Mi`, `limits.cpu=200m`, `limits.memory=256Mi` |
| `livenessProbe` / `readinessProbe` | Probe configuration | HTTP GET on `/health` and `/ready` (disabled in some environments for debugging) |

---

## Hook Implementation

- Pre‑install hook: Runs before the main resources are created. Used for tasks like database migration, validation, or environment setup.

- Post‑install hook: Runs after all resources are installed. Used for smoke tests, notifications, or initialisation tasks.

### Hook Execution Order and Weights
```yaml
# pre-install-job.yaml
annotations:
  "helm.sh/hook": pre-install
  "helm.sh/hook-weight": "-5"

# post-install-job.yaml
annotations:
  "helm.sh/hook": post-install
  "helm.sh/hook-weight": "5"

```

- Weight -5 for pre‑install ensures it runs before any other pre‑install hooks (default weight is 0).

- Weight 5 for post‑install ensures it runs after other post‑install hooks if any.

## Evidence of the entire process (Installation, Operations, Testing & Validation)

```bash
$ ./get_helm.sh

Downloading https://get.helm.sh/helm-v4.1.3-linux-amd64.tar.gz
Verifying checksum... Done.
Preparing to install helm into /usr/local/bin
helm installed into /usr/local/bin/helm
```


```bash
$ helm version

version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.25.8", KubeClientVersion:"v1.35"}
```


```bash
$ helm lint simple-app-chart
==> Linting simple-app-chart
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

```bash
$ helm template simple-app-chart k8s/simple-app-chart

---
# Source: simple-app/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: simple-app-service
  labels:
    helm.sh/chart: simple-app-0.1.0
    app.kubernetes.io/name: simple-app
    app.kubernetes.io/instance: simple-app-chart
    app.kubernetes.io/version: 2026.03.09
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  selector:
    app: thevex-simple-app
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
      nodePort: 30080
---
# Source: simple-app/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: simple-app-chart-simple-app
  labels:
    app: thevex-simple-app
    helm.sh/chart: simple-app-0.1.0
    app.kubernetes.io/name: simple-app
    app.kubernetes.io/instance: simple-app-chart
    app.kubernetes.io/version: 2026.03.09
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 5
  selector:
    matchLabels:
      app: thevex-simple-app
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: thevex-simple-app
        app.kubernetes.io/name: simple-app
        app.kubernetes.io/instance: simple-app-chart
    spec:
      containers:
      - name: simple-app
        image: "thevex/simple-app:2026.03.09"
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          name: http
        resources:
          limits:
            cpu: 200m
            memory: 256Mi
          requests:
            cpu: 100m
            memory: 128Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 3
```

```bash
$ helm install --dry-run --debug test-release k8s/simple-app-chart

level=WARN msg="--dry-run is deprecated and should be replaced with '--dry-run=client'"
level=DEBUG msg="Original chart version" version=""
level=DEBUG msg="Chart path" path=/home/vexell/DevOps/DevOps-Core-Course/labs/k8s/simple-app-chart
level=DEBUG msg="number of dependencies in the chart" chart=simple-app dependencies=0
NAME: test-release
LAST DEPLOYED: Tue Mar 31 13:56:14 2026
NAMESPACE: default
STATUS: pending-install
REVISION: 1
DESCRIPTION: Dry run complete
TEST SUITE: None
USER-SUPPLIED VALUES:
{}

COMPUTED VALUES:
image:
  pullPolicy: IfNotPresent
  repository: thevex/simple-app
  tag: 2026.03.09
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 3
replicaCount: 5
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
service:
  name: simple-app-service
  nodePort: 30080
  port: 80
  targetPort: 8000
  type: NodePort
updateStrategy:
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
  type: RollingUpdate

HOOKS:
MANIFEST:
---
# Source: simple-app/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: simple-app-service
  labels:
    helm.sh/chart: simple-app-0.1.0
    app.kubernetes.io/name: simple-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: 2026.03.09
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  selector:
    app: thevex-simple-app
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
      nodePort: 30080
---
# Source: simple-app/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-release-simple-app
  labels:
    app: thevex-simple-app
    helm.sh/chart: simple-app-0.1.0
    app.kubernetes.io/name: simple-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: 2026.03.09
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 5
  selector:
    matchLabels:
      app: thevex-simple-app
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: thevex-simple-app
        app.kubernetes.io/name: simple-app
        app.kubernetes.io/instance: test-release
    spec:
      containers:
      - name: simple-app
        image: "thevex/simple-app:2026.03.09"
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          name: http
        resources:
          limits:
            cpu: 200m
            memory: 256Mi
          requests:
            cpu: 100m
            memory: 128Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 3
```

```bash
helm install myrelease k8s/simple-app-chart
NAME: myrelease
LAST DEPLOYED: Tue Mar 31 14:01:46 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
```

```bash

$ helm install simple-app-prod k8s/simple-app-chart -f k8s/simple-app-chart/values-prod.yaml 

NAME: simple-app-prod
LAST DEPLOYED: Tue Mar 31 14:08:03 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None

$ helm upgrade simple-app-prod k8s/simple-app-chart -f k8s/simple-app-chart/values-dev.yaml 

Release "simple-app-prod" has been upgraded. Happy Helming!
NAME: simple-app-prod
LAST DEPLOYED: Tue Mar 31 14:09:36 2026
NAMESPACE: default
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
TEST SUITE: None
```

```bash
$ kubectl get all

NAME                                                 READY   STATUS    RESTARTS   AGE
pod/simple-app-release-simple-app-557b65db5d-5h282   1/1     Running   0          21s
pod/simple-app-release-simple-app-557b65db5d-8xwbz   1/1     Running   0          21s
pod/simple-app-release-simple-app-557b65db5d-kqzxk   1/1     Running   0          21s
pod/simple-app-release-simple-app-557b65db5d-mzfrg   1/1     Running   0          21s
pod/simple-app-release-simple-app-557b65db5d-s4mtb   1/1     Running   0          21s

NAME                         TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/kubernetes           ClusterIP   10.96.0.1        <none>        443/TCP        9d
service/simple-app-service   NodePort    10.111.101.217   <none>        80:30080/TCP   21s

NAME                                            READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/simple-app-release-simple-app   5/5     5            5           21s

NAME                                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/simple-app-release-simple-app-557b65db5d   5         5         5       21s

```

```bash
$ kubectl describe deployment simple-app-release-simple-app

Name:                   simple-app-release-simple-app
Namespace:              default
CreationTimestamp:      Wed, 01 Apr 2026 16:10:06 +0300
Labels:                 app=thevex-simple-app
                        app.kubernetes.io/instance=simple-app-release
                        app.kubernetes.io/managed-by=Helm
                        app.kubernetes.io/name=simple-app
                        app.kubernetes.io/version=latest
                        helm.sh/chart=simple-app-0.1.0
Annotations:            deployment.kubernetes.io/revision: 1
                        meta.helm.sh/release-name: simple-app-release
                        meta.helm.sh/release-namespace: default
Selector:               app=thevex-simple-app
Replicas:               5 desired | 5 updated | 5 total | 5 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Pod Template:
  Labels:  app=thevex-simple-app
           app.kubernetes.io/instance=simple-app-release
           app.kubernetes.io/name=simple-app
  Containers:
   simple-app:
    Image:      thevex/simple-app:latest
    Port:       8000/TCP (http)
    Host Port:  0/TCP (http)
    Limits:
      cpu:     200m
      memory:  256Mi
    Requests:
      cpu:         100m
      memory:      128Mi
    Liveness:      http-get http://:8000/health delay=10s timeout=1s period=5s #success=1 #failure=3
    Readiness:     http-get http://:8000/ready delay=5s timeout=1s period=3s #success=1 #failure=3
    Environment:   <none>
    Mounts:        <none>
  Volumes:         <none>
  Node-Selectors:  <none>
  Tolerations:     <none>
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing    True    NewReplicaSetAvailable
OldReplicaSets:  <none>
NewReplicaSet:   simple-app-release-simple-app-557b65db5d (5/5 replicas created)
Events:
  Type    Reason             Age   From                   Message
  ----    ------             ----  ----                   -------
  Normal  ScalingReplicaSet  80s   deployment-controller  Scaled up replica set simple-app-release-simple-app-557b65db5d from 0 to 5
```
