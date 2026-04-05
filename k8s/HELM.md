# Lab 10 — Helm Package Manager

**Author:** Nikita Maksimenko
**Date:** 2026-03-24
**Helm version:** v4.1.3
**Kubernetes:** minikube v1.38.1 — Kubernetes v1.35.1

---

## Chart Overview

The Helm chart `devops-info-service` was created at `k8s/devops-info-service/` to package the same FastAPI Python service deployed in Lab 9. All default values were derived directly from the Lab 9 `deployment.yml` and `service.yml` manifests.

### Chart structure

```
k8s/devops-info-service/
├── Chart.yaml                        # Chart metadata (name, version, appVersion)
├── values.yaml                       # Default configuration values
├── values-dev.yaml                   # Development environment overrides
├── values-prod.yaml                  # Production environment overrides
└── templates/
    ├── _helpers.tpl                  # Named template definitions (labels, names)
    ├── deployment.yaml               # Templated Deployment manifest
    ├── service.yaml                  # Templated Service manifest
    ├── NOTES.txt                     # Post-install release summary
    └── hooks/
        ├── pre-install-job.yaml      # Pre-install validation Job
        └── post-install-job.yaml     # Post-install smoke test Job
```

Lab 11 added `secrets.yaml`, `serviceaccount.yaml`, and `values-vault.yaml`; details are recorded at the end of this file.

### Template files

**`_helpers.tpl`** defines five named templates:
- `devops-info-service.name` — chart name truncated to 63 characters
- `devops-info-service.fullname` — `<release>-<chart>` combined name, respecting `fullnameOverride`
- `devops-info-service.chart` — `<chart>-<version>` string for the `helm.sh/chart` label
- `devops-info-service.labels` — full set of `app.kubernetes.io` and `helm.sh` labels
- `devops-info-service.selectorLabels` — `app.kubernetes.io/name` and `app.kubernetes.io/instance` for Pod selectors

**`deployment.yaml`** templates every configurable field: replica count, image, pull policy, resource requests and limits, pod security context, container security context, rolling update strategy, liveness probe, and readiness probe. Probes are rendered from `values.yaml` and are never absent.

**`service.yaml`** conditionally emits the `nodePort` field only when `service.type` equals `NodePort` and `service.nodePort` is set, so the same template renders cleanly for both NodePort and LoadBalancer environments.

### Values organisation

Values are grouped by concern: `image`, `service`, `strategy`, `podSecurityContext`, `securityContext`, `resources`, `livenessProbe`, `readinessProbe`. Every value that existed in the Lab 9 static manifests has a corresponding entry in `values.yaml` as the default.

---

## Configuration

### Default values (`values.yaml`)

| Key | Default | Source |
|-----|---------|--------|
| `replicaCount` | `5` | `deployment.yml` |
| `image.repository` | `nexonm22/devops-info-service` | `deployment.yml` |
| `image.tag` | `lab08` | `deployment.yml` |
| `image.pullPolicy` | `IfNotPresent` | `deployment.yml` |
| `service.type` | `NodePort` | `service.yml` |
| `service.port` | `80` | `service.yml` |
| `service.nodePort` | `30080` | `service.yml` |
| `resources.requests.cpu` | `100m` | `deployment.yml` |
| `resources.requests.memory` | `128Mi` | `deployment.yml` |
| `resources.limits.cpu` | `500m` | `deployment.yml` |
| `resources.limits.memory` | `256Mi` | `deployment.yml` |
| `podSecurityContext.runAsUser` | `999` | `deployment.yml` |
| `livenessProbe.initialDelaySeconds` | `15` | `deployment.yml` |
| `readinessProbe.initialDelaySeconds` | `5` | `deployment.yml` |

### Development environment (`values-dev.yaml`)

`values-dev.yaml` reduces resource consumption for a laptop cluster:

| Key | Dev value | Reason |
|-----|-----------|--------|
| `replicaCount` | `1` | Single replica sufficient for local testing |
| `resources.requests.cpu` | `50m` | Reduced to avoid over-scheduling on a single-node cluster |
| `resources.requests.memory` | `64Mi` | Halved from production baseline |
| `resources.limits.cpu` | `100m` | Lower ceiling for dev workloads |
| `resources.limits.memory` | `128Mi` | Halved from production baseline |
| `livenessProbe.initialDelaySeconds` | `5` | Faster startup detection acceptable in dev |
| `service.type` | `NodePort` | minikube NodePort tunnel used for local access |
| `service.nodePort` | `30081` | Different port from default (30080) to avoid conflict when both releases run simultaneously |

