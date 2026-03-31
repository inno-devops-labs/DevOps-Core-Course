# Lab 10 — Helm Package Manager

## 1. Chart Overview

**Chart location:** `k8s/devops-info-chart`

**Structure:**
```
 k8s/devops-info-chart/
 ├── Chart.yaml
 ├── values.yaml
 ├── values-dev.yaml
 ├── values-prod.yaml
 └── templates/
     ├── _helpers.tpl
     ├── deployment.yaml
     ├── service.yaml
     ├── NOTES.txt
     └── hooks/
         ├── pre-install-job.yaml
         └── post-install-job.yaml
```

**Key templates:**
- `templates/deployment.yaml`: Deployment with replicas, image, resources, probes, and security context templated from values.
- `templates/service.yaml`: Service with configurable type and ports (NodePort supported).
- `templates/_helpers.tpl`: Reusable naming and label helpers for consistent metadata.
- `templates/hooks/pre-install-job.yaml`: Pre-install hook job for pre-flight checks.
- `templates/hooks/post-install-job.yaml`: Post-install hook job for a quick smoke check.

**Values organization strategy:**
- Global defaults in `values.yaml`.
- Environment overrides in `values-dev.yaml` and `values-prod.yaml`.
- Hooks and deployment strategy are configurable so the chart can be reused in different environments without editing templates.

## 2. Configuration Guide

**Important values (high impact):**
- `replicaCount`: Number of application replicas.
- `image.repository`, `image.tag`, `image.pullPolicy`: Container image settings.
- `service.type`, `service.port`, `service.nodePort`: Service exposure and ports.
- `resources.requests/limits`: CPU and memory sizing.
- `livenessProbe`, `readinessProbe`: Health checks (kept enabled and configurable).
- `hooks.*`: Hook image and commands.

**How to customize for different environments:**
- Development uses `values-dev.yaml` with 1 replica, relaxed resources, and `NodePort`.
- Production uses `values-prod.yaml` with 3 replicas, higher resources, and `LoadBalancer`.
- Install the same chart with different values files to switch environments without changing templates.

```bash
# Dev environment
helm install devops-info-dev k8s/devops-info-chart -f k8s/devops-info-chart/values-dev.yaml

# Prod environment
helm install devops-info-prod k8s/devops-info-chart -f k8s/devops-info-chart/values-prod.yaml

# Upgrade dev to prod values
helm upgrade devops-info-dev k8s/devops-info-chart -f k8s/devops-info-chart/values-prod.yaml
```

**Example installs:**
```bash
# Default values
helm install devops-info k8s/devops-info-chart

# Dev environment
helm install devops-info-dev k8s/devops-info-chart -f k8s/devops-info-chart/values-dev.yaml

# Prod environment
helm install devops-info-prod k8s/devops-info-chart -f k8s/devops-info-chart/values-prod.yaml
```

## 3. Hook Implementation

**Implemented hooks:**
- **Pre-install**: `templates/hooks/pre-install-job.yaml`
  - Purpose: pre-flight validation before resources are created.
  - Annotation: `helm.sh/hook: pre-install`
  - Weight: `-5` (runs early)
  - Deletion: `before-hook-creation,hook-succeeded`

- **Post-install**: `templates/hooks/post-install-job.yaml`
  - Purpose: smoke check right after deployment.
  - Annotation: `helm.sh/hook: post-install`
  - Weight: `5` (runs after pre-install)
  - Deletion: `before-hook-creation,hook-succeeded`

**Execution order:** Pre-install job (weight -5) → main resources → post-install job (weight +5).

**Deletion policy explanation:** The hooks use `before-hook-creation,hook-succeeded`. This means Helm deletes any previous hook resource before creating a new one, and removes the hook Job automatically after a successful run. This keeps the namespace clean while still showing hook execution during install/upgrade.

## 4. Installation Evidence

### Cluster creation and info
```bash
kind create cluster --name devops-lab9
kubectl cluster-info
```
```
Creating cluster "devops-lab9" ...
 ✓ Ensuring node image (kindest/node:v1.35.0) 🖼
 ✓ Preparing nodes 📦
 ✓ Writing configuration 📜
 ✓ Starting control-plane 🕹️
 ✓ Installing CNI 🔌
 ✓ Installing StorageClass 💾
Set kubectl context to "kind-devops-lab9"
You can now use your cluster with:

kubectl cluster-info --context kind-devops-lab9

Not sure what to do next? 😅  Check out https://kind.sigs.k8s.io/docs/user/quick-start/

Kubernetes control plane is running at https://127.0.0.1:34245
CoreDNS is running at https://127.0.0.1:34245/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
```

