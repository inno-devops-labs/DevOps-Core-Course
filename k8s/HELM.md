# Lab 10 — Helm Package Manager

## 1. Chart Overview

### Helm value proposition
- Helm packages Kubernetes manifests as reusable charts.
- The same chart can be deployed in different environments via values overrides.
- Releases provide lifecycle control (install, upgrade, rollback, uninstall).
- Hooks allow operational logic to run around install/upgrade events.

### Chart structure

```text
k8s/devops-info/
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

### Key template files
- `templates/deployment.yaml`: app Deployment, probes, resources, env, rolling update strategy.
- `templates/service.yaml`: configurable service type/ports (`NodePort` or `LoadBalancer` pattern).
- `templates/_helpers.tpl`: reusable naming and labels helpers.
- `templates/hooks/pre-install-job.yaml`: pre-install validation hook job.
- `templates/hooks/post-install-job.yaml`: post-install smoke-check hook job.

### Values organization strategy
- `values.yaml`: sane defaults matching Lab 09 baseline.
- `values-dev.yaml`: lightweight development profile.
- `values-prod.yaml`: production-ready profile (more replicas/resources, LB service type).

---

## 2. Configuration Guide

### Important values
- `replicaCount`: controls Deployment replicas.
- `image.repository`, `image.tag`, `image.pullPolicy`: container image settings.
- `container.port`, `container.env`: runtime container port and environment variables.
- `service.type`, `service.port`, `service.targetPort`, `service.nodePort`: service networking.
- `resources.requests/limits`: CPU and memory budgets.
- `livenessProbe` / `readinessProbe`: health-check behavior (never disabled).
- `hooks.*`: hook enablement, job image, and pre-install command.

### Environment customization
- Dev profile (`values-dev.yaml`)
  - `replicaCount: 1`
  - relaxed resources (`50m/64Mi` requests)
  - `service.type: NodePort`
  - `image.tag: latest`
- Prod profile (`values-prod.yaml`)
  - `replicaCount: 4`
  - stronger resources (`200m/256Mi` requests, `500m/512Mi` limits)
  - `service.type: LoadBalancer`
  - `image.tag: v1.0.0`

### Installation examples

```bash
helm install devops-info-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml

helm install devops-info-prod k8s/devops-info -f k8s/devops-info/values-prod.yaml

helm upgrade devops-info-dev k8s/devops-info -f k8s/devops-info/values-prod.yaml
```

---

## 3. Hook Implementation

### Implemented hooks
- Pre-install hook:
  - Job name pattern: `<release>-pre-install`
  - Purpose: validation gate before resource install.
- Post-install hook:
  - Job name pattern: `<release>-post-install`
  - Purpose: run a smoke check against app health endpoint.

### Execution order and weights
- `pre-install` weight: `-5` (runs first).
- `post-install` weight: `5` (runs after install resources are created).

### Deletion policy
- Both jobs use:
  - `"helm.sh/hook-delete-policy": hook-succeeded`
- Result: successful hook Jobs are automatically cleaned up.

---

## 4. Installation Evidence

### Task 1 evidence (Helm fundamentals)

Helm installed and verified:

```bash
$ helm version --short
v4.1.3+gc94d381
```

Repository exploration:

```bash
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
"prometheus-community" already exists with the same configuration, skipping

$ helm repo update
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈

$ helm search repo prometheus-community/prometheus --versions | head -n 5
NAME                                     CHART VERSION  APP VERSION  DESCRIPTION
prometheus-community/prometheus          28.14.1        v3.10.0      Prometheus is a monitoring system...
prometheus-community/prometheus          28.14.0        v3.10.0      Prometheus is a monitoring system...
```

Public chart inspection:

```bash
$ helm show chart prometheus-community/prometheus
apiVersion: v2
name: prometheus
type: application
version: 28.14.1
appVersion: v3.10.0
```

### Task 2/3/4 evidence (chart rendering and dry-run)

Chart lint:

```bash
$ helm lint k8s/devops-info
==> Linting k8s/devops-info
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed
```

Environment renders:

```bash
$ helm template devops-info-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml | head
spec:
  type: NodePort

$ helm template devops-info-prod k8s/devops-info -f k8s/devops-info/values-prod.yaml | head
spec:
  type: LoadBalancer
```

Dry-run with hooks rendered:

```bash
$ helm install --dry-run=client --debug devops-info-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml
STATUS: pending-install
HOOKS:
  "helm.sh/hook": pre-install
  "helm.sh/hook-weight": "-5"
  "helm.sh/hook-delete-policy": hook-succeeded
  "helm.sh/hook": post-install
  "helm.sh/hook-weight": "5"