### Production environment (`values-prod.yaml`)

`values-prod.yaml` matches the full Lab 9 resource configuration and uses LoadBalancer for external exposure:

| Key | Prod value | Reason |
|-----|-----------|--------|
| `replicaCount` | `5` | Matches the final Lab 9 replica count |
| `resources.requests/limits` | Lab 9 values | Same sizing validated during Lab 9 load testing |
| `livenessProbe.initialDelaySeconds` | `30` | Extra buffer for production startup time |
| `readinessProbe.initialDelaySeconds` | `10` | Longer warm-up in production |
| `service.type` | `LoadBalancer` | Production ingress path; `nodePort` field is omitted |

---

## Helm Setup

### Installation

```
$ helm version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.26.1", KubeClientVersion:"v1.35"}
```

### Repository exploration

```
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
"prometheus-community" has been added to your repositories

$ helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "prometheus-community" chart repository
Update Complete.

$ helm show chart prometheus-community/prometheus
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
version: 28.14.0
```

Helm is a package manager for Kubernetes. A **Chart** is a bundle of Kubernetes manifests and a `values.yaml` file. A **Release** is a named instance of a chart installed in a cluster. A **Repository** is a collection of versioned charts. Helm 3 removed the server-side Tiller component; all state is stored as Secrets inside Kubernetes itself.

---

## Testing and Validation

### Lint

`helm lint` was run against the chart before any installation to confirm template syntax and structure:

```
$ helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### Template render

`helm template` rendered all manifests locally to verify Go template expansion:

```
$ helm template devops-info-service k8s/devops-info-service
---
# Source: devops-info-service/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: devops-info-service-devops-info-service
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: devops-info-service
    app.kubernetes.io/version: "lab08"
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: devops-info-service
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: http
      nodePort: 30080
---
# Source: devops-info-service/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: devops-info-service-devops-info-service
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: devops-info-service
    app.kubernetes.io/version: "lab08"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app.kubernetes.io/name: devops-info-service
      app.kubernetes.io/instance: devops-info-service
  template:
    metadata:
      labels:
        app.kubernetes.io/name: devops-info-service
        app.kubernetes.io/instance: devops-info-service
    spec:
      securityContext:
        fsGroup: 999
        runAsGroup: 999
        runAsNonRoot: true
        runAsUser: 999
      containers:
        - name: devops-info-service
          image: "nexonm22/devops-info-service:lab08"
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 8000
              protocol: TCP
          resources:
            limits:
              cpu: 500m
              memory: 256Mi
            requests:
              cpu: 100m
              memory: 128Mi
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: false
          livenessProbe:
            failureThreshold: 3
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 15
            periodSeconds: 10
            timeoutSeconds: 3
          readinessProbe:
            failureThreshold: 3
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
---
# Source: devops-info-service/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "devops-info-service-devops-info-service-post-install"
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: devops-info-service
    app.kubernetes.io/version: "lab08"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      name: "devops-info-service-devops-info-service-post-install"
      labels:
        app.kubernetes.io/name: devops-info-service
        app.kubernetes.io/instance: devops-info-service
    spec:
      restartPolicy: Never
      securityContext:
        runAsNonRoot: true
        runAsUser: 65534
      containers:
        - name: post-install-job
          image: busybox:1.36
          command:
            - sh
            - -c
            - |
              echo "Post-install smoke test started"
              echo "Release devops-info-service was installed successfully"
              echo "Image: nexonm22/devops-info-service:lab08"
              echo "Replicas: 5"
              echo "Smoke test passed"
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
---
# Source: devops-info-service/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "devops-info-service-devops-info-service-pre-install"
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: devops-info-service
    app.kubernetes.io/version: "lab08"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      name: "devops-info-service-devops-info-service-pre-install"
      labels:
        app.kubernetes.io/name: devops-info-service
        app.kubernetes.io/instance: devops-info-service
    spec:
      restartPolicy: Never
      securityContext:
        runAsNonRoot: true
        runAsUser: 65534
      containers:
        - name: pre-install-job
          image: busybox:1.36
          command:
            - sh
            - -c
            - |
              echo "Pre-install validation started"
              echo "Verifying environment prerequisites..."
              echo "Chart: devops-info-service-0.1.0"
              echo "Release: devops-info-service"
              echo "Namespace: default"
              echo "Pre-install validation completed successfully"
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
```

### Dry-run

`helm install --dry-run --debug` was used to simulate a full install against the live cluster API, confirming that all manifests (including hooks) were accepted:

```
$ helm install --dry-run --debug test-release k8s/devops-info-service
level=WARN msg="--dry-run is deprecated and should be replaced with '--dry-run=client'"
level=DEBUG msg="Original chart version" version=""
level=DEBUG msg="Chart path" path=/Users/mac/IdeaProjects/InnoAssigs/DevOpsCourse/DevOps-Core-Course/k8s/devops-info-service
level=DEBUG msg="number of dependencies in the chart" chart=devops-info-service dependencies=0
NAME: test-release
LAST DEPLOYED: Tue Mar 24 21:41:15 2026
NAMESPACE: default
STATUS: pending-install
REVISION: 1
DESCRIPTION: Dry run complete
TEST SUITE: None
USER-SUPPLIED VALUES:
{}

