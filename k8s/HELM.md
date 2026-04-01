# Lab10

# Lab Report: Helm Chart Implementation

## Chart Overview

### Chart Structure Explanation

A Helm chart is organized as a directory containing configuration files and Kubernetes manifest templates. The standard structure provides a clear separation of concerns:

| Component | Location | Purpose |
| --- | --- | --- |
| **Chart metadata** | `Chart.yaml` | Defines chart name, version, description, and maintainer information |
| **Default values** | `values.yaml` | Contains default configuration parameters that can be overridden during installation |
| **Dependencies** | `charts/` | Stores dependent charts that this chart relies on |
| **Manifest templates** | `templates/` | Contains Kubernetes resource definitions (YAML files) with templating logic |
| **Template helpers** | `templates/_helpers.tpl` | Reusable template functions and variable definitions |
| **Installation notes** | `templates/NOTES.txt` | User-friendly instructions displayed after successful installation |

### Key Template Files and Their Purpose

The `templates/` directory contains the core Kubernetes manifests that Helm renders into valid YAML:

- **`deployment.yaml`** — Defines the Kubernetes Deployment resource, specifying pod replicas, container images, resource limits, and lifecycle configurations
- **`service.yaml`** — Exposes the application through a Kubernetes Service, enabling network access to deployed pods
- **`_helpers.tpl`** — Contains template functions (e.g., `include "mychart.labels"`) that reduce duplication across manifest files
- **`NOTES.txt`** — Provides post-installation guidance to users, such as how to access the application or verify deployment status

### Values Organization Strategy

The `values.yaml` file uses a hierarchical structure to organize configuration parameters by functional area. This approach improves readability and allows selective overrides:

## Configuration Guide

### Important Values and Their Purpose

| Property | Value | Purpose |
| - | - | - |
| **`replicaCount`** | `1` | Number of pod replicas to deploy for high availability |
| **`image.repository`** | `python-app` | Container image name or registry path |
| **`image.tag`** | `1.0.0` | Container image version/tag |
| **`image.pullPolicy`** | `IfNotPresent` | When to pull the image (`Always`, `IfNotPresent`, `Never`) |
| **`service.type`** | `NodePort` | Service type (`ClusterIP`, `NodePort`, `LoadBalancer`) |
| **`service.port`** | `80` | Port exposed by the service |
| **`resources.limits.cpu`** | `500m` | Maximum CPU allocation per pod |
| **`resources.limits.memory`** | `512Mi` | Maximum memory allocation per pod |
| **`resources.requests.cpu`** | `250m` | Guaranteed minimum CPU per pod |
| **`resources.requests.memory`** | `256Mi` | Guaranteed minimum memory per pod |

### How to Customize for Different Environments

Override default values using the `-f` flag with environment-specific files or inline with `--set`:

**Using a values file:**

```bash
helm install myapp-dev k8s/mychart -f k8s/mychart/values-dev.yaml
helm install myapp-prod k8s/mychart -f k8s/mychart/values-prod.yaml
```

**Using inline overrides:**

```bash
helm install myapp k8s/mychart --set replicaCount=10
```

## Hook Implementation

### What Hooks You Implemented and Why

Helm hooks are specialized resources that execute at specific points in the Helm release lifecycle. Common hook use cases include:

| Hook Type | Timing | Common Use Cases |
|--|--||
| **`pre-install`** | Before resources are created | Database schema initialization, prerequisite validation |
| **`post-install`** | After resources are created | Application configuration, smoke tests, notifications |
| **`pre-upgrade`** | Before upgrade begins | Database backups, state snapshots |
| **`post-upgrade`** | After upgrade completes | Data migrations, cache clearing |
| **`pre-delete`** | Before resources are deleted | Backup creation, graceful shutdown coordination |
| **`post-delete`** | After resources are deleted | Cleanup tasks, external system notifications |

### Hook Execution Order and Weights

Hooks execute in order determined by their **weight** annotation (lowest to highest). Hooks with the same weight execute in alphabetical order by name:

```yaml
annotations:
  "helm.sh/hook": pre-install
  "helm.sh/hook-weight": "-5"  # Executes first (lowest number)
```