### Helm installation and version
```bash
helm version
```
```
version.BuildInfo{Version:"v3.14.4", GitCommit:"81c902a123462fd4052bc5e9aa9c513c4c8fc142", GitTreeState:"clean", GoVersion:"go1.21.9"}
```

### Repository exploration
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm show chart prometheus-community/prometheus
```
```
"prometheus-community" already exists with the same configuration, skipping
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
annotations:
  artifacthub.io/license: Apache-2.0
  artifacthub.io/links: |
    - name: Chart Source
      url: https://github.com/prometheus-community/helm-charts
    - name: Upstream Project
      url: https://github.com/prometheus/prometheus
apiVersion: v2
appVersion: v3.10.0
dependencies:
- condition: alertmanager.enabled
  name: alertmanager
  repository: https://prometheus-community.github.io/helm-charts
  version: 1.34.*
- condition: kube-state-metrics.enabled
  name: kube-state-metrics
  repository: https://prometheus-community.github.io/helm-charts
  version: 7.2.*
- condition: prometheus-node-exporter.enabled
  name: prometheus-node-exporter
  repository: https://prometheus-community.github.io/helm-charts
  version: 4.52.*
- condition: prometheus-pushgateway.enabled
  name: prometheus-pushgateway
  repository: https://prometheus-community.github.io/helm-charts
  version: 3.6.*
description: Prometheus is a monitoring system and time series database.
home: https://prometheus.io/
icon: https://raw.githubusercontent.com/prometheus/prometheus.github.io/master/assets/prometheus_logo-cb55bb5c346.png
keywords:
- monitoring
- prometheus
kubeVersion: '>=1.19.0-0'
maintainers:
- email: gianrubio@gmail.com
  name: gianrubio
  url: https://github.com/gianrubio
- email: zanhsieh@gmail.com
  name: zanhsieh
  url: https://github.com/zanhsieh
- email: miroslav.hadzhiev@gmail.com
  name: Xtigyro
  url: https://github.com/Xtigyro
- email: naseem@transit.app
  name: naseemkullah
  url: https://github.com/naseemkullah
- email: rootsandtrees@posteo.de
  name: zeritti
  url: https://github.com/zeritti
name: prometheus
sources:
- https://github.com/prometheus/alertmanager
- https://github.com/prometheus/prometheus
- https://github.com/prometheus/pushgateway
- https://github.com/prometheus/node_exporter
- https://github.com/kubernetes/kube-state-metrics
type: application
version: 28.14.1
```

### Helm lint
```bash
helm lint k8s/devops-info-chart
```
```
==> Linting k8s/devops-info-chart
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### Helm template (rendered manifests)
```bash
helm template devops-info k8s/devops-info-chart
```
```
---
# Source: devops-info/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: devops-info-devops-info
  labels:
    helm.sh/chart: devops-info-0.1.0
    app.kubernetes.io/name: devops-info
    app.kubernetes.io/instance: devops-info
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: devops-info
    app.kubernetes.io/instance: devops-info
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: http
      nodePort: 30080
---
# Source: devops-info/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: devops-info-devops-info
  labels:
    helm.sh/chart: devops-info-0.1.0
    app.kubernetes.io/name: devops-info
    app.kubernetes.io/instance: devops-info
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 3
  revisionHistoryLimit: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app.kubernetes.io/name: devops-info
      app.kubernetes.io/instance: devops-info
  template:
    metadata:
      labels:
        app.kubernetes.io/name: devops-info
        app.kubernetes.io/instance: devops-info
        tier: backend
    spec:
      containers:
        - name: devops-info-service
          image: "alsstarikova/devops-info-service:lab09"
          imagePullPolicy: IfNotPresent
          workingDir: /home/app
          command:
            - python
            - -m
            - uvicorn
          args:
            - app:app
            - --host
            - 0.0.0.0
            - --port
            - "5000"
          ports:
            - name: http
              containerPort: 5000
              protocol: TCP
          env:
            - name: PORT
              value: "5000"
            - name: PYTHONPATH
              value: /home/app
          resources:
            limits:
              cpu: 250m
              memory: 256Mi
            requests:
              cpu: 100m
              memory: 128Mi
          livenessProbe:
            failureThreshold: 3
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 2
          readinessProbe:
            failureThreshold: 3
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 2
          securityContext:
            allowPrivilegeEscalation: false
---
# Source: devops-info/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "devops-info-devops-info-post-install"
  labels:
    helm.sh/chart: devops-info-0.1.0
    app.kubernetes.io/name: devops-info
    app.kubernetes.io/instance: devops-info
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  template:
    metadata:
      name: "devops-info-devops-info-post-install"
      labels:
        helm.sh/chart: devops-info-0.1.0
        app.kubernetes.io/name: devops-info
        app.kubernetes.io/instance: devops-info
        app.kubernetes.io/version: "1.0.0"
        app.kubernetes.io/managed-by: Helm
    spec:
      restartPolicy: Never
      containers:
        - name: post-install-job
          image: busybox:1.36
          command:
            - sh
            - -c
            - echo Post-install smoke test && sleep 5 && echo Post-install completed
---
# Source: devops-info/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "devops-info-devops-info-pre-install"
  labels:
    helm.sh/chart: devops-info-0.1.0
    app.kubernetes.io/name: devops-info
    app.kubernetes.io/instance: devops-info
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  template:
    metadata:
      name: "devops-info-devops-info-pre-install"
      labels:
        helm.sh/chart: devops-info-0.1.0
        app.kubernetes.io/name: devops-info
        app.kubernetes.io/instance: devops-info
        app.kubernetes.io/version: "1.0.0"
        app.kubernetes.io/managed-by: Helm
    spec:
      restartPolicy: Never
      containers:
        - name: pre-install-job
          image: busybox:1.36
          command:
            - sh
            - -c
            - echo Pre-install check && sleep 5 && echo Pre-install completed
```

