# Lab 10: Helm Package Manager

## Chart Overview

### Implementation

Chart structure:

```text
k8s/devops-python/
├── Chart.yaml # contains chart metadata
├── values.yaml # contains default configuration
├── values-dev.yaml # contains development overrides
├── values-prod.yaml # contains production overrides
└── templates/
    ├── _helpers.tpl # defines reusable names and labels
    ├── deployment.yaml # renders the application Deployment
    ├── service.yaml # renders the Service
    ├── pre-install-job.yaml # defines the pre-install hook
    └── post-install-job.yaml # defines the post-install hook
```

The values are organized by concern:

- `image` for repository, tag, and pull policy
- `service` for service type and ports
- `container` for container port
- `env` for environment variables
- `resources` for requests and limits
- `livenessProbe` and `readinessProbe` for health checks
- `hooks` for hook image and weights

### Helm Fundamentals Evidence

#### Helm Version

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab10 λ helm version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"", GoVersion:"go1.26.1-X:nodwarf5", KubeClientVersion:"v1.35"}
```

#### Public Chart Exploration

I explored a public chart from the `prometheus-community` repository.

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab10 λ helm show chart prometheus-community/prometheus
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

Helm's main value proposition is that it turns static Kubernetes YAML into reusable, parameterized, and versioned application packages that can be installed, upgraded, rolled back, and customized for different environments.


## Configuration Guide

### Important Values

Default chart values:

```yaml
nameOverride: ""
fullnameOverride: ""

replicaCount: 3

image:
  repository: s3rap1s/devops-info-service
  tag: "v2"
  pullPolicy: IfNotPresent

service:
  type: NodePort
  port: 80
  targetPort: 5000
  nodePort: null

container:
  port: 5000

env:
  - name: PORT
    value: "5000"
  - name: HOST
    value: "0.0.0.0"

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 200m
    memory: 256Mi

livenessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 15
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 5
  periodSeconds: 5

hooks:
  image: busybox:1.36.1
  preInstall:
    enabled: true
    weight: -5
  postInstall:
    enabled: true
    weight: 5
```

### Environment Differences

`values-dev.yaml`:

- `replicaCount: 1`
- reduced resources
- `service.type: NodePort`
- shorter health-check delays

`values-prod.yaml`:

- `replicaCount: 5`
- higher resource requests and limits
- `service.type: LoadBalancer`
- more conservative health-check delays

### Example Usage

- Development installation: `helm install lab10-release k8s/devops-python -f k8s/devops-python/values-dev.yaml`
- Production upgrade: `helm upgrade lab10-release k8s/devops-python -f k8s/devops-python/values-prod.yaml`


## Hook Implementation

### Implementation

Two Helm hooks were implemented:

- `pre-install` job for configuration validation
- `post-install` job for smoke testing the deployed service

Hook execution order:

- pre-install weight: `-5`
- post-install weight: `5`

Both hooks use the same deletion policy:

```yaml
"helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
```

This ensures that successful hook jobs are removed automatically and old hook jobs do not block future installs.

### Hook Evidence

#### Pre-install Hook

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab10 λ kubectl get jobs
NAME                                      STATUS     COMPLETIONS   DURATION   AGE
lab10-release-devops-python-pre-install   Complete   1/1           13s        13s
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab10 λ kubectl logs job/lab10-release-devops-python-pre-install
Pre-install validation passed for s3rap1s/devops-info-service:v2
```

#### Post-install Hook

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab10 λ kubectl get jobs
NAME                                       STATUS    COMPLETIONS   DURATION   AGE
lab10-release-devops-python-post-install   Running   0/1           11s        11s
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab10 λ kubectl describe job lab10-release-devops-python-post-install
Name:             lab10-release-devops-python-post-install
Namespace:        default
Selector:         batch.kubernetes.io/controller-uid=0b5c2b5d-e3f8-47fd-b934-cfa34a4cd100
Labels:           app.kubernetes.io/instance=lab10-release
                  app.kubernetes.io/managed-by=Helm
                  app.kubernetes.io/name=devops-python
                  app.kubernetes.io/version=2.0.0
                  helm.sh/chart=devops-python-0.1.0
Annotations:      helm.sh/hook: post-install
                  helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
                  helm.sh/hook-weight: 5