**Example execution sequence:**

1. **Weight -10:** Database initialization (first)
2. **Weight -5:** Schema migration
3. **Weight 0:** Configuration setup
4. **Weight 5:** Health checks (last)

### Deletion Policies Explanation

The `helm.sh/hook-delete-policy` annotation controls when hook resources are cleaned up:

| Policy | Behavior |
| ----- | ------ |
| **`before-hook-creation`** | Delete the previous hook resource before creating a new one (prevents duplicates on re-runs) |
| **`hook-succeeded`** | Delete the hook resource after successful completion |
| **`hook-failed`** | Delete the hook resource after failure |

**Combined example:**

```yaml
annotations:
  "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
```

This ensures the job is cleaned up both before a new run and after successful execution, preventing resource accumulation.

## Installation Evidence

```bash
helm list
NAME            NAMESPACE       REVISION        UPDATED                                 STATUS          CHART           APP VERSION
myapp-dev       default         1               2026-04-02 00:34:56.090265606 +0300 MSK deployed        mychart-0.1.0   1.0.1      
myapp-prod      default         1               2026-04-02 01:38:42.85756205 +0300 MSK  deployed        mychart-0.1.0   1.0.1      
myrelease       default         2               2026-04-02 01:18:39.960191365 +0300 MSK deployed        mychart-0.1.0   1.0.1 
```

```bash
kubectl get all
NAME                                     READY   STATUS    RESTARTS   AGE
pod/myapp-dev-mychart-948cc95cd-z5snm    1/1     Running   0          65m
pod/myapp-prod-mychart-585898dc9-8bdll   1/1     Running   0          107s
pod/myapp-prod-mychart-585898dc9-l2f8z   1/1     Running   0          107s
pod/myapp-prod-mychart-585898dc9-tfkwm   1/1     Running   0          107s
pod/myapp-prod-mychart-585898dc9-vjknm   1/1     Running   0          107s
pod/myapp-prod-mychart-585898dc9-wph62   1/1     Running   0          107s
pod/myrelease-mychart-7f5796499f-6nfnq   1/1     Running   0          52m

NAME                         TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/kubernetes           ClusterIP      10.96.0.1        <none>        443/TCP        111m
service/myapp-dev-mychart    NodePort       10.101.255.236   <none>        80:32750/TCP   65m
service/myapp-prod-mychart   LoadBalancer   10.103.246.152   <pending>     80:31631/TCP   107s
service/myrelease-mychart    NodePort       10.100.134.30    <none>        80:32475/TCP   52m

NAME                                 READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/myapp-dev-mychart    1/1     1            1           65m
deployment.apps/myapp-prod-mychart   5/5     5            5           107s
deployment.apps/myrelease-mychart    1/1     1            1           52m

NAME                                           DESIRED   CURRENT   READY   AGE
replicaset.apps/myapp-dev-mychart-948cc95cd    1         1         1       65m
replicaset.apps/myapp-prod-mychart-585898dc9   5         5         5       107s
replicaset.apps/myrelease-mychart-7f5796499f   1         1         1       52m
```

## Operations

### Installation Commands Used

```bash
helm install myrelease mychart/
NAME: myrelease
LAST DEPLOYED: Wed Apr  1 23:53:31 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
NOTES:
1. Get the application URL by running these commands:
  export NODE_PORT=$(kubectl get --namespace default -o jsonpath="{.spec.ports[0].nodePort}" services myrelease-mychart)
  export NODE_IP=$(kubectl get nodes --namespace default -o jsonpath="{.items[0].status.addresses[0].address}")
  echo http://$NODE_IP:$NODE_PORT
```

### How to Upgrade a Release

**Upgrade to a new chart version:**

```bash
helm upgrade myrelease ./mychart
```

### How to Rollback

**Rollback to the previous release revision:**

```bash
helm rollback myrelease
```

### Helm installation