### Helm dry-run (debug)
```bash
helm install --dry-run --debug devops-info k8s/devops-info-chart
```
```
install.go:218: [debug] Original chart version: ""
install.go:235: [debug] CHART PATH: /mnt/c/Users/1alen/Desktop/My_Py_Projects/DevOps-Core-Course/k8s/devops-info-chart

NAME: devops-info
LAST DEPLOYED: Tue Mar 31 21:20:49 2026
NAMESPACE: default
STATUS: pending-install
REVISION: 1
TEST SUITE: None
USER-SUPPLIED VALUES:
{}

COMPUTED VALUES:
container:
  args:
  - app:app
  - --host
  - 0.0.0.0
  - --port
  - "5000"
  command:
  - python
  - -m
  - uvicorn
  name: devops-info-service
  port: 5000
  workingDir: /home/app
deployment:
  revisionHistoryLimit: 5
  strategy:
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
    type: RollingUpdate
env:
- name: PORT
  value: "5000"
- name: PYTHONPATH
  value: /home/app
fullnameOverride: ""
hooks:
  image: busybox:1.36
  postInstall:
    command:
    - sh
    - -c
    - echo Post-install smoke test && sleep 5 && echo Post-install completed
    weight: 5
  preInstall:
    command:
    - sh
    - -c
    - echo Pre-install check && sleep 5 && echo Pre-install completed
    weight: -5
image:
  pullPolicy: IfNotPresent
  repository: alsstarikova/devops-info-service
  tag: lab09
livenessProbe:
  failureThreshold: 3
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 2
nameOverride: ""
readinessProbe:
  failureThreshold: 3
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 2
replicaCount: 3
resources:
  limits:
    cpu: 250m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
securityContext:
  allowPrivilegeEscalation: false
service:
  nodePort: 30080
  port: 80
  targetPort: http
  type: NodePort

HOOKS:
---
# Source: devops-info/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "devops-info-devops-info-post-install"
  labels:
    helm.sh/chart: devops-info-0.1.0
    app.kubernetes.io/name: devops-info
    app.kubernetes.io/instance: devops-info
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  template:
    metadata:
      name: "devops-info-devops-info-post-install"
      labels:
        helm.sh/chart: devops-info-0.1.0
        app.kubernetes.io/name: devops-info
        app.kubernetes.io/instance: devops-info
        app.kubernetes.io/version: "1.0.0"
        app.kubernetes.io/managed-by: Helm
    spec:
      restartPolicy: Never
      containers:
        - name: post-install-job
          image: busybox:1.36
          command:
            - sh
            - -c
            - echo Post-install smoke test && sleep 5 && echo Post-install completed
---
# Source: devops-info/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "devops-info-devops-info-pre-install"
  labels:
    helm.sh/chart: devops-info-0.1.0
    app.kubernetes.io/name: devops-info
    app.kubernetes.io/instance: devops-info
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  template:
    metadata:
      name: "devops-info-devops-info-pre-install"
      labels:
        helm.sh/chart: devops-info-0.1.0
        app.kubernetes.io/name: devops-info
        app.kubernetes.io/instance: devops-info
        app.kubernetes.io/version: "1.0.0"
        app.kubernetes.io/managed-by: Helm
    spec:
      restartPolicy: Never
      containers:
        - name: pre-install-job
          image: busybox:1.36
          command:
            - sh
            - -c
            - echo Pre-install check && sleep 5 && echo Pre-install completed
MANIFEST:
---
# Source: devops-info/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: devops-info-devops-info
  labels:
    helm.sh/chart: devops-info-0.1.0
    app.kubernetes.io/name: devops-info
    app.kubernetes.io/instance: devops-info
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: devops-info
    app.kubernetes.io/instance: devops-info
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: http
      nodePort: 30080
---
# Source: devops-info/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: devops-info-devops-info
  labels:
    helm.sh/chart: devops-info-0.1.0
    app.kubernetes.io/name: devops-info
    app.kubernetes.io/instance: devops-info
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 3
  revisionHistoryLimit: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app.kubernetes.io/name: devops-info
      app.kubernetes.io/instance: devops-info
  template:
    metadata:
      labels:
        app.kubernetes.io/name: devops-info
        app.kubernetes.io/instance: devops-info
        tier: backend
    spec:
      containers:
        - name: devops-info-service
          image: "alsstarikova/devops-info-service:lab09"
          imagePullPolicy: IfNotPresent
          workingDir: /home/app
          command:
            - python
            - -m
            - uvicorn
          args:
            - app:app
            - --host
            - 0.0.0.0
            - --port
            - "5000"
          ports:
            - name: http
              containerPort: 5000
              protocol: TCP
          env:
            - name: PORT
              value: "5000"
            - name: PYTHONPATH
              value: /home/app
          resources:
            limits:
              cpu: 250m
              memory: 256Mi
            requests:
              cpu: 100m
              memory: 128Mi
          livenessProbe:
            failureThreshold: 3
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 2
          readinessProbe:
            failureThreshold: 3
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 2
          securityContext:
            allowPrivilegeEscalation: false

NOTES:
Thank you for installing devops-info.

Release: devops-info
Namespace: default

Service type: NodePort
Service port: 80

If you used NodePort, access the service via the node IP and the NodePort.
```

