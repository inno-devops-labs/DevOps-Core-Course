# Lab 10 - Helm Package Manager

This submission converts the Lab 9 Kubernetes manifests into a reusable Helm chart, adds environment-specific values, and implements lifecycle hooks.

## 1. Helm Fundamentals

### Why Helm
- Helm packages Kubernetes resources into versioned charts.
- The same chart can be installed multiple times as separate releases.
- Values files let us keep one set of templates and switch behavior by environment.
- Hooks make release lifecycle automation part of the chart itself.

In this lab, Helm replaces static manifests with configurable templates for:
- image settings
- replica count
- service type and ports
- resource requests and limits
- health probes
- lifecycle hook Jobs

### Tooling verification
```bash
$ helm version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.26.1", KubeClientVersion:"v1.35"}

$ kubectl version --client
Client Version: v1.33.0
Kustomize Version: v5.6.0

$ minikube version
minikube version: v1.35.0
commit: dd5d320e41b5451cdf3c01891bc4e13d189586ed
```

### Configured repositories
```bash
$ helm repo list
NAME                 URL
prometheus-community https://prometheus-community.github.io/helm-charts
grafana              https://grafana.github.io/helm-charts
bitnami              https://charts.bitnami.com/bitnami
```

### Public chart exploration
```bash
$ helm show chart prometheus-community/prometheus
apiVersion: v2
appVersion: v3.5.0
description: Prometheus is a monitoring system and time series database.
keywords:
- monitoring
- prometheus
kubeVersion: '>=1.19.0-0'
name: prometheus
type: application
version: 27.27.0
```

What this shows:
- public charts use `apiVersion: v2`
- metadata is rich enough for discovery and maintenance
- Helm charts are versioned separately from the packaged application

## 2. Chart Overview

### Main chart structure
```text
k8s/
└── python-app/
    ├── Chart.yaml
    ├── templates/
    │   ├── _helpers.tpl
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   ├── NOTES.txt
    │   └── hooks/
    │       ├── post-install-job.yaml
    │       └── pre-install-job.yaml
    ├── values.yaml
    ├── values-dev.yaml
    └── values-prod.yaml
```

### Key files and purpose
- `k8s/python-app/Chart.yaml`: chart metadata
- `k8s/python-app/templates/_helpers.tpl`: reusable naming and labeling helpers
- `k8s/python-app/templates/deployment.yaml`: deployment template with configurable image, replicas, resources, env vars, and probes
- `k8s/python-app/templates/service.yaml`: templated service type, ports, and optional `nodePort`
- `k8s/python-app/templates/hooks/*.yaml`: pre-install and post-install Jobs
- `k8s/python-app/values.yaml`: safe defaults matching the Lab 9 deployment
- `k8s/python-app/values-dev.yaml`: low-resource NodePort development profile
- `k8s/python-app/values-prod.yaml`: 3-replica LoadBalancer-ready production profile

### Values organization strategy
- Shared defaults live in `values.yaml`.
- Environment differences are layered with `-f values-dev.yaml` or `-f values-prod.yaml`.
- Nested maps keep related settings together: `image`, `service`, `resources`, `readinessProbe`, `livenessProbe`, `hooks`.
- Health probes stayed enabled and configurable the whole time.

## 3. Configuration Guide

### Important values
```yaml
replicaCount: 3

image:
  repository: s1mphonia/devops-core-course-python-app
  tag: latest
  pullPolicy: IfNotPresent

service:
  type: NodePort
  port: 80
  targetPort: http
  containerPort: 8000
  nodePort: 30080

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 250m
    memory: 256Mi
```

### Environment differences
Development:
- 1 replica
- `NodePort`
- lighter CPU and memory requests/limits
- `APP_ENV=development`

Production:
- 3 replicas
- `LoadBalancer`
- stronger CPU and memory requests/limits
- `APP_ENV=production`

### Example commands
```bash
helm install python-lab10 k8s/python-app -f k8s/python-app/values-dev.yaml --wait --timeout 5m
helm upgrade python-lab10 k8s/python-app -f k8s/python-app/values-prod.yaml --wait --timeout 5m
helm template python-dev k8s/python-app -f k8s/python-app/values-dev.yaml
```

## 4. Hook Implementation

### Implemented hooks
- `pre-install`: validates the release before the main resources are created
- `post-install`: runs a simple smoke-test style Job after install

### Order and policies
- pre-install weight: `-5`
- post-install weight: `5`
- delete policy: `before-hook-creation,hook-succeeded`

This means:
- the validation Job runs first
- the smoke-test Job runs after the release is installed
- successful hook Jobs are automatically deleted

### Hook evidence
During install, the pre-install hook existed as a real Job:
```bash
$ kubectl get jobs,pods
NAME                                            STATUS    COMPLETIONS   DURATION   AGE
job.batch/python-lab10-python-app-pre-install   Running   0/1           13s        13s

NAME                                            READY   STATUS    RESTARTS   AGE
pod/python-lab10-python-app-pre-install-p4586   1/1     Running   0          13s
```

```bash
$ kubectl describe job python-lab10-python-app-pre-install
Name:             python-lab10-python-app-pre-install
Namespace:        default
Annotations:      helm.sh/hook: pre-install
                  helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
                  helm.sh/hook-weight: -5
Start Time:       Thu, 02 Apr 2026 21:22:08 +0300
Pods Statuses:    1 Active (1 Ready) / 0 Succeeded / 0 Failed
Containers:
  pre-install-job:
    Image:      busybox:1.36.1
    Command:
      sh
      -c
      echo "Validating python-app release before install" && sleep 10 && echo "Pre-install validation complete"
```