```bash
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-4
chmod 700 get_helm.sh
./get_helm.sh
Downloading https://get.helm.sh/helm-v4.1.3-linux-amd64.tar.gz
Verifying checksum... Done.
Preparing to install helm into /usr/local/bin
helm installed into /usr/local/bin/helm
bulatgazizov@fedora:~/Projects/DevOps-Core-Course$ helm version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.25.8", KubeClientVersion:"v1.35"}

helm show chart prometheus-community/prometheus
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

```bash
minikube kubectl -- get jobs -w
NAME                            STATUS    COMPLETIONS   DURATION   AGE
myrelease-mychart-pre-install   Running   0/1           9s         9s
myrelease-mychart-pre-install   Running   0/1           19s        19s
myrelease-mychart-pre-install   SuccessCriteriaMet   0/1           20s        20s
myrelease-mychart-pre-install   Complete             1/1           20s        20s
myrelease-mychart-pre-install   Complete             1/1           20s        20s
myrelease-mychart-post-install   Running              0/1                      0s
myrelease-mychart-post-install   Running              0/1           0s         0s
myrelease-mychart-post-install   Running              0/1           4s         4s
myrelease-mychart-post-install   Running              0/1           14s        14s
myrelease-mychart-post-install   SuccessCriteriaMet   0/1           15s        15s
myrelease-mychart-post-install   Complete             1/1           15s        15s
myrelease-mychart-post-install   Complete             1/1           15s        15s
```

### Testing & validation

```bash
 helm install --dry-run --debug test-release mychart/
level=WARN msg="--dry-run is deprecated and should be replaced with '--dry-run=client'"
level=DEBUG msg="Original chart version" version=""
level=DEBUG msg="Chart path" path=/home/bulatgazizov/Projects/DevOps-Core-Course/k8s/mychart
level=DEBUG msg="number of dependencies in the chart" chart=mychart dependencies=0
NAME: test-release
LAST DEPLOYED: Wed Apr  1 23:55:41 2026
NAMESPACE: default
STATUS: pending-install
REVISION: 1
DESCRIPTION: Dry run complete
USER-SUPPLIED VALUES:
{}

COMPUTED VALUES:
affinity: {}
autoscaling:
  enabled: false
  maxReplicas: 100
  minReplicas: 1
  targetCPUUtilizationPercentage: 80
fullnameOverride: ""
httpRoute:
  annotations: {}
  enabled: false
  hostnames:
  - chart-example.local
  parentRefs:
  - name: gateway
    sectionName: http
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /headers
image:
  pullPolicy: IfNotPresent
  repository: bulatgazizov/python-app
  tag: ""
imagePullSecrets: []
ingress:
  annotations: {}
  className: ""
  enabled: false
  hosts:
  - host: chart-example.local
    paths:
    - path: /
      pathType: ImplementationSpecific
  tls: []
livenessProbe:
  httpGet:
    path: /health
    port: 5000
nameOverride: ""
nodeSelector: {}
podAnnotations: {}
podLabels: {}
podSecurityContext: {}
readinessProbe:
  httpGet:
    path: /
    port: 5000
replicaCount: 1
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
securityContext: {}
service:
  port: 80
  targetPort: 5000
  type: NodePort
serviceAccount:
  annotations: {}
  automount: true
  create: true
  name: ""
tolerations: []
volumeMounts: []
volumes: []

HOOKS:

# Source: mychart/templates/tests/test-connection.yaml
apiVersion: v1
kind: Pod
metadata:
  name: "test-release-mychart-test-connection"
  labels:
    helm.sh/chart: mychart-0.1.0
    app.kubernetes.io/name: mychart
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0.1"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": test
spec:
  containers:
    - name: wget
      image: busybox
      command: ['wget']
      args: ['test-release-mychart:80']
  restartPolicy: Never
MANIFEST:

# Source: mychart/templates/serviceaccount.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: test-release-mychart
  labels:
    helm.sh/chart: mychart-0.1.0
    app.kubernetes.io/name: mychart
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0.1"
    app.kubernetes.io/managed-by: Helm
automountServiceAccountToken: true