Parallelism:      1
Completions:      1
Completion Mode:  NonIndexed
Suspend:          false
Backoff Limit:    0
Start Time:       Wed, 01 Apr 2026 15:22:01 +0300
Pods Statuses:    1 Active (1 Ready) / 0 Succeeded / 0 Failed
Pod Template:
  Labels:  app.kubernetes.io/instance=lab10-release
           app.kubernetes.io/name=devops-python
           batch.kubernetes.io/controller-uid=0b5c2b5d-e3f8-47fd-b934-cfa34a4cd100
           batch.kubernetes.io/job-name=lab10-release-devops-python-post-install
           controller-uid=0b5c2b5d-e3f8-47fd-b934-cfa34a4cd100
           job-name=lab10-release-devops-python-post-install
  Containers:
   post-install-smoke-test:
    Image:      busybox:1.36.1
    Port:       <none>
    Host Port:  <none>
    Command:
      sh
      -c
      wget -qO- http://lab10-release-devops-python:80/health && \
      echo "Post-install smoke test passed" && \
      sleep 10
      
    Environment:   <none>
    Mounts:        <none>
  Volumes:         <none>
  Node-Selectors:  <none>
  Tolerations:     <none>
Events:
  Type    Reason            Age   From            Message
  ----    ------            ----  ----            -------
  Normal  SuccessfulCreate  11s   job-controller  Created pod: lab10-release-devops-python-post-install-q48b2
```

#### Hook Deletion Policy Evidence

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab10 λ kubectl get jobs
No resources found in default namespace.
```


## Installation Evidence

### Installed Releases

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab10 λ helm list
NAME         	NAMESPACE	REVISION	UPDATED                                	STATUS  	CHART              	APP VERSION
lab10-release	default  	2       	2026-04-01 15:22:37.468973619 +0300 MSK	deployed	devops-python-0.1.0	2.0.0
```

### Development Deployment

The chart was first installed with `values-dev.yaml`.

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab10 λ kubectl get all -l app.kubernetes.io/instance=lab10-release
NAME                                               READY   STATUS    RESTARTS   AGE
pod/lab10-release-devops-python-54484c56d7-r2v6f   1/1     Running   0          37s

NAME                                  TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/lab10-release-devops-python   NodePort   10.100.167.57   <none>        80:30599/TCP   37s

NAME                                          READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/lab10-release-devops-python   1/1     1            1           37s

NAME                                                     DESIRED   CURRENT   READY   AGE
replicaset.apps/lab10-release-devops-python-54484c56d7   1         1         1       37s
```

### Production Upgrade

The same release was upgraded with `values-prod.yaml`.

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab10 λ helm get values lab10-release
USER-SUPPLIED VALUES:
image:
  tag: v2
livenessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 30
  periodSeconds: 5
readinessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 10
  periodSeconds: 3
replicaCount: 5
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 200m
    memory: 256Mi
service:
  type: LoadBalancer
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab10 λ kubectl get all -l app.kubernetes.io/instance=lab10-release
NAME                                               READY   STATUS    RESTARTS   AGE
pod/lab10-release-devops-python-79cc745644-9r8qw   1/1     Running   0          2m44s
pod/lab10-release-devops-python-79cc745644-ccjqv   1/1     Running   0          2m32s
pod/lab10-release-devops-python-79cc745644-m9fjs   1/1     Running   0          2m44s
pod/lab10-release-devops-python-79cc745644-v2drp   1/1     Running   0          2m44s
pod/lab10-release-devops-python-79cc745644-vldzr   1/1     Running   0          2m32s

NAME                                  TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/lab10-release-devops-python   LoadBalancer   10.100.167.57   <pending>     80:30599/TCP   3m33s

NAME                                          READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/lab10-release-devops-python   5/5     5            5           3m33s

NAME                                                     DESIRED   CURRENT   READY   AGE
replicaset.apps/lab10-release-devops-python-54484c56d7   0         0         0       3m33s
replicaset.apps/lab10-release-devops-python-79cc745644   5         5         5       2m44s
```


## Operations

**Install** - `helm install lab10-release k8s/devops-python -f k8s/devops-python/values-dev.yaml --wait --wait-for-jobs --debug`

**Upgrade** - `helm upgrade lab10-release k8s/devops-python -f k8s/devops-python/values-prod.yaml --wait --debug`

**Rollback** - `helm rollback lab10-release 1`

**Uninstall** - `helm uninstall lab10-release`


## Testing & Validation

### `helm lint`

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab10 λ helm lint k8s/devops-python
==> Linting k8s/devops-python
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### `helm template`

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab10 λ helm template lab10-release k8s/devops-python -f k8s/devops-python/values-dev.yaml
# Source: devops-python/templates/service.yaml
kind: Service
# Source: devops-python/templates/deployment.yaml
kind: Deployment
# Source: devops-python/templates/post-install-job.yaml
kind: Job
# Source: devops-python/templates/pre-install-job.yaml
kind: Job
```