### Dev vs Prod installs
```bash
helm install devops-info-dev k8s/devops-info-chart -f k8s/devops-info-chart/values-dev.yaml --wait --timeout 5m
helm install devops-info-prod k8s/devops-info-chart -f k8s/devops-info-chart/values-prod.yaml
helm list
```
```
NAME: devops-info-dev
LAST DEPLOYED: Tue Mar 31 21:21:29 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
Thank you for installing devops-info.

Release: devops-info-dev
Namespace: default

Service type: NodePort
Service port: 80

If you used NodePort, access the service via the node IP and the NodePort.

NAME: devops-info-prod
LAST DEPLOYED: Tue Mar 31 21:28:37 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
Thank you for installing devops-info.

Release: devops-info-prod
Namespace: default

Service type: LoadBalancer
Service port: 80

If you used NodePort, access the service via the node IP and the NodePort.

NAME                    NAMESPACE       REVISION        UPDATED                                       STATUS          CHART                   APP VERSION
devops-info-dev         default         1               2026-03-31 21:21:29.41349486 +0300 MSK        deployed        devops-info-0.1.0       1.0.0
devops-info-prod        default         1               2026-03-31 21:28:37.547532546 +0300 MSK       deployed        devops-info-0.1.0       1.0.0
```

### Kubernetes resources
```bash
kubectl get all
```
```
NAME                                                READY   STATUS             RESTARTS   AGE
pod/devops-info-dev-devops-info-6fdcd5f574-x7z69    1/1     Running            0          7m28s
pod/devops-info-prod-devops-info-8574ddf8d5-5wfnd   0/1     ImagePullBackOff   0          23s
pod/devops-info-prod-devops-info-8574ddf8d5-bzqdz   0/1     ImagePullBackOff   0          23s
pod/devops-info-prod-devops-info-8574ddf8d5-s5frr   0/1     ImagePullBackOff   0          23s

NAME                                   TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-info-dev-devops-info    NodePort       10.96.14.216    <none>        80:30080/TCP   7m28s
service/devops-info-prod-devops-info   LoadBalancer   10.96.137.241   <pending>     80:31598/TCP   23s
service/kubernetes                     ClusterIP      10.96.0.1       <none>        443/TCP        11m

NAME                                           READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-dev-devops-info    1/1     1            1           7m28s
deployment.apps/devops-info-prod-devops-info   0/3     3            0           23s

NAME                                                      DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-info-dev-devops-info-6fdcd5f574    1         1         1       7m28s
replicaset.apps/devops-info-prod-devops-info-8574ddf8d5   3         3         0       23s
```