```

### Cluster runtime evidence (completed)

Cluster connectivity:

```bash
$ kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:56810
CoreDNS is running at https://127.0.0.1:56810/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

$ kubectl get nodes -o wide
NAME                  STATUS   ROLES           VERSION   INTERNAL-IP
lab09-control-plane   Ready    control-plane   v1.32.2   172.19.0.2
```

Dev install with hooks:

```bash
$ helm install devops-info-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml --wait=watcher --wait-for-jobs --timeout 5m
NAME: devops-info-dev
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

Hook execution output:

```bash
$ kubectl get jobs -n default -o wide
NAME                           STATUS    COMPLETIONS   DURATION   AGE   CONTAINERS           IMAGES
devops-info-dev-post-install   Running   0/1           3s         3s    post-install-check   busybox:1.36

$ kubectl describe job devops-info-dev-post-install -n default
Annotations:
  helm.sh/hook: post-install
  helm.sh/hook-delete-policy: hook-succeeded
  helm.sh/hook-weight: 5
Events:
  Normal  SuccessfulCreate  3s  job-controller  Created pod: devops-info-dev-post-install-kznx7

$ kubectl get events -n default --sort-by=.metadata.creationTimestamp | rg 'devops-info-dev-(pre-install|post-install)|Completed'
4m29s  Normal  Completed  job/devops-info-dev-pre-install   Job completed
4m16s  Normal  Completed  job/devops-info-dev-post-install  Job completed

$ kubectl get jobs -n default
No resources found in default namespace.
```

Evidence of dev -> prod upgrade:

```bash
$ helm upgrade devops-info-dev k8s/devops-info -f k8s/devops-info/values-prod.yaml --wait=watcher --timeout 5m
$ helm history devops-info-dev -n default
REVISION  STATUS      DESCRIPTION
1         superseded  Install complete
2         deployed    Upgrade complete

$ helm get values devops-info-dev -n default
replicaCount: 4
service:
  type: LoadBalancer
image:
  tag: v1.0.0

$ kubectl get deployment devops-info-dev -n default -o wide
NAME              READY   UP-TO-DATE   AVAILABLE   CONTAINERS    IMAGES
devops-info-dev   4/4     4            4           devops-info   devops_lab02:v1.0.0

$ kubectl get svc devops-info-dev -n default -o wide
NAME              TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)
devops-info-dev   LoadBalancer   10.96.42.221    <pending>     80:30080/TCP
```

Release/resource state:

```bash
$ helm list -A
NAME             NAMESPACE  REVISION  STATUS    CHART             APP VERSION
devops-info-dev  default    2         deployed  devops-info-0.1.0 cilc

$ kubectl get all -n default
deployment.apps/devops-info-dev   4/4
service/devops-info-dev           LoadBalancer
```

Application accessibility verification:

```bash
$ kubectl port-forward service/devops-info-dev -n default 18080:80
$ curl -sS http://127.0.0.1:18080/health
{"status":"healthy","timestamp":"2026-03-29T10:19:59.602429+00:00","uptime_seconds":83}
```

---

## 5. Operations

### Installation commands used

```bash
helm install devops-info-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml --wait=watcher --wait-for-jobs --timeout 5m
```

### Upgrade

```bash
helm upgrade devops-info-dev k8s/devops-info -f k8s/devops-info/values-prod.yaml --wait=watcher --timeout 5m
```

### Rollback

```bash
helm history devops-info-dev
helm rollback devops-info-dev <REVISION>
```

### Uninstall

```bash
helm uninstall devops-info-dev
```

---

## 6. Testing & Validation

### Commands used

```bash
helm lint k8s/devops-info
helm template devops-info-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml
helm template devops-info-prod k8s/devops-info -f k8s/devops-info/values-prod.yaml
helm install --dry-run=client --debug devops-info-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml
helm install --dry-run=client --debug devops-info-prod k8s/devops-info -f k8s/devops-info/values-prod.yaml
```

### Validation summary
- Helm chart is syntactically valid (`helm lint` passed).
- Dev/prod values render distinct manifests as expected.
- Pre-install/post-install hooks render correctly with weights and delete policy.
- Hook lifecycle verified in cluster (`kubectl get jobs`, `kubectl describe job`, completion events, auto-deletion).
- Dev-to-prod upgrade verified (`replicas=4`, image `devops_lab02:v1.0.0`, service type `LoadBalancer`).
- Application accessibility verified via port-forward and `/health` response.