After completion, the deletion policy worked:
```bash
$ kubectl get jobs
No resources found in default namespace.
```

## 5. Installation Evidence

### Cluster note
On April 2, 2026 there was no active Minikube profile on this machine, so I started a fresh local cluster with:

```bash
minikube start --driver=docker
```

### Development install
```bash
$ helm install python-lab10 k8s/python-app -f k8s/python-app/values-dev.yaml --wait --timeout 5m
NAME: python-lab10
LAST DEPLOYED: Thu Apr  2 21:22:07 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
```

```bash
$ helm list
NAME         NAMESPACE REVISION UPDATED                              STATUS   CHART            APP VERSION
python-lab10 default   1        2026-04-02 21:22:07.785493 +0300 MSK deployed python-app-0.1.0 1.0.0
```

```bash
$ kubectl get all
NAME                                          READY   STATUS    RESTARTS   AGE
pod/python-lab10-python-app-d4ff8ddbd-b722j   1/1     Running   0          2m51s

NAME                              TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/kubernetes                ClusterIP   10.96.0.1       <none>        443/TCP        4m11s
service/python-lab10-python-app   NodePort    10.101.121.26   <none>        80:30080/TCP   2m51s

NAME                                      READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/python-lab10-python-app   1/1     1            1           2m51s

NAME                                                DESIRED   CURRENT   READY   AGE
replicaset.apps/python-lab10-python-app-d4ff8ddbd   1         1         1       2m51s
```

Application reachability:
```bash
$ minikube service python-lab10-python-app --url
http://127.0.0.1:59549

$ curl -s http://127.0.0.1:59549/health
{"status":"healthy","timestamp":"2026-04-02T18:25:40.461459+00:00","uptime_seconds":122}
```

### Production upgrade
```bash
$ helm upgrade python-lab10 k8s/python-app -f k8s/python-app/values-prod.yaml --wait --timeout 5m
Release "python-lab10" has been upgraded. Happy Helming!
NAME: python-lab10
LAST DEPLOYED: Thu Apr  2 21:25:55 2026
NAMESPACE: default
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
TEST SUITE: None
```

```bash
$ helm get values python-lab10
USER-SUPPLIED VALUES:
env:
- name: APP_ENV
  value: production
- name: PORT
  value: "8000"
replicaCount: 3
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 200m
    memory: 256Mi
service:
  nodePort: null
  type: LoadBalancer
```

```bash
$ helm list
NAME         NAMESPACE REVISION UPDATED                              STATUS   CHART            APP VERSION
python-lab10 default   2        2026-04-02 21:25:55.122807 +0300 MSK deployed python-app-0.1.0 1.0.0
```

```bash
$ kubectl get all
NAME                                           READY   STATUS    RESTARTS   AGE
pod/python-lab10-python-app-7848f6dfff-777n6   1/1     Running   0          52s
pod/python-lab10-python-app-7848f6dfff-9jm6m   1/1     Running   0          63s
pod/python-lab10-python-app-7848f6dfff-vmxvj   1/1     Running   0          44s

NAME                              TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/kubernetes                ClusterIP      10.96.0.1       <none>        443/TCP        5m48s
service/python-lab10-python-app   LoadBalancer   10.101.121.26   <pending>     80:30080/TCP   4m28s

NAME                                      READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/python-lab10-python-app   3/3     3            3           4m28s

NAME                                                 DESIRED   CURRENT   READY   AGE
replicaset.apps/python-lab10-python-app-7848f6dfff   3         3         3       63s
replicaset.apps/python-lab10-python-app-d4ff8ddbd    0         0         0       4m28s
```

Application still reachable after upgrade:
```bash
$ minikube service python-lab10-python-app --url
http://127.0.0.1:59655

$ curl -s http://127.0.0.1:59655/health
{"status":"healthy","timestamp":"2026-04-02T18:27:20.313467+00:00","uptime_seconds":81}
```

## 6. Operations

### Commands used most often
```bash
helm lint k8s/python-app
helm template python-dev k8s/python-app -f k8s/python-app/values-dev.yaml
helm install --dry-run=client --debug python-dev k8s/python-app -f k8s/python-app/values-dev.yaml

helm install python-lab10 k8s/python-app -f k8s/python-app/values-dev.yaml --wait --timeout 5m
helm upgrade python-lab10 k8s/python-app -f k8s/python-app/values-prod.yaml --wait --timeout 5m
helm get values python-lab10
helm list

kubectl get all
kubectl get jobs
kubectl describe job python-lab10-python-app-pre-install

helm rollback python-lab10 1
helm uninstall python-lab10
```

## 7. Testing and Validation

### Linting
```bash
$ helm lint k8s/python-app
==> Linting k8s/python-app
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### Local rendering
Development render confirms:
- 1 replica
- `NodePort`
- `APP_ENV=development`
- lighter resources
- both hook Jobs render

Production render confirms:
- 3 replicas
- `LoadBalancer`
- `APP_ENV=production`
- larger resources

Example:
```bash
$ helm template python-prod k8s/python-app -f k8s/python-app/values-prod.yaml
# Source: python-app/templates/service.yaml
spec:
  type: LoadBalancer
...
# Source: python-app/templates/deployment.yaml
spec:
  replicas: 3
```

### Dry run
```bash
$ helm install --dry-run=client --debug python-dev k8s/python-app -f k8s/python-app/values-dev.yaml
NAME: python-dev
STATUS: pending-install
DESCRIPTION: Dry run complete
```

### App accessibility verification
- Dev release responded successfully on `/health`
- Prod-valued release also responded successfully on `/health`
- readiness and liveness probes remained active throughout the chart conversion