### Hook execution evidence
```bash
kubectl describe job devops-info-dev-devops-info-pre-install
kubectl describe job devops-info-dev-devops-info-post-install
```
```
Name:             devops-info-dev-devops-info-pre-install
Namespace:        default
Selector:         batch.kubernetes.io/controller-uid=f8cfd8c8-7fa5-4c1b-acbc-fcd9e2af8074
Labels:           app.kubernetes.io/instance=devops-info-dev
                  app.kubernetes.io/managed-by=Helm
                  app.kubernetes.io/name=devops-info
                  app.kubernetes.io/version=1.0.0
                  helm.sh/chart=devops-info-0.1.0
Annotations:      helm.sh/hook: pre-install
                  helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
                  helm.sh/hook-weight: -5
Parallelism:      1
Completions:      1
Completion Mode:  NonIndexed
Suspend:          false
Backoff Limit:    6
Start Time:       Tue, 31 Mar 2026 21:50:20 +0300
Pods Statuses:    1 Active (1 Ready) / 0 Succeeded / 0 Failed
Pod Template:
  Labels:  app.kubernetes.io/instance=devops-info-dev
           app.kubernetes.io/managed-by=Helm
           app.kubernetes.io/name=devops-info
           app.kubernetes.io/version=1.0.0
           batch.kubernetes.io/controller-uid=f8cfd8c8-7fa5-4c1b-acbc-fcd9e2af8074
           batch.kubernetes.io/job-name=devops-info-dev-devops-info-pre-install
           controller-uid=f8cfd8c8-7fa5-4c1b-acbc-fcd9e2af8074
           helm.sh/chart=devops-info-0.1.0
           job-name=devops-info-dev-devops-info-pre-install
  Containers:
   pre-install-job:
    Image:      busybox:1.36
    Port:       <none>
    Host Port:  <none>
    Command:
      sh
      -c
      echo Pre-install check && sleep 5 && echo Pre-install completed
    Environment:   <none>
    Mounts:        <none>
  Volumes:         <none>
  Node-Selectors:  <none>
  Tolerations:     <none>
Events:
  Type    Reason            Age   From            Message
  ----    ------            ----  ----            -------
  Normal  SuccessfulCreate  4s    job-controller  Created pod: devops-info-dev-devops-info-pre-install-qmbvb
Error from server (NotFound): jobs.batch "devops-info-dev-devops-info-post-install" not found
Name:             devops-info-dev-devops-info-pre-install
Namespace:        default
Selector:         batch.kubernetes.io/controller-uid=f8cfd8c8-7fa5-4c1b-acbc-fcd9e2af8074
Labels:           app.kubernetes.io/instance=devops-info-dev
                  app.kubernetes.io/managed-by=Helm
                  app.kubernetes.io/name=devops-info
                  app.kubernetes.io/version=1.0.0
                  helm.sh/chart=devops-info-0.1.0
Annotations:      helm.sh/hook: pre-install
                  helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
                  helm.sh/hook-weight: -5
Parallelism:      1
Completions:      1
Completion Mode:  NonIndexed
Suspend:          false
Backoff Limit:    6
Start Time:       Tue, 31 Mar 2026 21:50:20 +0300
Pods Statuses:    1 Active (0 Ready) / 0 Succeeded / 0 Failed
Pod Template:
  Labels:  app.kubernetes.io/instance=devops-info-dev
           app.kubernetes.io/managed-by=Helm
           app.kubernetes.io/name=devops-info
           app.kubernetes.io/version=1.0.0
           batch.kubernetes.io/controller-uid=f8cfd8c8-7fa5-4c1b-acbc-fcd9e2af8074
           batch.kubernetes.io/job-name=devops-info-dev-devops-info-pre-install
           controller-uid=f8cfd8c8-7fa5-4c1b-acbc-fcd9e2af8074
           helm.sh/chart=devops-info-0.1.0
           job-name=devops-info-dev-devops-info-pre-install
  Containers:
   pre-install-job:
    Image:      busybox:1.36
    Port:       <none>
    Host Port:  <none>
    Command:
      sh
      -c
      echo Pre-install check && sleep 5 && echo Pre-install completed
    Environment:   <none>
    Mounts:        <none>
  Volumes:         <none>
  Node-Selectors:  <none>
  Tolerations:     <none>
Events:
  Type    Reason            Age   From            Message
  ----    ------            ----  ----            -------
  Normal  SuccessfulCreate  7s    job-controller  Created pod: devops-info-dev-devops-info-pre-install-qmbvb
Error from server (NotFound): jobs.batch "devops-info-dev-devops-info-pre-install" not found
Name:             devops-info-dev-devops-info-post-install
Namespace:        default
Selector:         batch.kubernetes.io/controller-uid=aee1e157-901a-466c-8930-1b9a5867dbbc
Labels:           app.kubernetes.io/instance=devops-info-dev
                  app.kubernetes.io/managed-by=Helm
                  app.kubernetes.io/name=devops-info
                  app.kubernetes.io/version=1.0.0
                  helm.sh/chart=devops-info-0.1.0
Annotations:      helm.sh/hook: post-install
                  helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
                  helm.sh/hook-weight: 5
Parallelism:      1
Completions:      1
Completion Mode:  NonIndexed
Suspend:          false
Backoff Limit:    6
Start Time:       Tue, 31 Mar 2026 21:50:28 +0300
Pods Statuses:    1 Active (1 Ready) / 0 Succeeded / 0 Failed
Pod Template:
  Labels:  app.kubernetes.io/instance=devops-info-dev
           app.kubernetes.io/managed-by=Helm
           app.kubernetes.io/name=devops-info
           app.kubernetes.io/version=1.0.0
           batch.kubernetes.io/controller-uid=aee1e157-901a-466c-8930-1b9a5867dbbc
           batch.kubernetes.io/job-name=devops-info-dev-devops-info-post-install
           controller-uid=aee1e157-901a-466c-8930-1b9a5867dbbc
           helm.sh/chart=devops-info-0.1.0
           job-name=devops-info-dev-devops-info-post-install
  Containers:
   post-install-job:
    Image:      busybox:1.36
    Port:       <none>
    Host Port:  <none>
    Command:
      sh
      -c
      echo Post-install smoke test && sleep 5 && echo Post-install completed
    Environment:   <none>
    Mounts:        <none>
  Volumes:         <none>
  Node-Selectors:  <none>
  Tolerations:     <none>
Events:
  Type    Reason            Age   From            Message
  ----    ------            ----  ----            -------
  Normal  SuccessfulCreate  3s    job-controller  Created pod: devops-info-dev-devops-info-post-install-rzfkq
```

### Application accessibility (Port-forward)
```bash
kubectl port-forward svc/devops-info-dev-devops-info 8080:80
curl http://localhost:8080/health
```
```
Forwarding from 127.0.0.1:8080 -> 5000
Forwarding from [::1]:8080 -> 5000
{"status":"healthy","timestamp":"2026-03-31T19:19:28.059250Z","uptime_seconds":1732}
```

## 5. Operations

**Install:**
```bash
helm install devops-info k8s/devops-info-chart
```

**Upgrade (e.g., switch to prod values):**
```bash
helm upgrade devops-info k8s/devops-info-chart -f k8s/devops-info-chart/values-prod.yaml
```

**Rollback:**
```bash
helm rollback devops-info 1
```

**Uninstall:**
```bash
helm uninstall devops-info
```

## 6. Testing & Validation

**Lint:**
```bash
helm lint k8s/devops-info-chart
```
```
==> Linting k8s/devops-info-chart
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

Part of validation command output were pasted in Installation Evidence (part 4 of this report).