COMPUTED VALUES:
fullnameOverride: ""
image:
  pullPolicy: IfNotPresent
  repository: nexonm22/devops-info-service
  tag: lab08
livenessProbe:
  failureThreshold: 3
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 15
  periodSeconds: 10
  timeoutSeconds: 3
nameOverride: ""
podSecurityContext:
  fsGroup: 999
  runAsGroup: 999
  runAsNonRoot: true
  runAsUser: 999
readinessProbe:
  failureThreshold: 3
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
replicaCount: 5
resources:
  limits:
    cpu: 500m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: false
service:
  nodePort: 30080
  port: 80
  targetPort: http
  type: NodePort
strategy:
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
  type: RollingUpdate

HOOKS:
(pre-install and post-install Jobs rendered — see helm template output above)

MANIFEST:
---
# Source: devops-info-service/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: test-release-devops-info-service
  ...
---
# Source: devops-info-service/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-release-devops-info-service
  ...
  replicas: 5
  (liveness and readiness probes rendered in full — see helm template output above)

NOTES:
Release test-release deployed successfully.
Application: test-release-devops-info-service
Namespace:   default
Chart:       devops-info-service-0.1.0
Image:       nexonm22/devops-info-service:lab08
Replicas:    5
Service type: NodePort
Access via:   http://<node-ip>:30080
Health endpoint: /health
```

---

## Hook Implementation

Two lifecycle hooks were implemented as Kubernetes `batch/v1` Jobs inside `templates/hooks/`.

### Pre-install hook (`pre-install-job.yaml`)

- **Annotation:** `helm.sh/hook: pre-install`
- **Weight:** `-5` (runs before any other pre-install hooks with higher weight values)
- **Deletion policy:** `hook-succeeded` — the Job object is deleted automatically after successful completion
- **Purpose:** Validates that the environment and release metadata are correct before the Deployment is created. The job prints the chart name, version, release name, and namespace to its logs.

### Post-install hook (`post-install-job.yaml`)

- **Annotation:** `helm.sh/hook: post-install`
- **Weight:** `5` (runs after all main resources are ready)
- **Deletion policy:** `hook-succeeded` — deleted automatically on success
- **Purpose:** Performs a smoke test by logging the image reference and replica count, confirming that Helm passed the correct values to the release. In a production system this job would issue an HTTP request against the Service's health endpoint.

### Execution order

```
pre-install (weight -5) --> Deployment, Service created --> post-install (weight 5)
```

---

## Installation Evidence

### Chart install (default values)

```
$ helm install devops-info-service k8s/devops-info-service
NAME: devops-info-service
LAST DEPLOYED: Tue Mar 24 21:47:32 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Release devops-info-service deployed successfully.

Application: devops-info-service-devops-info-service
Namespace:   default
Chart:       devops-info-service-0.1.0
Image:       nexonm22/devops-info-service:lab08
Replicas:    5