### `helm install --dry-run=client --debug`

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab10 λ helm install --dry-run=client --debug lab10-dryrun k8s/devops-python -f k8s/devops-python/values-dev.yaml
NAME: lab10-dryrun
STATUS: pending-install
DESCRIPTION: Dry run complete
HOOKS:
# Source: devops-python/templates/post-install-job.yaml
kind: Job
# Source: devops-python/templates/pre-install-job.yaml
kind: Job
MANIFEST:
# Source: devops-python/templates/service.yaml
kind: Service
# Source: devops-python/templates/deployment.yaml
kind: Deployment
```

### Application Accessibility

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab10 λ kubectl get svc lab10-release-devops-python -o wide
NAME                          TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE     SELECTOR
lab10-release-devops-python   LoadBalancer   10.100.167.57   <pending>     80:30599/TCP   3m44s   app.kubernetes.io/instance=lab10-release,app.kubernetes.io/name=devops-python
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab10 λ minikube ip
192.168.49.2
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab10 λ curl -s http://192.168.49.2:30599/health
{"status":"healthy","timestamp":"2026-04-01T12:25:32.023915+00:00","uptime_seconds":172}
```


## Bonus: Library Chart

### Implementation

For the bonus task, I created a shared library chart in `k8s/common-lib` and a second application chart in `k8s/devops-go`.

Library chart structure:

```text
k8s/common-lib/
├── Chart.yaml
└── templates/
    └── _helpers.tpl
```

Shared templates extracted into the library:

- `common.name`
- `common.fullname`
- `common.chart`
- `common.selectorLabels`
- `common.labels`

Both application charts use the library as a dependency:

- `k8s/devops-python`
- `k8s/devops-go`

Both `Chart.yaml` files now include:

```yaml
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: "file://../common-lib"
```

This removed duplicated helper logic and gave both charts the same naming and label conventions.

### Library Usage Evidence

Rendered output for the Python chart:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab10 λ helm template bonus-python k8s/devops-python
# Source: devops-python/templates/service.yaml
kind: Service
  name: bonus-python-devops-python
# Source: devops-python/templates/deployment.yaml
kind: Deployment
  name: bonus-python-devops-python
# Source: devops-python/templates/post-install-job.yaml
kind: Job
# Source: devops-python/templates/pre-install-job.yaml
kind: Job
```

Rendered output for the Go chart:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab10 λ helm template bonus-go k8s/devops-go
# Source: devops-go/templates/service.yaml
kind: Service
  name: bonus-go-devops-go
# Source: devops-go/templates/deployment.yaml
kind: Deployment
  name: bonus-go-devops-go
```

### Deployment Evidence

Both charts were installed successfully:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab10 λ helm list 
bonus-go     	default  	1       	2026-04-01 16:15:58.477947427 +0300 MSK	deployed	devops-go-0.1.0    	1.0.0
bonus-python 	default  	1       	2026-04-01 16:15:58.481181983 +0300 MSK	deployed	devops-python-0.1.0	2.0.0
```

Python chart resources:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab10 λ kubectl get all -l app.kubernetes.io/instance=bonus-python
NAME                                              READY   STATUS    RESTARTS   AGE
pod/bonus-python-devops-python-7595f7674c-4xk62   1/1     Running   0          38s
pod/bonus-python-devops-python-7595f7674c-rdk2c   1/1     Running   0          38s
pod/bonus-python-devops-python-7595f7674c-z24xn   1/1     Running   0          38s

NAME                                 TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/bonus-python-devops-python   NodePort   10.107.222.96   <none>        80:32036/TCP   38s

NAME                                         READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/bonus-python-devops-python   3/3     3            3           38s
```

Go chart resources:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab10 λ kubectl get all -l app.kubernetes.io/instance=bonus-go
NAME                                      READY   STATUS    RESTARTS   AGE
pod/bonus-go-devops-go-6487688d6b-4rjzd   1/1     Running   0          26s
pod/bonus-go-devops-go-6487688d6b-cb96v   1/1     Running   0          26s

NAME                         TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
service/bonus-go-devops-go   ClusterIP   10.99.193.94   <none>        80/TCP    26s

NAME                                 READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/bonus-go-devops-go   2/2     2            2           26s
```

### Benefits

- DRY: one shared source of helper templates instead of duplicated `_helpers.tpl`
- consistency: both charts use the same naming and labeling conventions
- maintainability: helper changes now happen in one library chart instead of multiple application charts