# Source: mychart/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: test-release-mychart
  labels:
    helm.sh/chart: mychart-0.1.0
    app.kubernetes.io/name: mychart
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0.1"
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  ports:
    - port: 80
      targetPort: 5000
      protocol: TCP
      name: http
  selector:
    app.kubernetes.io/name: mychart
    app.kubernetes.io/instance: test-release

# Source: mychart/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-release-mychart
  labels:
    helm.sh/chart: mychart-0.1.0
    app.kubernetes.io/name: mychart
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0.1"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: mychart
      app.kubernetes.io/instance: test-release
  template:
    metadata:
      labels:
        helm.sh/chart: mychart-0.1.0
        app.kubernetes.io/name: mychart
        app.kubernetes.io/instance: test-release
        app.kubernetes.io/version: "1.0.1"
        app.kubernetes.io/managed-by: Helm
    spec:
      serviceAccountName: test-release-mychart
      containers:
        - name: mychart
          image: "bulatgazizov/python-app:1.0.1"
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 5000
              protocol: TCP
          livenessProbe:
            httpGet:
              path: /health
              port: 5000
          readinessProbe:
            httpGet:
              path: /
              port: 5000
          resources:
            limits:
              cpu: 200m
              memory: 256Mi
            requests:
              cpu: 100m
              memory: 128Mi

NOTES:
1. Get the application URL by running these commands:
  export NODE_PORT=$(kubectl get --namespace default -o jsonpath="{.spec.ports[0].nodePort}" services test-release-mychart)
  export NODE_IP=$(kubectl get nodes --namespace default -o jsonpath="{.items[0].status.addresses[0].address}")
  echo http://$NODE_IP:$NODE_PORT
```

```bash
helm lint k8s/mychart/
==> Linting k8s/mychart/
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```


```bash
helm template mychart k8s/mychart
---
# Source: mychart/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: mychart
  labels:
    helm.sh/chart: mychart-0.1.0
    app.kubernetes.io/name: mychart
    app.kubernetes.io/instance: mychart
    app.kubernetes.io/version: "1.0.1"
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  ports:
    - port: 80
      targetPort: 5000
      protocol: TCP
      name: http
  selector:
    app.kubernetes.io/name: mychart
    app.kubernetes.io/instance: mychart
---
# Source: mychart/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mychart
  labels:
    helm.sh/chart: mychart-0.1.0
    app.kubernetes.io/name: mychart
    app.kubernetes.io/instance: mychart
    app.kubernetes.io/version: "1.0.1"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: mychart
      app.kubernetes.io/instance: mychart
  template:
    metadata:
      labels:
        helm.sh/chart: mychart-0.1.0
        app.kubernetes.io/name: mychart
        app.kubernetes.io/instance: mychart
        app.kubernetes.io/version: "1.0.1"
        app.kubernetes.io/managed-by: Helm
    spec:
      containers:
        - name: mychart
          image: "bulatgazizov/python_app:1.0.1"
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 5000
              protocol: TCP
          livenessProbe:
            httpGet:
              path: /health
              port: 5000
          readinessProbe:
            httpGet:
              path: /
              port: 5000
          resources:
            limits:
              cpu: 200m
              memory: 256Mi
            requests:
              cpu: 100m
              memory: 128Mi
---
# Source: mychart/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "mychart-post-install"
  labels:
    helm.sh/chart: mychart-0.1.0
    app.kubernetes.io/name: mychart
    app.kubernetes.io/instance: mychart
    app.kubernetes.io/version: "1.0.1"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      name: "mychart-post-install"
    spec:
      restartPolicy: Never
      containers:
      - name: post-install-job
        image: busybox
        command: ['sh', '-c', 'echo Post-install validation && sleep 10 && echo Validation passed']
---
# Source: mychart/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "mychart-pre-install"
  labels:
    helm.sh/chart: mychart-0.1.0
    app.kubernetes.io/name: mychart
    app.kubernetes.io/instance: mychart
    app.kubernetes.io/version: "1.0.1"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      name: "mychart-pre-install"
    spec:
      restartPolicy: Never
      containers:
      - name: pre-install-job
        image: busybox
        command: ['sh', '-c', 'echo Pre-install task running && sleep 10 && echo Pre-install completed']
```