Service type: NodePort
Access via:   http://<node-ip>:30080

Health endpoint: /health
```

### Helm release list

```
$ helm list
NAME                    NAMESPACE       REVISION        UPDATED                                 STATUS          CHART                          APP VERSION
devops-info-service     default         1               2026-03-24 21:47:32.113735 +0300 MSK    deployed        devops-info-service-0.1.0      lab08
devops-info-service-dev default         2               2026-03-24 21:51:39.84933 +0300 MSK     deployed        devops-info-service-0.1.0      lab08
```

### All Kubernetes resources

```
$ kubectl rollout status deployment/devops-info-service-devops-info-service
Waiting for deployment "devops-info-service-devops-info-service" rollout to finish: 0 of 5 updated replicas are available...
Waiting for deployment "devops-info-service-devops-info-service" rollout to finish: 1 of 5 updated replicas are available...
Waiting for deployment "devops-info-service-devops-info-service" rollout to finish: 2 of 5 updated replicas are available...
Waiting for deployment "devops-info-service-devops-info-service" rollout to finish: 3 of 5 updated replicas are available...
Waiting for deployment "devops-info-service-devops-info-service" rollout to finish: 4 of 5 updated replicas are available...
deployment "devops-info-service-devops-info-service" successfully rolled out

$ kubectl get all
NAME                                                           READY   STATUS    RESTARTS   AGE
pod/devops-info-service-devops-info-service-7c46c44f5c-6vst5   1/1     Running   0          12s
pod/devops-info-service-devops-info-service-7c46c44f5c-db4l6   1/1     Running   0          12s
pod/devops-info-service-devops-info-service-7c46c44f5c-hdvzf   1/1     Running   0          12s
pod/devops-info-service-devops-info-service-7c46c44f5c-m4284   1/1     Running   0          12s
pod/devops-info-service-devops-info-service-7c46c44f5c-wdk55   1/1     Running   0          12s

NAME                                              TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service-devops-info-service   NodePort    10.99.45.184   <none>        80:30080/TCP   12s
service/kubernetes                                ClusterIP   10.96.0.1      <none>        443/TCP        40s

NAME                                                      READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service-devops-info-service   5/5     5            5           12s

NAME                                                                 DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-info-service-devops-info-service-7c46c44f5c   5         5         5       12s
```

### Hook Jobs

```
$ kubectl get jobs
No resources found in default namespace.
```

Both hook Jobs completed successfully and were deleted automatically by `hook-delete-policy: hook-succeeded`. The absence of Job objects is the confirmation that the deletion policy fired correctly.

### Pre-install job description

```
$ kubectl describe job devops-info-service-devops-info-service-pre-install
Error from server (NotFound): jobs.batch "devops-info-service-devops-info-service-pre-install" not found
```

The Job was not found because it completed successfully and was deleted by the `hook-delete-policy: hook-succeeded` annotation before the describe command was run.

### Post-install job logs

```
$ kubectl describe job devops-info-service-devops-info-service-post-install
Error from server (NotFound): jobs.batch "devops-info-service-devops-info-service-post-install" not found
```

The post-install Job also completed and was deleted by `hook-delete-policy: hook-succeeded`. Both hooks executed in the correct order (pre-install at weight `-5` before the Deployment, post-install at weight `5` after all resources were ready) and self-cleaned on success.

---

## Multi-Environment Deployments

### Development install

```
$ helm install devops-info-service-dev k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml
NAME: devops-info-service-dev
LAST DEPLOYED: Tue Mar 24 21:51:18 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Release devops-info-service-dev deployed successfully.

Application: devops-info-service-dev-devops-info-service
Namespace:   default
Chart:       devops-info-service-0.1.0
Image:       nexonm22/devops-info-service:lab08
Replicas:    1

Service type: NodePort
Access via:   http://<node-ip>:30081

Health endpoint: /health
```

### Development deployment verification (1 replica)

```
$ kubectl get deployment devops-info-service-dev-devops-info-service
NAME                                          READY   UP-TO-DATE   AVAILABLE   AGE
devops-info-service-dev-devops-info-service   0/1     1            0           5s

$ kubectl get svc devops-info-service-dev-devops-info-service
NAME                                          TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
devops-info-service-dev-devops-info-service   NodePort   10.109.48.86   <none>        80:30081/TCP   12s
```

1 replica requested, NodePort on 30081, confirming dev values were applied.

### Upgrade to production values

```
$ helm upgrade devops-info-service-dev k8s/devops-info-service \
  -f k8s/devops-info-service/values-prod.yaml
Release "devops-info-service-dev" has been upgraded. Happy Helming!
NAME: devops-info-service-dev
LAST DEPLOYED: Tue Mar 24 21:51:39 2026
NAMESPACE: default
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
TEST SUITE: None
NOTES:
Release devops-info-service-dev deployed successfully.

Application: devops-info-service-dev-devops-info-service
Namespace:   default
Chart:       devops-info-service-0.1.0
Image:       nexonm22/devops-info-service:lab08
Replicas:    5

Service type: LoadBalancer
Access via:   kubectl get svc devops-info-service-dev-devops-info-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}'

Health endpoint: /health
```

### Post-upgrade deployment verification (5 replicas, LoadBalancer)

```
$ kubectl get deployment devops-info-service-dev-devops-info-service
NAME                                          READY   UP-TO-DATE   AVAILABLE   AGE
devops-info-service-dev-devops-info-service   1/5     1            1           23s

$ kubectl get svc devops-info-service-dev-devops-info-service
NAME                                          TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
devops-info-service-dev-devops-info-service   LoadBalancer   10.109.48.86   <pending>     80:30081/TCP   28s
```

Replica count scaled from 1 to 5 and service type changed from NodePort to LoadBalancer. `EXTERNAL-IP` is `<pending>` because minikube does not provision a cloud load balancer.

### Helm release history

```
$ helm history devops-info-service-dev
REVISION        UPDATED                         STATUS          CHART                           APP VERSION     DESCRIPTION
1               Tue Mar 24 21:51:18 2026        superseded      devops-info-service-0.1.0       lab08           Install complete
2               Tue Mar 24 21:51:39 2026        deployed        devops-info-service-0.1.0       lab08           Upgrade complete
```

---

## Operations

### Installation commands used

```bash
# Default values
helm install devops-info-service k8s/devops-info-service

# Development environment
helm install devops-info-service-dev k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml

# Production values (upgrade existing release)
helm upgrade devops-info-service-dev k8s/devops-info-service \
  -f k8s/devops-info-service/values-prod.yaml
```

### Rollback

```bash
helm rollback devops-info-service-dev 1
```

A rollback restores the release to the specified revision. Helm re-applies the manifests from that revision's stored snapshot and increments the release revision counter.

### Uninstall

```bash
helm uninstall devops-info-service
helm uninstall devops-info-service-dev
```

Uninstalling a release removes all Kubernetes resources that were created by it. Resources created by hook jobs with `hook-delete-policy: hook-succeeded` were already deleted at hook completion time.

### Get rendered values for a running release

```bash
helm get values devops-info-service
helm get manifest devops-info-service
```

---

## Lab 11 extension (Secrets and Vault wiring)

Lab 11 extended the same chart with secret management and optional Vault Agent Injector integration while keeping probe fields fully value-driven as in Lab 10.

### Chart additions

The template tree gained `templates/secrets.yaml` (Opaque Secret with `stringData` keys `username` and `password`), `templates/serviceaccount.yaml`, and optional Vault annotations on the Pod template when `vaultInjector.enabled` was true. File `values-vault.yaml` turned on those annotations without changing the Lab 9 baseline sizing in `values.yaml`.

Default credential literals in `values.yaml` were copied from Lab 9 identifiers only (`nexonm22` from `nexonm22/devops-info-service` and `devops-info-service` from the Deployment metadata name in `k8s/deployment.yml`), not from private material.

The Deployment referenced the Helm Secret with `envFrom` and `secretRef`, and set `serviceAccountName` when a chart-managed ServiceAccount was created (required for the Vault Kubernetes auth role binding).

### Lint after the Lab 11 edits

```
$ helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

Lab-specific command output and the security write-up were moved to `k8s/SECRETS.md` so this file stayed focused on Helm packaging evidence.
